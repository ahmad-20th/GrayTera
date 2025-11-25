from typing import List, Dict
from scanners.base_scanner import BaseScanner
from scanners.sqli_scanner import SQLiScanner
from scanners.zap_scanner import ZAPScanner

class ScannerRegistry:
    """Registry for managing vulnerability scanners"""
    
    def __init__(self, config: dict = None):
        self.scanners: Dict[str, BaseScanner] = {}
        self.config = config or {}
        self._register_default_scanners()

    def _register_default_scanners(self):
        self.register(SQLiScanner())
        
        # Config is already the vulnerability_scan section
        zap_config = self.config.get('zap', {})
        
        if zap_config.get('enabled') and zap_config.get('api_key'):
            self.register(ZAPScanner(
                api_key=zap_config['api_key'],
                proxy_url=zap_config.get('proxy_url', 'http://127.0.0.1:8080')
            ))    
                      
    def register(self, scanner: BaseScanner):
        """Register a new scanner"""
        self.scanners[scanner.name] = scanner
    
    def get_scanner(self, name: str) -> BaseScanner:
        """Get a scanner by name"""
        return self.scanners.get(name)
    
    def get_all_scanners(self) -> List[BaseScanner]:
        """Get all registered scanners"""
        return list(self.scanners.values())
    