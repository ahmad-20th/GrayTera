import yaml
from typing import Optional, List
from core.stage import Stage
from core.target import Target
from core.data_store import DataStore
from stages.subdomain_enum import SubdomainEnumStage
from stages.vulnerability_scan import VulnerabilityScanStage
from stages.exploitation import ExploitationStage


class Pipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, data_store: DataStore, config_path: str = 'config.yaml'):
        self.data_store = data_store
        self.config = self._load_config(config_path)
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
            'vulnerability_scan': {
                'threads': 10,
                'timeout': 30
            },
            'exploitation': {
                'auto_exploit': False,
                'max_attempts': 3
            },
            'retry': {
                'max_retries': 3,
                'backoff_factor': 2
            }
        }
    
    def _initialize_stages(self) -> List[Stage]:
        stages = [
            SubdomainEnumStage(self.config['subdomain_enum']),
            VulnerabilityScanStage(self.config['vulnerability_scan']),
            ExploitationStage(self.config['exploitation'])
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
    
    def _run_all_stages(self, target: Target):
        """Execute all stages in sequence"""
        for idx, stage in enumerate(self.stages):
            self.current_stage_index = idx
            self._notify_all(f"Starting stage: {stage.name}")
            
            success = stage.execute(target)
            
            if not success:
                self._notify_all(f"Stage {stage.name} failed")
                break
            
            # Save progress after each stage
            self.data_store.save_target(target)
            self._notify_all(f"Completed stage: {stage.name}")
    
    def _run_specific_stage(self, target: Target, stage_name: str):
        """Execute a specific stage"""
        stage_map = {
            'enum': 0,
            'scan': 1,
            'exploit': 2
        }
        
        if stage_name not in stage_map:
            raise ValueError(f"Unknown stage: {stage_name}")
        
        stage = self.stages[stage_map[stage_name]]
        stage.execute(target)
    
    def pause(self):
        """Save current state for resuming"""
        self._notify_all("Pipeline paused")
    
    def resume(self, domain: str):
        """Resume from saved state"""
        target = self.data_store.load_target(domain)
        if not target:
            raise ValueError(f"No saved state found for {domain}")
        
        # Resume from next incomplete stage
        self._run_all_stages(target)
    
    def _notify_all(self, message: str):
        for observer in self.observers:
            observer.update("Pipeline", "info", message)

