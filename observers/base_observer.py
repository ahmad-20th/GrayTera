from abc import ABC, abstractmethod
from typing import Any


class BaseObserver(ABC):
    """Base observer interface for monitoring pipeline events"""
    
    @abstractmethod
    def update(self, stage: str, event: str, data: Any = None):
        """
        Called when an event occurs
        
        Args:
            stage: Name of the stage emitting the event
            event: Event type (start, complete, error, etc.)
            data: Optional event data
        """
        pass

