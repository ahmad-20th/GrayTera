# enums/dns_zone.py

import dns.resolver
import dns.query
import dns.zone
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import List, Optional, Tuple, Dict, Any

# Assuming these are defined in a central utility file later, but for now, they are here.
STOP_EVENT = threading.Event()
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs, flush=True)
    except Exception:
        pass

def load_file_lines(path: str) -> List[str]:
    if not path or not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        return lines
    except Exception:
        return []

class DNSRecon:
    def __init__(self, domain: str, threads: int = 10, subdomain_wordlist: Optional[str] = None):
        self.domain = domain.lower().strip()
        self.threads = max(1, min(threads, 50))
        self.subdomain_wordlist = subdomain_wordlist
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 5
        self.resolver.lifetime = 5

    def get_nameservers(self) -> List[str]:
        safe_print(f"\n[DNS] Querying nameservers for {self.domain}...")
        try:
            answers = self.resolver.resolve(self.domain, "NS")
            nameservers = [str(rdata.target).rstrip('.') for rdata in answers]
            safe_print(f"[+] Found {len(nameservers)} nameserver(s)")
            for ns in nameservers:
                safe_print(f"    - {ns}")
            return nameservers
        except Exception as e:
            safe_print(f"[!] NS query failed: {type(e).__name__}")
            return []

    def try_axfr(self, nameserver: str) -> List[Tuple[str, str, str]]:
        safe_print(f"[DNS] Attempting zone transfer from {nameserver}...")
        records = []
        try:
            ns_ip = socket.gethostbyname(nameserver)
            zone = dns.zone.from_xfr(dns.query.xfr(ns_ip, self.domain, timeout=10))
            if zone:
                for name, node in zone.nodes.items():
                    for rdataset in node.rdatasets:
                        for rdata in rdataset:
                            records.append((str(name), dns.rdatatype.to_text(rdataset.rdtype), str(rdata)))
                safe_print(f"[+] SUCCESS! Got {len(records)} records")
        except:
            safe_print(f"[-] Zone transfer failed")
        return records

    def _resolve_name(self, fqdn: str) -> Optional[Tuple[str, List[str]]]:
        if STOP_EVENT.is_set():
            return None
        try:
            answers = self.resolver.resolve(fqdn, "A")
            ips = [str(rdata) for rdata in answers]
            return (fqdn, ips)
        except:
            return None

    def enumerate_subdomains(self, wordlist: str) -> List[Tuple[str, List[str]]]:
        words = load_file_lines(wordlist)
        if not words:
            return []
        
        results = []
        safe_print(f"[*] Enumerating {len(words)} subdomains with {self.threads} threads...")
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self._resolve_name, f"{word}.{self.domain}"): word for word in words}
            
            with tqdm(total=len(words), desc="DNS Enum", unit="sub") as pbar:
                for future in as_completed(futures):
                    if STOP_EVENT.is_set():
                        break
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                            safe_print(f"[+] Found: {result[0]} -> {result[1]}")
                    except:
                        pass
                    pbar.update(1)
        
        return results

    def get_common_records(self) -> Dict[str, List[str]]:
        safe_print(f"\n[DNS] Querying common record types...")
        records = {}
        for rtype in ["A", "AAAA", "MX", "TXT", "SOA"]:
            try:
                answers = self.resolver.resolve(self.domain, rtype)
                records[rtype] = [str(rdata) for rdata in answers]
                safe_print(f"[+] {rtype}: {len(records[rtype])} record(s)")
            except:
                records[rtype] = []
        return records

    def run(self, results_container: Optional[Dict] = None) -> Dict[str, Any]:
        safe_print(f"\n{'='*60}")
        safe_print(f"[*] DNS RECONNAISSANCE: {self.domain}")
        safe_print(f"{'='*60}")
        
        results = {"domain": self.domain, "ns": [], "axfr": [], "common_records": {}, "subs": []}
        
        nameservers = self.get_nameservers()
        results["ns"] = nameservers
        
        for ns in nameservers:
            if STOP_EVENT.is_set():
                break
            records = self.try_axfr(ns)
            if records:
                results["axfr"].append({"nameserver": ns, "records": records})
        
        results["common_records"] = self.get_common_records()
        
        if not results["axfr"] and self.subdomain_wordlist:
            subs = self.enumerate_subdomains(self.subdomain_wordlist)
            results["subs"] = [{"fqdn": fqdn, "ips": ips} for fqdn, ips in subs]
        
        if results_container is not None:
            results_container["dns"] = results
        
        return results
