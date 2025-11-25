"""
Scanner registry for GrayTera
This file registers all scanners so the framework can load them.
"""

from .nikto_scanner import NiktoScanner


# Registry dictionary (example structure)
scanner_registry = {
    "nikto": NiktoScanner
}


def get_scanner(name: str):
    """
    Return scanner class by name.
    """
    return scanner_registry.get(name.lower())
