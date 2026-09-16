"""
LinkedIn Scraper for SilentReach
Public pages via agent-reach, authenticated via nodriver.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """LinkedIn scraper - public pages via Jina, authenticated via nodriver."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
    
    async def search_public(self, query: str, limit: int = 20) -> dict:
        """Search LinkedIn using agent-reach (public pages only)."""
        try:
            from agent_reach import AgentReach
            reach = AgentReach()
            
            # LinkedIn public search
            url = f"https://www.linkedin.com/search/results/all/?keywords={query.replace(' ', '+')}"
            result = reach.read(url)
            
            if result:
                profiles = self._parse_linkedin_content(result.content, query)
                return {
                    "query": query,
                    "profiles": profiles[:limit],
                    "method": "public",
                    "note": "Limited to public profiles only",
                }
        except Exception as e:
            logger.warning(f"LinkedIn public search failed: {e}")
        
        return {"query": query, "profiles": [], "method": "public"}
    
    async def search_auth(self, query: str, limit: int = 20) -> dict:
        """Search LinkedIn with authenticated session."""
        import nodriver as uc
        
        browser = await uc.start(headless=True)
        
        cookie_path = self.config.get("cookie_path", f"{Path.home()}/.silentreach/cookies/linkedin.json")
        if Path(cookie_path).exists():
            try:
                browser = await browser.load_cookies(cookie_path)
            except:
                pass
        
        try:
            page = await browser.get(f"https://www.linkedin.com/search/results/all/?keywords={query}")
            await asyncio.sleep(3)
            
            content = await page.get_content()
            profiles = self._parse_linkedin_content(content, query)
            
            return {
                "query": query,
                "profiles": profiles[:limit],
                "method": "authenticated",
            }
        except Exception as e:
            return {"query": query, "profiles": [], "error": str(e)}
        finally:
            await browser.stop()
    
    async def get_profile(self, profile_url: str) -> dict:
        """Get a specific LinkedIn profile."""
        try:
            from agent_reach import AgentReach
            reach = AgentReach()
            
            result = reach.read(profile_url)
            
            if result:
                profile = self._parse_profile(result.content)
                return {"url": profile_url, "profile": profile}
        except Exception as e:
            logger.error(f"LinkedIn profile fetch failed: {e}")
        
        return {"url": profile_url, "error": str(e)}
    
    def _parse_linkedin_content(self, content: str, query: str) -> list:
        """Parse LinkedIn search results."""
        from bs4 import BeautifulSoup
        
        profiles = []
        soup = BeautifulSoup(content, "html.parser")
        
        # LinkedIn result containers
        result_containers = soup.select(".ember-view, .artdeco-card, [class*='search-result']")
        
        for container in result_containers[:30]:
            # Look for name
            name_elem = container.select_one("[class*='name'], h3, .t-16")
            name = name_elem.get_text(strip=True) if name_elem else ""
            
            # Look for headline
            headline = container.select_one("[class*='headline'], .t-black--light")
            headline_text = headline.get_text(strip=True) if headline else ""
            
            if name or headline_text:
                profiles.append({
                    "name": name,
                    "headline": headline_text,
                    "query": query,
                })
        
        return profiles
    
    def _parse_profile(self, content: str) -> dict:
        """Parse individual LinkedIn profile."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(content, "html.parser")
        
        name = soup.select_one(".text-heading-xlarge")
        headline = soup.select_one(".text-body-medium")
        about = soup.select_one(".display-flex")
        
        return {
            "name": name.get_text(strip=True) if name else "",
            "headline": headline.get_text(strip=True) if headline else "",
            "about": about.get_text(strip=True)[:500] if about else "",
        }
