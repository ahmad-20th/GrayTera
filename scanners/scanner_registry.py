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

