import yaml
from typing import Optional, List
from core.stage import Stage
from core.target import Target
from core.data_store import DataStore
from stages.subdomain_enum import SubdomainEnumStage
from stages.scope_filtering import ScopeFilteringStage
from stages.vulnerability_scan import VulnerabilityScanStage
from stages.exploitation import ExploitationStage


class Pipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, data_store: DataStore, config_path: str = 'config.yaml', scope_file: Optional[str] = None):
        self.data_store = data_store
        self.config_path = config_path  # Store the path for stages that need it
        self.config = self._load_config(config_path)
        self.scope_file = scope_file
        self.observers = []
        self.stages = self._initialize_stages()
        self.current_stage_index = 0
    
    def _load_config(self, path: str) -> dict:
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_config()
    
    def _default_config(self) -> dict:
        return {
            'subdomain_enum': {
                'timeout': 10,
                'max_subdomains': 1000
            },
            'scope_filtering': {},
            'vulnerability_scan': {
                'threads': 10,
                'timeout': 30
            },
            'exploitation': {
                'auto_exploit': False,
                'max_attempts': 3
            }
        }
    
    def _initialize_stages(self) -> List[Stage]:
        stages = [
            SubdomainEnumStage(self.config.get('subdomain_enum', {})),
            ScopeFilteringStage(self.config.get('scope_filtering', {}), self.scope_file),
            VulnerabilityScanStage(self.config.get('vulnerability_scan', {})),
            ExploitationStage(self.config.get('exploitation', {}))
        ]
        # Attach observers to all stages
        for stage in stages:
            for observer in self.observers:
                stage.attach_observer(observer)
        return stages
    
    def attach(self, observer):
        """Attach an observer to the pipeline"""
        self.observers.append(observer)
        for stage in self.stages:
            stage.attach_observer(observer)
    
    def run(self, domain: str, specific_stage: Optional[str] = None):
        """Run the full pipeline or a specific stage"""
        target = self.data_store.load_target(domain) or Target(domain=domain)
        
        if specific_stage:
            self._run_specific_stage(target, specific_stage)
        else:
            self._run_all_stages(target)
        
        self.data_store.save_target(target)
    
    def _run_all_stages(self, target: Target, start_from: int = 0):
        """Execute all stages in sequence"""
        for idx in range(start_from, len(self.stages)):
            stage = self.stages[idx]
            self.current_stage_index = idx
            self._notify_all(f"Starting stage: {stage.name}")
            
            success = stage.execute(target)
            
            if not success:
                self._notify_all(f"Stage {stage.name} failed")
                # Save current progress even on failure
                target.metadata['last_completed_stage'] = idx - 1
                target.metadata['last_failed_stage'] = idx
                self.data_store.save_target(target)
                break
            
            # Save progress after each stage
            target.metadata['last_completed_stage'] = idx
            target.metadata.pop('last_failed_stage', None)  # Clear any previous failure
            self.data_store.save_target(target)
            self._notify_all(f"Completed stage: {stage.name}")
    
    def _run_specific_stage(self, target: Target, stage_name: str):
        """Execute a specific stage"""
        stage_map = {
            'enum': 0,
            'filter': 1,
            'scan': 2,
            'exploit': 3
        }
        
        if stage_name not in stage_map:
            raise ValueError(f"Unknown stage: {stage_name}. Valid: {list(stage_map.keys())}")
        
        idx = stage_map[stage_name]
        stage = self.stages[idx]
        self._notify_all(f"Running specific stage: {stage.name}")
        stage.execute(target)
    
    def can_resume(self, domain: str) -> bool:
        """Check if there's saved data to resume from"""
        return self.data_store.target_exists(domain)
    
    def pause(self, target: Target = None):
        """Save current state for resuming"""
        if target:
            self.data_store.save_target(target)
        self._notify_all("Pipeline paused - progress saved")
    
    def resume(self, domain: str):
        """Resume from saved state"""
        target = self.data_store.load_target(domain)
        if not target:
            raise ValueError(f"No saved state found for {domain}")
        
        # Get last completed stage (-1 means none completed yet)
        last_completed = target.metadata.get('last_completed_stage', -1)
        last_failed = target.metadata.get('last_failed_stage', None)
        
        # Determine where to start
        if last_failed is not None:
            # Retry the failed stage
            start_from = last_failed
            self._notify_all(f"Retrying failed stage {start_from + 1}/{len(self.stages)}")
        else:
            # Continue from next stage after last completed
            start_from = last_completed + 1
        
        if start_from >= len(self.stages):
            self._notify_all("All stages already completed")
            return
        
        self._notify_all(f"Resuming from stage {start_from + 1}/{len(self.stages)}")
        self._run_all_stages(target, start_from=start_from)
    
    def _notify_all(self, message: str):
        """Notify all observers"""
        for observer in self.observers:
            observer.update("Pipeline", "info", message)