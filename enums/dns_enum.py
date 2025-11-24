"""DNS enumeration using dnspython"""

import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Set, List, Optional, Dict, Any

import dns.resolver
import dns.query
import dns.zone
from tqdm import tqdm

from enums.base_enum import BaseEnumerator
from enums.enum_utils import safe_print, load_wordlist, STOP_EVENT


class DNSEnumerator(BaseEnumerator):
    """Strategy: DNS-based enumeration (NS queries, AXFR, bruteforce)"""
    
    def __init__(self, config: dict = None):
        super().__init__("DNS Enumeration")
        self.config = config or {}
        self.threads = int(self.config.get("threads", 10))
        self.wordlist = self.config.get("wordlist")
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 5
        self.resolver.lifetime = 5
    
    def enumerate(self, domain: str) -> Set[str]:
        """Perform DNS enumeration"""
        safe_print(f"\n{'='*60}")
        safe_print(f"[*] DNS RECONNAISSANCE: {domain}")
        safe_print(f"{'='*60}")
        
        found = set()
        
        # 1. Get nameservers
        nameservers = self._get_nameservers(domain)
        
        # 2. Attempt zone transfers
        for ns in nameservers:
            axfr_results = self._attempt_zone_transfer(ns, domain)
            found.update(axfr_results)
        
        # 3. Bruteforce subdomains
        brute_results = self._bruteforce_subdomains(domain)
        found.update(brute_results)
        
        safe_print(f"\n[+] DNS Enumeration found {len(found)} subdomains")
        return found
    
    def _get_nameservers(self, domain: str) -> List[str]:
        """Query nameservers for domain"""
        safe_print(f"\n[DNS] Querying nameservers...")
        try:
            answers = self.resolver.resolve(domain, "NS")
            nameservers = [str(rdata.target).rstrip('.') for rdata in answers]
            safe_print(f"[+] Found {len(nameservers)} nameserver(s)")
            for ns in nameservers:
                safe_print(f"    - {ns}")
            return nameservers
        except Exception as e:
            safe_print(f"[!] NS query failed: {type(e).__name__}")
            return []
    
    def _attempt_zone_transfer(self, ns: str, domain: str) -> Set[str]:
        """Attempt AXFR from a nameserver"""
        if STOP_EVENT.is_set():
            return set()
        
        found = set()
        safe_print(f"[DNS] Attempting zone transfer from {ns}...")
        
        try:
            ns_ip = socket.gethostbyname(ns)
            zone = dns.zone.from_xfr(
                dns.query.xfr(ns_ip, domain, timeout=10)
            )
            
            for name, node in zone.nodes.items():
                for rdataset in node.rdatasets:
                    for rdata in rdataset:
                        name_str = str(name)
                        if name_str and name_str != "@":
                            fqdn = f"{name_str}.{domain}" if not name_str.endswith(domain) else name_str
                            found.add(fqdn.lower())
            
            if found:
                safe_print(f"[+] SUCCESS! Got {len(found)} records from AXFR")
        
        except Exception:
            safe_print(f"[-] Zone transfer failed")
        
        return found
    
    def _bruteforce_subdomains(self, domain: str) -> Set[str]:
        """Brute-force subdomains using wordlist"""
        words = load_wordlist(self.wordlist)
        if not words:
            return set()
        
        found = set()
        safe_print(f"\n[*] Enumerating {len(words)} subdomains with {self.threads} threads...")
        
        def check_subdomain(word: str) -> Optional[str]:
            if STOP_EVENT.is_set():
                return None
            
            fqdn = f"{word}.{domain}"
            try:
                self.resolver.resolve(fqdn, "A")
                return fqdn.lower()
            except Exception:
                return None
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = [executor.submit(check_subdomain, word) for word in words]
            
            with tqdm(total=len(words), desc="DNS Brute", unit="sub") as pbar:
                for future in as_completed(futures):
                    if STOP_EVENT.is_set():
                        break
                    
                    try:
                        result = future.result()
                        if result:
                            found.add(result)
                            safe_print(f"[+] Found: {result}")
                    except Exception:
                        pass
                    
                    pbar.update(1)
        
        return found