"""Certificate Transparency enumeration"""

from typing import Set

import requests

from enums.base_enum import BaseEnumerator


class CTEnumerator(BaseEnumerator):
    """Strategy: Certificate Transparency enumeration via crt.sh"""
    
    def __init__(self, config: dict = None):
        super().__init__("Certificate Transparency")
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GrayTera/1.0 (authorized-testing-only)'
        })
    
    def enumerate(self, domain: str) -> Set[str]:
        """Query crt.sh for subdomains"""
        return self._query_crtsh(domain)
    
    def _query_crtsh(self, domain: str) -> Set[str]:
        """Query crt.sh API for subdomains"""
        subdomains: Set[str] = set()
        
        try:
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            response = self.session.get(url, timeout=20)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if not isinstance(data, list):
                        return subdomains
                    
                    for entry in data:
                        if not isinstance(entry, dict):
                            continue
                        
                        for name in entry.get("name_value", "").split("\n"):
                            name = name.strip().lower().lstrip("*.")
                            if name and (name.endswith(domain) or name == domain):
                                subdomains.add(name)
                
                except ValueError:
                    pass
        
        except Exception:
            pass
        
        return subdomains