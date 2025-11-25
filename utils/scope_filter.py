"""
Scope filtering utilities for pentest scope management.
Allows loading HackerOne and custom scope definitions to filter subdomains.
"""
import json
import re
from typing import Set, List, Dict, Any
from pathlib import Path


class ScopeFilter:
    """Manages scope definitions and filters subdomains"""
    
    def __init__(self, scope_file: str = None):
        """
        Initialize scope filter from file
        
        Args:
            scope_file: Path to scope.json file
        """
        self.in_scope: Set[str] = set()
        self.out_of_scope: Set[str] = set()
        self.wildcard_patterns: List[re.Pattern] = []
        self.loaded = False
        
        if scope_file:
            self.load_from_file(scope_file)
    
    def load_from_file(self, scope_file: str) -> bool:
        """
        Load scope from JSON file
        
        Expected format:
        {
            "in_scope": {
                "domains": ["example.com", "*.internal.example.com"],
                "patterns": [".*\\.example\\.com$"]
            },
            "out_of_scope": {
                "domains": ["test.example.com", "staging.example.com"],
                "patterns": [".*-test\\.example\\.com$"]
            }
        }
        
        Args:
            scope_file: Path to scope.json
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            path = Path(scope_file)
            if not path.exists():
                return False
            
            with open(path, 'r') as f:
                scope_data = json.load(f)
            
            # Load in-scope domains and patterns
            in_scope = scope_data.get('in_scope', {})
            if isinstance(in_scope, dict):
                self.in_scope = set(in_scope.get('domains', []))
                for pattern in in_scope.get('patterns', []):
                    try:
                        self.wildcard_patterns.append(('in', re.compile(pattern)))
                    except re.error:
                        pass
            
            # Load out-of-scope domains and patterns
            out_of_scope = scope_data.get('out_of_scope', {})
            if isinstance(out_of_scope, dict):
                self.out_of_scope = set(out_of_scope.get('domains', []))
                for pattern in out_of_scope.get('patterns', []):
                    try:
                        self.wildcard_patterns.append(('out', re.compile(pattern)))
                    except re.error:
                        pass
            
            self.loaded = True
            return True
            
        except json.JSONDecodeError:
            return False
        except Exception:
            return False
    
    def create_sample_scope_file(self, output_path: str = 'scope.json') -> bool:
        """
        Create a sample scope.json file for user reference
        
        Args:
            output_path: Where to write the sample file
            
        Returns:
            True if created successfully
        """
        sample = {
            "in_scope": {
                "domains": [
                    "example.com",
                    "www.example.com",
                    "api.example.com",
                    "*.internal.example.com"
                ],
                "patterns": [
                    "^[a-z0-9-]+\\.example\\.com$"
                ]
            },
            "out_of_scope": {
                "domains": [
                    "test.example.com",
                    "staging.example.com",
                    "dev.example.com"
                ],
                "patterns": [
                    ".*-test\\.example\\.com$",
                    ".*\\.staging\\.example\\.com$"
                ]
            }
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(sample, f, indent=2)
            return True
        except Exception:
            return False
    
    def is_in_scope(self, subdomain: str) -> bool:
        """
        Check if a subdomain is within scope
        
        Args:
            subdomain: FQDN to check
            
        Returns:
            True if in scope, False if out of scope or scope not loaded
        """
        if not self.loaded:
            return True  # If no scope loaded, allow all
        
        subdomain_lower = subdomain.lower()
        
        # Check exact out-of-scope matches first (they take precedence)
        if subdomain_lower in self.out_of_scope:
            return False
        
        # Check patterns
        for scope_type, pattern in self.wildcard_patterns:
            if pattern.match(subdomain_lower):
                if scope_type == 'out':
                    return False
                elif scope_type == 'in':
                    return True
        
        # Check exact in-scope matches
        if subdomain_lower in self.in_scope:
            return True
        
        # Check if subdomain matches any in-scope domain as subdomain
        for in_scope_domain in self.in_scope:
            domain_lower = in_scope_domain.lower()
            
            # Handle wildcard domains (e.g., *.example.com)
            if domain_lower.startswith('*.'):
                base_domain = domain_lower[2:]  # Remove *.
                if subdomain_lower.endswith('.' + base_domain) or subdomain_lower == base_domain:
                    return True
            # Exact match or subdomain match
            elif subdomain_lower == domain_lower or subdomain_lower.endswith('.' + domain_lower):
                return True
        
        return False
    
    def filter_subdomains(self, subdomains: List[str]) -> tuple:
        """
        Filter subdomains into in-scope and out-of-scope lists
        
        Args:
            subdomains: List of FQDNs to filter
            
        Returns:
            Tuple of (in_scope_list, out_of_scope_list)
        """
        in_scope_list = []
        out_of_scope_list = []
        
        for subdomain in subdomains:
            if self.is_in_scope(subdomain):
                in_scope_list.append(subdomain)
            else:
                out_of_scope_list.append(subdomain)
        
        return in_scope_list, out_of_scope_list
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded scope"""
        return {
            'loaded': self.loaded,
            'in_scope_domains': len(self.in_scope),
            'out_of_scope_domains': len(self.out_of_scope),
            'patterns': len(self.wildcard_patterns)
        }
