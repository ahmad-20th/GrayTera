from observers.base_observer import BaseObserver
from typing import Any


class ProgressObserver(BaseObserver):
    """Observer that tracks and displays progress"""
    
    def __init__(self):
        self.stage_progress = {}
        self.total_tasks = 0
        self.completed_tasks = 0
    
    def update(self, stage: str, event: str, data: Any = None):
        """Update progress tracking"""
        if event == 'start':
            self.stage_progress[stage] = {'status': 'running', 'progress': 0}
        
        elif event == 'complete':
            self.stage_progress[stage] = {'status': 'completed', 'progress': 100}
            self.completed_tasks += 1
        
        elif event == 'error':
            self.stage_progress[stage] = {'status': 'failed', 'progress': 0}
        
        self._display_progress()
    
    def _display_progress(self):
        """Display progress bar (simple implementation)"""
        if self.total_tasks > 0:
            percentage = (self.completed_tasks / self.total_tasks) * 100
            bar_length = 40
            filled = int(bar_length * percentage / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f'\rProgress: [{bar}] {percentage:.1f}%', end='', flush=True)

