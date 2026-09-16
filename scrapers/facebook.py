"""
Facebook Scraper for SilentReach
Uses nodriver with desktop browser session.
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FacebookScraper:
    """Facebook scraper using nodriver."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.cookie_path = Path.home() / ".silentreach" / "cookies" / "facebook.json"
    
    async def search(self, query: str, limit: int = 20) -> dict:
        """Search Facebook posts."""
        import nodriver as uc
        
        browser = await uc.start(headless=False)
        
        if self.cookie_path.exists():
            try:
                browser = await browser.load_cookies(self.cookie_path)
            except:
                pass
        
        try:
            page = await browser.get(f"https://www.facebook.com/search/posts?q={query}")
            await asyncio.sleep(5)
            
            content = await page.get_content()
            posts = self._parse_posts(content, query)
            
            return {
                "query": query,
                "posts": posts[:limit],
                "total": len(posts),
            }
        except Exception as e:
            logger.error(f"Facebook search failed: {e}")
            return {"query": query, "posts": [], "error": str(e)}
        finally:
            await browser.stop()
    
    async def get_profile(self, username: str) -> dict:
        """Get Facebook user profile."""
        import nodriver as uc
        
        browser = await uc.start(headless=False)
        
        if self.cookie_path.exists():
            try:
                browser = await browser.load_cookies(self.cookie_path)
            except:
                pass
        
        try:
            page = await browser.get(f"https://www.facebook.com/{username}")
            await asyncio.sleep(3)
            
            content = await page.get_content()
            profile = self._parse_profile(content, username)
            
            return profile
        except Exception as e:
            return {"username": username, "error": str(e)}
        finally:
            await browser.stop()
    
    async def login(self, email: str, password: str) -> bool:
        """Login to Facebook."""
        import nodriver as uc
        
        browser = await uc.start(headless=False)
        
        try:
            page = await browser.get("https://www.facebook.com/login")
            await asyncio.sleep(2)
            
            # Find inputs
            email_input = await page.select('input[name="email"]')
            password_input = await page.select('input[name="pass"]')
            
            if email_input and password_input:
                await email_input.click()
                await email_input.send_keys(email)
                
                await password_input.click()
                await password_input.send_keys(password)
                
                submit = await page.select('button[type="submit"]')
                if submit:
                    await submit.click()
                    await asyncio.sleep(5)
                
                cookies = await page.get_cookies()
                self.cookie_path.parent.mkdir(parents=True, exist_ok=True)
                
                import json
                with open(self.cookie_path, "w") as f:
                    json.dump(cookies, f)
                
                logger.info(f"Facebook login successful")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Facebook login failed: {e}")
            return False
        finally:
            await browser.stop()
    
    def _parse_posts(self, content: str, query: str) -> list:
        """Parse Facebook posts from HTML."""
        from bs4 import BeautifulSoup
        
        posts = []
        soup = BeautifulSoup(content, "html.parser")
        
        # Facebook post containers
        post_containers = soup.select("div[class*='story']")
        
        for container in post_containers[:30]:
            # Get post text
            text_elem = container.select_one("div[class*='selectedText']")
            text = text_elem.get_text(strip=True) if text_elem else ""
            
            # Get author
            author = container.select_one("a[href*='/profile.php']")
            author_name = author.get_text(strip=True) if author else ""
            
            if text:
                posts.append({
                    "text": text[:500],
                    "author": author_name,
                    "query": query,
                })
        
        return posts
    
    def _parse_profile(self, content: str, username: str) -> dict:
        """Parse Facebook profile."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(content, "html.parser")
        
        # Look for profile info
        name_elem = soup.select_one("h1")
        bio_elem = soup.select_one("div[class*='biography']")
        
        return {
            "username": username,
            "name": name_elem.get_text(strip=True) if name_elem else "",
            "bio": bio_elem.get_text(strip=True)[:300] if bio_elem else "",
        }
