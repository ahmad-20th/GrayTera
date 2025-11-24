"""Shared utilities for enumeration"""

import os
import threading
from typing import List, Optional

# Global stop event (shared across all enumerators)
STOP_EVENT = threading.Event()

def safe_print(*args, **kwargs) -> None:
    """Thread-safe print to console"""
    try:
        print(*args, **kwargs, flush=True)
    except Exception:
        pass

def load_wordlist(path: Optional[str]) -> List[str]:
    """Load lines from a wordlist file"""
    if not path or not os.path.exists(path):
        return []
    
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f 
                   if line.strip() and not line.startswith('#')]
    except Exception:
        return []