import json
from pathlib import Path
from datetime import datetime
from observers.base_observer import BaseObserver
from typing import Any


class FileObserver(BaseObserver):
    """Observer that logs events to file"""
    
    def __init__(self, output_dir: str = 'data/scans'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.events = []
    
    def update(self, stage: str, event: str, data: Any = None):
        """Log event to file"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'event': event,
            'data': str(data) if data else None
        }
        
        self.events.append(log_entry)
        
        # Append to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

