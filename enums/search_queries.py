# enums/search_queries.py

import requests
import time
import random
from bs4 import BeautifulSoup
from typing import List, Optional, Set, Dict

# Assuming these are defined in a central utility file later
USER_AGENT = "ReconTool/2.0 (authorized-testing-only)"
HEADERS = {"User-Agent": USER_AGENT}
DEFAULT_TIMEOUT = 8
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs, flush=True)
    except Exception:
        pass

class DorkScanner:
    def __init__(self, domain: str, pages: int = 2):
        self.domain = domain.lower().strip()
        self.pages = max(1, min(pages, 3))
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _bing_search(self, query: str, page: int = 1) -> str:
        try:
            params = {"q": query, "first": (page - 1) * 10 + 1}
            response = self.session.get("https://www.bing.com/search", params=params, timeout=DEFAULT_TIMEOUT )
            return response.text if response.status_code == 200 else ""
        except:
            return ""

    def _extract_links(self, html: str) -> Set[str]:
        links = set()
        try:
            soup = BeautifulSoup(html, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if href.startswith("http" ) and self.domain in href:
                    href = href.split("#")[0].split("?")[0]
                    links.add(href.rstrip("/"))
        except:
            pass
        return links

    def run(self, output_container: Optional[Dict] = None) -> List[str]:
        safe_print(f"\n{'='*60}")
        safe_print(f"[*] SEARCH ENGINE DORKING: {self.domain}")
        safe_print(f"{'='*60}")
        
        found = set()
        dorks = [
            f"site:{self.domain}",
            f"site:{self.domain} inurl:login",
            f"site:{self.domain} inurl:admin"
        ]
        
        for dork in dorks:
            safe_print(f"\n[DORK] {dork}")
            for page in range(1, self.pages + 1):
                html = self._bing_search(dork, page)
                if html:
                    links = self._extract_links(html)
                    if links:
                        safe_print(f"  Page {page}: {len(links)} URLs")
                        found.update(links)
                time.sleep(random.uniform(2.0, 3.0))
        
        results = sorted(found)
        safe_print(f"\n[+] Total: {len(results)} URLs")
        
        if output_container is not None:
            output_container["dork"] = {"domain": self.domain, "urls": results, "count": len(results)}
        
        return results
