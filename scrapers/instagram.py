"""
Instagram Scraper for SilentReach
Uses nodriver with desktop browser session (required for Instagram).
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class InstagramScraper:
    """Instagram scraper using nodriver. Requires desktop mode."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.cookie_path = Path.home() / ".silentreach" / "cookies" / "instagram.json"
    
    async def search(self, query: str, limit: int = 20) -> dict:
        """Search Instagram posts."""
        try:
            import nodriver as uc
            
            # Instagram requires headful mode
            browser = await uc.start(headless=False)
            
            # Load cookies
            if self.cookie_path.exists():
                try:
                    browser = await browser.load_cookies(self.cookie_path)
                except Exception as e:
                    logger.warning(f"Failed to load cookies: {e}")
            
            # Navigate to search
            encoded_query = query.replace(" ", "%20")
            page = await browser.get(f"https://www.instagram.com/explore/tags/{encoded_query}/")
            await asyncio.sleep(5)  # Wait for heavy JS
            
            content = await page.get_content()
            posts = self._parse_posts(content, query)
            
            await browser.stop()
            
            return {
                "query": query,
                "posts": posts[:limit],
                "total": len(posts),
                "method": "nodriver",
            }
            
        except Exception as e:
            logger.error(f"Instagram search failed: {e}")
            return {"query": query, "posts": [], "error": str(e)}
    
    async def get_profile(self, username: str, limit: int = 20) -> dict:
        """Get Instagram user profile and recent posts."""
        try:
            import nodriver as uc
            
            browser = await uc.start(headless=False)
            
            if self.cookie_path.exists():
                try:
                    browser = await browser.load_cookies(self.cookie_path)
                except:
                    pass
            
            page = await browser.get(f"https://www.instagram.com/{username}/")
            await asyncio.sleep(5)
            
            content = await page.get_content()
            profile = self._parse_profile(content, username)
            
            await browser.stop()
            
            return profile
            
        except Exception as e:
            return {"username": username, "error": str(e)}
    
    async def login(self, username: str, password: str) -> bool:
        """Login to Instagram and save cookies."""
        try:
            import nodriver as uc
            
            # Must be non-headless for login
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
                    if "login" not in current_url.lower():
                        cookies = await page.get_cookies()
                        self.cookie_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        import json
                        with open(self.cookie_path, "w") as f:
                            json.dump(cookies, f)
                        
                        logger.info(f"Instagram login successful, saved {len(cookies)} cookies")
                        return True
                
                return False
                
            finally:
                await browser.stop()
                
        except Exception as e:
            logger.error(f"Instagram login failed: {e}")
            return False
    
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
                
                # Get link
                link = container.select_one("a")
                link_url = link.get("href", "") if link else ""
                
                posts.append({
                    "image_url": src,
                    "caption": caption_text[:300],
                    "link": link_url,
                    "query": query,
                })
        
        return posts
    
    def _parse_profile(self, content: str, username: str) -> dict:
        """Parse Instagram profile info."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, "html.parser")

        # Profile stats - different selectors for posts vs followers
        # Instagram uses nested divs with specific classes
        stats_containers = soup.select("ul[class*='gdHQl'] li span") or soup.select('[class*="g47SY"]')

        # Try to find specific elements by context
        posts = 0
        followers = 0

        # Look for posts count (usually first number in stats)
        for elem in stats_containers:
            text = elem.get_text(strip=True)
            if text and text.replace(',', '').isdigit():
                num = int(text.replace(',', ''))
                if num > 1000:  # Likely followers
                    followers = num
                elif posts == 0:  # First number is posts
                    posts = num

        # Fallback: try meta tags
        if not posts:
            posts_meta = soup.select_one("meta[property='og:url']")
            if posts_meta:
                # Can't get exact counts from meta, set defaults
                posts = 0

        # Bio
        bio_elem = soup.select_one("meta[name='description']")
        bio = bio_elem.get("content", "") if bio_elem else ""

        return {
            "username": username,
            "posts": posts,
            "followers": followers,
            "bio": bio[:300],
        }
