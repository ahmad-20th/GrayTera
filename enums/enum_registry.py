from typing import List, Dict
from enums.base_enum import BaseEnumerator
from enums.dns_enum import DNSEnumerator
from enums.ct_enum import CTEnumerator
from enums.dork_enum import DorkEnumerator

class EnumeratorRegistry:
    """Registry for managing subdomain enumeration strategies"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.enumerators: Dict[str, BaseEnumerator] = {}
        self._register_default_enumerators()
    
    def _register_default_enumerators(self):
        """Register built-in enumerators based on config"""
        # Register enabled enumerators
        if self.config.get("use_dns", True):
            self.register(DNSEnumerator(self.config.get("dns", {})))
        
        if self.config.get("use_crt_sh", True):
            self.register(CTEnumerator(self.config.get("ct", {})))
        
        if self.config.get("use_dorking", True):
            self.register(DorkEnumerator(self.config.get("dork", {})))
    
    def register(self, enumerator: BaseEnumerator):
        """Register a new enumerator strategy"""
        self.enumerators[enumerator.name] = enumerator
    
    def get_enumerator(self, name: str) -> BaseEnumerator:
        """Get enumerator by name"""
        return self.enumerators.get(name)
    
    def get_all_enumerators(self) -> List[BaseEnumerator]:
        """Get all registered enumerators"""
        return list(self.enumerators.values())
    
    def unregister(self, name: str):
        """Remove an enumerator"""
        if name in self.enumerators:
            del self.enumerators[name]