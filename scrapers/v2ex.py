"""
V2EX Scraper for SilentReach
Uses agent-reach for public V2EX content.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class V2EXScraper:
    """V2EX (Chinese tech community) scraper."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
    
    async def search(self, query: str, limit: int = 20) -> dict:
        """Search V2EX topics."""
        try:
            from agent_reach import AgentReach
            reach = AgentReach()
            
            # V2EX search
            url = f"https://www.v2ex.com/search?q={query}"
            result = reach.read(url)
            
            if result:
                topics = self._parse_topics(result.content, query)
                return {
                    "query": query,
                    "topics": topics[:limit],
                    "total": len(topics),
                }
        except Exception as e:
            logger.warning(f"V2EX search failed: {e}")
        
        return {"query": query, "topics": []}
    
    async def get_node(self, node: str, limit: int = 20) -> dict:
        """Get topics from a specific V2EX node."""
        try:
            from agent_reach import AgentReach
            reach = AgentReach()
            
            url = f"https://www.v2ex.com/go/{node}"
            result = reach.read(url)
            
            if result:
                topics = self._parse_topics(result.content, node)
                return {
                    "node": node,
                    "topics": topics[:limit],
                    "total": len(topics),
                }
        except Exception as e:
            logger.error(f"V2EX node fetch failed: {e}")
            return {"node": node, "topics": [], "error": str(e)}
    
    def _parse_topics(self, content: str, query: str) -> list:
        """Parse V2EX topics from HTML."""
        from bs4 import BeautifulSoup
        
        topics = []
        soup = BeautifulSoup(content, "html.parser")
        
        # V2EX topic rows
        topic_rows = soup.select("div.cell.item, tr[class*='cell']")
        
        for row in topic_rows[:30]:
            # Title
            title_elem = row.select_one("a[href^='/t/']")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Link
            link = title_elem.get("href", "") if title_elem else ""
            
            # Author
            author = row.select_one("a[href^='/member/']")
            author_name = author.get_text(strip=True) if author else ""
            
            if title:
                topics.append({
                    "title": title,
                    "link": f"https://www.v2ex.com{link}" if link.startswith("/") else link,
                    "author": author_name,
                    "query": query,
                })
        
        return topics
