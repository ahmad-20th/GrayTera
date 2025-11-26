import json
import pickle
import logging
import shutil
import re
from pathlib import Path
from typing import Optional
from datetime import datetime
from core.target import Target, Vulnerability


class RestrictedUnpickler(pickle.Unpickler):
    """Secure unpickler that only allows specific classes"""
    
    def find_class(self, module, name):
        # Only allow Target and Vulnerability classes
        if module == "core.target" and name in ["Target", "Vulnerability"]:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Forbidden class: {module}.{name}")


class DataStore:
    """Handles persistence of scan data with security and reliability features"""
    
    def __init__(self, base_path: str = 'data/scans'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def save_target(self, target: Target, create_backup: bool = True):
        """
        Save target data to disk in both JSON and pickle formats
        
        Args:
            target: Target object to save
            create_backup: Whether to backup existing data before overwriting
        """
        target_dir = self.base_path / self._sanitize_domain(target.domain)
        target_dir.mkdir(exist_ok=True)
        
        # Create backup if requested and files exist
        if create_backup:
            try:
                self._backup_existing(target_dir)
            except Exception as e:
                self.logger.debug(f"Backup failed: {e}")
        
        # Define paths
        json_path = target_dir / 'scan_data.json'
        pickle_path = target_dir / 'scan_data.pkl'
        
        try:
            # Save as JSON (human-readable)
            with open(json_path, 'w') as f:
                json.dump(self._target_to_dict(target), f, indent=2, default=str)
            
            # Save as pickle (full object state)
            with open(pickle_path, 'wb') as f:
                pickle.dump(target, f)
            
        except Exception as e:
            self.logger.error(f"Failed to save target {target.domain}: {e}")
            raise
    
    def load_target(self, domain: str) -> Optional[Target]:
        """
        Load target data from disk with automatic fallback
        
        Args:
            domain: Target domain name
            
        Returns:
            Target object or None if not found
        """
        target_dir = self.base_path / self._sanitize_domain(domain)
        pickle_path = target_dir / 'scan_data.pkl'
        json_path = target_dir / 'scan_data.json'
        
        # Check if any data exists
        if not pickle_path.exists() and not json_path.exists():
            return None
        
        # Try pickle first (faster and preserves full state)
        if pickle_path.exists():
            try:
                with open(pickle_path, 'rb') as f:
                    data = RestrictedUnpickler(f).load()
                    if not isinstance(data, Target):
                        raise TypeError(f"Expected Target, got {type(data)}")
                    return data
            except (pickle.UnpicklingError, TypeError, EOFError, AttributeError) as e:
                self.logger.debug(f"Pickle load failed, trying JSON: {e}")
        
        # Fallback to JSON
        if json_path.exists():
            try:
                return self._load_from_json(json_path)
            except Exception as e:
                self.logger.error(f"Failed to load {domain}: {e}")
                raise ValueError(f"Failed to load target data for {domain}") from e
        
        return None
    
    def target_exists(self, domain: str) -> bool:
        """Check if saved data exists for a domain"""
        target_dir = self.base_path / self._sanitize_domain(domain)
        return (target_dir / 'scan_data.pkl').exists() or \
               (target_dir / 'scan_data.json').exists()
    
    def delete_target(self, domain: str):
        """Delete all data for a target"""
        target_dir = self.base_path / self._sanitize_domain(domain)
        if target_dir.exists():
            shutil.rmtree(target_dir)
    
    def list_targets(self) -> list[str]:
        """List all saved target domains"""
        targets = []
        for target_dir in self.base_path.iterdir():
            if target_dir.is_dir():
                # Reverse sanitization to get original domain
                domain = target_dir.name.replace('_', '.')
                targets.append(domain)
        return sorted(targets)
    
    def _backup_existing(self, target_dir: Path):
        """Create timestamped backup of existing data"""
        backup_dir = target_dir / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for filename in ['scan_data.json', 'scan_data.pkl']:
            src = target_dir / filename
            if src.exists():
                dst = backup_dir / f"{filename}.{timestamp}"
                shutil.copy2(src, dst)
    
    def _sanitize_domain(self, domain: str) -> str:
        """
        Convert domain to safe directory name
        
        Handles protocols, invalid filesystem characters, and edge cases
        """
        # Remove protocol if present
        domain = domain.replace('https://', '').replace('http://', '')
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Replace invalid filesystem characters with underscores
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', domain)
        
        # Remove leading/trailing dots and spaces
        safe_name = safe_name.strip('. ')
        
        # Ensure not empty
        if not safe_name:
            safe_name = 'unknown_domain'
        
        return safe_name
    
    def _target_to_dict(self, target: Target) -> dict:
        """Convert Target to JSON-serializable dict"""
        return {
            'domain': target.domain,
            'subdomains': list(target.subdomains),
            'vulnerabilities': [
                {
                    'type': v.vuln_type,
                    'severity': v.severity,
                    'url': v.url,
                    'parameter': v.parameter,
                    'payload': v.payload,
                    'evidence': v.evidence,
                    'timestamp': v.timestamp.isoformat() if hasattr(v, 'timestamp') else None
                }
                for v in target.vulnerabilities
            ],
            'exploited': target.exploited if hasattr(target, 'exploited') else [],
            'metadata': target.metadata if hasattr(target, 'metadata') else {},
            'saved_at': datetime.now().isoformat()
        }
    
    def _load_from_json(self, json_path: Path) -> Target:
        """Reconstruct Target object from JSON file"""
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Create target with basic info
        target = Target(data['domain'])
        
        # Restore subdomains
        target.subdomains = set(data.get('subdomains', []))
        
        # Restore vulnerabilities
        for v_data in data.get('vulnerabilities', []):
            vuln = Vulnerability(
                vuln_type=v_data['type'],
                severity=v_data['severity'],
                url=v_data['url'],
                parameter=v_data.get('parameter'),
                payload=v_data.get('payload'),
                evidence=v_data.get('evidence')
            )
            # Restore timestamp if available
            if v_data.get('timestamp'):
                vuln.timestamp = datetime.fromisoformat(v_data['timestamp'])
            target.vulnerabilities.append(vuln)
        
        # Restore other attributes
        target.exploited = data.get('exploited', [])
        target.metadata = data.get('metadata', {})
        
        return target
    
    def export_json(self, domain: str, output_path: Optional[Path] = None) -> Path:
        """
        Export target data as a standalone JSON report
        
        Args:
            domain: Target domain
            output_path: Optional custom output path
            
        Returns:
            Path to exported file
        """
        target = self.load_target(domain)
        if not target:
            raise ValueError(f"No data found for {domain}")
        
        # Default output path
        if output_path is None:
            export_dir = self.base_path / self._sanitize_domain(domain) / 'exports'
            export_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = export_dir / f"report_{timestamp}.json"
        
        # Export
        with open(output_path, 'w') as f:
            json.dump(self._target_to_dict(target), f, indent=2, default=str)
        
        return output_path