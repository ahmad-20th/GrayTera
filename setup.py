# DAST Pentesting Tool - Complete Project Structure
# Copy this structure to your project directory

"""
Project Folder Structure:
========================

dast-tool/
│
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── README.md                        # Documentation
├── config.yaml                      # Configuration file
│
├── core/
│   ├── __init__.py
│   ├── pipeline.py                  # Main pipeline orchestrator
│   ├── stage.py                     # Base stage class
│   ├── data_store.py               # Persistence layer
│   └── target.py                    # Target data model
│
├── stages/
│   ├── __init__.py
│   ├── subdomain_enum.py           # Stage 1: Subdomain enumeration
│   ├── vulnerability_scan.py       # Stage 2: Vulnerability scanning
│   └── exploitation.py             # Stage 3: Exploitation
│
├── scanners/
│   ├── __init__.py
│   ├── base_scanner.py             # Base scanner interface
│   ├── sqli_scanner.py             # SQLi detection
│   └── scanner_registry.py         # Scanner management
│
├── exploits/
│   ├── __init__.py
│   ├── base_exploit.py             # Base exploit interface
│   ├── sqli_exploit.py             # SQLi exploitation
│   └── exploit_registry.py         # Exploit management
│
├── utils/
│   ├── __init__.py
│   ├── http_client.py              # HTTP requests with retry
│   ├── logger.py                   # Logging setup
│   └── validators.py               # Input validation
│
├── observers/
│   ├── __init__.py
│   ├── base_observer.py            # Observer interface
│   ├── console_observer.py         # Console output
│   ├── file_observer.py            # File logging
│   └── progress_observer.py        # Progress tracking
│
├── tests/
│   ├── __init__.py
│   ├── test_pipeline.py
│   ├── test_scanners.py
│   └── test_exploits.py
│
└── data/                            # Runtime data
    ├── scans/                       # Scan results
    └── logs/                        # Log files
"""

# ============================================================================
# main.py - Entry Point
# ============================================================================

import argparse
import sys
from pathlib import Path
from core.pipeline import Pipeline
from core.data_store import DataStore
from observers.console_observer import ConsoleObserver
from observers.file_observer import FileObserver
from utils.logger import setup_logging


def main():
    parser = argparse.ArgumentParser(description='DAST Pentesting Tool')
    parser.add_argument('target', help='Target domain (e.g., example.com)')
    parser.add_argument('--resume', action='store_true', help='Resume previous scan')
    parser.add_argument('--stage', choices=['enum', 'scan', 'exploit'], 
                       help='Run specific stage only')
    parser.add_argument('--output', default='data/scans', help='Output directory')
    parser.add_argument('--config', default='config.yaml', help='Config file')
    args = parser.parse_args()
    
    # Setup
    setup_logging()
    data_store = DataStore(args.output)
    
    # Create pipeline with observers
    pipeline = Pipeline(data_store, config_path=args.config)
    pipeline.attach(ConsoleObserver())
    pipeline.attach(FileObserver(args.output))
    
    try:
        if args.resume:
            pipeline.resume(args.target)
        else:
            pipeline.run(args.target, specific_stage=args.stage)
    except KeyboardInterrupt:
        print("\n[!] Scan paused. Use --resume to continue.")
        pipeline.pause()
        sys.exit(0)
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()


# ============================================================================
# core/target.py - Target Data Model
# ============================================================================

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class Vulnerability:
    """Represents a discovered vulnerability"""
    vuln_type: str  # 'sqli', 'xss', etc.
    severity: str   # 'critical', 'high', 'medium', 'low'
    url: str
    parameter: str
    payload: str
    evidence: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Target:
    """Represents a target domain and its scan data"""
    domain: str
    subdomains: List[str] = field(default_factory=list)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    exploited: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_subdomain(self, subdomain: str):
        if subdomain not in self.subdomains:
            self.subdomains.append(subdomain)
    
    def add_vulnerability(self, vuln: Vulnerability):
        self.vulnerabilities.append(vuln)
    
    def add_exploit_result(self, result: Dict[str, Any]):
        self.exploited.append(result)


# ============================================================================
# core/stage.py - Base Stage Class
# ============================================================================

from abc import ABC, abstractmethod
from typing import List


class Stage(ABC):
    """Base class for all pipeline stages"""
    
    def __init__(self, name: str):
        self.name = name
        self.observers = []
    
    @abstractmethod
    def execute(self, target: Target) -> bool:
        """
        Execute the stage logic
        Returns True if successful, False otherwise
        """
        pass
    
    def notify(self, event: str, data: Any = None):
        """Notify all observers of an event"""
        for observer in self.observers:
            observer.update(self.name, event, data)
    
    def attach_observer(self, observer):
        self.observers.append(observer)


# ============================================================================
# core/pipeline.py - Main Pipeline Orchestrator
# ============================================================================

import yaml
from typing import Optional, List
from core.stage import Stage
from core.target import Target
from core.data_store import DataStore
from stages.subdomain_enum import SubdomainEnumStage
from stages.vulnerability_scan import VulnerabilityScanStage
from stages.exploitation import ExploitationStage


class Pipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, data_store: DataStore, config_path: str = 'config.yaml'):
        self.data_store = data_store
        self.config = self._load_config(config_path)
        self.observers = []
        self.stages = self._initialize_stages()
        self.current_stage_index = 0
    
    def _load_config(self, path: str) -> dict:
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_config()
    
    def _default_config(self) -> dict:
        return {
            'subdomain_enum': {
                'timeout': 10,
                'max_subdomains': 1000
            },
            'vulnerability_scan': {
                'threads': 10,
                'timeout': 30
            },
            'exploitation': {
                'auto_exploit': False,
                'max_attempts': 3
            },
            'retry': {
                'max_retries': 3,
                'backoff_factor': 2
            }
        }
    
    def _initialize_stages(self) -> List[Stage]:
        stages = [
            SubdomainEnumStage(self.config['subdomain_enum']),
            VulnerabilityScanStage(self.config['vulnerability_scan']),
            ExploitationStage(self.config['exploitation'])
        ]
        # Attach observers to all stages
        for stage in stages:
            for observer in self.observers:
                stage.attach_observer(observer)
        return stages
    
    def attach(self, observer):
        """Attach an observer to the pipeline"""
        self.observers.append(observer)
        for stage in self.stages:
            stage.attach_observer(observer)
    
    def run(self, domain: str, specific_stage: Optional[str] = None):
        """Run the full pipeline or a specific stage"""
        target = self.data_store.load_target(domain) or Target(domain=domain)
        
        if specific_stage:
            self._run_specific_stage(target, specific_stage)
        else:
            self._run_all_stages(target)
        
        self.data_store.save_target(target)
    
    def _run_all_stages(self, target: Target):
        """Execute all stages in sequence"""
        for idx, stage in enumerate(self.stages):
            self.current_stage_index = idx
            self._notify_all(f"Starting stage: {stage.name}")
            
            success = stage.execute(target)
            
            if not success:
                self._notify_all(f"Stage {stage.name} failed")
                break
            
            # Save progress after each stage
            self.data_store.save_target(target)
            self._notify_all(f"Completed stage: {stage.name}")
    
    def _run_specific_stage(self, target: Target, stage_name: str):
        """Execute a specific stage"""
        stage_map = {
            'enum': 0,
            'scan': 1,
            'exploit': 2
        }
        
        if stage_name not in stage_map:
            raise ValueError(f"Unknown stage: {stage_name}")
        
        stage = self.stages[stage_map[stage_name]]
        stage.execute(target)
    
    def pause(self):
        """Save current state for resuming"""
        self._notify_all("Pipeline paused")
    
    def resume(self, domain: str):
        """Resume from saved state"""
        target = self.data_store.load_target(domain)
        if not target:
            raise ValueError(f"No saved state found for {domain}")
        
        # Resume from next incomplete stage
        self._run_all_stages(target)
    
    def _notify_all(self, message: str):
        for observer in self.observers:
            observer.update("Pipeline", "info", message)


# ============================================================================
# core/data_store.py - Persistence Layer
# ============================================================================

import json
import pickle
from pathlib import Path
from typing import Optional
from datetime import datetime
from core.target import Target


class DataStore:
    """Handles persistence of scan data"""
    
    def __init__(self, base_path: str = 'data/scans'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_target(self, target: Target):
        """Save target data to disk"""
        target_dir = self.base_path / self._sanitize_domain(target.domain)
        target_dir.mkdir(exist_ok=True)
        
        # Save as both JSON (human-readable) and pickle (full object)
        json_path = target_dir / 'scan_data.json'
        pickle_path = target_dir / 'scan_data.pkl'
        
        # JSON export
        with open(json_path, 'w') as f:
            json.dump(self._target_to_dict(target), f, indent=2, default=str)
        
        # Pickle for full state
        with open(pickle_path, 'wb') as f:
            pickle.dump(target, f)
    
    def load_target(self, domain: str) -> Optional[Target]:
        """Load target data from disk"""
        pickle_path = self.base_path / self._sanitize_domain(domain) / 'scan_data.pkl'
        
        if not pickle_path.exists():
            return None
        
        with open(pickle_path, 'rb') as f:
            return pickle.load(f)
    
    def _sanitize_domain(self, domain: str) -> str:
        """Convert domain to safe directory name"""
        return domain.replace(':', '_').replace('/', '_')
    
    def _target_to_dict(self, target: Target) -> dict:
        """Convert Target to JSON-serializable dict"""
        return {
            'domain': target.domain,
            'subdomains': target.subdomains,
            'vulnerabilities': [
                {
                    'type': v.vuln_type,
                    'severity': v.severity,
                    'url': v.url,
                    'parameter': v.parameter,
                    'payload': v.payload,
                    'evidence': v.evidence,
                    'timestamp': v.timestamp.isoformat()
                }
                for v in target.vulnerabilities
            ],
            'exploited': target.exploited,
            'metadata': target.metadata
        }


# ============================================================================
# stages/subdomain_enum.py - Subdomain Enumeration Stage
# ============================================================================

import dns.resolver
import requests
from core.stage import Stage
from core.target import Target
from typing import Set


class SubdomainEnumStage(Stage):
    """Stage 1: Subdomain Enumeration"""
    
    def __init__(self, config: dict):
        super().__init__("Subdomain Enumeration")
        self.config = config
        self.timeout = config.get('timeout', 10)
    
    def execute(self, target: Target) -> bool:
        """Enumerate subdomains for the target"""
        self.notify("start", f"Enumerating subdomains for {target.domain}")
        
        try:
            subdomains = self._enumerate_subdomains(target.domain)
            
            for subdomain in subdomains:
                target.add_subdomain(subdomain)
                self.notify("subdomain_found", subdomain)
            
            self.notify("complete", f"Found {len(subdomains)} subdomains")
            return True
            
        except Exception as e:
            self.notify("error", str(e))
            return False
    
    def _enumerate_subdomains(self, domain: str) -> Set[str]:
        """
        Perform subdomain enumeration using multiple techniques
        Team members should implement:
        1. Dictionary-based brute force
        2. DNS zone transfer
        3. Certificate transparency logs
        4. Search engine queries
        """
        subdomains = set()
        
        # Technique 1: Common subdomain wordlist
        common_subdomains = ['www', 'mail', 'ftp', 'admin', 'blog', 'dev', 'api']
        for sub in common_subdomains:
            subdomain = f"{sub}.{domain}"
            if self._check_subdomain_exists(subdomain):
                subdomains.add(subdomain)
        
        # TODO: Add more enumeration techniques here
        # - crt.sh API for certificate transparency
        # - Subdomain scraping from search engines
        # - DNS brute forcing with larger wordlists
        
        return subdomains
    
    def _check_subdomain_exists(self, subdomain: str) -> bool:
        """Verify if subdomain exists"""
        try:
            dns.resolver.resolve(subdomain, 'A')
            return True
        except:
            return False


# ============================================================================
# stages/vulnerability_scan.py - Vulnerability Scanning Stage
# ============================================================================

from concurrent.futures import ThreadPoolExecutor, as_completed
from core.stage import Stage
from core.target import Target
from scanners.scanner_registry import ScannerRegistry


class VulnerabilityScanStage(Stage):
    """Stage 2: Vulnerability Scanning"""
    
    def __init__(self, config: dict):
        super().__init__("Vulnerability Scanning")
        self.config = config
        self.threads = config.get('threads', 10)
        self.scanner_registry = ScannerRegistry()
    
    def execute(self, target: Target) -> bool:
        """Scan all discovered subdomains for vulnerabilities"""
        self.notify("start", f"Scanning {len(target.subdomains)} subdomains")
        
        if not target.subdomains:
            self.notify("warning", "No subdomains to scan")
            return True
        
        try:
            self._scan_subdomains(target)
            self.notify("complete", f"Found {len(target.vulnerabilities)} vulnerabilities")
            return True
            
        except Exception as e:
            self.notify("error", str(e))
            return False
    
    def _scan_subdomains(self, target: Target):
        """Scan subdomains concurrently"""
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            
            for subdomain in target.subdomains:
                future = executor.submit(self._scan_single_target, subdomain)
                futures.append((future, subdomain))
            
            for future, subdomain in futures:
                try:
                    vulnerabilities = future.result()
                    for vuln in vulnerabilities:
                        target.add_vulnerability(vuln)
                        self.notify("vulnerability_found", {
                            'subdomain': subdomain,
                            'type': vuln.vuln_type,
                            'severity': vuln.severity
                        })
                except Exception as e:
                    self.notify("error", f"Failed to scan {subdomain}: {e}")
    
    def _scan_single_target(self, subdomain: str):
        """Run all registered scanners against a target"""
        vulnerabilities = []
        
        for scanner in self.scanner_registry.get_all_scanners():
            try:
                vulns = scanner.scan(subdomain)
                vulnerabilities.extend(vulns)
            except Exception as e:
                self.notify("error", f"Scanner {scanner.name} failed: {e}")
        
        return vulnerabilities


# ============================================================================
# stages/exploitation.py - Exploitation Stage
# ============================================================================

from core.stage import Stage
from core.target import Target, Vulnerability
from exploits.exploit_registry import ExploitRegistry


class ExploitationStage(Stage):
    """Stage 3: Exploitation"""
    
    def __init__(self, config: dict):
        super().__init__("Exploitation")
        self.config = config
        self.auto_exploit = config.get('auto_exploit', False)
        self.exploit_registry = ExploitRegistry()
    
    def execute(self, target: Target) -> bool:
        """Attempt to exploit discovered vulnerabilities"""
        self.notify("start", f"Attempting to exploit {len(target.vulnerabilities)} vulnerabilities")
        
        if not target.vulnerabilities:
            self.notify("warning", "No vulnerabilities to exploit")
            return True
        
        try:
            if self.auto_exploit:
                self._auto_exploit_all(target)
            else:
                self._interactive_exploit(target)
            
            self.notify("complete", f"Successfully exploited {len(target.exploited)} vulnerabilities")
            return True
            
        except Exception as e:
            self.notify("error", str(e))
            return False
    
    def _auto_exploit_all(self, target: Target):
        """Automatically exploit all vulnerabilities"""
        for vuln in target.vulnerabilities:
            self._attempt_exploit(target, vuln)
    
    def _interactive_exploit(self, target: Target):
        """Let user choose which vulnerabilities to exploit"""
        print("\n[*] Discovered Vulnerabilities:")
        for idx, vuln in enumerate(target.vulnerabilities, 1):
            print(f"  {idx}. [{vuln.severity.upper()}] {vuln.vuln_type} at {vuln.url}")
        
        print("\nEnter vulnerability numbers to exploit (comma-separated, or 'all'):")
        choice = input("> ").strip()
        
        if choice.lower() == 'all':
            indices = range(len(target.vulnerabilities))
        else:
            indices = [int(x.strip()) - 1 for x in choice.split(',') if x.strip().isdigit()]
        
        for idx in indices:
            if 0 <= idx < len(target.vulnerabilities):
                vuln = target.vulnerabilities[idx]
                self._attempt_exploit(target, vuln)
    
    def _attempt_exploit(self, target: Target, vuln: Vulnerability):
        """Attempt to exploit a single vulnerability"""
        exploit = self.exploit_registry.get_exploit(vuln.vuln_type)
        
        if not exploit:
            self.notify("warning", f"No exploit available for {vuln.vuln_type}")
            return
        
        try:
            result = exploit.execute(vuln)
            if result['success']:
                target.add_exploit_result(result)
                self.notify("exploit_success", {
                    'type': vuln.vuln_type,
                    'url': vuln.url,
                    'result': result
                })
            else:
                self.notify("exploit_failed", f"{vuln.vuln_type} at {vuln.url}")
                
        except Exception as e:
            self.notify("error", f"Exploit failed: {e}")


# ============================================================================
# scanners/base_scanner.py - Base Scanner Interface
# ============================================================================

from abc import ABC, abstractmethod
from typing import List
from core.target import Vulnerability


class BaseScanner(ABC):
    """Base class for all vulnerability scanners"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def scan(self, target_url: str) -> List[Vulnerability]:
        """
        Scan a target URL for vulnerabilities
        Returns a list of discovered vulnerabilities
        """
        pass


# ============================================================================
# scanners/sqli_scanner.py - SQL Injection Scanner
# ============================================================================

import requests
from typing import List
from datetime import datetime
from scanners.base_scanner import BaseScanner
from core.target import Vulnerability
from utils.http_client import HTTPClient


class SQLiScanner(BaseScanner):
    """SQL Injection vulnerability scanner"""
    
    def __init__(self):
        super().__init__("SQLi Scanner")
        self.http_client = HTTPClient()
        
        # Common SQLi payloads
        self.payloads = [
            "'",
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "admin' --",
            "admin' #",
            "' UNION SELECT NULL--",
            "1' ORDER BY 1--+",
            "1' ORDER BY 2--+",
            "1' ORDER BY 3--+",
        ]
        
        # Error patterns indicating SQLi
        self.error_patterns = [
            "SQL syntax",
            "mysql_fetch",
            "ORA-01756",
            "PostgreSQL",
            "SQLite",
            "Microsoft SQL Server",
            "Unclosed quotation mark",
            "syntax error"
        ]
    
    def scan(self, target_url: str) -> List[Vulnerability]:
        """Scan target for SQL injection vulnerabilities"""
        vulnerabilities = []
        
        # TODO: Implement full SQLi detection logic
        # 1. Discover parameters (GET, POST, cookies, headers)
        # 2. Test each parameter with payloads
        # 3. Analyze responses for SQLi indicators
        # 4. Verify findings to reduce false positives
        
        # Example skeleton:
        # parameters = self._discover_parameters(target_url)
        # for param in parameters:
        #     for payload in self.payloads:
        #         if self._test_sqli(target_url, param, payload):
        #             vuln = Vulnerability(...)
        #             vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _test_sqli(self, url: str, parameter: str, payload: str) -> bool:
        """Test a specific parameter with a SQLi payload"""
        try:
            # Inject payload
            response = self.http_client.get(url, params={parameter: payload})
            
            # Check for error-based SQLi
            for pattern in self.error_patterns:
                if pattern.lower() in response.text.lower():
                    return True
            
            # TODO: Add more detection techniques:
            # - Boolean-based blind SQLi
            # - Time-based blind SQLi
            # - Union-based SQLi
            
            return False
            
        except Exception:
            return False


# ============================================================================
# scanners/scanner_registry.py - Scanner Management
# ============================================================================

from typing import List, Dict
from scanners.base_scanner import BaseScanner
from scanners.sqli_scanner import SQLiScanner


class ScannerRegistry:
    """Registry for managing vulnerability scanners"""
    
    def __init__(self):
        self.scanners: Dict[str, BaseScanner] = {}
        self._register_default_scanners()
    
    def _register_default_scanners(self):
        """Register built-in scanners"""
        self.register(SQLiScanner())
        # TODO: Add more scanners as they're developed
        # self.register(XSSScanner())
        # self.register(CSRFScanner())
    
    def register(self, scanner: BaseScanner):
        """Register a new scanner"""
        self.scanners[scanner.name] = scanner
    
    def get_scanner(self, name: str) -> BaseScanner:
        """Get a scanner by name"""
        return self.scanners.get(name)
    
    def get_all_scanners(self) -> List[BaseScanner]:
        """Get all registered scanners"""
        return list(self.scanners.values())


# ============================================================================
# exploits/base_exploit.py - Base Exploit Interface
# ============================================================================

from abc import ABC, abstractmethod
from typing import Dict, Any
from core.target import Vulnerability


class BaseExploit(ABC):
    """Base class for all exploits"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, vulnerability: Vulnerability) -> Dict[str, Any]:
        """
        Execute the exploit
        Returns a dict with:
        - success: bool
        - data: Any extracted data
        - evidence: Proof of exploitation
        """
        pass


# ============================================================================
# exploits/sqli_exploit.py - SQL Injection Exploit
# ============================================================================

from typing import Dict, Any
from exploits.base_exploit import BaseExploit
from core.target import Vulnerability
from utils.http_client import HTTPClient


class SQLiExploit(BaseExploit):
    """SQL Injection exploitation module"""
    
    def __init__(self):
        super().__init__("SQLi Exploit")
        self.http_client = HTTPClient()
    
    def execute(self, vulnerability: Vulnerability) -> Dict[str, Any]:
        """Exploit SQL injection to extract data"""
        
        # TODO: Implement exploitation techniques:
        # 1. Determine database type
        # 2. Extract database structure
        # 3. Dump sensitive data (carefully and ethically!)
        # 4. Document findings
        
        result = {
            'success': False,
            'data': None,
            'evidence': '',
            'technique': 'union-based'  # or 'blind', 'error-based', etc.
        }
        
        try:
            # Example: Try UNION-based extraction
            db_version = self._extract_version(vulnerability)
            if db_version:
                result['success'] = True
                result['data'] = {'db_version': db_version}
                result['evidence'] = f"Successfully extracted DB version: {db_version}"
            
        except Exception as e:
            result['evidence'] = f"Exploitation failed: {str(e)}"
        
        return result
    
    def _extract_version(self, vuln: Vulnerability) -> str:
        """Extract database version"""
        # Placeholder - implement actual extraction logic
        return None


# ============================================================================
# exploits/exploit_registry.py - Exploit Management
# ============================================================================

from typing import Dict, Optional
from exploits.base_exploit import BaseExploit
from exploits.sqli_exploit import SQLiExploit


class ExploitRegistry:
    """Registry for managing exploits"""
    
    def __init__(self):
        self.exploits: Dict[str, BaseExploit] = {}
        self._register_default_exploits()
    
    def _register_default_exploits(self):
        """Register built-in exploits"""
        self.register('sqli', SQLiExploit())
        # TODO: Add more exploits
        # self.register('xss', XSSExploit())
    
    def register(self, vuln_type: str, exploit: BaseExploit):
        """Register an exploit for a vulnerability type"""
        self.exploits[vuln_type] = exploit
    
    def get_exploit(self, vuln_type: str) -> Optional[BaseExploit]:
        """Get exploit for a vulnerability type"""
        return self.exploits.get(vuln_type)


# ============================================================================
# utils/http_client.py - HTTP Client with Retry Logic
# ============================================================================

import requests
from typing import Optional, Dict
import time


class HTTPClient:
    """HTTP client with retry logic and error handling"""
    
    def __init__(self, max_retries: int = 3, timeout: int = 30):
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DAST-Tool/1.0 (Security Testing)'
        })
    
    def get(self, url: str, params: Optional[Dict] = None, **kwargs):
        """GET request with retry logic"""
        return self._request('GET', url, params=params, **kwargs)
    
    def post(self, url: str, data: Optional[Dict] = None, **kwargs):
        """POST request with retry logic"""
        return self._request('POST', url, data=data, **kwargs)
    
    def _request(self, method: str, url: str, **kwargs):
        """Execute request with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                kwargs.setdefault('timeout', self.timeout)
                kwargs.setdefault('allow_redirects', True)
                
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt)  # Exponential backoff
                    time.sleep(wait_time)
                else:
                    raise last_exception


# ============================================================================
# utils/logger.py - Logging Setup
# ============================================================================

import logging
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: str = 'data/logs'):
    """Setup logging configuration"""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    log_file = Path(log_dir) / f"dast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('DAST')


# ============================================================================
# utils/validators.py - Input Validation
# ============================================================================

import re
from urllib.parse import urlparse


def is_valid_domain(domain: str) -> bool:
    """Validate domain format"""
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}
    return bool(re.match(pattern, domain))


def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def sanitize_input(user_input: str) -> str:
    """Sanitize user input to prevent injection"""
    # Remove potentially dangerous characters
    return re.sub(r'[^\w\s\-\.]', '', user_input)


# ============================================================================
# observers/base_observer.py - Observer Interface
# ============================================================================

from abc import ABC, abstractmethod
from typing import Any


class BaseObserver(ABC):
    """Base observer interface for monitoring pipeline events"""
    
    @abstractmethod
    def update(self, stage: str, event: str, data: Any = None):
        """
        Called when an event occurs
        
        Args:
            stage: Name of the stage emitting the event
            event: Event type (start, complete, error, etc.)
            data: Optional event data
        """
        pass


# ============================================================================
# observers/console_observer.py - Console Output Observer
# ============================================================================

from observers.base_observer import BaseObserver
from typing import Any
from datetime import datetime


class ConsoleObserver(BaseObserver):
    """Observer that outputs to console"""
    
    def __init__(self):
        self.colors = {
            'info': '\033[94m',      # Blue
            'success': '\033[92m',   # Green
            'warning': '\033[93m',   # Yellow
            'error': '\033[91m',     # Red
            'reset': '\033[0m'
        }
    
    def update(self, stage: str, event: str, data: Any = None):
        """Print formatted output to console"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if event == 'start':
            self._print_info(f"[{timestamp}] [{stage}] Started")
        
        elif event == 'complete':
            self._print_success(f"[{timestamp}] [{stage}] {data}")
        
        elif event == 'error':
            self._print_error(f"[{timestamp}] [{stage}] ERROR: {data}")
        
        elif event == 'warning':
            self._print_warning(f"[{timestamp}] [{stage}] WARNING: {data}")
        
        elif event == 'subdomain_found':
            self._print_info(f"[{timestamp}] [+] Subdomain: {data}")
        
        elif event == 'vulnerability_found':
            severity_color = self._get_severity_color(data.get('severity', 'medium'))
            print(f"{severity_color}[{timestamp}] [!] Vulnerability: {data['type']} "
                  f"at {data['subdomain']}{self.colors['reset']}")
        
        elif event == 'exploit_success':
            self._print_success(f"[{timestamp}] [✓] Exploited {data['type']} at {data['url']}")
        
        elif event == 'exploit_failed':
            self._print_warning(f"[{timestamp}] [✗] Failed to exploit: {data}")
    
    def _print_info(self, message: str):
        print(f"{self.colors['info']}{message}{self.colors['reset']}")
    
    def _print_success(self, message: str):
        print(f"{self.colors['success']}{message}{self.colors['reset']}")
    
    def _print_warning(self, message: str):
        print(f"{self.colors['warning']}{message}{self.colors['reset']}")
    
    def _print_error(self, message: str):
        print(f"{self.colors['error']}{message}{self.colors['reset']}")
    
    def _get_severity_color(self, severity: str) -> str:
        severity_map = {
            'critical': self.colors['error'],
            'high': self.colors['error'],
            'medium': self.colors['warning'],
            'low': self.colors['info']
        }
        return severity_map.get(severity.lower(), self.colors['info'])


# ============================================================================
# observers/file_observer.py - File Logging Observer
# ============================================================================

import json
from pathlib import Path
from datetime import datetime
from observers.base_observer import BaseObserver
from typing import Any


class FileObserver(BaseObserver):
    """Observer that logs events to file"""
    
    def __init__(self, output_dir: str = 'data/scans'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.events = []
    
    def update(self, stage: str, event: str, data: Any = None):
        """Log event to file"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'event': event,
            'data': str(data) if data else None
        }
        
        self.events.append(log_entry)
        
        # Append to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


# ============================================================================
# observers/progress_observer.py - Progress Tracking Observer
# ============================================================================

from observers.base_observer import BaseObserver
from typing import Any


class ProgressObserver(BaseObserver):
    """Observer that tracks and displays progress"""
    
    def __init__(self):
        self.stage_progress = {}
        self.total_tasks = 0
        self.completed_tasks = 0
    
    def update(self, stage: str, event: str, data: Any = None):
        """Update progress tracking"""
        if event == 'start':
            self.stage_progress[stage] = {'status': 'running', 'progress': 0}
        
        elif event == 'complete':
            self.stage_progress[stage] = {'status': 'completed', 'progress': 100}
            self.completed_tasks += 1
        
        elif event == 'error':
            self.stage_progress[stage] = {'status': 'failed', 'progress': 0}
        
        self._display_progress()
    
    def _display_progress(self):
        """Display progress bar (simple implementation)"""
        if self.total_tasks > 0:
            percentage = (self.completed_tasks / self.total_tasks) * 100
            bar_length = 40
            filled = int(bar_length * percentage / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f'\rProgress: [{bar}] {percentage:.1f}%', end='', flush=True)


# ============================================================================
# requirements.txt - Python Dependencies
# ============================================================================

"""
requests>=2.31.0
dnspython>=2.4.2
pyyaml>=6.0.1
"""


# ============================================================================
# config.yaml - Configuration File
# ============================================================================

"""
# DAST Tool Configuration

subdomain_enum:
  timeout: 10
  max_subdomains: 1000
  wordlist: wordlists/subdomains.txt
  use_crt_sh: true
  use_dns_bruteforce: true

vulnerability_scan:
  threads: 10
  timeout: 30
  max_depth: 3  # For crawling
  follow_redirects: true
  
  # Scanner-specific configs
  sqli:
    enabled: true
    payloads_file: payloads/sqli.txt
    detect_waf: true
  
  xss:
    enabled: false  # Enable when implemented
  
  csrf:
    enabled: false  # Enable when implemented

exploitation:
  auto_exploit: false  # Require manual confirmation
  max_attempts: 3
  timeout: 60
  
  # Exploit-specific configs
  sqli:
    extract_tables: true
    extract_users: false  # Be careful with this!
    max_rows: 10

retry:
  max_retries: 3
  backoff_factor: 2
  retry_on_status: [500, 502, 503, 504]

output:
  save_format: json  # json, html, xml
  include_raw_requests: false
  include_screenshots: false

logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  file: data/logs/dast.log
  console: true
"""


# ============================================================================
# README.md - Documentation
# ============================================================================

"""
# DAST Pentesting Tool

A modular Dynamic Application Security Testing (DAST) tool for automated penetration testing.

## Features

- **Subdomain Enumeration**: Discover subdomains using multiple techniques
- **Vulnerability Scanning**: Detect security vulnerabilities (SQLi, XSS, etc.)
- **Exploitation**: Attempt to exploit discovered vulnerabilities
- **Modular Architecture**: Easy to extend with new scanners and exploits

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd dast-tool

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
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
dast-tool/
├── main.py                 # Entry point
├── core/                   # Core pipeline logic
├── stages/                 # Pipeline stages
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

## License

[Your License Here]
```


# ============================================================================
# tests/test_pipeline.py - Pipeline Tests
# ============================================================================

"""
import unittest
from core.pipeline import Pipeline
from core.data_store import DataStore
from core.target import Target
import tempfile
import shutil


class TestPipeline(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data_store = DataStore(self.temp_dir)
        self.pipeline = Pipeline(self.data_store)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_pipeline_initialization(self):
        self.assertEqual(len(self.pipeline.stages), 3)
        self.assertEqual(self.pipeline.current_stage_index, 0)
    
    def test_target_creation(self):
        target = Target(domain="example.com")
        self.assertEqual(target.domain, "example.com")
        self.assertEqual(len(target.subdomains), 0)
    
    # Add more tests...


if __name__ == '__main__':
    unittest.main()
"""


# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================

"""
QUICK START GUIDE
=================

1. Create project directory:
   mkdir dast-tool
   cd dast-tool

2. Copy this entire code into a file called 'setup.py'

3. Run the setup script:
   python setup.py

4. This will create all necessary files and folders

5. Install dependencies:
   pip install -r requirements.txt

6. Test the tool:
   python main.py example.com --help


TEAM DEVELOPMENT WORKFLOW
==========================

Week 1 (Days 1-7):
------------------
- Day 1-2: Setup project structure, define interfaces
- Day 3-4: Implement core pipeline and CLI
- Day 5-7: Build subdomain enumeration module

Team 1 (Pipeline & Core): 
  - Implement Pipeline.run(), pause(), resume()
  - Implement DataStore save/load
  - Test stage transitions

Team 2 (Subdomain Enum):
  - Implement dictionary-based enumeration
  - Add crt.sh API integration
  - Add DNS brute forcing

Team 3 (SQLi Scanner):
  - Implement payload injection
  - Add error-based detection
  - Begin boolean-based detection


Week 2 (Days 8-14):
-------------------
- Day 8-10: Complete vulnerability scanning
- Day 11-12: Implement exploitation module
- Day 13: Integration testing
- Day 14: Final testing and documentation

Team 3 (SQLi Scanner):
  - Complete all SQLi detection methods
  - Reduce false positives
  - Optimize performance

Team 4 (SQLi Exploit):
  - Implement UNION-based extraction
  - Add blind SQLi exploitation
  - Handle edge cases

All Teams:
  - Integration testing
  - Bug fixes
  - Documentation
  - Prepare demo


PRIORITY TASKS
==============

CRITICAL (Must have for MVP):
1. Working pipeline orchestrator
2. Basic subdomain enumeration (even just dictionary-based)
3. SQLi scanner with error-based detection
4. Basic SQLi exploit (database version extraction)
5. Data persistence (save/load scans)

HIGH (Should have):
6. Retry logic for network errors
7. Console output with colors
8. Multiple subdomain enumeration techniques
9. Boolean-based SQLi detection
10. Proper error logging

MEDIUM (Nice to have):
11. Progress tracking
12. Time-based blind SQLi
13. Interactive exploit selection
14. HTML report generation

LOW (If time permits):
15. XSS scanner
16. CSRF scanner
17. Automated report generation
18. Web interface


TESTING CHECKLIST
=================

Before demo:
□ Test against safe test sites (testphp.vulnweb.com, etc.)
□ Verify subdomain enumeration works
□ Confirm SQLi detection works
□ Test save/resume functionality
□ Check error handling (network failures, invalid inputs)
□ Verify logging works
□ Test with multiple targets
□ Check memory usage with many subdomains


COMMON PITFALLS TO AVOID
========================

1. **Over-engineering**: Don't add features you don't need for MVP
2. **Merge conflicts**: Coordinate who works on which files
3. **Testing late**: Test early and often
4. **Ignoring errors**: Implement proper error handling from start
5. **No code reviews**: Review each other's code
6. **Poor communication**: Daily standups are crucial
7. **Scope creep**: Stick to the plan, resist adding "cool" features


SAFE TESTING TARGETS
====================

Use these for testing (they're designed for security testing):
- http://testphp.vulnweb.com
- http://testaspnet.vulnweb.com  
- https://portswigger.net/web-security (various labs)
- http://demo.testfire.net

NEVER test production sites without written permission!
"""