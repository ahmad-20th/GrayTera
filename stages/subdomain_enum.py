import dns.resolver
import requests
import threading
from typing import Set, Dict, Optional
from urllib.parse import urlparse

from core.stage import Stage
from core.target import Target

# Import scanners implemented in enums/ so this stage can orchestrate them
from enums import CTScanner, DNSRecon, DorkScanner


class SubdomainEnumStage(Stage):
    """Stage 1: Subdomain Enumeration (integrates CT, DNS, and dorking)

    This implementation wires together the standalone enumerators found in
    `enums/` so the stage follows the project's Pipeline/Strategy/Observer
    conventions (see DESIGN.md).

    Behavior summary:
    - Runs DNSRecon.run() (which attempts NS, AXFR and optional wordlist bruteforce)
    - Runs CTScanner.run() to collect certificate-transparency discovered names
    - Runs DorkScanner.run() to scrape public URLs and extract hostnames
    - Adds all discovered unique hostnames to the Target via target.add_subdomain()
    - Notifies observers of each discovered subdomain using self.notify("subdomain_found", ...)
    """

    def __init__(self, config: dict):
        super().__init__("Subdomain Enumeration")
        self.config = config or {}
        self.timeout = int(self.config.get("timeout", 10))
        self.lock = threading.Lock()

    def execute(self, target: Target) -> bool:
        """Enumerate subdomains for the target and attach them to the Target object."""
        self.notify("start", f"Enumerating subdomains for {target.domain}")
        domain = target.domain
        found: Set[str] = set()
        results_container: Dict[str, any] = {}

        # 1) DNSRecon - nameservers, AXFR, and optional wordlist enumeration
        try:
            dns_conf = self.config.get("dns", {}) if isinstance(self.config.get("dns"), dict) else {}
            wordlist = dns_conf.get("wordlist") or self.config.get("subdomain_wordlist")
            threads = int(dns_conf.get("threads", self.config.get("threads", 10)))
            dns_recon = DNSRecon(domain, threads=threads, subdomain_wordlist=wordlist)
            dns_results = dns_recon.run(results_container)

            # dns_results may contain 'subs' as a list of {"fqdn":..., "ips": [...]} entries
            for entry in dns_results.get("subs", []):
                fqdn = entry.get("fqdn")
                if fqdn:
                    found.add(fqdn.lower())

            # AXFR records (if any) may also contain raw names
            for axfr in dns_results.get("axfr", []):
                for record in axfr.get("records", []):
                    # record is (name, type, value)
                    if record and len(record) >= 1:
                        name = str(record[0])
                        if name and name != "@":
                            fqdn = f"{name}.{domain}" if not str(name).endswith(domain) else str(name)
                            found.add(fqdn.lower())

        except Exception as e:
            self.notify("warning", f"DNSRecon failed: {type(e).__name__}: {e}")

        # 2) Certificate Transparency (crt.sh / CT logs)
        try:
            ct = CTScanner(domain)
            ct_domains = ct.run(results_container)
            for d in ct_domains or []:
                found.add(d.lower())
        except Exception as e:
            self.notify("warning", f"CTScanner failed: {type(e).__name__}: {e}")

        # 3) Search engine dorking (extract hosts from returned URLs)
        try:
            pages = int(self.config.get("dork_pages", 2))
            dork = DorkScanner(domain, pages=pages)
            urls = dork.run(results_container)
            for u in urls or []:
                host = self._extract_host(u)
                if host and host.endswith(domain):
                    found.add(host.lower())
        except Exception as e:
            self.notify("warning", f"DorkScanner failed: {type(e).__name__}: {e}")

        # 4) Common subdomain heuristics (quick checks)
        try:
            common_subdomains = self.config.get("common_subdomains", ['www', 'mail', 'ftp', 'admin', 'blog', 'dev', 'api'])
            for sub in common_subdomains:
                fqdn = f"{sub}.{domain}"
                if self._check_subdomain_exists(fqdn):
                    found.add(fqdn.lower())
        except Exception:
            # non-fatal
            pass

        # Finalize: add to target and notify observers
        added = 0
        for fqdn in sorted(found):
            with self.lock:
                target.add_subdomain(fqdn)
                self.notify("subdomain_found", fqdn)
                added += 1

        self.notify("complete", f"Found {added} subdomains")
        # Optionally persist raw results into target.meta if it exists
        try:
            if hasattr(target, 'meta') and isinstance(target.meta, dict):
                target.meta.setdefault('enum_results', {}).update(results_container)
        except Exception:
            pass

        return True

    def _extract_host(self, url: str) -> Optional[str]:
        try:
            parsed = urlparse(url)
            return parsed.netloc.split(':')[0]
        except Exception:
            return None

    def _check_subdomain_exists(self, subdomain: str) -> bool:
        """Verify if subdomain resolves to an A record"""
        try:
            dns.resolver.resolve(subdomain, 'A')
            return True
        except Exception:
            return False
