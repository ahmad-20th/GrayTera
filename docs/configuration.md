# Configuration Reference

## Overview

GrayTera uses YAML-based configuration with sensible defaults. This guide covers all available settings and their effects.

## Configuration File Location

Default: `config.yaml` in project root

Override via command line:
```bash
python main.py example.com --config /path/to/custom_config.yaml
```

## Configuration Structure

### Subdomain Enumeration

```yaml
subdomain_enum:
  # Maximum time (seconds) for enumeration phase
  timeout: 10
  
  # Maximum subdomains to discover before stopping
  max_subdomains: 1000
  
  # Enable specific enumeration strategies
  use_dns: true           # DNS wordlist + reverse DNS
  use_crt_sh: true        # Certificate Transparency logs
  use_dorking: false      # Google dorking (slower)
  
  # DNS Enumeration Configuration
  dns:
    threads: 10           # Concurrent DNS queries
    wordlist: wordlists/subdomains.txt  # Subdomain wordlist
  
  # Certificate Transparency Configuration
  ct:
    timeout: 20           # Seconds for CT queries
  
  # Google Dorking Configuration
  dork:
    pages: 5              # Number of search result pages
    timeout: 10           # Seconds per page
  
  # Common subdomains always checked
  common_subdomains:
    - www
    - mail
    - ftp
    - admin
    - blog
    - dev
    - api
```

**Performance Notes:**
- Increasing `threads` speeds up DNS enumeration but increases network load
- Larger wordlist increases coverage but slows enumeration
- Google dorking is disabled by default (slower, requires API credentials)

### Scope Filtering

```yaml
scope_filtering:
  enabled: true
  # Scope file specified via --scope argument, e.g.:
  # python main.py example.com --scope scope.json
```

**Scope File Format:**
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
      "staging.example.com"
    ],
    "patterns": [
      ".*-test\\.example\\.com$"
    ]
  }
}
```

### Vulnerability Scanning

```yaml
vulnerability_scan:
  # Concurrent worker threads for scanning
  threads: 10            # Recommended: 2-20
  
  # Total timeout for scanning phase
  timeout: 30            # Seconds
  
  # Maximum crawl depth for applications
  max_depth: 3
  
  # Follow HTTP redirects
  follow_redirects: true
  
  # SQL Injection Scanner
  sqli:
    enabled: true        # Enable SQLi detection
    timeout: 30          # Per-target timeout
    payloads_file: payloads/sqli_strategies.yaml
    detect_waf: true     # Detect WAF presence
  
  # Nikto Web Server Scanner
  nikto:
    enabled: false       # Disabled by default (slower)
    nikto_path: null     # Auto-detect from PATH if null
    timeout: 30          # Per-target timeout
  
  # OWASP ZAP Integration
  zap:
    enabled: false       # Requires ZAP daemon running
    api_key: 'YOUR_API_KEY'
    proxy_url: 'http://127.0.0.1:8080'
    spider_enabled: true
    active_scan_enabled: true
    max_depth: 2
    max_children: 5
```

**Thread Configuration Guide:**
- Low-resource systems: 2-5 threads
- Standard systems: 10 threads
- High-capacity systems: 10-20 threads
- **Caution**: Excessive threads may trigger rate limiting

### Exploitation

```yaml
exploitation:
  # Automatic exploitation without confirmation
  auto_exploit: false    # false = manual confirmation required
  
  # Maximum exploitation attempts per vulnerability
  max_attempts: 3
  
  # Total timeout for exploitation phase
  timeout: 60            # Seconds per vulnerability
  
  # SQLMap Integration
  sqlmap:
    path: null           # null = auto-detect from PATH
    level: 5             # 1-5 (higher = more comprehensive)
    risk: 3              # 1-3 (higher = more aggressive)
    threads: 10
    timeout: 600         # 10 minutes
    crawl_depth: 3
  
  # SQLi Exploitation Settings
  sqli:
    extract_tables: true
    extract_users: false # Disabled for safety
    max_rows: 10         # Limit data extraction
```

**SQLMap Level/Risk Explanation:**

| Level | Description |
|-------|-------------|
| 1 | Basic tests (fast) |
| 2 | Moderate tests |
| 3 | Comprehensive tests |
| 4 | Advanced tests |
| 5 | All tests (slowest) |

| Risk | Description |
|-----|-------------|
| 1 | Non-destructive (safe) |
| 2 | Moderate risk |
| 3 | Aggressive (may disrupt service) |

### Retry Configuration

```yaml
retry:
  # Maximum retry attempts on failure
  max_retries: 3
  
  # Backoff multiplier between retries
  backoff_factor: 2
  
  # HTTP status codes triggering retry
  retry_on_status:
    - 500
    - 502
    - 503
    - 504
```

### Output Configuration

```yaml
output:
  # Format for exported reports
  save_format: json      # json = default
  
  # Include raw HTTP requests in reports
  include_raw_requests: false
  
  # Include screenshots (if available)
  include_screenshots: false
```

### Logging Configuration

```yaml
logging:
  # Logging level
  level: INFO            # DEBUG, INFO, WARNING, ERROR
  
  # Log file location
  file: data/logs/graytera.log
  
  # Also log to console
  console: true
```

## Environment Variables

Override configuration via environment variables:

```bash
# SQLMap location
export SQLMAP_PATH="/usr/local/bin/sqlmap"

# Custom wordlist
export WORDLIST_PATH="/path/to/custom_subdomains.txt"

# Proxy (if behind corporate proxy)
export HTTP_PROXY="http://proxy:8080"
export HTTPS_PROXY="http://proxy:8080"
```

## Command-Line Overrides

Override specific settings via CLI:

```bash
# Run specific stage
python main.py example.com --stage enum

# Use custom config
python main.py example.com --config custom.yaml

# Apply scope filtering
python main.py example.com --scope scope.json

# Custom output directory
python main.py example.com --output /path/to/results

# Enable debug logging
python main.py example.com --debug

# Interactive mode (pause between stages)
python main.py example.com --interactive
```

## Performance Tuning

### For Speed (Quick Scan)

```yaml
subdomain_enum:
  timeout: 5
  use_dork: false
  dns:
    threads: 20

vulnerability_scan:
  threads: 20
  timeout: 15
  sqli:
    timeout: 10
```

### For Thoroughness (Deep Scan)

```yaml
subdomain_enum:
  timeout: 30
  use_dork: true
  dns:
    threads: 10

vulnerability_scan:
  threads: 10
  timeout: 60
  sqli:
    timeout: 30
  nikto:
    enabled: true
  
exploitation:
  timeout: 120
  sqlmap:
    level: 5
    risk: 3
```

### For Resource-Constrained Environments

```yaml
subdomain_enum:
  max_subdomains: 100
  dns:
    threads: 2

vulnerability_scan:
  threads: 2
  timeout: 20
  nikto:
    enabled: false
  zap:
    enabled: false

exploitation:
  timeout: 30
  sqlmap:
    timeout: 300
```

## Security-Focused Configuration

```yaml
exploitation:
  auto_exploit: false    # Require manual approval
  max_attempts: 1        # Single attempt only
  
  sqli:
    extract_users: false # Never extract user data
    extract_tables: false # Never extract table data
```

## Validation

GrayTera validates configuration on startup:

- File existence checks
- Type validation for all settings
- Range validation (threads, timeouts)
- Required field presence
- Invalid configuration warnings

## Default Configuration

If `config.yaml` is missing or invalid, GrayTera uses built-in defaults suitable for most scenarios.

View defaults in: [core/pipeline.py](../core/pipeline.py) - `_default_config()` method

## Configuration Examples

### Minimal Configuration (Fast)
```yaml
subdomain_enum:
  timeout: 5
  use_crt_sh: false

vulnerability_scan:
  threads: 5
  timeout: 10
  sqli:
    timeout: 10
```

### Standard Configuration (Balanced)
Uses defaults - see `config.yaml`

### Comprehensive Configuration (Thorough)
```yaml
subdomain_enum:
  timeout: 30
  use_crt_sh: true
  use_dorking: true

vulnerability_scan:
  threads: 10
  timeout: 60
  nikto:
    enabled: true

exploitation:
  auto_exploit: false
  sqlmap:
    level: 5
```

## Troubleshooting Configuration

**Problem**: Enumeration too slow
- Solution: Reduce `subdomain_enum.timeout`, increase `dns.threads`

**Problem**: Scanner skipped (says "not found")
- Solution: Check `nikto_path` in config, verify tool is installed

**Problem**: Out of memory
- Solution: Reduce `max_subdomains`, decrease `threads`

**Problem**: Rate limited by target
- Solution: Reduce `threads`, increase `timeout`, disable aggressive scanners

**Problem**: SQLMap not found
- Solution: Set `SQLMAP_PATH` environment variable or specify in config