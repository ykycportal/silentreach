"""
RSS Scraper for SilentReach
Uses agent-reach for RSS feed monitoring.
"""

import asyncio
import logging
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class RSSScraper:
    """RSS feed scraper using agent-reach."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
    
    async def read_feed(self, url: str, limit: int = 20) -> dict:
        """Read an RSS/Atom feed."""
        try:
            from agent_reach import AgentReach
            reach = AgentReach()
            
            result = reach.read(url)
            
            if result:
                items = self._parse_feed(result.content, url)
                return {
                    "url": url,
                    "title": result.metadata.get("title", url) if hasattr(result, 'metadata') else url,
                    "items": items[:limit],
                    "total": len(items),
                }
        except Exception as e:
            logger.error(f"RSS feed read failed: {e}")
            return {"url": url, "items": [], "error": str(e)}
    
    async def search_feeds(self, topic: str, limit: int = 10) -> List[dict]:
        """Search for RSS feeds related to a topic."""
        feeds = []
        
        # Common tech/business RSS feeds
        default_feeds = [
            "https://news.ycombinator.com/rss",
            "https://www.reddit.com/r/dropshipping/.rss",
            "https://www.reddit.com/r/ecommerce/.rss",
            "https://www.reddit.com/r/shopify/.rss",
            "https://feeds.bbci.co.uk/news/business/rss.xml",
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
        ]
        
        for feed_url in default_feeds:
            try:
                result = await self.read_feed(feed_url, limit=5)
                if result.get("items"):
                    feeds.append(result)
            except:
                continue
        
        return feeds[:limit]
    
    def _parse_feed(self, content: str, url: str) -> List[dict]:
        """Parse RSS/Atom feed content."""
        import feedparser
        
        feed = feedparser.parse(content)
        
        items = []
        for entry in feed.entries[:20]:
            item = {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", entry.get("updated", "")),
                "summary": entry.get("summary", entry.get("description", ""))[:500],
                "source": url,
            }
            items.append(item)
        
        return items
