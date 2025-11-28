# API Reference

Complete API documentation for GrayTera core components.

## Table of Contents

1. [Data Models](#data-models)
2. [Core Classes](#core-classes)
3. [Registry Pattern](#registry-pattern)
4. [Observer Interface](#observer-interface)
5. [Utilities](#utilities)
6. [Examples](#examples)

## Data Models

### Target

Represents a complete assessment target with all associated data.

```python
class Target:
    """Represents a single target domain with all scan data."""
    
    domain: str                          # Primary domain (e.g., 'example.com')
    subdomains: Set[str]                # All discovered subdomains
    in_scope_subdomains: Set[str]       # Filtered in-scope subdomains
    out_of_scope_subdomains: Set[str]   # Filtered out-of-scope subdomains
    vulnerabilities: List[Vulnerability] # Discovered vulnerabilities
    exploits: Dict[str, Any]            # Exploitation results
    metadata: Dict[str, Any]            # Additional metadata
    timestamp: datetime                 # Creation timestamp
```

**Key Methods:**

```python
def to_json() -> str
    """Serialize target to JSON string."""
    
def to_dict() -> Dict[str, Any]
    """Convert to dictionary representation."""
    
def add_subdomain(subdomain: str) -> None
    """Add discovered subdomain."""
    
def add_vulnerability(vuln: Vulnerability) -> None
    """Add vulnerability finding."""
    
def add_exploit_result(vuln_id: str, result: Dict) -> None
    """Record exploitation result."""
```

### Vulnerability

Represents a single vulnerability discovery.

```python
class Vulnerability:
    """Represents a single discovered vulnerability."""
    
    vuln_id: str                # Unique identifier (auto-generated)
    vuln_type: str              # Type (sqli, xss, etc.)
    severity: str               # high, medium, low, info
    url: str                    # Vulnerable URL
    parameter: str              # Vulnerable parameter name
    payload: str                # Payload that triggered vulnerability
    evidence: str               # Proof/evidence of vulnerability
    timestamp: datetime         # Discovery timestamp
    exploitable: bool           # Can be exploited
    status: str                 # pending, exploited, failed
```

**Key Methods:**

```python
def to_dict() -> Dict[str, Any]
    """Convert to dictionary."""
    
def __repr__() -> str
    """String representation."""
```

### ExploitResult

Represents exploitation attempt outcome.

```python
class ExploitResult:
    """Result of exploitation attempt."""
    
    success: bool               # Whether exploitation succeeded
    evidence: str               # Proof of successful exploitation
    data: Dict[str, Any]       # Extracted data (tables, users, etc.)
    error: Optional[str]        # Error message if failed
    timestamp: datetime         # Execution timestamp
    technique: str              # Technique used (blind, union, etc.)
```

## Core Classes

### Pipeline

Orchestrates the 4-stage assessment pipeline.

```python
class Pipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self, 
                 data_store: DataStore,
                 config: Dict[str, Any] = None,
                 observers: List[BaseObserver] = None):
        """Initialize pipeline.
        
        Args:
            data_store: DataStore instance for persistence
            config: Configuration dictionary (YAML loaded)
            observers: List of observers for notifications
        """
    
    def run(self, domain: str, 
            stages: Optional[List[str]] = None,
            interactive: bool = False) -> Target:
        """Execute pipeline.
        
        Args:
            domain: Target domain
            stages: List of stages to run (default: all)
                   Valid: ['enum', 'filter', 'scan', 'exploit']
            interactive: Pause between stages
        
        Returns:
            Target object with all results
        
        Raises:
            Exception: On critical pipeline failures
        """
    
    def resume(self, domain: str) -> Target:
        """Resume incomplete assessment.
        
        Args:
            domain: Target domain
        
        Returns:
            Resumed Target object
        """
    
    def add_observer(self, observer: BaseObserver) -> None:
        """Register observer for events."""
    
    def notify(self, event: str, data: Any = None) -> None:
        """Notify all observers of event."""
```

### Stage

Abstract base class for all pipeline stages.

```python
class Stage(ABC):
    """Abstract base class for pipeline stages."""
    
    def __init__(self, name: str):
        """Initialize stage.
        
        Args:
            name: Human-readable stage name
        """
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if stage is enabled in config."""
    
    @abstractmethod
    def execute(self, target: Target) -> bool:
        """Execute stage logic.
        
        Args:
            target: Target object to process
        
        Returns:
            True if successful, False otherwise
        """
    
    def notify(self, event: str, data: Any = None) -> None:
        """Notify observers of stage event."""
    
    def add_observer(self, observer: BaseObserver) -> None:
        """Register observer."""
```

### DataStore

Handles persistence of target data.

```python
class DataStore:
    """Persistent storage for target data."""
    
    def __init__(self, base_path: str = "data"):
        """Initialize data store.
        
        Args:
            base_path: Root directory for data storage
        """
    
    def save_target(self, target: Target) -> None:
        """Save target to JSON file.
        
        Args:
            target: Target object to save
        """
    
    def load_target(self, domain: str) -> Optional[Target]:
        """Load target from JSON file.
        
        Args:
            domain: Domain to load
        
        Returns:
            Target object or None if not found
        """
    
    def save_state(self, target: Target) -> None:
        """Save complete state (pickle) for resume.
        
        Args:
            target: Target object to save
        """
    
    def load_state(self, domain: str) -> Optional[Target]:
        """Load pickled state for resume.
        
        Args:
            domain: Domain to load
        
        Returns:
            Target object or None if not found
        """
    
    def delete_target(self, domain: str) -> None:
        """Delete all data for domain."""
    
    def list_targets(self) -> List[str]:
        """List all stored targets."""
```

## Registry Pattern

### ScannerRegistry

Manages available vulnerability scanners.

```python
class ScannerRegistry:
    """Registry for vulnerability scanners."""
    
    def register(self, name: str, scanner: BaseScanner) -> None:
        """Register a scanner.
        
        Args:
            name: Unique scanner identifier
            scanner: Scanner instance
        """
    
    def get(self, name: str) -> Optional[BaseScanner]:
        """Get scanner by name.
        
        Args:
            name: Scanner name
        
        Returns:
            Scanner instance or None
        """
    
    def get_enabled(self, config: Dict) -> List[BaseScanner]:
        """Get enabled scanners from config.
        
        Args:
            config: vulnerability_scan config section
        
        Returns:
            List of enabled scanner instances
        """
    
    def list_all(self) -> List[str]:
        """List all registered scanners."""
```

### EnumRegistry

Manages enumeration strategies.

```python
class EnumRegistry:
    """Registry for enumeration strategies."""
    
    def register(self, name: str, enumerator: BaseEnumerator) -> None:
        """Register enumerator.
        
        Args:
            name: Unique identifier
            enumerator: Enumerator instance
        """
    
    def get_enabled(self, config: Dict) -> List[BaseEnumerator]:
        """Get enabled enumerators from config.
        
        Args:
            config: subdomain_enum config section
        
        Returns:
            List of enabled enumerator instances
        """
```

### ExploitRegistry

Manages exploitation modules.

```python
class ExploitRegistry:
    """Registry for exploitation modules."""
    
    def register(self, vuln_type: str, exploit: BaseExploit) -> None:
        """Register exploit handler.
        
        Args:
            vuln_type: Vulnerability type this handles
            exploit: Exploit instance
        """
    
    def get(self, vuln_type: str) -> Optional[BaseExploit]:
        """Get exploit for vulnerability type.
        
        Args:
            vuln_type: Type of vulnerability
        
        Returns:
            Exploit instance or None
        """
```

## Observer Interface

### BaseObserver

Receives notifications of pipeline events.

```python
class BaseObserver(ABC):
    """Abstract observer interface."""
    
    @abstractmethod
    def update(self, stage: str, event: str, data: Any = None) -> None:
        """Handle event notification.
        
        Args:
            stage: Name of stage emitting event
            event: Event type (start, complete, error, etc.)
            data: Event-specific data
        """
```

### ConsoleObserver

Logs events to console output.

```python
class ConsoleObserver(BaseObserver):
    """Logs events to console with formatting."""
    
    def update(self, stage: str, event: str, data: Any = None) -> None:
        """Print formatted event to console."""
```

### FileObserver

Logs events to file.

```python
class FileObserver(BaseObserver):
    """Logs events to file with timestamps."""
    
    def __init__(self, filepath: str):
        """Initialize file observer.
        
        Args:
            filepath: Path to log file
        """
    
    def update(self, stage: str, event: str, data: Any = None) -> None:
        """Write event to log file."""
```

## Utilities

### HTTPClient

Wrapper for HTTP requests with features like timeouts and retries.

```python
class HTTPClient:
    """HTTP client with timeout and retry support."""
    
    def __init__(self, timeout: int = 10, retries: int = 3):
        """Initialize HTTP client.
        
        Args:
            timeout: Request timeout in seconds
            retries: Number of retry attempts
        """
    
    def get(self, url: str, headers: Dict = None) -> Response:
        """Make GET request.
        
        Args:
            url: Target URL
            headers: Optional HTTP headers
        
        Returns:
            Response object
        """
    
    def post(self, url: str, data: Any, headers: Dict = None) -> Response:
        """Make POST request."""
    
    def request(self, method: str, url: str, **kwargs) -> Response:
        """Make HTTP request with method."""
```

### ScopeFilter

Evaluates subdomains against scope rules.

```python
class ScopeFilter:
    """Filter subdomains against inclusion/exclusion rules."""
    
    def __init__(self, scope_file: str = None):
        """Initialize scope filter.
        
        Args:
            scope_file: Path to scope.json file
        """
    
    def is_in_scope(self, subdomain: str) -> bool:
        """Check if subdomain is in scope.
        
        Args:
            subdomain: Domain to check
        
        Returns:
            True if in scope, False otherwise
        """
    
    def filter(self, subdomains: Set[str]) -> Tuple[Set[str], Set[str]]:
        """Filter subdomains into in/out scope.
        
        Args:
            subdomains: Set of subdomains to filter
        
        Returns:
            Tuple of (in_scope, out_of_scope) sets
        """
```

### Validators

Input validation utilities.

```python
def is_valid_domain(domain: str) -> bool:
    """Validate domain name format."""

def is_valid_url(url: str) -> bool:
    """Validate URL format."""

def sanitize_domain(domain: str) -> str:
    """Normalize domain string."""
```

## Examples

### Example 1: Run Complete Pipeline

```python
from core.pipeline import Pipeline
from core.data_store import DataStore
from observers.console_observer import ConsoleObserver
import yaml

# Load configuration
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# Initialize components
data_store = DataStore()
pipeline = Pipeline(data_store, config)
pipeline.add_observer(ConsoleObserver())

# Run pipeline
target = pipeline.run('example.com')

# Access results
print(f"Found {len(target.subdomains)} subdomains")
print(f"Found {len(target.vulnerabilities)} vulnerabilities")
```

### Example 2: Run Specific Stage

```python
from core.pipeline import Pipeline

pipeline = Pipeline(data_store, config)
target = pipeline.run('example.com', stages=['enum', 'filter'])
# Only enumeration and filtering stages execute
```

### Example 3: Resume Assessment

```python
# Initial scan
target = pipeline.run('example.com')

# Later: Resume from where it stopped
resumed_target = pipeline.resume('example.com')
```

### Example 4: Create Custom Observer

```python
from observers.base_observer import BaseObserver

class MetricsObserver(BaseObserver):
    def __init__(self):
        self.metrics = {}
    
    def update(self, stage, event, data=None):
        key = f"{stage}_{event}"
        self.metrics[key] = data

# Use observer
observer = MetricsObserver()
pipeline.add_observer(observer)
pipeline.run('example.com')
print(observer.metrics)
```

### Example 5: Direct Scanner Usage

```python
from scanners.sqli_scanner import SQLiScanner

scanner = SQLiScanner()
vulnerabilities = scanner.scan('http://example.com/page.php?id=1')

for vuln in vulnerabilities:
    print(f"Found: {vuln.vuln_type} in {vuln.parameter}")
```

### Example 6: Direct Exploitation

```python
from exploits.sqli_exploit import SQLiExploit
from core.target import Vulnerability

exploit = SQLiExploit()
vuln = Vulnerability(
    vuln_type='sqli',
    severity='high',
    url='http://example.com/page.php?id=1',
    parameter='id',
    payload="' OR '1'='1",
    evidence='SQL error detected'
)

result = exploit.execute(vuln)
if result['success']:
    print(f"Exploited! Data: {result['data']}")
```

### Example 7: Scope Filtering

```python
from utils.scope_filter import ScopeFilter

scope_filter = ScopeFilter('scope.json')

subdomains = {
    'api.example.com',
    'test.example.com',
    'admin.example.com'
}

in_scope, out_scope = scope_filter.filter(subdomains)
print(f"In scope: {in_scope}")
print(f"Out of scope: {out_scope}")
```

### Example 8: Data Persistence

```python
from core.data_store import DataStore

store = DataStore()

# Save target
store.save_target(target)

# Load target
loaded = store.load_target('example.com')

# Save state for resume
store.save_state(target)

# Load state for resume
state = store.load_state('example.com')
```

## Integration Example: Custom Assessment Script

```python
#!/usr/bin/env python3
"""Custom assessment script using GrayTera API."""

from core.pipeline import Pipeline
from core.data_store import DataStore
from observers.console_observer import ConsoleObserver
from observers.file_observer import FileObserver
from utils.scope_filter import ScopeFilter
import yaml
import json

def run_assessment(domain, scope_file=None, output_dir=None):
    """Run complete assessment with custom configuration."""
    
    # Load configuration
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
    
    # Initialize components
    data_store = DataStore(output_dir or 'data')
    pipeline = Pipeline(data_store, config)
    
    # Add observers
    pipeline.add_observer(ConsoleObserver())
    pipeline.add_observer(FileObserver(f'{output_dir}/assessment.log'))
    
    # Run pipeline
    target = pipeline.run(domain)
    
    # Post-processing
    print(f"\n=== Assessment Results ===")
    print(f"Domain: {target.domain}")
    print(f"Subdomains: {len(target.subdomains)}")
    print(f"In Scope: {len(target.in_scope_subdomains)}")
    print(f"Vulnerabilities: {len(target.vulnerabilities)}")
    
    # Export results
    with open(f'{output_dir}/results.json', 'w') as f:
        json.dump(target.to_dict(), f, indent=2, default=str)
    
    return target

if __name__ == '__main__':
    import sys
    domain = sys.argv[1] if len(sys.argv) > 1 else 'example.com'
    run_assessment(domain)
```

## Error Handling

All components raise appropriate exceptions:

```python
try:
    target = pipeline.run('example.com')
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Pipeline error: {e}")
```

## Thread Safety

- `Pipeline` is thread-safe for multiple domain assessments
- `DataStore` uses atomic operations
- `ScannerRegistry` is immutable after initialization

---

**Last Updated**: November 27, 2025  
**API Version**: 1.0
