from abc import ABC, abstractmethod
from typing import List, Any
from core.target import Target
from observers.base_observer import BaseObserver


class Stage(ABC):
    """Base class for all pipeline stages"""
    
    def __init__(self, name: str):
        self.name = name
        self.observers: List[BaseObserver] = []
    
    @abstractmethod
    def execute(self, target: Target) -> bool:
        """
        Execute the stage logic
        Returns True if successful, False otherwise
        """
        pass
    
    def notify(self, event: str, data: Any = None):
        """Notify all observers of an event"""
        for observer in self.observers:
            observer.update(self.name, event, data)
    
    def attach_observer(self, observer: BaseObserver):
        self.observers.append(observer)
