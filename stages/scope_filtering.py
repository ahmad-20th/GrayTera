"""
Scope Filtering Stage: Filter subdomains based on pentesting scope
Follows the Stage pattern and integrates with observer pattern
"""
from core.stage import Stage
from core.target import Target
from utils.scope_filter import ScopeFilter
from typing import Optional


class ScopeFilteringStage(Stage):
    """Stage 1.5: Scope Filtering (between Enumeration and Vulnerability Scanning)"""
    
    def __init__(self, config: dict, scope_file: Optional[str] = None):
        super().__init__("Scope Filtering")
        self.config = config or {}
        self.scope_filter = ScopeFilter(scope_file) if scope_file else None
        self.filtered_count = 0
        self.in_scope_count = 0
    
    def execute(self, target: Target) -> bool:
        """
        Filter subdomains based on scope
        
        Args:
            target: Target object with enumerated subdomains
            
        Returns:
            True if filtering completed successfully
        """
        if not self.scope_filter or not self.scope_filter.loaded:
            self.notify("warning", "No scope file loaded, skipping scope filtering")
            return True
        
        if not target.subdomains:
            self.notify("warning", "No subdomains to filter")
            return True
        
        try:
            self.notify("start", f"Filtering {len(target.subdomains)} subdomains against scope")
            
            # Filter subdomains
            in_scope, out_of_scope = self.scope_filter.filter_subdomains(target.subdomains)
            
            self.in_scope_count = len(in_scope)
            self.filtered_count = len(out_of_scope)
            
            # Notify about filtered subdomains
            for subdomain in out_of_scope:
                self.notify("filtered_subdomain", subdomain)
            
            # Update target with only in-scope subdomains (convert back to set)
            target.subdomains = set(in_scope)
            target.metadata['filtered_subdomains'] = out_of_scope
            target.metadata['scope_stats'] = self.scope_filter.get_stats()
            
            # Log summary
            if self.filtered_count > 0:
                self.notify("info", f"Filtered out {self.filtered_count} out-of-scope subdomains")
            
            self.notify("complete", f"{self.in_scope_count} in-scope subdomains remaining")
            return True
            
        except Exception as e:
            self.notify("error", f"Scope filtering failed: {type(e).__name__}: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Check if scope filtering is enabled"""
        return self.scope_filter is not None and self.scope_filter.loaded
