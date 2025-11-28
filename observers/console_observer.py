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
            'cve': '\033[95m',       # Magenta (prominent for CVEs)
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
        
        elif event == 'info':
            self._print_info(f"[{timestamp}] [{stage}] {data}")
        
        elif event == 'info_stop':
            # Just ignore this event
            pass
        
        elif event == 'subdomain_found':
            self._print_info(f"[{timestamp}] [+] Subdomain: {data}")
        
        elif event == 'filtered_subdomain':
            self._print_warning(f"[{timestamp}] [-] Out-of-scope: {data}")
        
        elif event == 'vulnerability_found':
            # Suppress individual vulnerability output - will show consolidated later
            pass
        
        elif event == 'exploit_success':
            cve_id = data.get('cve_id', 'Unknown')
            param_count = data.get('parameters_exploited', 1)
            self._print_success(f"[{timestamp}] [✓] Exploited {cve_id}: {param_count} parameter(s) compromised")
        
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
    
    def print_consolidated_cve_findings(self, cve_map: dict) -> None:
        """
        Display consolidated CVE findings in standard format with NIST links
        
        Args:
            cve_map: Dict from CVEMapper.deduplicate_by_cve()
        """
        if not cve_map:
            return
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if 'UNCATEGORIZED' in cve_map:
            uncategorized = cve_map.pop('UNCATEGORIZED')
            total_uncategorized = uncategorized.get('count', 0)
            print(f"{self.colors['warning']}[{timestamp}] [!] {total_uncategorized} Uncategorized Vulnerability(ies){self.colors['reset']}")
            print(f"    Type: {uncategorized['vuln_type'].upper()}")
            print(f"    Severity: {uncategorized.get('severity', 'unknown').upper()}\n")
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_cves = sorted(cve_map.items(), 
                            key=lambda x: severity_order.get(x[1]['severity'], 4))
        
        for cve_id, finding in sorted_cves:
            severity = finding.get('severity', 'unknown').upper()
            severity_color = self._get_severity_color(finding.get('severity', 'medium'))
            count = finding.get('count', 1)
            affected_params = finding.get('affected_parameters', [])
            
            # Standard format with timestamp and stage
            nist_url = f"https://nvd.nist.gov/vuln/detail/{cve_id}"
            print(f"{severity_color}[{timestamp}] [CVE] {cve_id}{self.colors['reset']}")
            print(f"    Type: {finding['vuln_type'].upper()}")
            print(f"    Severity: {severity}")
            print(f"    Affected: {count} parameter(s) across {len(set(p['url'] for p in affected_params))} endpoint(s)")
            print(f"    Details: {nist_url}\n")

