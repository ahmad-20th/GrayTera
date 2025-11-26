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
    subdomains: set = field(default_factory=set)  # Changed from List to set
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    exploited: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_subdomain(self, subdomain: str) -> None:
        """Add subdomain (automatically deduplicates)"""
        if subdomain:
            self.subdomains.add(subdomain)  # Changed from append to add
    
    def add_vulnerability(self, vuln: Vulnerability) -> None:
        """Add vulnerability with validation"""
        if vuln and isinstance(vuln, Vulnerability):
            self.vulnerabilities.append(vuln)
    
    def add_exploit_result(self, result: Dict[str, Any]) -> None:
        """Add exploitation result"""
        if result:
            self.exploited.append(result)