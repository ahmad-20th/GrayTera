"""Search engine dorking enumeration"""

import random
import time
import re
from typing import Set, Optional
from urllib.parse import urlparse, unquote

import requests
from bs4 import BeautifulSoup

from enums.base_enum import BaseEnumerator
from enums.enum_utils import STOP_EVENT


class DorkEnumerator(BaseEnumerator):
    """Strategy: Search engine dorking enumeration via Bing and Google cache"""
    
    def __init__(self, config: dict = None):
        super().__init__("Search Engine Dorking")
        self.config = config or {}
        self.pages = int(self.config.get("dork_pages", 3))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def enumerate(self, domain: str) -> Set[str]:
        """Perform search engine dorking"""
        if STOP_EVENT.is_set():
            return set()
        
        found = set()
        
        # Try multiple dork strategies
        dorks = [
            f"site:{domain}",
            f"site:{domain} inurl:/",
            f"site:{domain} inurl:admin",
            f"site:{domain} inurl:login",
            f"site:{domain} inurl:api",
            f"site:{domain} inurl:dev",
            f"site:{domain} inurl:test",
        ]
        
        for dork in dorks:
            if STOP_EVENT.is_set():
                break
                
            for page in range(1, self.pages + 1):
                if STOP_EVENT.is_set():
                    break
                    
                # Try Bing
                html = self._bing_search(dork, page)
                if html:
                    links = self._extract_links(html, domain)
                    found.update(links)
                
                time.sleep(random.uniform(1.0, 2.0))
        
        # Convert URLs to subdomains
        subdomains = self._extract_subdomains_from_urls(found, domain)
        
        return subdomains
    
    def _bing_search(self, query: str, page: int = 1) -> str:
        """Perform Bing search query"""
        try:
            params = {
                "q": query,
                "first": (page - 1) * 10 + 1
            }
            response = self.session.get(
                "https://www.bing.com/search",
                params=params,
                timeout=10,
                allow_redirects=True
            )
            if response.status_code == 200:
                return response.text
            return ""
        except Exception:
            return ""
    
    def _extract_links(self, html: str, domain: str) -> Set[str]:
        """Extract domain URLs from HTML using multiple strategies"""
        links = set()
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Strategy 1: Find all links in search results
            for a_tag in soup.find_all("a", href=True):
                href = a_tag.get("href", "")
                if not href:
                    continue
                    
                # Decode URL
                try:
                    href = unquote(href)
                except:
                    pass
                
                # Look for actual domain URLs
                if domain in href and href.startswith("http"):
                    # Clean URL
                    href = href.split("#")[0].split("?")[0]
                    links.add(href.rstrip("/"))
                
                # Look for /search?q= style links that contain domain
                elif "/search?q=" in href and domain in href:
                    # Extract the URL from the search parameter
                    match = re.search(r'q=([^&]+)', href)
                    if match:
                        extracted = unquote(match.group(1))
                        if domain in extracted and extracted.startswith("http"):
                            extracted = extracted.split("#")[0].split("?")[0]
                            links.add(extracted.rstrip("/"))
            
            # Strategy 2: Look for h2 or h3 with links
            for heading in soup.find_all(['h2', 'h3']):
                link = heading.find('a')
                if link and link.get('href'):
                    href = link.get('href', '')
                    if domain in href and href.startswith("http"):
                        href = href.split("#")[0].split("?")[0]
                        links.add(href.rstrip("/"))
            
            # Strategy 3: Regex fallback - find URLs in text
            url_pattern = r'https?://[^\s"<>)]+' + domain + r'[^\s"<>)*]*'
            for match in re.finditer(url_pattern, html):
                url = match.group(0).split("#")[0].split("?")[0].rstrip(")/")
                if url.startswith("http"):
                    links.add(url)
        
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