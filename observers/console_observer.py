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
