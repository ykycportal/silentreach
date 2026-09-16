"""
Reddit Scraper for SilentReach
Supports both public (agent-reach) and authenticated (nodriver) modes.
"""

import asyncio
import logging
from typing import Optional
from scrapers.base import BaseScraper, ScrapedResult

logger = logging.getLogger(__name__)


class RedditScraper(BaseScraper):
    platform = "reddit"
    primary_method = "agent_reach"
    fallback_method = "nodriver"
    auth_required = True
    stealth_level = "high"
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.subreddits = ["dropshipping", "ecommerce", "amazonfba", "shopify"]
    
    async def search(self, query: str, limit: int = 20, **kwargs) -> ScrapedResult:
        await self._apply_rate_limit()
        
        # Try agent-reach first
        try:
            from agent_reach import AgentReach
            reach = AgentReach()
            
            # Search Reddit
            url = f"https://reddit.com/search/?q={query}&sort=relevance"
            result = reach.read(url)
            
            if result:
                content = result.content
                items = self._parse_reddit_content(content, query)
                
                return ScrapedResult(
                    platform=self.platform,
                    query=query,
                    data=items,
                    raw_html=content,
                )
        except Exception as e:
            logger.warning(f"Agent-reach failed: {e}")
        
        # Fallback to nodriver
        try:
            import nodriver as uc
            browser = await uc.start(headless=True)
            
            # Load cookies if available
            cookies = self._load_cookies()
            if cookies:
                browser = await browser.load_cookies(self._cookie_path)
            
            page = await browser.get(f"https://www.reddit.com/search/?q={query}")
            await asyncio.sleep(2)  # Wait for JS to render
            
            content = await page.get_content()
            items = self._parse_reddit_content(content, query)
            
            await browser.stop()
            
            return ScrapedResult(
                platform=self.platform,
                query=query,
                data=items,
                raw_html=content,
            )
        except Exception as e:
            logger.error(f"Nodriver failed: {e}")
            return ScrapedResult(
                platform=self.platform,
                query=query,
                error=str(e),
                status="error",
            )
    
    async def get_item(self, item_id: str, **kwargs) -> ScrapedResult:
        """Get a specific Reddit post/comment."""
        await self._apply_rate_limit()
        
        try:
            from agent_reach import AgentReach
            reach = AgentReach()
            url = f"https://reddit.com/{item_id}"
            result = reach.read(url)
            
            if result:
                return ScrapedResult(
                    platform=self.platform,
                    query=item_id,
                    data=[result.content],
                    raw_html=result.content,
                )
        except Exception as e:
            logger.error(f"Error fetching Reddit item: {e}")
            return ScrapedResult(
                platform=self.platform,
                query=item_id,
                error=str(e),
                status="error",
            )
    
    async def get_profile(self, username: str, **kwargs) -> ScrapedResult:
        """Get Reddit user profile."""
        await self._apply_rate_limit()
        
        try:
            from agent_reach import AgentReach
            reach = AgentReach()
            url = f"https://reddit.com/user/{username}"
            result = reach.read(url)
            
            if result:
                return ScrapedResult(
                    platform=self.platform,
                    query=username,
                    data=[result.content],
                )
        except Exception as e:
            return ScrapedResult(
                platform=self.platform,
                query=username,
                error=str(e),
                status="error",
            )
    
    def _parse_reddit_content(self, content: str, query: str) -> list:
        """Parse Reddit HTML/content into structured items."""
        from bs4 import BeautifulSoup
        
        items = []
        soup = BeautifulSoup(content, "html.parser")
        
        # Try to find post elements
        post_elements = soup.select(".Post, .thing, article, [data-testid='post-container']")
        
        for elem in post_elements[:limit]:
            title = elem.select_one(".PostTitle, .title, h1, h2, a")
            if title:
                items.append({
                    "title": title.get_text(strip=True),
                    "url": title.get("href", ""),
                    "text": elem.get_text(strip=True)[:500],
                })
        
        # If no structured elements, extract all text
        if not items:
            text = self._extract_text_from_html(content)
            items.append({"title": query, "text": text[:1000]})
        
        return items[:20]
