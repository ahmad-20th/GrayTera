# Scanner Reference Guide

## Overview

GrayTera includes multiple vulnerability scanners, each designed for specific vulnerability types. Scanners can be enabled/disabled and configured independently.

## SQL Injection Scanner

### Overview

Detects SQL injection vulnerabilities across multiple techniques:
- Union-based injection
- Boolean-based blind injection
- Time-based blind injection
- Error-based injection
- Stacked queries

### Configuration

```yaml
vulnerability_scan:
  sqli:
    enabled: true
    timeout: 30
    payloads_file: payloads/sqli_strategies.yaml
    detect_waf: true
```

### Parameters Tested

- URL query parameters
- POST body parameters
- HTTP headers (Cookie, User-Agent, etc.)
- JSON body fields
- XML attributes

### Payload Strategies

Located in `payloads/sqli_strategies.yaml`:

1. **UNION-based Detection**
   - Identifies column count via ORDER BY
   - Tests UNION SELECT statements
   - Fast, usually successful against vulnerable targets

2. **Boolean-based Blind**
   - Uses conditional logic to infer data
   - Slower but works through filtering
   - Example: `' AND 1=1--` vs `' AND 1=2--`

3. **Time-based Blind**
   - Uses database sleep functions
   - Works when output is filtered
   - Example: `' AND SLEEP(5)--`

4. **Error-based Injection**
   - Extracts data through error messages
   - Fast and reliable when enabled
   - Example: `' AND extractvalue(0,version())--`

### Example Vulnerable Endpoints

```
http://target.com/product.php?id=1
http://target.com/search?query=test
http://target.com/login.php (POST: username, password)
```

### Limitations

- Requires at least one testable parameter
- Some WAF/filters may block payloads
- Time-based is slower (must wait for timeouts)
- Database type must be inferred or guessed

### Performance Notes

- Base detection: ~5-10 seconds
- Deep analysis: ~20-30 seconds
- Timeout on non-vulnerable targets
- Early exit when vulnerability found

## Nikto Web Server Scanner

### Overview

Comprehensive web server and application vulnerability scanner:
- Known vulnerability detection
- Dangerous file detection
- CGI scripts auditing
- Server misconfiguration detection
- Outdated software detection

### Configuration

```yaml
vulnerability_scan:
  nikto:
    enabled: false  # Disabled by default (slower)
    nikto_path: null  # Auto-detect from PATH
    timeout: 30
```

### Installation

```bash
# Debian/Ubuntu
sudo apt-get install nikto

# From source
git clone https://github.com/sullo/nikto
cd nikto/program
perl nikto.pl -h target.com
```

### Features

- Multi-threaded scanning
- SSL/HTTPS support
- Proxy support
- Custom port scanning
- Version detection
- Cookie/header customization

### Example Output

```
Target: http://example.com:80
Found 5 potential security vulnerabilities:
  - Default CGI files
  - Web server disclosure
  - Outdated PHP version
  - Known vulnerable plugins
  - Directory indexing enabled
```

### Performance Considerations

- Slower than SQLi scanner (intrusive testing)
- Generates multiple HTTP requests
- Can trigger IDS/WAF alerts
- Recommended for authorized testing only

## OWASP ZAP Scanner

### Overview

Enterprise-grade vulnerability scanner:
- Passive scanning
- Active scanning
- API security testing
- AJAX application support

### Configuration

```yaml
vulnerability_scan:
  zap:
    enabled: false
    api_key: 'YOUR_API_KEY'
    proxy_url: 'http://127.0.0.1:8080'
    spider_enabled: true
    active_scan_enabled: true
    max_depth: 2
    max_children: 5
```

### Prerequisites

```bash
# Install ZAP (Java required)
sudo apt-get install zaproxy

# Start ZAP daemon
zaproxy -daemon -port 8080 -config api.key=abc123
```

### Supported Vulnerability Types

- SQL Injection
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Path Traversal
- Remote Command Execution
- And 70+ others

### Performance Notes

- Slowest scanner (comprehensive)
- Requires daemon running
- High memory footprint
- Best for comprehensive assessments

## Custom Scanner Extension

### Creating a Scanner Plugin

```python
# scanners/custom_scanner.py
from scanners.base_scanner import BaseScanner
from core.target import Vulnerability

class CustomScanner(BaseScanner):
    def __init__(self):
        super().__init__("Custom Scanner")
    
    def scan(self, target_url: str) -> List[Vulnerability]:
        """
        Scan target and return vulnerabilities
        
        Args:
            target_url: Full URL to scan (e.g., http://example.com/page.php?id=1)
        
        Returns:
            List of Vulnerability objects found
        """
        vulnerabilities = []
        
        try:
            # Your scanning logic here
            # Example: test for specific vulnerability
            response = self._make_request(target_url)
            
            if self._is_vulnerable(response):
                vuln = Vulnerability(
                    vuln_type='custom_vuln',
                    severity='high',
                    url=target_url,
                    parameter='custom_param',
                    payload='custom_payload',
                    evidence='Vulnerability evidence here',
                    timestamp=datetime.now()
                )
                vulnerabilities.append(vuln)
        
        except Exception as e:
            self.logger.error(f"Scan failed: {e}")
        
        return vulnerabilities
```

### Registering Scanner

```python
# scanners/scanner_registry.py
from scanners.custom_scanner import CustomScanner

registry.register("custom", CustomScanner())
```

### Enabling Scanner

```yaml
# config.yaml
vulnerability_scan:
  custom:
    enabled: true
    timeout: 30
```

## Scanner Comparison Matrix

| Feature | SQLi Scanner | Nikto | ZAP |
|---------|-------------|-------|-----|
| Speed | Fast | Medium | Slow |
| Detection Types | SQLi only | 70+ types | 70+ types |
| False Positives | Low | Medium | Low |
| Configuration | Simple | Medium | Complex |
| Resource Usage | Low | Medium | High |
| Active Scanning | Yes | Yes | Yes |
| Default Enabled | Yes | No | No |

## Scanner Selection Guide

### Use SQLi Scanner When:
- Testing web applications with database backends
- Need fast vulnerability detection
- Resources are limited
- Focusing on SQL injection assessment

### Use Nikto When:
- Performing comprehensive web server assessment
- Need to detect known vulnerabilities
- Scanning for configuration issues
- Testing older applications

### Use ZAP When:
- Enterprise-grade assessment required
- Testing modern web applications/APIs
- Need detailed vulnerability reporting
- Running automated security testing pipelines

## Troubleshooting Scanners

### SQLi Scanner Issues

**Problem**: Scanner reports "Parameter not found"
- **Solution**: Target may not have testable parameters, try different endpoints

**Problem**: All tests timeout
- **Solution**: Increase timeout in config, check target responsiveness

**Problem**: False positives/negatives
- **Solution**: Adjust payload strategies in YAML file, test manually

### Nikto Scanner Issues

**Problem**: "Nikto not found"
- **Solution**: Install with `apt-get install nikto` or set `nikto_path` in config

**Problem**: Scanner hangs
- **Solution**: Reduce timeout, check target responsiveness

### ZAP Scanner Issues

**Problem**: "Cannot connect to ZAP daemon"
- **Solution**: Start ZAP with: `zaproxy -daemon -port 8080`

**Problem**: Slow scanning
- **Solution**: Reduce `max_depth` and `max_children` in config

## Performance Tuning

### For Speed

```yaml
vulnerability_scan:
  sqli:
    timeout: 10    # Reduced from 30
  nikto:
    enabled: false # Disable slower scanners
```

### For Accuracy

```yaml
vulnerability_scan:
  sqli:
    timeout: 60    # Increased timeout
  nikto:
    enabled: true  # Enable all scanners
  zap:
    enabled: true
    max_depth: 3   # More thorough crawling
```

## Payload Management

Payloads are defined in YAML files under `payloads/`:

- `sqli_strategies.yaml`: Standard SQLi payloads
- `blind_sqli_advanced.yaml`: Advanced blind SQLi techniques

### Custom Payloads

Create custom payload files:

```yaml
# payloads/custom_payloads.yaml
strategies:
  - name: custom_injection
    description: "Custom injection technique"
    target: query
    detection:
      type: length_delta
      min_delta: 100
    payloads:
      - "' CUSTOM_PAYLOAD --"
      - "' CUSTOM_PAYLOAD /*"
```

Configure in `config.yaml`:
```yaml
vulnerability_scan:
  sqli:
    payloads_file: payloads/custom_payloads.yaml
```

## Best Practices

1. **Start with SQLi Scanner**: Fast, focused detection
2. **Add Nikto if needed**: For web server assessment
3. **Use ZAP for comprehensive scans**: Complete vulnerability coverage
4. **Respect target limitations**: Adjust threads and timeouts
5. **Combine with manual testing**: Automated scanning isn't complete
6. **Review false positives**: Verify findings before reporting
7. **Use scope filtering**: Limit scope to authorized targets

## Integration with Exploitation

Scanner findings feed directly into exploitation stage:

```
Scanner Output → Vulnerability Object
                      ↓
              Exploitation Engine
                      ↓
         Exploitation Results & Evidence
```

Exploitation automatically selects appropriate technique based on vulnerability type found by scanner.