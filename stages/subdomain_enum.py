import dns.resolver
import threading
from typing import Set
from urllib.parse import urlparse

from core.stage import Stage
from core.target import Target
from enums.enum_registry import EnumeratorRegistry


class SubdomainEnumStage(Stage):
    """Stage 1: Subdomain Enumeration (using Strategy Pattern)"""

    def __init__(self, config: dict):
        super().__init__("Subdomain Enumeration")
        self.config = config or {}
        self.lock = threading.Lock()
        try:
            self.enum_registry = EnumeratorRegistry(config)
        except Exception as e:
            self.notify("error", f"Failed to initialize EnumeratorRegistry: {e}")
            self.enum_registry = None

    def execute(self, target: Target) -> bool:
        """Enumerate subdomains using all registered strategies"""
        self.notify("start", f"Enumerating subdomains for {target.domain}")
        domain = target.domain
        found: Set[str] = set()

        # Run all enumeration strategies
        for enumerator in self.enum_registry.get_all_enumerators():
            try:
                self.notify("info", f"Running {enumerator.name}...")
                subdomains = enumerator.enumerate(domain)
                found.update(subdomains)
                self.notify("info", f"{enumerator.name} found {len(subdomains)} subdomains")

            except Exception as e:
                self.notify("warning", f"{enumerator.name} failed: {type(e).__name__}: {e}")

        # Add common subdomains (simple heuristic strategy)
        try:
            common_subdomains = self.config.get("common_subdomains",
                                                ['www', 'mail', 'ftp', 'admin', 'blog', 'dev', 'api'])
            for sub in common_subdomains:
                fqdn = f"{sub}.{domain}"
                if self._check_subdomain_exists(fqdn):
                    found.add(fqdn.lower())
        except Exception:
            pass

        # Finalize: add to target and notify observers
        added = 0
        for fqdn in sorted(found):
            with self.lock:
                target.add_subdomain(fqdn)
                self.notify("subdomain_found", fqdn)
                added += 1

        self.notify("complete", f"Found {added} subdomains")
        return True

    def _check_subdomain_exists(self, subdomain: str) -> bool:
        """Verify if subdomain resolves to an A record"""
        try:
            dns.resolver.resolve(subdomain, 'A')
            return True
        except Exception:
            return False
