# GrayTera Architecture

## Overview

GrayTera is built on a modular, extensible architecture designed for efficient penetration testing automation. The system follows established design patterns including Pipeline, Strategy, Observer, and Registry patterns.

## Core Design Principles

- **Modularity**: Each component has a single, well-defined responsibility
- **Extensibility**: New scanners, exploits, and strategies can be added without modifying core code
- **Concurrency**: Multi-threaded operations with configurable thread pools
- **Persistence**: Complete state management and resume capability
- **Reliability**: Comprehensive error handling and graceful degradation

## 4-Stage Pipeline Architecture

### Stage 1: Subdomain Enumeration
Discovers all subdomains associated with the target domain using multiple strategies:
- **DNS Strategy**: Direct DNS resolution queries with wordlist-based discovery
- **Certificate Transparency**: Mining publicly available SSL certificates
- **Google Dorking**: Search engine-based enumeration
- **Common Subdomains**: Static list of frequently used subdomain names

**Output**: Set of discovered FQDNs with metadata

### Stage 2: Scope Filtering
Applies user-defined inclusion/exclusion rules to discovered subdomains:
- Exact domain matching
- Wildcard pattern support (`*.example.com`)
- Regex-based filtering
- Case-insensitive matching

**Output**: Filtered subdomains separated into in-scope and out-of-scope lists

### Stage 3: Vulnerability Scanning
Identifies security vulnerabilities across in-scope subdomains:
- **SQL Injection Scanner**: Detects SQLi vulnerabilities
- **Nikto Scanner**: Web server vulnerability assessment (optional)
- **OWASP ZAP**: Comprehensive vulnerability scanning (optional)
- Multi-threaded concurrent scanning with configurable timeouts

**Output**: Vulnerability findings with severity classification

### Stage 4: Exploitation
Attempts to exploit discovered vulnerabilities:
- **SQLi Exploitation**: 3-layer exploitation engine
  - Layer 1: Target analysis and parameter discovery
  - Layer 2: SQLMap integration for advanced detection
  - Layer 3: Custom exploitation fallback
- Blind SQLi, Time-based, Boolean-based, and UNION-based techniques

**Output**: Exploitation results with evidence and extracted data

## Component Architecture

### Core Components

#### Pipeline (`core/pipeline.py`)
Orchestrates stage execution and manages data flow between stages:
- Sequential stage execution
- Resume capability from checkpoints
- Observer pattern for event notification
- Interactive mode with pauses between stages

#### Target (`core/target.py`)
Data model representing the assessment target:
- Domain and subdomain tracking
- Vulnerability storage
- Metadata and timestamps
- Exploitation results

#### DataStore (`core/data_store.py`)
Persistent storage and retrieval:
- JSON-based reports
- Pickle serialization for complete state
- Directory structure: `data/scans/{domain}/`
- Atomic file operations for data integrity

### Strategy Pattern Components

#### Enumerators (`enums/`)
Pluggable subdomain discovery strategies:
- `BaseEnumerator`: Abstract interface
- `DNSEnumerator`: DNS-based discovery
- `CTEnumerator`: Certificate Transparency mining
- `DorkEnumerator`: Search engine dorking
- `EnumRegistry`: Strategy registration and management

#### Scanners (`scanners/`)
Pluggable vulnerability detection strategies:
- `BaseScanner`: Abstract scanner interface
- `SQLiScanner`: SQL Injection detection
- `NiktoScanner`: Nikto wrapper
- `ZAPScanner`: OWASP ZAP integration
- `ScannerRegistry`: Scanner management

#### Exploits (`exploits/`)
Pluggable exploitation strategies:
- `BaseExploit`: Abstract exploit interface
- `SQLiExploit`: 3-layer SQLi exploitation
- `BlindSQLiAdvanced`: Advanced blind techniques
- `ExploitRegistry`: Exploit management

### Observer Pattern Components

Decoupled event notification system:

#### Observers (`observers/`)
- `BaseObserver`: Observer interface
- `ConsoleObserver`: Real-time console output
- `FileObserver`: Log file persistence

#### Events
- `start`: Stage initialization
- `complete`: Stage completion
- `error`: Error notification
- `warning`: Warning notification
- `info`: Information message
- Stage-specific events (e.g., `subdomain_found`)

## Data Flow

```
Input: Target Domain
  ↓
[Stage 1] Enumeration
  - Execute all registered enumerators
  - Merge results into subdomain set
  - Notify observers of discoveries
  ↓ Target.subdomains populated
[Stage 2] Scope Filtering
  - Load scope from JSON file
  - Filter subdomains using in/out scope rules
  - Separate into in_scope and out_of_scope lists
  ↓ Target.in_scope_subdomains updated
[Stage 3] Scanning
  - For each in-scope subdomain:
    - Execute registered scanners
    - Collect vulnerability findings
  - Aggregate results across subdomains
  ↓ Target.vulnerabilities populated
[Stage 4] Exploitation
  - For each vulnerability:
    - Select appropriate exploit handler
    - Execute exploitation chain
    - Capture evidence and extracted data
  ↓ Target.exploits populated
[DataStore] Persistence
  - Serialize Target object to JSON
  - Save pickled state for resume
  - Generate human-readable reports
  ↓
Output: Comprehensive assessment results
```

## Configuration Management

### YAML-Based Configuration (`config.yaml`)

Organized by stage with sensible defaults:

```yaml
subdomain_enum:
  timeout: 10
  strategies:
    dns: true
    ct: true
    dork: false

vulnerability_scan:
  timeout: 60
  threads: 10
  scanners:
    sqli:
      enabled: true
    nikto:
      enabled: false

exploitation:
  auto_exploit: false
  timeout: 60
```

### Runtime Configuration

- **Environment Variables**: Override defaults (e.g., `SQLMAP_PATH`)
- **Command-Line Arguments**: Stage-specific overrides
- **Scope Filtering**: Separate JSON file with inclusion/exclusion rules

## Threading Model

### Thread Pool Management

- Configurable pool size (default: 10)
- Work distribution across worker threads
- Thread-safe queue management
- Graceful shutdown on completion or interruption

### Thread Safety

- Lock-protected shared resources
- Atomic operations for state updates
- Thread-safe data structures (Queue, Lock)

## Error Handling Strategy

### Graceful Degradation

1. **Stage Failure**: Continue to next stage, log error
2. **Scanner Failure**: Continue with next scanner, flag in results
3. **Network Timeout**: Retry with backoff, then skip target
4. **Malformed Response**: Skip and continue enumeration

### Recovery Mechanisms

- Resume from last successful stage
- Retry logic with exponential backoff
- State preservation in case of crash
- Human-readable error messages

## Extension Points

### Adding New Enumeration Strategy

1. Inherit from `BaseEnumerator`
2. Implement `enumerate(domain)` method
3. Register in `EnumRegistry`
4. Enable in `config.yaml`

### Adding New Scanner

1. Inherit from `BaseScanner`
2. Implement `scan(target_url)` method
3. Register in `ScannerRegistry`
4. Enable in `config.yaml`

### Adding New Exploit

1. Inherit from `BaseExploit`
2. Implement `execute(vulnerability)` method
3. Register in `ExploitRegistry`
4. Select via vulnerability type matching

## Performance Characteristics

### Memory Management

- Baseline: 20-30MB
- Per-subdomain overhead: ~1-2KB
- Scanner-specific overhead: 10-50MB
- Total typical usage: 50-100MB

### Time Complexity

- Enumeration: O(n) where n = number of enumeration sources
- Scanning: O(m×t) where m = subdomains, t = per-target timeout
- Overall: Linear with respect to target scope

### Optimization Techniques

- Connection pooling for HTTP requests
- DNS cache management
- Concurrent scanner execution
- Early exit on exploitation success
- Parameter priority scoring

## Security Considerations

### Input Validation

- Domain name validation (RFC 1035 compliant)
- URL scheme validation (http/https only)
- Path traversal prevention in file operations
- Regex pattern validation

### Payload Handling

- Payload templates with variable substitution
- Encoded payload support (URL, Base64, XML)
- WAF evasion techniques (case variation, comments)
- Safe SQL injection detection (no data destruction)

### Access Control

- File permission checks for data access
- API key management for external services
- Configuration file validation
- Log file access restrictions

## Integration Points

### External Tools

- **SQLMap**: Subprocess execution with timeout management
- **Nikto**: XML output parsing and vulnerability mapping
- **OWASP ZAP**: REST API integration
- **DNS Servers**: Standard DNS protocol via dnspython

### APIs and Services

- **Shodan**: Certificate Transparency API
- **Google**: Custom Search API for dorking
- **NIST NVD**: CVE mapping (planned)

## Logging and Observability

### Log Levels

- **DEBUG**: Detailed execution flow and variable state
- **INFO**: Stage completion and major events
- **WARNING**: Skipped operations and minor failures
- **ERROR**: Critical failures requiring attention

### Log Outputs

- **Console**: Real-time progress via ConsoleObserver
- **File**: Persistent log in `data/logs/`
- **Event Stream**: Structured events for programmatic access

## Future Architecture Enhancements

1. **Plugin System**: Dynamic loading of external modules
2. **Distributed Scanning**: Multi-machine scan coordination
3. **Database Backend**: Centralized result storage
4. **REST API**: Remote execution and monitoring
5. **Web Dashboard**: Visual results presentation