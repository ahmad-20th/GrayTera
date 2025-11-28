# GrayTera - Advanced Pentesting Automation Tool

> Minimal-footprint, modular Dynamic Application Security Testing (DAST) platform for automated penetration testing with production-ready reliability.

![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 🎯 Overview

GrayTera is an enterprise-grade penetration testing automation framework designed for efficient vulnerability discovery and exploitation. Built with a 4-stage pipeline architecture, it combines multiple enumeration strategies, concurrent vulnerability scanning, and intelligent exploitation capabilities.

**Key Design Principles:**
- Minimal system footprint (~50-100MB memory baseline)
- Modular architecture for easy extension
- Production-ready error handling and recovery
- Efficient concurrent scanning (configurable thread pools)
- Comprehensive data persistence and resume capability

## ✨ Features

### Core Capabilities
- **Multi-technique Subdomain Enumeration**: DNS queries, Certificate Transparency logs, Google dorking
- **Intelligent Vulnerability Scanning**: SQLi detection with multiple strategies, extensible scanner registry
- **Automated Exploitation**: Blind SQLi, time-based SQLi, boolean-based SQLi with advanced techniques
- **4-Stage Pipeline Orchestration**: Enumeration → Filtering → Scanning → Exploitation

### Advanced Features
- **Scope Filtering**: JSON-based include/exclude patterns for targeted assessment
- **Resume Capability**: Save and restore scan state across sessions
- **Multi-threaded Scanning**: Concurrent processing with configurable worker pools
- **Observer Pattern Logging**: Console and file-based event tracking
- **Flexible Configuration**: YAML-based settings with sensible defaults
- **Data Persistence**: JSON snapshots and Pickle serialization for complete state recovery

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/ahmad-20th/GrayTera
cd GrayTera

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python main.py --help
```

### Basic Usage

```bash
# Scan a single domain
python main.py example.com

# Run only subdomain enumeration
python main.py example.com --stage enum

# Run only vulnerability scanning
python main.py example.com --stage scan

# Attempt exploitation on discovered vulnerabilities
python main.py example.com --stage exploit

# Resume previous incomplete scan
python main.py example.com --resume

# Use custom configuration
python main.py example.com --config custom_config.yaml

# Apply scope filtering
python main.py example.com --scope scope.json

# Verbose output
python main.py example.com --verbose

# Output to specific directory
python main.py example.com --output /path/to/results
```

## 📋 Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--stage {enum,scan,exploit}` | `-s` | Run specific pipeline stage only |
| `--resume` | `-r` | Resume from previous scan checkpoint |
| `--config <path>` | `-c` | Use alternate configuration file |
| `--scope <path>` | `-sc` | Apply JSON scope filtering rules |
| `--output <path>` | `-o` | Specify output directory for results |
| `--verbose` | `-v` | Enable verbose logging output |
| `--help` | `-h` | Display help information |

## 🏗️ Architecture

### 4-Stage Pipeline

```
Target Domain
    ↓
[1] Enumeration Stage
    - DNS resolution
    - Certificate Transparency
    - Google dorking
    ↓ (subdomains discovered)
[2] Scope Filtering Stage
    - Include/exclude patterns
    - Pattern-based filtering
    ↓ (filtered subdomains)
[3] Vulnerability Scanning Stage
    - Multi-threaded scanning
    - SQLMap integration
    - Nikto (optional)
    ↓ (vulnerabilities discovered)
[4] Exploitation Stage
    - Blind SQLi exploitation
    - Time-based detection
    - Boolean-based validation
    ↓ (results persisted)
Results & Analysis
```

### Project Structure

```
GrayTera/
├── main.py                      # CLI entry point
├── config.yaml                  # Central configuration
├── requirements.txt             # Python dependencies
├── exploit.py                   # Exploitation launcher
├── core/                        # Core pipeline framework
│   ├── pipeline.py             # 4-stage orchestrator
│   ├── stage.py                # Base stage interface
│   ├── target.py               # Target data model
│   └── data_store.py           # Persistence layer
├── stages/                      # Pipeline implementations
│   ├── subdomain_enum.py       # Enumeration stage
│   ├── scope_filtering.py      # Filtering stage
│   ├── vulnerability_scan.py   # Scanning stage
│   └── exploitation.py         # Exploitation stage
├── enums/                       # Enumeration strategies
│   ├── dns_enum.py             # DNS resolution
│   ├── ct_enum.py              # Certificate Transparency
│   ├── dork_enum.py            # Google dorking
│   └── enum_registry.py        # Strategy registry
├── scanners/                    # Vulnerability scanners
│   ├── sqli_scanner.py         # SQLi detection
│   ├── nikto_scanner.py        # Nikto integration
│   ├── zap_scanner.py          # OWASP ZAP integration
│   └── scanner_registry.py     # Scanner management
├── exploits/                    # Exploitation modules
│   ├── sqli_exploit.py         # SQLi exploitation
│   ├── blind_sqli_advanced.py  # Advanced blind SQLi
│   └── exploit_registry.py     # Exploit management
├── observers/                   # Event notification
│   ├── console_observer.py     # Console output
│   ├── file_observer.py        # File logging
│   └── base_observer.py        # Observer interface
├── payloads/                    # Exploitation payloads
│   ├── sqli_strategies.yaml    # SQLi techniques
│   └── blind_sqli_advanced.yaml # Advanced techniques
├── utils/                       # Utility modules
│   ├── http_client.py          # HTTP request handling
│   ├── scope_filter.py         # Scope filtering logic
│   ├── validators.py           # Input validation
│   ├── logger.py               # Logging utilities
│   └── output.py               # Output formatting
├── wordlists/                   # Enumeration wordlists
│   └── subdomains.txt          # Subdomain patterns
├── data/                        # Runtime data directory
│   ├── logs/                   # Execution logs
│   └── scans/                  # Scan results by domain
└── docs/                        # Comprehensive documentation
    ├── architecture.md         # Design deep-dive
    ├── configuration.md        # Settings reference
    ├── scanners.md            # Scanner details
    ├── development.md         # Contribution guide
    ├── api.md                 # API reference
    └── troubleshooting.md     # Common issues
```

## ⚙️ Configuration

### config.yaml Structure

```yaml
subdomain_enum:
  timeout: 10                    # Seconds per enumeration
  strategies:
    dns: true                    # Enable DNS queries
    ct: true                     # Enable Certificate Transparency
    dork: false                  # Enable Google dorking

vulnerability_scan:
  timeout: 60                    # Total scanning timeout
  threads: 10                    # Concurrent workers (2-20 recommended)
  scanners:
    sqli:
      enabled: true             # Enable SQLi detection
      timeout: 30               # Per-target timeout
    nikto:
      enabled: false            # Nikto disabled by default (enable if needed)
      timeout: 30
    sqlmap:
      enabled: true             # SQLMap for exploitation

exploitation:
  auto_exploit: false           # Automatic exploitation mode
  sqlmap:
    path: null                  # SQLMap path (auto-detect if null)
    batch: true                 # Non-interactive mode
    threads: 10
```

### Environment Variables

```bash
# Override SQLMap location
export SQLMAP_PATH="/path/to/sqlmap/sqlmap.py"

# Custom wordlist
export WORDLIST_PATH="/path/to/custom_subdomains.txt"
```

### Scope Filtering

Create `scope.json` for targeted scanning:

```json
{
  "include": [
    "*.example.com",
    "api.example.com",
    "admin.example.com"
  ],
  "exclude": [
    "*.internal.example.com",
    "old-*.example.com"
  ]
}
```

## 📊 Performance Metrics

| Operation | Time (4 subdomains) | Memory |
|-----------|-------------------|--------|
| Enumeration | ~5-10s | 20-30MB |
| Filtering | <1s | 10-15MB |
| Scanning (SQLi only) | ~15-20s | 30-50MB |
| Exploitation | ~10-15s | 25-40MB |
| **Total** | **~47s** | **50-100MB** |

*Metrics based on typical test domain with enabled strategies. Results vary by network latency and target responsiveness.*

## 🔐 Security & Best Practices

### Responsible Use
- **Only test systems you own or have explicit written permission to test**
- Always obtain authorization before conducting security assessments
- Respect network boundaries and system limitations
- Log all testing activities for compliance and audit trails

### Safe Configuration
- Disable unnecessary scanners (Nikto disabled by default)
- Set appropriate timeouts to prevent resource exhaustion
- Use scope filtering to limit assessment scope
- Adjust thread pool size based on target capacity
- Monitor memory and CPU usage during long scans

### Error Handling
- Graceful timeouts prevent application hanging
- Failed scans logged without interrupting pipeline
- Automatic recovery from malformed responses
- Silent error handling for test domains (non-existent domains)

## 🧪 Testing & Validation

### Run Test Suite
```bash
# All tests
python -m pytest tests/ -v

# Specific test module
python -m pytest tests/test_pipeline.py -v

# With coverage
python -m pytest tests/ --cov=core --cov=stages --cov-report=html
```

### Manual Verification
```bash
# Verify installation
python main.py --help

# Test with public domain
python main.py google.com --stage enum

# Test resume capability
python main.py google.com --stage enum
python main.py google.com --resume
```

## 🛠️ Extension Guide

### Adding a New Scanner

1. **Create scanner module** in `scanners/`:
```python
from scanners.base_scanner import BaseScanner

class CustomScanner(BaseScanner):
    def __init__(self):
        super().__init__("Custom Scanner")
    
    def scan(self, target_url: str):
        """Scan target and return vulnerabilities."""
        vulnerabilities = []
        # Your scanning logic here
        return vulnerabilities
```

2. **Register scanner** in `scanners/scanner_registry.py`:
```python
from scanners.custom_scanner import CustomScanner
registry.register("custom", CustomScanner())
```

3. **Enable in config.yaml**:
```yaml
vulnerability_scan:
  scanners:
    custom:
      enabled: true
```

### Adding a New Enumeration Strategy

1. **Create enum module** in `enums/`:
```python
from enums.base_enum import BaseEnum

class CustomEnum(BaseEnum):
    def __init__(self):
        super().__init__("Custom Strategy")
    
    def enumerate(self, domain: str):
        """Enumerate and return subdomains."""
        subdomains = set()
        # Your enumeration logic here
        return subdomains
```

2. **Register strategy** in `enums/enum_registry.py`
3. **Enable in config.yaml**

## 📚 Documentation

Comprehensive documentation available in `docs/`:
- **[Architecture](docs/architecture.md)** - Design patterns and component interactions
- **[Configuration Reference](docs/configuration.md)** - All settings explained
- **[Scanner Details](docs/scanners.md)** - Scanner capabilities and tuning
- **[Development Guide](docs/development.md)** - Contribution guidelines

## 🐛 Troubleshooting

### Program Freezes
- **Check timeouts** in `config.yaml` (vulnerability_scan.timeout should be 60s)
- **Verify target reachability** - test with `ping` or `curl`
- **Disable Nikto** if experiencing hangs (set `nikto.enabled: false`)
- **Reduce thread count** if resource-constrained

### SQLMap Not Found
```bash
# Set explicit path in config.yaml
# Or export environment variable
export SQLMAP_PATH="/usr/local/bin/sqlmap"
```

### XML Parsing Errors
- **Update Nikto** to latest version
- **Disable Nikto** if errors persist
- **Check target URL validity** - Nikto fails on non-existent domains

### Resume Not Working
- **Verify data directory** exists: `data/scans/domain/`
- **Check permissions** on pickle files
- **Inspect logs** in `data/logs/` for errors

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.8+ | Runtime |
| dnspython | Latest | DNS resolution |
| requests | Latest | HTTP requests |
| PyYAML | Latest | Configuration parsing |
| sqlmap | Latest | SQLi exploitation |
| nikto | Latest | Web scanning (optional) |

Install with:
```bash
pip install -r requirements.txt
```

## 📄 License

MIT License - See LICENSE.md for details

**Disclaimer**: This tool is for authorized security testing only. Unauthorized access is illegal. Users are responsible for ensuring legal compliance.

## 👥 Contributing

Contributions welcome! Please see [Development Guide](docs/development.md) for guidelines.

## 🔗 Resources

- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [SQLMap Documentation](http://sqlmap.org/)
- [Nikto Documentation](https://github.com/sullo/nikto/wiki)
- [DAST Best Practices](https://cheatsheetseries.owasp.org/)