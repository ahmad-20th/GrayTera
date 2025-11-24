"""Certificate Transparency enumeration"""

from typing import Set, List, Optional, Dict, Any

import requests

from enums.base_enum import BaseEnumerator
from enums.enum_utils import safe_print


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
        safe_print(f"\n{'='*60}")
        safe_print(f"[*] CERTIFICATE TRANSPARENCY: {domain}")
        safe_print(f"{'='*60}")
        
        found = self._query_crtsh(domain)
        
        safe_print(f"\n[+] Found {len(found)} unique domains from CT logs")
        
        if found and len(found) <= 10:
            safe_print(f"[*] Results:")
            for sub in sorted(found):
                safe_print(f"    - {sub}")
        elif found:
            safe_print(f"[*] Sample (first 10):")
            for sub in sorted(found)[:10]:
                safe_print(f"    - {sub}")
        
        return found
    
    def _query_crtsh(self, domain: str) -> Set[str]:
        """Query crt.sh API for subdomains"""
        safe_print("\n[CT] Querying crt.sh...")
        subdomains = set()
        
        try:
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            response = self.session.get(url, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                for entry in data:
                    for name in entry.get("name_value", "").split("\n"):
                        name = name.strip().lower().lstrip("*.")
                        if name and (name.endswith(domain) or name == domain):
                            subdomains.add(name)
        
        except Exception as e:
            safe_print(f"[!] Error: {type(e).__name__}")
        
        return subdomains