"""
Subdomain Validation Stage: Check if subdomains are live and accessible
Filters out dead/unreachable subdomains before vulnerability scanning
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.stage import Stage
from core.target import Target
from typing import Set, Tuple
import socket
import requests
from urllib.parse import urlparse
import warnings
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class SubdomainValidationStage(Stage):
    """Stage 1.5: Subdomain Validation (between Enumeration and Scope Filtering)"""
    
    def __init__(self, config: dict):
        super().__init__("Subdomain Validation")
        self.config = config or {}
        self.threads = config.get('threads', 20)
        self.timeout = config.get('timeout', 5)  # Reduced from 10 to 5 seconds
        self.dns_timeout = config.get('dns_timeout', 2)  # DNS check timeout
        self.valid_subdomains: Set[str] = set()
        self.dead_subdomains: Set[str] = set()
    
    def execute(self, target: Target) -> bool:
        """
        Validate discovered subdomains by attempting HTTP/HTTPS connections
        
        Args:
            target: Target object with enumerated subdomains
            
        Returns:
            True if validation completed successfully
        """
        if not target.subdomains:
            self.notify("warning", "No subdomains to validate")
            return True
        
        try:
            self.notify("start", f"Validating {len(target.subdomains)} subdomains for live hosts")
            
            self._validate_subdomains(target)
            
            # Update target with only live subdomains
            original_count = len(target.subdomains)
            target.subdomains = self.valid_subdomains.copy()
            
            # Store validation results in metadata
            target.metadata['validated_subdomains'] = list(self.valid_subdomains)
            target.metadata['dead_subdomains'] = list(self.dead_subdomains)
            target.metadata['validation_stats'] = {
                'total_enumerated': original_count,
                'live': len(self.valid_subdomains),
                'dead': len(self.dead_subdomains),
                'uptime_percentage': (len(self.valid_subdomains) / original_count * 100) if original_count > 0 else 0
            }
            
            if self.dead_subdomains:
                self.notify("info", f"Filtered out {len(self.dead_subdomains)} dead subdomain(s)")
            
            self.notify("complete", f"{len(self.valid_subdomains)} live subdomains ready for scanning")
            return True
            
        except Exception as e:
            self.notify("error", f"Subdomain validation failed: {type(e).__name__}: {e}")
            return False
    
    def _validate_subdomains(self, target: Target):
        """Validate subdomains concurrently with fast DNS + HTTP checks"""
        # Calculate total timeout: allow threads to work + buffer
        total_timeout = (len(target.subdomains) * self.timeout) + 30
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            # Submit all tasks
            future_to_subdomain = {
                executor.submit(self._check_subdomain_live, subdomain): subdomain
                for subdomain in target.subdomains
            }
            
            # Process results as they complete
            completed = 0
            for future in as_completed(future_to_subdomain, timeout=total_timeout):
                subdomain = future_to_subdomain[future]
                completed += 1
                
                try:
                    is_live, check_type = future.result(timeout=self.timeout + 3)
                    
                    if is_live:
                        self.valid_subdomains.add(subdomain)
                        self.notify("info", f"✓ Live: {subdomain} [{check_type}]")
                    else:
                        self.dead_subdomains.add(subdomain)
                        
                except Exception as e:
                    self.dead_subdomains.add(subdomain)
    
    def _check_subdomain_live(self, subdomain: str) -> Tuple[bool, str]:
        """
        Fast subdomain validation: DNS check first, then quick HTTP probe
        Returns (is_live, check_type)
        """
        # Normalize subdomain URL
        if not subdomain.startswith(('http://', 'https://')):
            domain_only = subdomain
        else:
            parsed = urlparse(subdomain)
            domain_only = parsed.netloc or parsed.path
        
        # Step 1: Quick DNS resolution (fastest check)
        try:
            socket.setdefaulttimeout(self.dns_timeout)
            socket.gethostbyname(domain_only)
            
            # Step 2: Try quick HTTP HEAD request
            try:
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain_only}"
                    response = requests.head(
                        url,
                        timeout=self.timeout,
                        allow_redirects=False,
                        verify=False
                    )
                    # Consider any response except timeout/connection error as "live"
                    if response.status_code < 500:
                        return True, f"{protocol}"
            except (requests.Timeout, requests.ConnectionError):
                pass
            except Exception:
                pass
            
            # If HTTP checks failed but DNS resolved, it's still "live" (DNS resolved)
            return True, "DNS"
            
        except (socket.gaierror, socket.timeout, OSError):
            return False, "unreachable"
        finally:
            socket.setdefaulttimeout(None)
    
    def is_enabled(self) -> bool:
        """Check if subdomain validation is enabled"""
        return self.config.get('enabled', True)
