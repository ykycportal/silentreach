"""
Twitter/X Scraper for SilentReach
Uses nodriver with authenticated sessions for best stealth.
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TwitterScraper:
    """
    Twitter/X scraper using nodriver with cookie persistence.
    Best stealth: uses real browser session, not headless detection.
    """
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.cookie_path = Path.home() / ".silentreach" / "cookies" / "twitter.json"
    
    async def search(self, query: str, limit: int = 30, **kwargs) -> dict:
        """Search tweets."""
        import nodriver as uc
        
        browser = await uc.start(headless=True)
        
        # Load existing cookies
        if self.cookie_path.exists():
            try:
                browser = await browser.load_cookies(self.cookie_path)
            except Exception as e:
                logger.warning(f"Failed to load cookies: {e}")
        
        try:
            # Search
            page = await browser.get(f"https://x.com/search?q={query}&f=live")
            await asyncio.sleep(3)  # Wait for JS
            
            content = await page.get_content()
            tweets = self._parse_tweets(content, query)
            
            return {
                "query": query,
                "tweets": tweets[:limit],
                "total": len(tweets),
                "auth_required": True,
            }
        except Exception as e:
            logger.error(f"Twitter search failed: {e}")
            return {"query": query, "tweets": [], "error": str(e)}
        finally:
            await browser.stop()
    
    async def get_timeline(self, username: str, limit: int = 20) -> dict:
        """Get user's timeline."""
        import nodriver as uc
        
        browser = await uc.start(headless=True)
        
        if self.cookie_path.exists():
            try:
                browser = await browser.load_cookies(self.cookie_path)
            except:
                pass
        
        try:
            page = await browser.get(f"https://x.com/{username}")
            await asyncio.sleep(3)
            
            content = await page.get_content()
            tweets = self._parse_tweets(content, username)
            
            return {
                "username": username,
                "tweets": tweets[:limit],
            }
        except Exception as e:
            return {"username": username, "error": str(e)}
        finally:
            await browser.stop()
    
    async def login(self, username: str, password: str) -> bool:
        """Login to Twitter and save cookies."""
        import nodriver as uc
        
        browser = await uc.start(headless=False)  # Non-headless for login
        
        try:
            page = await browser.get("https://x.com/login")
            
            # Find username input
            username_input = await page.select("#username")
            if username_input:
                await username_input.click()
                await username_input.send_keys(username)
                await page.submit()
            
            # Find password input
            password_input = await page.select('input[name="password"]')
            if password_input:
                await password_input.click()
                await password_input.send_keys(password)
                await page.submit()
            
            # Wait for login
            await asyncio.sleep(5)
            
            # Save cookies
            cookies = await page.get_cookies()
            self.cookie_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(self.cookie_path, "w") as f:
                json.dump(cookies, f)
            
            logger.info(f"Saved {len(cookies)} cookies to {self.cookie_path}")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
        finally:
            await browser.stop()
    
    def _parse_tweets(self, content: str, query: str) -> list:
        """Parse tweet content from HTML."""
        from bs4 import BeautifulSoup
        
        tweets = []
        soup = BeautifulSoup(content, "html.parser")
        
        # Twitter/X tweet containers
        tweet_containers = soup.select('[data-testid="tweet"], article, .css-175oi2r')
        
        for container in tweet_containers[:50]:
            # Get tweet text
            text_elem = container.select_one('[data-testid="tweetText"], div[data-contents="true"]')
            if text_elem:
                text = text_elem.get_text(strip=True)
                
                # Get author
                author = container.select_one('[data-testid="User-Name"]')
                author_name = author.get_text(strip=True) if author else ""
                
                # Get link
                link_elem = container.select_one("a[href^='/status/']")
                tweet_id = link_elem.get("href", "").split("/")[-1] if link_elem else ""
                
                tweets.append({
                    "text": text[:500],
                    "author": author_name,
                    "tweet_id": tweet_id,
                    "query": query,
                })
        
        return tweets
