"""
Stealth Engine - Core anti-detection logic for SilentReach.
"""

import asyncio
import random
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Fingerprint:
    """Browser fingerprint data."""
    user_agent: str
    accept_language: str
    platform: str
    viewport_width: int
    viewport_height: int
    screen_resolution: tuple
    timezone: str
    color_depth: int
    pixel_ratio: float


class StealthEngine:
    """
    Manages stealth features for undetected scraping.
    """
    
    # Common user agents
    USER_AGENTS = [
        # Windows Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # macOS Chrome
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        # Linux Chrome
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    ]
    
    LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9",
        "en-US,en;q=0.9,ja;q=0.8",
        "de-DE,de;q=0.9,en;q=0.8",
        "fr-FR,fr;q=0.9,en;q=0.8",
        "es-ES,es;q=0.9,en;q=0.8",
        "zh-CN,zh;q=0.9,en;q=0.8",
    ]
    
    PLATFORMS = ["Windows", "Macintosh", "Linux"]
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self._request_count = 0
        self._last_request_time = 0
    
    def get_random_fingerprint(self) -> Fingerprint:
        """Generate a random browser fingerprint."""
        return Fingerprint(
            user_agent=random.choice(self.USER_AGENTS),
            accept_language=random.choice(self.LANGUAGES),
            platform=random.choice(self.PLATFORMS),
            viewport_width=random.choice([1366, 1440, 1536, 1920]),
            viewport_height=random.choice([768, 900, 1024, 1080]),
            screen_resolution=(random.choice([1440, 1920]), random.choice([900, 1080])),
            timezone=random.choice(["America/New_York", "America/Chicago", "America/Los_Angeles", 
                                   "Europe/London", "Europe/Berlin", "Asia/Tokyo", "Asia/Shanghai"]),
            color_depth=random.choice([24, 32]),
            pixel_ratio=random.choice([1.0, 1.25, 1.5, 2.0]),
        )
    
    def get_headers(self, fingerprint: Optional[Fingerprint] = None) -> Dict[str, str]:
        """Generate realistic browser headers."""
        fp = fingerprint or self.get_random_fingerprint()
        
        return {
            "User-Agent": fp.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": fp.accept_language,
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": f'"{fp.platform}"',
        }
    
    async def wait(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Wait with random delay to simulate human behavior."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def smart_wait(self, platform: str = "generic"):
        """Platform-specific wait times."""
        delays = {
            "reddit": (2.0, 4.0),
            "twitter": (3.0, 5.0),
            "instagram": (4.0, 6.0),
            "linkedin": (2.0, 4.0),
            "youtube": (1.0, 2.0),
            "generic": (1.5, 3.0),
        }
        
        min_delay, max_delay = delays.get(platform, delays["generic"])
        await self.wait(min_delay, max_delay)
    
    def rotate_headers(self) -> Dict[str, str]:
        """Rotate to new headers."""
        self._request_count += 1
        return self.get_headers()
    
    def should_rotate(self, interval: int = 10) -> bool:
        """Check if headers should be rotated."""
        return self._request_count % interval == 0


class RateLimiter:
    """
    Manages request rate limiting with exponential backoff.
    """
    
    def __init__(self, requests_per_minute: int = 30):
        self.rpm = requests_per_minute
        self._window = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            
            # Remove old requests from window
            self._window = [t for t in self._window if now - t < 60]
            
            if len(self._window) >= self.rpm:
                # Wait until oldest request expires
                wait_time = 60 - (now - self._window[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            self._window.append(asyncio.get_event_loop().time())
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        return {
            "rpm_limit": self.rpm,
            "requests_in_window": len(self._window),
        }


class ProxyRotator:
    """
    Rotates through proxy list for additional stealth.
    """
    
    def __init__(self, proxies: Optional[List[str]] = None):
        self.proxies = proxies or []
        self._current_index = 0
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation."""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self._current_index % len(self.proxies)]
        self._current_index += 1
        return proxy
    
    def add_proxy(self, proxy: str):
        """Add a proxy to the rotation list."""
        self.proxies.append(proxy)
    
    def clear(self):
        """Clear all proxies."""
        self.proxies = []
        self._current_index = 0
