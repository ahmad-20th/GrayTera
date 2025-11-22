from abc import ABC, abstractmethod
from typing import List
from core.target import Vulnerability


class BaseScanner(ABC):
    """Base class for all vulnerability scanners"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def scan(self, target_url: str) -> List[Vulnerability]:
        """
        Scan a target URL for vulnerabilities
        Returns a list of discovered vulnerabilities
        """
        pass
