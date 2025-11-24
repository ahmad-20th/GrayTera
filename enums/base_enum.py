from abc import ABC, abstractmethod
from typing import Set

class BaseEnumerator(ABC):
    """Strategy interface for subdomain enumeration techniques"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def enumerate(self, domain: str) -> Set[str]:
        """
        Enumerate subdomains using a specific technique.
        Returns a set of discovered subdomains (FQDNs).
        """
        pass