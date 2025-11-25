# Scope Filtering - Quick Start Guide

## Overview
GrayTera now supports scope filtering to ensure enumerated subdomains are validated against your pentest scope before scanning.

## Quick Start

### 1. Create a scope.json file

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
      "^prod-[a-z0-9-]+\\.example\\.com$"
    ]
  },
  "out_of_scope": {
    "domains": [
      "test.example.com",
      "staging.example.com"
    ],
    "patterns": [
      ".*-dev\\.example\\.com$"
    ]
  }
}
```

### 2. Run GrayTera with scope file

```bash
python main.py example.com --scope scope.json
```

### 3. Review filtered results

The console output will show:
- ✓ In-scope subdomains that proceed to scanning
- ✗ Out-of-scope subdomains that are filtered out

Example output:
```
[12:34:56] [+] Subdomain: api.example.com
[12:34:56] [-] Out-of-scope: test.example.com
[12:35:10] [Scope Filtering] 10 in-scope subdomains remaining
```

## Scope Format Reference

### in_scope.domains
- **Exact match**: `example.com` matches only `example.com`
- **Wildcard**: `*.api.example.com` matches any subdomain of `api.example.com`
- **Implicit subdomain**: `api.example.com` matches `api.example.com` AND any subdomain like `v1.api.example.com`

### in_scope.patterns
- Regex patterns for complex matching
- Example: `^prod-[a-z0-9-]+\\.example\\.com$` matches `prod-api.example.com`, `prod-db-001.example.com`, etc.

### out_of_scope
- Same format as in_scope
- Takes precedence - explicitly excluded from scanning
- Use for test/staging/dev environments

## Common Scenarios

### Single Domain Target
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

### Multi-subdomain with Exclusions
```json
{
  "in_scope": {
    "domains": [
      "api.example.com",
      "web.example.com",
      "*.internal.example.com"
    ],
    "patterns": []
  },
  "out_of_scope": {
    "domains": [
      "dev.example.com",
      "test.example.com"
    ],
    "patterns": []
  }
}
```

### Production-only with Regex
```json
{
  "in_scope": {
    "domains": [],
    "patterns": [
      "^prod-[a-z0-9-]+\\.example\\.com$",
      "^api\\.example\\.com$"
    ]
  },
  "out_of_scope": {
    "domains": ["staging.example.com", "dev.example.com"],
    "patterns": []
  }
}
```

## Usage Examples

### Run enumeration only (no scope filtering)
```bash
python main.py example.com --stage enum
```

### Run with scope file
```bash
python main.py example.com --scope scope.json
```

### Run specific stage with scope
```bash
python main.py example.com --scope scope.json --stage scan
```

## Pipeline Flow

```
1. Enumeration    → Discovers subdomains (DNS, CT, Dork)
2. Scope Filter   → Compares against scope.json
3. Vulnerability  → Scans only in-scope subdomains
4. Exploitation   → Exploits vulnerabilities
```

## Tips & Best Practices

✓ **Always verify scope** - Review scope.json before running  
✓ **Test patterns** - Use online regex tester to validate patterns  
✓ **Be explicit about exclusions** - Add test/staging/dev domains to out_of_scope  
✓ **Use patterns for flexibility** - Regex patterns handle complex subdomain patterns  
✓ **Check file permissions** - Ensure scope.json is readable  
✓ **HackerOne integration** - Copy domains directly from your H1 scope page  

## Troubleshooting

**Q: All subdomains are being filtered out**  
A: Check your in_scope domains are correct. Run with `--stage enum` to see all discovered subdomains.

**Q: Out-of-scope subdomains are still being scanned**  
A: Verify they match a domain or pattern in out_of_scope section.

**Q: Scope file not found**  
A: Check file path is correct and file exists:
```bash
ls -la scope.json
python -m json.tool scope.json  # Validate JSON
```

## Advanced Usage

For programmatic use:
```python
from utils.scope_filter import ScopeFilter

scope = ScopeFilter('scope.json')
is_in_scope = scope.is_in_scope('api.example.com')
in_scope, out_of_scope = scope.filter_subdomains(subdomains_list)
```

For complete documentation, see: `SCOPE_FILTERING.md`

## Example scope.json from HackerOne

1. Go to your HackerOne program's "Scope" page
2. Create scope.json with discovered assets:

```json
{
  "in_scope": {
    "domains": [
      "api.myprogram.com",
      "web.myprogram.com",
      "*.internal.myprogram.com"
    ],
    "patterns": []
  },
  "out_of_scope": {
    "domains": [
      "test.myprogram.com",
      "staging.myprogram.com"
    ],
    "patterns": []
  }
}
```

3. Run with: `python main.py myprogram.com --scope scope.json`
