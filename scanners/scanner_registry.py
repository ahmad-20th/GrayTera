from typing import List, Dict
from scanners.base_scanner import BaseScanner
from scanners.sqli_scanner import SQLiScanner
from scanners.zap_scanner import ZAPScanner
from scanners.nikto_scanner import NiktoScanner

class ScannerRegistry:
    """Registry for managing vulnerability scanners"""
    
    def __init__(self, config: dict = None):
        self.scanners: Dict[str, BaseScanner] = {}
        self.config = config or {}
        self._register_default_scanners()

    def _register_default_scanners(self):
        self.register(SQLiScanner())
        
        # ZAP Scanner
        zap_config = self.config.get('zap', {})
        
        if zap_config.get('enabled', False):
            api_key = zap_config.get('api_key')
            proxy_url = zap_config.get('proxy_url', 'http://127.0.0.1:8080')
            max_depth = zap_config.get('max_depth', 2)
            max_children = zap_config.get('max_children', 10)
            
            if api_key:
                self.register(ZAPScanner(api_key=api_key, proxy_url=proxy_url,
                                        max_depth=max_depth, max_children=max_children))   

        # Nikto Scanner
        try:
            nikto_config = self.config.get('nikto', {})
            
            if nikto_config.get('enabled', False):
                nikto_path = nikto_config.get('nikto_path')
                timeout = nikto_config.get('timeout', 300)
                
                self.register(NiktoScanner(nikto_path=nikto_path, timeout=timeout))
        except Exception:
            pass
                 
    def register(self, scanner: BaseScanner):
        """Register a new scanner"""
        self.scanners[scanner.name] = scanner
    
    def get_scanner(self, name: str) -> BaseScanner:
        """Get a scanner by name"""
        return self.scanners.get(name)
    
    def get_all_scanners(self) -> List[BaseScanner]:
        """Get all registered scanners"""
        return list(self.scanners.values())
    