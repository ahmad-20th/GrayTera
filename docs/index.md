# GrayTera Wiki

Welcome to the GrayTera documentation wiki. This comprehensive guide covers all aspects of the penetration testing automation framework.

## 📑 Documentation Index

### Getting Started
- **[Quick Start Guide](#quick-start)** - Installation and basic usage
- **[Architecture Overview](architecture.md)** - System design and component interactions
- **[Configuration Reference](configuration.md)** - Detailed settings and tuning

### Core Concepts
- **[Pipeline Architecture](architecture.md#4-stage-pipeline-architecture)** - How the 4-stage pipeline works
- **[Data Models](api.md#data-models)** - Target, Vulnerability, and other core classes
- **[Observer Pattern](architecture.md#observer-pattern-components)** - Event notification system

### Scanning & Detection
- **[Scanner Reference](scanners.md)** - All vulnerability scanners explained
  - [SQL Injection Scanner](scanners.md#sql-injection-scanner)
  - [Nikto Scanner](scanners.md#nikto-web-server-scanner)
  - [OWASP ZAP Scanner](scanners.md#owasp-zap-scanner)
- **[Enumeration Strategies](architecture.md#enumerators)** - Subdomain discovery methods
- **[Exploitation Techniques](api.md#exploitation-engine)** - Blind SQLi and advanced exploitation

### Development
- **[Development Guide](development.md)** - Contributing and extending GrayTera
  - [Adding Scanners](development.md#2-adding-a-new-scanner)
  - [Adding Enumerators](development.md#1-adding-a-new-enumeration-strategy)
  - [Adding Exploits](development.md#3-adding-a-new-exploitation-module)
  - [Testing](development.md#testing)

### Reference
- **[API Reference](api.md)** - Complete API documentation
- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions
- **[Security Best Practices](security.md)** - Safe and responsible usage

## Quick Start

### Installation

```bash
git clone https://github.com/ahmad-20th/GrayTera
cd GrayTera
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Basic Usage

```bash
# Full pipeline scan
python main.py example.com

# Specific stage
python main.py example.com --stage enum

# With scope filtering
python main.py example.com --scope scope.json

# Resume previous scan
python main.py example.com --resume
```

## Project Structure

```
GrayTera/
├── core/                 # Pipeline orchestration
├── stages/               # 4 pipeline stages
├── enums/                # Enumeration strategies
├── scanners/             # Vulnerability scanners
├── exploits/             # Exploitation modules
├── observers/            # Event notification
├── payloads/             # Exploitation payloads
├── utils/                # Utilities
├── tests/                # Test suite
├── data/                 # Runtime data
└── docs/                 # Documentation (you are here)
```

## Key Features

✨ **Multi-technique Enumeration**
- DNS resolution with wordlists
- Certificate Transparency mining
- Google dorking support

🔍 **Advanced Scanning**
- SQL Injection detection
- Multi-threaded concurrent scanning
- Extensible scanner framework

⚡ **Intelligent Exploitation**
- Blind SQLi techniques
- Time-based detection
- Boolean-based validation
- 3-layer exploitation engine

📊 **Complete Automation**
- 4-stage pipeline orchestration
- Scope filtering and control
- Resume from checkpoints
- Data persistence

## Performance Profile

| Component | Memory | Time |
|-----------|--------|------|
| Baseline | 20-30MB | - |
| Enumeration | +20-40MB | 5-10s |
| Scanning | +30-50MB | 15-20s |
| Exploitation | +25-40MB | 10-15s |
| **Total** | **50-100MB** | **~47s** |

*For typical assessment with 4 subdomains*

## Configuration Overview

```yaml
# Enumeration settings
subdomain_enum:
  timeout: 10
  strategies:
    dns: true
    ct: true
    dork: false

# Scanning settings
vulnerability_scan:
  threads: 10
  timeout: 60
  sqli:
    enabled: true

# Exploitation settings
exploitation:
  auto_exploit: false
  timeout: 60
```

See [Configuration Reference](configuration.md) for complete details.

## Documentation Navigation

### By Role

**Security Testers**
1. [Quick Start Guide](#quick-start)
2. [Configuration Reference](configuration.md)
3. [Scanner Reference](scanners.md)
4. [Troubleshooting Guide](troubleshooting.md)

**Developers**
1. [Architecture Overview](architecture.md)
2. [API Reference](api.md)
3. [Development Guide](development.md)
4. [Security Best Practices](security.md)

**DevOps/Infrastructure**
1. [Configuration Reference](configuration.md)
2. [Architecture Overview](architecture.md#threading-model)
3. [Troubleshooting Guide](troubleshooting.md)

### By Topic

**System Design**
- [Architecture Overview](architecture.md)
- [API Reference](api.md)
- [Data Models](api.md#data-models)

**Usage & Configuration**
- [Configuration Reference](configuration.md)
- [Scanner Reference](scanners.md)
- [Troubleshooting Guide](troubleshooting.md)

**Extension & Development**
- [Development Guide](development.md)
- [Security Best Practices](security.md)
- [API Reference](api.md)

## Common Tasks

### Run a Complete Assessment
```bash
python main.py example.com --scope scope.json --output /path/to/results
```
See: [Configuration Reference](configuration.md)

### Add a Custom Scanner
See: [Development Guide - Adding a New Scanner](development.md#2-adding-a-new-scanner)

### Configure for High-Throughput
See: [Configuration Reference - Performance Tuning](configuration.md#performance-tuning)

### Troubleshoot Scan Issues
See: [Troubleshooting Guide](troubleshooting.md)

### Understand the Pipeline
See: [Architecture Overview](architecture.md#4-stage-pipeline-architecture)

## Getting Help

- **Documentation Issues**: Check relevant guide first
- **Configuration Problems**: See [Configuration Reference](configuration.md)
- **Scan Issues**: Check [Troubleshooting Guide](troubleshooting.md)
- **Development Help**: See [Development Guide](development.md)
- **Security Questions**: See [Security Best Practices](security.md)

## Contributing

GrayTera welcomes contributions! See [Development Guide](development.md#contributing-guidelines) for details.

## License

MIT License - See LICENSE.md for details

---

**Last Updated**: November 27, 2025  
**Documentation Version**: 1.0
