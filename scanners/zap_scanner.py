from scanners.base_scanner import BaseScanner
from core.target import Vulnerability
from typing import List
from datetime import datetime
import time


class ZAPScanner(BaseScanner):
    """OWASP ZAP vulnerability scanner integration"""
    
    def __init__(self, api_key: str = None, proxy_url: str = 'http://127.0.0.1:8080'):
        super().__init__("ZAP Scanner")
        self.api_key = api_key
        self.proxy_url = proxy_url
        self.zap = None

    def _initialize_zap(self):
        """Initialize ZAP connection"""
        if self.zap:  # Already initialized
            return
            
        try:
            from zapv2 import ZAPv2
            
            if not self.api_key:
                raise ValueError("ZAP API key is required. Set it in config.yaml")
            
            self.zap = ZAPv2(
                apikey=self.api_key,
                proxies={'http': self.proxy_url, 'https': self.proxy_url}
            )
            
            # Test connection
            self.zap.core.version
            
        except ImportError:
            raise ImportError(
                "python-owasp-zap-v2.4 not installed. "
                "Install with: pip install python-owasp-zap-v2.4"
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to ZAP: {e}")

    def scan(self, target_url: str) -> List[Vulnerability]:
        # Initialize on first scan
        self._initialize_zap()
        
        if not self.zap:
            return []
    
    def _access_target(self, target_url: str):
        """Force ZAP to learn about the target"""
        try:
            self.zap.urlopen(target_url)
            time.sleep(2)
        except Exception as e:
            print(f"[!] Failed to access target: {e}")
    
    def _run_spider(self, target_url: str):
        """Run ZAP spider scan"""
        try:
            print(f"[ZAP] Starting spider scan on {target_url}")
            spider_scan_id = self.zap.spider.scan(target_url)
            
            # Wait for spider completion
            while int(self.zap.spider.status(spider_scan_id)) < 100:
                status = self.zap.spider.status(spider_scan_id)
                print(f"[ZAP] Spider progress: {status}%")
                time.sleep(5)
            
            print(f"[ZAP] Spider scan completed")
            
        except Exception as e:
            print(f"[!] Spider scan error: {e}")
    
    def _run_active_scan(self, target_url: str):
        """Run ZAP active scan"""
        try:
            print(f"[ZAP] Starting active scan on {target_url}")
            active_scan_id = self.zap.ascan.scan(target_url)
            
            # Wait for active scan completion
            while int(self.zap.ascan.status(active_scan_id)) < 100:
                status = self.zap.ascan.status(active_scan_id)
                print(f"[ZAP] Active scan progress: {status}%")
                time.sleep(10)
            
            print(f"[ZAP] Active scan completed")
            
        except Exception as e:
            print(f"[!] Active scan error: {e}")
    
    def _retrieve_alerts(self, target_url: str) -> List[Vulnerability]:
        """Retrieve and convert ZAP alerts to GrayTera vulnerabilities"""
        vulnerabilities = []
        
        try:
            alerts = self.zap.core.alerts()
            
            print(f"[ZAP] Found {len(alerts)} alerts")
            
            for alert in alerts:
                vuln = self._convert_alert_to_vulnerability(alert, target_url)
                if vuln:
                    vulnerabilities.append(vuln)
            
        except Exception as e:
            print(f"[!] Failed to retrieve alerts: {e}")
        
        return vulnerabilities
    
    def _convert_alert_to_vulnerability(self, alert: dict, base_url: str) -> Vulnerability:
        """Convert ZAP alert to GrayTera Vulnerability object"""
        try:
            # Map ZAP risk levels to severity
            risk_mapping = {
                'High': 'high',
                'Medium': 'medium',
                'Low': 'low',
                'Informational': 'info'
            }
            
            severity = risk_mapping.get(alert.get('risk', 'Low'), 'low')
            
            # Create vulnerability object
            vuln = Vulnerability(
                vuln_type=self._categorize_alert(alert.get('alert', 'Unknown')),
                severity=severity,
                url=alert.get('url', base_url),
                parameter=alert.get('param', 'N/A'),
                payload=alert.get('attack', 'N/A'),
                evidence=self._build_evidence(alert),
                timestamp=datetime.now()
            )
            
            return vuln
            
        except Exception as e:
            print(f"[!] Failed to convert alert: {e}")
            return None
    
    def _categorize_alert(self, alert_name: str) -> str:
        """Categorize ZAP alert into vulnerability type"""
        alert_lower = alert_name.lower()
        
        if 'sql' in alert_lower or 'injection' in alert_lower:
            return 'sqli'
        elif 'xss' in alert_lower or 'cross site scripting' in alert_lower:
            return 'xss'
        elif 'csrf' in alert_lower or 'cross site request forgery' in alert_lower:
            return 'csrf'
        elif 'xxe' in alert_lower:
            return 'xxe'
        elif 'path traversal' in alert_lower or 'directory' in alert_lower:
            return 'path_traversal'
        elif 'file inclusion' in alert_lower:
            return 'lfi'
        elif 'command injection' in alert_lower:
            return 'command_injection'
        else:
            return 'other'
    
    def _build_evidence(self, alert: dict) -> str:
        """Build evidence string from ZAP alert"""
        evidence_parts = []
        
        if alert.get('alert'):
            evidence_parts.append(f"Alert: {alert['alert']}")
        
        if alert.get('description'):
            evidence_parts.append(f"Description: {alert['description']}")
        
        if alert.get('confidence'):
            evidence_parts.append(f"Confidence: {alert['confidence']}")
        
        if alert.get('evidence'):
            evidence_parts.append(f"Evidence: {alert['evidence']}")
        
        return " | ".join(evidence_parts)