"""
SilentReach - Ultimate undetected web intelligence framework.
Combines agent-reach (public) + nodriver (authenticated) for complete coverage.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ScrapedResult:
    """Standardized result from any scraper."""
    platform: str
    query: str
    timestamp: float = field(default_factory=time.time)
    data: list = field(default_factory=list)
    raw_html: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    error: Optional[str] = None
    status: str = "success"
    
    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "query": self.query,
            "timestamp": self.timestamp,
            "data": self.data[:100],
            "total_results": len(self.data),
            "error": self.error,
            "status": self.status,
        }


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.
    Implements common stealth features and result formatting.
    """
    
    platform: str = "base"
    primary_method: str = "agent_reach"
    fallback_method: str = "nodriver"
    auth_required: bool = False
    stealth_level: str = "medium"
    delay_range: tuple = (1.0, 3.0)
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self._cookie_path = Path.home() / ".silentreach" / "cookies" / f"{self.platform}.json"
        self._last_request_time = 0
        self._stats = {
            "requests": 0,
            "errors": 0,
            "bytes_fetched": 0,
        }
    
    @abstractmethod
    async def search(self, query: str, limit: int = 20, **kwargs) -> ScrapedResult:
        pass
    
    @abstractmethod
    async def get_item(self, item_id: str, **kwargs) -> ScrapedResult:
        pass
    
    @abstractmethod
    async def get_profile(self, username: str, **kwargs) -> ScrapedResult:
        pass
    
    async def _apply_rate_limit(self):
        if not self.config.get("rate_limit", True):
            return
        
        delay = self._get_random_delay()
        elapsed = time.time() - self._last_request_time
        
        if elapsed < delay:
            wait_time = delay - elapsed
            await asyncio.sleep(wait_time)
        
        self._last_request_time = time.time()
        self._stats["requests"] += 1
    
    def _get_random_delay(self) -> float:
        import random
        base = random.uniform(*self.delay_range)
        multipliers = {"low": 0.5, "medium": 1.0, "high": 1.5, "very_high": 2.0}
        return base * multipliers.get(self.stealth_level, 1.0)
    
    def _get_random_headers(self) -> dict:
        import random
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        ]
        languages = ["en-US,en;q=0.9", "en-GB,en;q=0.9", "de-DE,de;q=0.9,en;q=0.8"]
        
        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": random.choice(languages),
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }
    
    def _extract_text_from_html(self, html: str) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
    
    def _save_cookies(self, cookies: dict):
        self._cookie_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(self._cookie_path, "w") as f:
            json.dump(cookies, f)
    
    def _load_cookies(self) -> Optional[dict]:
        if not self._cookie_path.exists():
            return None
        import json
        with open(self._cookie_path) as f:
            return json.load(f)
    
    def get_stats(self) -> dict:
        return {**self._stats, "platform": self.platform}


async def run_async(coro):
    """Helper to run async code from sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return await coro
        else:
            return await coro
    except RuntimeError:
        return await coro
