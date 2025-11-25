"""Search engine dorking enumeration"""

import random
import time
from typing import Set, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from enums.base_enum import BaseEnumerator
from enums.enum_utils import STOP_EVENT


class DorkEnumerator(BaseEnumerator):
    """Strategy: Search engine dorking enumeration via Bing"""
    
    def __init__(self, config: dict = None):
        super().__init__("Search Engine Dorking")
        self.config = config or {}
        self.pages = int(self.config.get("dork_pages", 2))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GrayTera/1.0 (authorized-testing-only)'
        })
    
    def enumerate(self, domain: str) -> Set[str]:
        """Perform search engine dorking"""
        if STOP_EVENT.is_set():
            return set()
        
        found = set()
        dorks = [
            f"site:{domain}",
            f"site:{domain} inurl:login",
            f"site:{domain} inurl:admin"
        ]
        
        for dork in dorks:
            for page in range(1, self.pages + 1):
                html = self._bing_search(dork, page)
                if html:
                    links = self._extract_links(html, domain)
                    found.update(links)
                time.sleep(random.uniform(2.0, 3.0))
        
        # Convert URLs to subdomains
        subdomains = self._extract_subdomains_from_urls(found, domain)
        
        return subdomains
    
    def _bing_search(self, query: str, page: int = 1) -> str:
        """Perform Bing search query"""
        try:
            params = {"q": query, "first": (page - 1) * 10 + 1}
            response = self.session.get(
                "https://www.bing.com/search",
                params=params,
                timeout=8
            )
            return response.text if response.status_code == 200 else ""
        except Exception:
            return ""
    
    def _extract_links(self, html: str, domain: str) -> Set[str]:
        """Extract domain URLs from HTML"""
        links = set()
        try:
            soup = BeautifulSoup(html, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if href.startswith("http") and domain in href:
                    href = href.split("#")[0].split("?")[0]
                    links.add(href.rstrip("/"))
        except Exception:
            pass
        
        return links
    
    def _extract_subdomains_from_urls(self, urls: Set[str], domain: str) -> Set[str]:
        """Extract subdomains from a set of URLs"""
        subdomains = set()
        
        for url in urls:
            try:
                parsed = urlparse(url)
                host = parsed.netloc.split(':')[0].lower()
                
                # Only add if it's actually part of the target domain
                if host.endswith(domain) or host == domain:
                    subdomains.add(host)
            except Exception:
                pass
        
        return subdomains