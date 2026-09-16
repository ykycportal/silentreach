"""
Proxy utilities for SilentReach.
"""

import random
import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    """Represents a proxy server."""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    
    @property
    def url(self) -> str:
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @classmethod
    def from_string(cls, proxy_str: str) -> 'Proxy':
        """Parse proxy string like 'http://user:pass@host:port'."""
        # Simple parser - in production, use a proper library
        protocol = "http"
        if "@" in proxy_str:
            auth, rest = proxy_str.rsplit("@", 1)
            protocol, auth = auth.split("://", 1)
            username, password = auth.split(":")
        else:
            rest = proxy_str.replace(f"{protocol}://", "")
            username = password = None
        
        host, port = rest.split(":")
        return cls(host=host, port=int(port), username=username, password=password, protocol=protocol)


class ProxyPool:
    """Manages a pool of proxies with rotation."""
    
    def __init__(self, proxies: Optional[List[str]] = None):
        self._proxies = []
        self._current_index = 0
        self._failed_proxies = set()
        
        if proxies:
            for proxy_str in proxies:
                try:
                    self._proxies.append(Proxy.from_string(proxy_str))
                except Exception as e:
                    logger.warning(f"Failed to parse proxy '{proxy_str}': {e}")
    
    def add_proxy(self, proxy: Proxy):
        """Add a proxy to the pool."""
        self._proxies.append(proxy)
        if proxy in self._failed_proxies:
            self._failed_proxies.discard(proxy)
    
    def add_proxy_string(self, proxy_str: str):
        """Add a proxy from string."""
        try:
            self._proxies.append(Proxy.from_string(proxy_str))
        except Exception as e:
            logger.warning(f"Failed to add proxy '{proxy_str}': {e}")
    
    def get_proxy(self) -> Optional[Proxy]:
        """Get next proxy in rotation, skipping failed ones."""
        if not self._proxies:
            return None
        
        # Filter out failed proxies
        available = [p for p in self._proxies if p not in self._failed_proxies]
        
        if not available:
            self._failed_proxies.clear()  # Reset if all failed
            return self._proxies[self._current_index % len(self._proxies)]
        
        proxy = available[self._current_index % len(available)]
        self._current_index += 1
        return proxy
    
    def mark_failed(self, proxy: Proxy):
        """Mark a proxy as failed."""
        self._failed_proxies.add(proxy)
        logger.warning(f"Proxy marked as failed: {proxy.url}")
    
    def mark_success(self, proxy: Proxy):
        """Mark a proxy as working."""
        self._failed_proxies.discard(proxy)
    
    def clear_failed(self):
        """Clear all failed proxy marks."""
        self._failed_proxies.clear()
    
    @property
    def size(self) -> int:
        return len(self._proxies)
    
    @property
    def available_count(self) -> int:
        return len(self._proxies) - len(self._failed_proxies)
