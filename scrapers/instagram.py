"""
Instagram Scraper for SilentReach
Uses nodriver with desktop browser session for best stealth.
Note: Instagram requires desktop (non-headless) mode.
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class InstagramScraper:
    """
    Instagram scraper using nodriver.
    IMPORTANT: Requires desktop mode and real browser session.
    """
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.cookie_path = Path.home() / ".silentreach" / "cookies" / "instagram.json"
    
    async def search(self, query: str, limit: int = 20) -> dict:
        """Search Instagram posts."""
        import nodriver as uc
        
        # Instagram requires headful mode
        browser = await uc.start(headless=False)
        
        # Load cookies
        if self.cookie_path.exists():
            try:
                browser = await browser.load_cookies(self.cookie_path)
            except Exception as e:
                logger.warning(f"Failed to load cookies: {e}")
        
        try:
            # Navigate to search
            page = await browser.get(f"https://www.instagram.com/explore/tags/{query}/")
            await asyncio.sleep(5)  # Wait for heavy JS
            
            content = await page.get_content()
            posts = self._parse_posts(content, query)
            
            return {
                "query": query,
                "posts": posts[:limit],
                "total": len(posts),
            }
        except Exception as e:
            logger.error(f"Instagram search failed: {e}")
            return {"query": query, "posts": [], "error": str(e)}
        finally:
            await browser.stop()
    
    async def get_profile(self, username: str, limit: int = 20) -> dict:
        """Get Instagram user profile and recent posts."""
        import nodriver as uc
        
        browser = await uc.start(headless=False)
        
        if self.cookie_path.exists():
            try:
                browser = await browser.load_cookies(self.cookie_path)
            except:
                pass
        
        try:
            page = await browser.get(f"https://www.instagram.com/{username}/")
            await asyncio.sleep(5)
            
            content = await page.get_content()
            profile = self._parse_profile(content, username)
            
            return profile
        except Exception as e:
            return {"username": username, "error": str(e)}
        finally:
            await browser.stop()
    
    async def login(self, username: str, password: str) -> bool:
        """Login to Instagram and save cookies."""
        import nodriver as uc
        
        browser = await uc.start(headless=False)
        
        try:
            page = await browser.get("https://www.instagram.com/accounts/login/")
            await asyncio.sleep(2)
            
            # Find inputs
            username_input = await page.select('input[name="username"]')
            password_input = await page.select('input[name="password"]')
            
            if username_input and password_input:
                await username_input.click()
                await username_input.send_keys(username)
                
                await password_input.click()
                await password_input.send_keys(password)
                
                # Submit
                submit_btn = await page.select('button[type="submit"]')
                if submit_btn:
                    await submit_btn.click()
                    await asyncio.sleep(5)
                
                # Check if login successful
                current_url = await page.get_url()
                if "login" not in current_url:
                    cookies = await page.get_cookies()
                    self.cookie_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    import json
                    with open(self.cookie_path, "w") as f:
                        json.dump(cookies, f)
                    
                    logger.info(f"Instagram login successful, saved {len(cookies)} cookies")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Instagram login failed: {e}")
            return False
        finally:
            await browser.stop()
    
    def _parse_posts(self, content: str, query: str) -> list:
        """Parse Instagram posts from HTML."""
        from bs4 import BeautifulSoup
        
        posts = []
        soup = BeautifulSoup(content, "html.parser")
        
        # Instagram post containers
        post_containers = soup.select("article, .v1N3e, [class*='gridImage']")
        
        for container in post_containers[:30]:
            # Get image
            img = container.select_one("img")
            if img:
                src = img.get("src", "")
                
                # Get caption
                caption = container.select_one("[class*='x1lliihq']")
                caption_text = caption.get_text(strip=True) if caption else ""
                
                posts.append({
                    "image_url": src,
                    "caption": caption_text[:300],
                    "query": query,
                })
        
        return posts
    
    def _parse_profile(self, content: str, username: str) -> dict:
        """Parse Instagram profile info."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, "html.parser")

        # Profile stats - use context-aware parsing
        # Find all stat items and extract posts/followers from context
        stats = []
        for stat_elem in soup.select("[class*='g47SY'], li[class*='g47SY']"):
            text = stat_elem.get_text(strip=True)
            if text and text.isdigit():
                stats.append(int(text))

        # Instagram profile stats are typically: posts, followers, following
        # We return what we can find, prioritizing the first two numeric values
        result = {"username": username}
        if len(stats) >= 1:
            result["posts"] = stats[0]
        if len(stats) >= 2:
            result["followers"] = stats[1]
        elif len(stats) >= 1:
            # Fallback: if only one stat found, assume it's followers
            result["followers"] = stats[0]

        return result
