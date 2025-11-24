import json
import pickle
from pathlib import Path
from typing import Optional
from datetime import datetime
from core.target import Target


class DataStore:
    """Handles persistence of scan data"""
    
    def __init__(self, base_path: str = 'data/scans'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_target(self, target: Target):
        """Save target data to disk"""
        target_dir = self.base_path / self._sanitize_domain(target.domain)
        target_dir.mkdir(exist_ok=True)
        
        # Save as both JSON (human-readable) and pickle (full object)
        json_path = target_dir / 'scan_data.json'
        pickle_path = target_dir / 'scan_data.pkl'
        
        # JSON export
        with open(json_path, 'w') as f:
            json.dump(self._target_to_dict(target), f, indent=2, default=str)
        
        # Pickle for full state
        with open(pickle_path, 'wb') as f:
            pickle.dump(target, f)
    
    def load_target(self, domain: str) -> Optional[Target]:
        """Load target data from disk"""
        pickle_path = self.base_path / self._sanitize_domain(domain) / 'scan_data.pkl'
        
        if not pickle_path.exists():
            return None
        
        try:
            with open(pickle_path, 'rb') as f:
                # Only allow Target objects to be unpickled
                data = pickle.load(f)
                if not isinstance(data, Target):
                    raise TypeError(f"Expected Target, got {type(data)}")
                return data
        except Exception as e:
            # Fall back to JSON if pickle fails
            json_path = self.base_path / self._sanitize_domain(domain) / 'scan_data.json'
            if json_path.exists():
                return self._load_from_json(json_path)
            raise
    
    def _sanitize_domain(self, domain: str) -> str:
        """Convert domain to safe directory name"""
        return domain.replace(':', '_').replace('/', '_')
    
    def _target_to_dict(self, target: Target) -> dict:
        """Convert Target to JSON-serializable dict"""
        return {
            'domain': target.domain,
            'subdomains': target.subdomains,
            'vulnerabilities': [
                {
                    'type': v.vuln_type,
                    'severity': v.severity,
                    'url': v.url,
                    'parameter': v.parameter,
                    'payload': v.payload,
                    'evidence': v.evidence,
                    'timestamp': v.timestamp.isoformat()
                }
                for v in target.vulnerabilities
            ],
            'exploited': target.exploited,
            'metadata': target.metadata
        }

