# GrayTera - Advanced Pentesting Automation Tool

A modular Dynamic Application Security Testing (DAST) tool for automated penetration testing.

## Features

- **Subdomain Enumeration**: Discover subdomains using multiple techniques
- **Vulnerability Scanning**: Detect security vulnerabilities (SQLi, XSS, etc.)
- **Exploitation**: Attempt to exploit discovered vulnerabilities

## Installation

```bash
# Clone repository
git clone https://github.com/ahmad-20th/GrayTera
cd graytera

# Create work environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install required packages
pip install -r requirements.txt
```

## Usage

### Basic Scan
```bash
python main.py example.com
```

### Run Specific Stage
```bash
# Only enumerate subdomains
python main.py example.com --stage enum

# Only scan for vulnerabilities
python main.py example.com --stage scan

# Only attempt exploitation
python main.py example.com --stage exploit
```

### Resume Previous Scan
```bash
python main.py example.com --resume
```

### Custom Configuration
```bash
python main.py example.com --config custom_config.yaml
```

## Project Structure

```
graytera/
├── main.py                 # Entry point
├── core/                   # Core pipeline logic
├── stages/                 # Pipeline stages
├── enums/                  # Subdomain enumration modules
├── scanners/               # Vulnerability scanners
├── exploits/               # Exploitation modules
├── observers/              # Event observers (logging, output)
├── utils/                  # Utility functions
└── data/                   # Runtime data (scans, logs)
```

## Development

### Adding a New Scanner

1. Create a new file in `scanners/` (e.g., `xss_scanner.py`)
2. Inherit from `BaseScanner`
3. Implement the `scan()` method
4. Register in `ScannerRegistry`

```python
from scanners.base_scanner import BaseScanner

class XSSScanner(BaseScanner):
    def __init__(self):
        super().__init__("XSS Scanner")
    
    def scan(self, target_url: str):
        # Your scanning logic here
        pass
```

### Adding a New Exploit

1. Create a new file in `exploits/` (e.g., `xss_exploit.py`)
2. Inherit from `BaseExploit`
3. Implement the `execute()` method
4. Register in `ExploitRegistry`

## Configuration

Edit `config.yaml` to customize:
- Scanner settings (threads, timeouts)
- Exploitation behavior
- Retry logic
- Output formats

### SQLMap detection
- Set `exploitation.sqlmap.path` to the exact command or script (e.g. `python -m sqlmap` or `C:\\Tools\\sqlmap\\sqlmap.py`) if SQLMap is not in your `PATH`.
- Alternatively export `SQLMAP_PATH` with the same value.

### Custom SQLi strategies
- Edit `payloads/sqli_strategies.yaml` to add advanced techniques (cookie-based, time-delay, XML, etc.). Each strategy describes its injection point, payloads, and success condition, and the exploit layer will report which strategy matched.

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_pipeline.py
```

## Legal Disclaimer

**This tool is for educational and authorized security testing only.**

- Only test systems you own or have explicit permission to test
- Unauthorized testing is illegal and unethical
- The authors are not responsible for misuse of this tool

## Team

- Developer 1: Pipeline & Core
- Developer 2: CLI Interface
- Developer 3-4: Subdomain Enumeration
- Developer 5-6: SQLi Scanner & Exploit
- Developer 7: Data Store
- Developer 8: Error Handling & Logging