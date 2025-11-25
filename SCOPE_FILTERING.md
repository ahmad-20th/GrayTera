# Scope Filtering Feature Documentation

## Overview

The Scope Filtering feature allows pentesters to define and enforce engagement scope when running GrayTera. This ensures that enumerated subdomains are filtered against the authorized scope before vulnerability scanning begins.

## Use Cases

- **HackerOne Integration**: Define scope from HackerOne bug bounty programs
- **Pentest Contracts**: Filter results to only in-scope subdomains as defined by the contract
- **Multi-domain Targets**: Handle complex scope with exact domains, wildcards, and regex patterns
- **Out-of-scope Discovery**: Log and report discovered but out-of-scope assets

## Scope File Format

The scope file is a JSON file that defines in-scope and out-of-scope domains:

```json
{
  "in_scope": {
    "domains": [
      "example.com",
      "www.example.com",
      "api.example.com",
      "*.internal.example.com"
    ],
    "patterns": [
      "^[a-z0-9-]+\\.example\\.com$"
    ]
  },
  "out_of_scope": {
    "domains": [
      "test.example.com",
      "staging.example.com",
      "dev.example.com"
    ],
    "patterns": [
      ".*-test\\.example\\.com$",
      ".*\\.staging\\.example\\.com$"
    ]
  }
}
```

### Field Descriptions

#### `in_scope`
- **domains**: List of exact or wildcard domains that are authorized for testing
  - Exact: `example.com`, `www.example.com`
  - Wildcard: `*.internal.example.com` (matches any subdomain)
  - Subdomain matching: `api.example.com` matches `api.example.com` and `*.api.example.com`

- **patterns**: List of regex patterns for complex matching (optional)
  - Patterns are matched against lowercased FQDNs
  - Example: `^[a-z0-9-]+\\.example\\.com$` matches `anything.example.com`

#### `out_of_scope`
- **domains**: Explicitly excluded domains (takes precedence over in_scope)
- **patterns**: Explicitly excluded patterns (takes precedence)

## Usage

### Basic Usage

```bash
# Run with scope filtering
python main.py example.com --scope scope.json

# Run without scope filtering (enumeration only)
python main.py example.com
```

### Creating a Scope File from HackerOne

1. Navigate to your HackerOne program page
2. Find the "Scope" section
3. Copy all in-scope domains and create a `scope.json` file:

```json
{
  "in_scope": {
    "domains": [
      "api.yourprogram.com",
      "*.internal.yourprogram.com",
      "mobile-backend.yourprogram.com"
    ],
    "patterns": []
  },
  "out_of_scope": {
    "domains": [
      "test.yourprogram.com",
      "staging.yourprogram.com"
    ],
    "patterns": []
  }
}
```

## Pipeline Integration

The scope filtering stage is integrated into the pipeline as follows:

```
SubdomainEnumStage
        ↓
ScopeFilteringStage ← NEW
        ↓
VulnerabilityScanStage
        ↓
ExploitationStage
```

### Stage Behavior

1. **Enumeration**: SubdomainEnumStage discovers subdomains using DNS, Certificate Transparency, and dorking
2. **Filtering**: ScopeFilteringStage compares discovered subdomains against scope.json
3. **Scanning**: Only in-scope subdomains proceed to vulnerability scanning
4. **Logging**: Filtered out-of-scope subdomains are logged in metadata

## Observer Integration

The scope filtering stage integrates with the observer pattern:

```
ConsoleObserver:
  - [+] Subdomain: in-scope-subdomain.com
  - [-] Out-of-scope: out-of-scope-subdomain.com

FileObserver:
  - Logs all filtering activities in JSON output
  - Includes filtered_subdomains in target metadata
```

## API Usage

### ScopeFilter Class

```python
from utils.scope_filter import ScopeFilter

# Load scope from file
scope = ScopeFilter('scope.json')

# Check if a subdomain is in scope
if scope.is_in_scope('api.example.com'):
    print("Proceed with scanning")

# Filter a list of subdomains
in_scope, out_of_scope = scope.filter_subdomains([
    'api.example.com',
    'staging.example.com',
    'test.example.com'
])

# Get scope statistics
stats = scope.get_stats()
print(f"In-scope domains: {stats['in_scope_domains']}")
print(f"Out-of-scope domains: {stats['out_of_scope_domains']}")
print(f"Patterns: {stats['patterns']}")
```

### ScopeFilteringStage Class

```python
from stages.scope_filtering import ScopeFilteringStage
from core.target import Target

# Create filtering stage
stage = ScopeFilteringStage({}, scope_file='scope.json')

# Execute filtering
target = Target(domain='example.com')
target.subdomains = ['api.example.com', 'test.example.com', ...]
stage.execute(target)

# Check results
print(f"In-scope: {len(target.subdomains)}")
print(f"Filtered out: {target.metadata['filtered_subdomains']}")
```

## Output and Reporting

### Console Output Example

```
[12:34:56] [Subdomain Enumeration] Started
[12:34:56] [+] Subdomain: api.example.com
[12:34:56] [+] Subdomain: test.example.com
[12:34:56] [+] Subdomain: staging.example.com
[12:35:10] [Subdomain Enumeration] 3 subdomains found

[12:35:10] [Scope Filtering] Started
[12:35:10] [-] Out-of-scope: test.example.com
[12:35:10] [-] Out-of-scope: staging.example.com
[12:35:10] [Scope Filtering] Filtered out 2 out-of-scope subdomains
[12:35:10] [Scope Filtering] 1 in-scope subdomains remaining

[12:35:10] [Vulnerability Scanning] Started
[12:35:10] [Vulnerability Scanning] Scanning 1 subdomains
```

### JSON Output

The file observer includes scope filtering details:

```json
{
  "domain": "example.com",
  "subdomains": ["api.example.com"],
  "filtered_subdomains": ["test.example.com", "staging.example.com"],
  "metadata": {
    "scope_stats": {
      "loaded": true,
      "in_scope_domains": 3,
      "out_of_scope_domains": 3,
      "patterns": 2
    }
  },
  "vulnerabilities": [...]
}
```

## Best Practices

1. **Always verify scope before running**: Review the scope.json file before pentesting
2. **Use patterns for flexibility**: Regex patterns can match complex subdomain patterns
3. **Explicit out-of-scope**: Always list out-of-scope domains explicitly to be safe
4. **Test scope configuration**: Run with `--stage enum` first to verify scope matches your expectations
5. **Keep scope updated**: If scope changes during the engagement, update scope.json and rerun

## Troubleshooting

### Issue: All subdomains filtered out

**Solution**: Review your scope.json to ensure in_scope domains are correctly defined:
- Check for typos in domain names
- Ensure wildcard domains are properly formatted (e.g., `*.example.com`)
- Verify domain case (matching is case-insensitive but worth checking)

### Issue: Out-of-scope subdomains being scanned

**Solution**: The out_of_scope section takes precedence. Ensure:
- The subdomain is listed in out_of_scope.domains or matches a pattern
- Regex patterns are correct (test with an online regex tester)

### Issue: Scope file not being loaded

**Solution**: Verify the file exists and is valid JSON:
```bash
python -m json.tool scope.json  # Validate JSON
ls -la scope.json                # Check file exists
```

## Examples

### Example 1: Simple Single Domain

```json
{
  "in_scope": {
    "domains": ["example.com"],
    "patterns": []
  },
  "out_of_scope": {
    "domains": [],
    "patterns": []
  }
}
```

### Example 2: Subdomain Wildcard

```json
{
  "in_scope": {
    "domains": ["*.api.example.com"],
    "patterns": []
  },
  "out_of_scope": {
    "domains": ["test.api.example.com"],
    "patterns": []
  }
}
```

### Example 3: Complex with Regex

```json
{
  "in_scope": {
    "domains": ["example.com"],
    "patterns": [
      "^[a-z0-9-]+\\.example\\.com$",
      "^prod-[a-z0-9]+\\.internal\\.com$"
    ]
  },
  "out_of_scope": {
    "domains": ["dev.example.com", "staging.example.com"],
    "patterns": [
      ".*-test\\.example\\.com$",
      "^internal-[0-9]+\\.internal\\.com$"
    ]
  }
}
```

## Files Modified/Added

- **New**: `/utils/scope_filter.py` - Core scope filtering logic
- **New**: `/stages/scope_filtering.py` - ScopeFilteringStage implementation
- **New**: `/scope.json.example` - Example scope configuration
- **Modified**: `/core/pipeline.py` - Integrated ScopeFilteringStage
- **Modified**: `/main.py` - Added --scope CLI argument
- **Modified**: `/config.yaml` - Added scope_filtering configuration section
- **Modified**: `/observers/console_observer.py` - Added filtered_subdomain event handling

## Future Enhancements

- HackerOne API integration to auto-fetch scope
- Bugcrowd scope format support
- Intigriti scope format support
- Scope violation alerts
- Automatic scope file generation from target domain whois records
