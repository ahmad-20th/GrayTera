import requests
from typing import Optional, Dict
import time


class HTTPClient:
    """HTTP client with retry logic and error handling"""
    
    def __init__(self, max_retries: int = 3, timeout: int = 30):
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if timeout < 1:
            raise ValueError("timeout must be >= 1")
        
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GrayTera/1.0 (Security Testing)'
        })
    
    def get(self, url: str, params: Optional[Dict] = None, **kwargs):
        """GET request with retry logic"""
        return self._request('GET', url, params=params, **kwargs)
    
    def post(self, url: str, data: Optional[Dict] = None, **kwargs):
        """POST request with retry logic"""
        return self._request('POST', url, data=data, **kwargs)
    
    def _request(self, method: str, url: str, **kwargs):
        """Execute request with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                kwargs.setdefault('timeout', self.timeout)
                kwargs.setdefault('allow_redirects', True)
                raise_for_status = kwargs.pop('raise_for_status', True)
                
                response = self.session.request(method, url, **kwargs)
                if raise_for_status:
                    response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt)  # Exponential backoff
                    time.sleep(wait_time)
                else:
                    raise last_exception
