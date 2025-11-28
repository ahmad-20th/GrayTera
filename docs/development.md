# Development Guide

## Getting Started

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/ahmad-20th/GrayTera
cd GrayTera

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools (optional)
pip install pytest pytest-cov black flake8
```

### Code Style

GrayTera follows PEP 8 style guidelines with these conventions:

- **Line length**: 100 characters (soft limit)
- **Imports**: Alphabetically sorted, grouped (standard, third-party, local)
- **Type hints**: Recommended for public methods
- **Docstrings**: Google-style docstrings for all modules and classes

### Format Code

```bash
# Using black formatter
black *.py core/ stages/ scanners/ exploits/

# Check with flake8
flake8 --max-line-length=100
```

## Project Structure Understanding

### Core Modules

```
core/
├── pipeline.py      # Pipeline orchestrator - study this first
├── stage.py         # Abstract stage interface
├── target.py        # Data models
└── data_store.py    # Persistence layer
```

### Extension Points

```
stages/             # Add new pipeline stages here
enums/              # Add enumeration strategies
scanners/           # Add vulnerability scanners
exploits/           # Add exploitation modules
observers/          # Add notification handlers
payloads/           # Add payload definitions (YAML)
```

## Adding Components

### 1. Adding a New Enumeration Strategy

**Step 1: Create Enumerator**

```python
# enums/my_enum.py
from enums.base_enum import BaseEnumerator
from typing import Set

class MyEnumerator(BaseEnumerator):
    """My custom subdomain enumeration strategy"""
    
    def __init__(self):
        super().__init__("My Enumerator")
    
    def enumerate(self, domain: str) -> Set[str]:
        """
        Discover subdomains for target domain
        
        Args:
            domain: Target domain (e.g., 'example.com')
        
        Returns:
            Set of discovered subdomains (FQDNs)
        
        Raises:
            Exception: On network errors or API failures
        """
        subdomains = set()
        
        try:
            # Your enumeration logic here
            # Example:
            # for source in self._sources:
            #     results = self._query_source(source, domain)
            #     subdomains.update(results)
            pass
        
        except Exception as e:
            self.logger.error(f"Enumeration failed: {e}")
            raise
        
        return subdomains
```

**Step 2: Register Enumerator**

```python
# enums/enum_registry.py - Add to the file
from enums.my_enum import MyEnumerator

registry.register("my_enum", MyEnumerator())
```

**Step 3: Enable in Configuration**

```yaml
# config.yaml
subdomain_enum:
  strategies:
    my_enum: true
```

### 2. Adding a New Scanner

**Step 1: Create Scanner**

```python
# scanners/my_scanner.py
from scanners.base_scanner import BaseScanner
from core.target import Vulnerability
from typing import List
from datetime import datetime

class MyScanner(BaseScanner):
    """My custom vulnerability scanner"""
    
    def __init__(self):
        super().__init__("My Scanner")
    
    def scan(self, target_url: str) -> List[Vulnerability]:
        """
        Scan target for vulnerabilities
        
        Args:
            target_url: Full URL to scan
        
        Returns:
            List of Vulnerability objects found
        """
        vulnerabilities = []
        
        try:
            # Perform scanning logic
            if self._check_vulnerable(target_url):
                vuln = Vulnerability(
                    vuln_type='my_vuln_type',
                    severity='high',
                    url=target_url,
                    parameter='target_param',
                    payload='test_payload',
                    evidence='Evidence of vulnerability',
                    timestamp=datetime.now()
                )
                vulnerabilities.append(vuln)
        
        except Exception as e:
            self.logger.error(f"Scan error: {e}")
        
        return vulnerabilities
    
    def _check_vulnerable(self, url: str) -> bool:
        """Check if target is vulnerable"""
        # Implementation here
        return False
```

**Step 2: Register Scanner**

```python
# scanners/scanner_registry.py
from scanners.my_scanner import MyScanner

registry.register("my_scanner", MyScanner())
```

**Step 3: Enable in Configuration**

```yaml
vulnerability_scan:
  my_scanner:
    enabled: true
    timeout: 30
```

### 3. Adding a New Exploitation Module

**Step 1: Create Exploit**

```python
# exploits/my_exploit.py
from exploits.base_exploit import BaseExploit
from core.target import Vulnerability
from typing import Dict, Any

class MyExploit(BaseExploit):
    """My custom exploitation module"""
    
    def __init__(self):
        super().__init__("My Exploit")
    
    def execute(self, vulnerability: Vulnerability) -> Dict[str, Any]:
        """
        Attempt to exploit the vulnerability
        
        Args:
            vulnerability: Vulnerability object to exploit
        
        Returns:
            Dictionary with exploitation results:
            {
                'success': bool,
                'evidence': str,
                'data': dict,
                'error': str (if failed)
            }
        """
        result = {
            'success': False,
            'evidence': '',
            'data': {},
            'error': None
        }
        
        try:
            # Exploitation logic here
            if self._attempt_exploitation(vulnerability.url):
                result['success'] = True
                result['evidence'] = 'Exploitation successful'
                result['data'] = {'extracted': 'data'}
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _attempt_exploitation(self, url: str) -> bool:
        """Attempt exploitation"""
        # Implementation here
        return False
```

**Step 2: Register Exploit**

```python
# exploits/exploit_registry.py
from exploits.my_exploit import MyExploit

registry.register("my_vuln_type", MyExploit())
```

### 4. Adding a New Pipeline Stage

**Step 1: Create Stage**

```python
# stages/my_stage.py
from core.stage import Stage
from core.target import Target
from typing import Optional

class MyStage(Stage):
    """My custom pipeline stage"""
    
    def __init__(self, config: dict = None, **kwargs):
        super().__init__("My Stage")
        self.config = config or {}
    
    def is_enabled(self) -> bool:
        """Check if stage is enabled"""
        return self.config.get('enabled', True)
    
    def execute(self, target: Target) -> bool:
        """
        Execute stage logic
        
        Args:
            target: Target object with data from previous stages
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.notify('start')
            
            # Stage logic here
            # Modify target object with results
            target.some_field = "value"
            
            self.notify('complete', 'Stage completed successfully')
            return True
        
        except Exception as e:
            self.notify('error', str(e))
            return False
```

**Step 2: Register in Pipeline**

```python
# core/pipeline.py - in _initialize_stages()
from stages.my_stage import MyStage

stages = [
    # ... existing stages ...
    MyStage(self.config.get('my_stage', {}))
]
```

## Testing

### Unit Testing

Create tests in `tests/` directory:

```python
# tests/test_my_scanner.py
import unittest
from scanners.my_scanner import MyScanner
from core.target import Vulnerability

class TestMyScanner(unittest.TestCase):
    
    def setUp(self):
        self.scanner = MyScanner()
    
    def test_scan_vulnerable_url(self):
        """Test scanning a vulnerable URL"""
        vulnerabilities = self.scanner.scan(
            "http://vulnerable.example.com/page.php?id=1"
        )
        self.assertTrue(len(vulnerabilities) > 0)
    
    def test_scan_safe_url(self):
        """Test scanning a non-vulnerable URL"""
        vulnerabilities = self.scanner.scan(
            "http://safe.example.com/"
        )
        self.assertEqual(len(vulnerabilities), 0)
    
    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
```

### Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_my_scanner.py::TestMyScanner::test_scan_vulnerable_url -v

# Run with coverage
python -m pytest tests/ --cov=scanners --cov-report=html
```

### Integration Testing

```python
# tests/test_my_scanner_integration.py
import unittest
from core.pipeline import Pipeline
from core.data_store import DataStore
import tempfile

class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data_store = DataStore(self.temp_dir)
        self.pipeline = Pipeline(self.data_store)
    
    def test_full_pipeline(self):
        """Test complete pipeline execution"""
        self.pipeline.run("example.com")
        target = self.data_store.load_target("example.com")
        self.assertIsNotNone(target)
        self.assertTrue(len(target.subdomains) > 0)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

if __name__ == '__main__':
    unittest.main()
```

## Debugging

### Enable Debug Logging

```bash
python main.py example.com --debug
```

### Logging in Code

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Using Python Debugger

```python
import pdb

def my_function():
    x = 10
    pdb.set_trace()  # Execution stops here
    return x * 2
```

Debugger commands:
- `n`: Next line
- `s`: Step into function
- `c`: Continue execution
- `p x`: Print variable `x`
- `l`: List code around current line
- `q`: Quit debugger

## Common Extension Tasks

### Task: Add support for new database type

**File**: `exploits/blind_sqli_advanced.py`

```python
class DatabaseType(Enum):
    """Supported Database Types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    NEW_DB = "newdb"  # Add your database

# Add payload generation
@staticmethod
def conditional_errors(db_type: DatabaseType) -> Dict[str, List[str]]:
    # ... existing code ...
    
    elif db_type == DatabaseType.NEW_DB:
        return {
            "default": [
                "' OR NEW_DB_ERROR --",
                "' AND NEW_DB_SLEEP(5)--"
            ]
        }
```

### Task: Add custom HTTP header to requests

**File**: `utils/http_client.py`

```python
class HTTPClient:
    def __init__(self, timeout=10, custom_headers=None):
        self.session = requests.Session()
        
        # Default headers
        self.session.headers.update({
            'User-Agent': 'GrayTera/1.0',
            'Accept': 'text/html,application/xhtml+xml'
        })
        
        # Add custom headers
        if custom_headers:
            self.session.headers.update(custom_headers)
```

### Task: Add new observer for metrics collection

**File**: `observers/metrics_observer.py`

```python
from observers.base_observer import BaseObserver
from typing import Any

class MetricsObserver(BaseObserver):
    """Collect scan metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def update(self, stage: str, event: str, data: Any = None):
        """Record metrics"""
        if event == 'complete':
            self.metrics[stage] = {
                'completed': True,
                'data': str(data)
            }
    
    def get_metrics(self) -> dict:
        """Get collected metrics"""
        return self.metrics
```

## Code Review Checklist

Before submitting changes:

- [ ] Code follows PEP 8 style guide
- [ ] All functions have docstrings
- [ ] Type hints added for public methods
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] No hardcoded values (use config)
- [ ] Error handling is comprehensive
- [ ] Logging statements appropriate
- [ ] No security vulnerabilities introduced
- [ ] Documentation updated

## Performance Optimization Tips

1. **Profile code**: Use `cProfile` to identify bottlenecks
   ```python
   import cProfile
   cProfile.run('my_function()')
   ```

2. **Use generators**: For large datasets
   ```python
   def load_wordlist(path):
       with open(path) as f:
           for line in f:
               yield line.strip()
   ```

3. **Cache expensive operations**: Use `functools.lru_cache`
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def expensive_function(arg):
       return result
   ```

4. **Parallelize I/O**: Use threading for network operations
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   with ThreadPoolExecutor(max_workers=10) as executor:
       results = executor.map(process_item, items)
   ```

## Contributing Guidelines

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Ensure all tests pass: `pytest tests/ -v`
5. Commit with clear messages: `git commit -m "Add my feature"`
6. Push to branch: `git push origin feature/my-feature`
7. Create Pull Request with description

## Getting Help

- **Documentation**: See `docs/` directory
- **Issues**: Check GitHub Issues for similar problems
- **Discussions**: Use GitHub Discussions for questions
- **Code Examples**: Review existing components for patterns

## Resources

- [PEP 8 Style Guide](https://pep8.org/)
- [Python Logging](https://docs.python.org/3/library/logging.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Requests Library](https://requests.readthedocs.io/)