# enums/cert_logs.py

import requests
import threading
from typing import List, Optional, Set, Dict

# Assuming these are defined in a central utility file later
USER_AGENT = "ReconTool/2.0 (authorized-testing-only)"
HEADERS = {"User-Agent": USER_AGENT}
STOP_EVENT = threading.Event()
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs, flush=True)
    except Exception:
        pass

class CTScanner:
    def __init__(self, domain: str):
        self.domain = domain.lower().strip()
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _query_crtsh(self) -> Set[str]:
        safe_print("\n[CT] Querying crt.sh...")
        subdomains = set()
        try:
            url = f"https://crt.sh/?q=%.{self.domain}&output=json"
            response = self.session.get(url, timeout=20 )
            if response.status_code == 200:
                data = response.json()
                for entry in data:
                    for name in entry.get("name_value", "").split("\n"):
                        name = name.strip().lower().lstrip("*.")
                        if name and (name.endswith(self.domain) or name == self.domain):
                            subdomains.add(name)
                safe_print(f"[+] Found {len(subdomains)} unique domains")
        except Exception as e:
            safe_print(f"[!] Error: {type(e).__name__}")
        return subdomains

    def run(self, output_container: Optional[Dict] = None) -> List[str]:
        safe_print(f"\n{'='*60}")
        safe_print(f"[*] CERTIFICATE TRANSPARENCY: {self.domain}")
        safe_print(f"{'='*60}")
        
        all_domains = self._query_crtsh()
        results = sorted(all_domains)
        
        if results:
            safe_print(f"\n[+] Total: {len(results)} domains")
            safe_print(f"[*] Sample (first 10):")
            for domain in results[:10]:
                safe_print(f"    - {domain}")
        
        if output_container is not None:
            output_container["ct"] = {"domain": self.domain, "found_domains": results, "count": len(results)}
        
        return results
