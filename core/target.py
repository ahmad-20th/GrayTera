from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
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
    cve_id: Optional[str] = None  # CVE identifier for deduplication
    
    def get_fingerprint(self) -> str:
        """Generate unique fingerprint for deduplication (url + param + payload)"""
        return f"{self.url}:{self.parameter}:{self.payload}:{self.vuln_type}".lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.vuln_type,
            "severity": self.severity,
            "url": self.url,
            "parameter": self.parameter,
            "payload": self.payload,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
            "cve_id": self.cve_id
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Vulnerability":
        """Create Vulnerability from dictionary (JSON deserialization)"""
        return Vulnerability(
            vuln_type=data.get("type", "unknown"),
            severity=data.get("severity", "medium"),
            url=data.get("url", ""),
            parameter=data.get("parameter", ""),
            payload=data.get("payload", ""),
            evidence=data.get("evidence", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            cve_id=data.get("cve_id")
        )


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
    
    def add_vulnerability(self, vuln: Vulnerability) -> bool:
        """
        Add vulnerability with deduplication
        
        Args:
            vuln: Vulnerability to add
            
        Returns:
            True if added (new), False if duplicate
        """
        if not vuln or not isinstance(vuln, Vulnerability):
            return False
        
        # Check if this vulnerability already exists (by fingerprint)
        fingerprint = vuln.get_fingerprint()
        for existing in self.vulnerabilities:
            if existing.get_fingerprint() == fingerprint:
                # Duplicate found, don't add
                return False
        
        # New vulnerability, add it
        self.vulnerabilities.append(vuln)
        return True
    
    def add_exploit_result(self, result: Dict[str, Any]) -> None:
        """Add exploitation result"""
        if result:
            self.exploited.append(result)
    
    def get_unique_vulnerabilities_by_type(self) -> Dict[str, List[Vulnerability]]:
        """Group vulnerabilities by type"""
        grouped = {}
        for vuln in self.vulnerabilities:
            if vuln.vuln_type not in grouped:
                grouped[vuln.vuln_type] = []
            grouped[vuln.vuln_type].append(vuln)
        return grouped
    
    def get_vulnerability_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        by_type = self.get_unique_vulnerabilities_by_type()
        by_severity = {}
        for vuln in self.vulnerabilities:
            if vuln.severity not in by_severity:
                by_severity[vuln.severity] = 0
            by_severity[vuln.severity] += 1
        
        return {
            "total": len(self.vulnerabilities),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "by_severity": by_severity
        }