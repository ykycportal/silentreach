"""
LinkedIn Scraper for SilentReach
Public pages via Jina Reader (agent-reach), authenticated via nodriver.
"""

import asyncio
import logging
import urllib.request
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """LinkedIn scraper - public pages via Jina, authenticated via nodriver."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.cookie_path = Path.home() / ".silentreach" / "cookies" / "linkedin.json"
    
    async def search_public(self, query: str, limit: int = 20) -> dict:
        """Search LinkedIn using Jina Reader (public pages only)."""
        try:
            # Use Jina Reader via agent-reach web channel
            url = f"https://www.linkedin.com/search/results/all/?keywords={query.replace(' ', '+')}"
            jina_url = f"https://r.jina.ai/{url}"
            
            req = urllib.request.Request(
                jina_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/plain",
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
                
            profiles = self._parse_linkedin_content(content, query)
            
            return {
                "query": query,
                "profiles": profiles[:limit],
                "total": len(profiles),
                "method": "jina-reader",
                "note": "Limited to public profiles only",
            }
            
        except Exception as e:
            logger.warning(f"LinkedIn public search failed: {e}")
            return {"query": query, "profiles": [], "method": "jina-reader"}
    
    async def search_auth(self, query: str, limit: int = 20) -> dict:
        """Search LinkedIn with authenticated session."""
        try:
            import nodriver as uc
            
            browser = await uc.start(headless=True)
            
            # Load cookies
            if self.cookie_path.exists():
                try:
                    browser = await browser.load_cookies(self.cookie_path)
                except:
                    pass
            
            page = await browser.get(f"https://www.linkedin.com/search/results/all/?keywords={query}")
            await asyncio.sleep(3)
            
            content = await page.get_content()
            profiles = self._parse_linkedin_content(content, query)
            
            await browser.stop()
            
            return {
                "query": query,
                "profiles": profiles[:limit],
                "total": len(profiles),
                "method": "nodriver",
            }
            
        except Exception as e:
            return {"query": query, "profiles": [], "error": str(e)}
    
    async def get_profile(self, profile_url: str) -> dict:
        """Get a specific LinkedIn profile."""
        try:
            # Try Jina Reader first
            jina_url = f"https://r.jina.ai/{profile_url}"
            
            req = urllib.request.Request(
                jina_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/plain",
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
                
            profile = self._parse_profile(content)
            
            return {"url": profile_url, "profile": profile, "method": "jina-reader"}
            
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
