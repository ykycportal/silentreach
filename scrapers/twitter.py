"""
Twitter/X Scraper for SilentReach
Uses twitter-cli (from agent-reach ecosystem) with cookie auth.
"""

import asyncio
import logging
import json
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TwitterScraper:
    """Twitter/X scraper using twitter-cli or nodriver."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.cookie_path = Path.home() / ".silentreach" / "cookies" / "twitter.json"
    
    async def search(self, query: str, limit: int = 30, **kwargs) -> dict:
        """Search tweets."""
        # Try twitter-cli first
        tc_result = await self._search_twitter_cli(query, limit)
        if tc_result.get("tweets"):
            return tc_result
        
        # Fallback to nodriver
        logger.info("twitter-cli failed, trying nodriver...")
        return await self._search_nodriver(query, limit)
    
    async def _search_twitter_cli(self, query: str, limit: int) -> dict:
        """Search Twitter using twitter-cli."""
        try:
            # Check if twitter-cli is installed
            probe = await asyncio.create_subprocess_exec(
                "twitter-cli", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await probe.communicate()
            
            if probe.returncode != 0:
                logger.warning("twitter-cli not found")
                return {"query": query, "tweets": []}
            
            # Run search
            proc = await asyncio.create_subprocess_exec(
                "twitter-cli", "search", query, "--count", str(limit),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0 and stdout:
                tweets = self._parse_twitter_cli_output(stdout.decode())
                return {
                    "query": query,
                    "tweets": tweets,
                    "total": len(tweets),
                    "method": "twitter-cli",
                }
            
            return {"query": query, "tweets": [], "error": stderr.decode() if stderr else "Unknown error"}
            
        except FileNotFoundError:
            logger.warning("twitter-cli not installed")
            return {"query": query, "tweets": []}
        except Exception as e:
            logger.error(f"twitter-cli error: {e}")
            return {"query": query, "tweets": [], "error": str(e)}
    
    async def _search_nodriver(self, query: str, limit: int) -> dict:
        """Search Twitter using nodriver."""
        try:
            import nodriver as uc
            
            browser = await uc.start(headless=True)
            
            # Load cookies
            if self.cookie_path.exists():
                try:
                    browser = await browser.load_cookies(self.cookie_path)
                except:
                    pass
            
            page = await browser.get(f"https://x.com/search?q={query}&f=live")
            await asyncio.sleep(3)
            
            content = await page.get_content()
            tweets = self._parse_tweets_html(content, query)
            
            await browser.stop()
            
            return {
                "query": query,
                "tweets": tweets[:limit],
                "total": len(tweets),
                "method": "nodriver",
            }
            
        except Exception as e:
            logger.error(f"nodriver search failed: {e}")
            return {"query": query, "tweets": [], "error": str(e)}
    
    async def get_tweet(self, tweet_id: str) -> dict:
        """Get a specific tweet."""
        try:
            import nodriver as uc
            
            browser = await uc.start(headless=True)
            
            if self.cookie_path.exists():
                try:
                    browser = await browser.load_cookies(self.cookie_path)
                except:
                    pass
            
            page = await browser.get(f"https://x.com/status/{tweet_id}")
            await asyncio.sleep(2)
            
            content = await page.get_content()
            tweet = self._parse_tweet_detail(content, tweet_id)
            
            await browser.stop()
            
            return {"tweet_id": tweet_id, "tweet": tweet}
            
        except Exception as e:
            return {"tweet_id": tweet_id, "error": str(e)}
    
    async def get_timeline(self, username: str, limit: int = 20) -> dict:
        """Get user's timeline."""
        try:
            import nodriver as uc
            
            browser = await uc.start(headless=True)
            
            if self.cookie_path.exists():
                try:
                    browser = await browser.load_cookies(self.cookie_path)
                except:
                    pass
            
            page = await browser.get(f"https://x.com/{username}")
            await asyncio.sleep(3)
            
            content = await page.get_content()
            tweets = self._parse_tweets_html(content, username)
            
            await browser.stop()
            
            return {
                "username": username,
                "tweets": tweets[:limit],
                "total": len(tweets),
            }
            
        except Exception as e:
            return {"username": username, "error": str(e)}
    
    def _parse_twitter_cli_output(self, output: str) -> list:
        """Parse twitter-cli JSON output."""
        tweets = []
        try:
            data = json.loads(output)
            if isinstance(data, list):
                for tweet in data[:30]:
                    tweets.append({
                        "id": tweet.get("id_str", tweet.get("id", "")),
                        "text": tweet.get("text", ""),
                        "author": tweet.get("user", {}).get("screen_name", ""),
                        "created_at": tweet.get("created_at", ""),
                        "retweet_count": tweet.get("retweet_count", 0),
                        "favorite_count": tweet.get("favorite_count", 0),
                        "lang": tweet.get("lang", ""),
                    })
        except json.JSONDecodeError:
            # Try line-by-line
            for line in output.strip().split("\n"):
                if line.startswith("{"):
                    try:
                        tweet = json.loads(line)
                        tweets.append({
                            "text": tweet.get("text", ""),
                            "author": tweet.get("user", {}).get("screen_name", ""),
                        })
                    except:
                        pass
        return tweets
    
    def _parse_tweets_html(self, html: str, query: str) -> list:
        """Parse Twitter/X HTML for tweets."""
        from bs4 import BeautifulSoup
        
        tweets = []
        soup = BeautifulSoup(html, "html.parser")
        
        # Twitter/X tweet containers
        tweet_containers = soup.select('[data-testid="tweet"], article, .css-175oi2r')
        
        for container in tweet_containers[:50]:
            # Get tweet text
            text_elem = container.select_one('[data-testid="tweetText"], div[data-contents="true"]')
            if not text_elem:
                continue
                
            text = text_elem.get_text(strip=True)
            
            # Get author
            author = container.select_one('[data-testid="User-Name"]')
            author_name = author.get_text(strip=True) if author else ""
            
            # Get link
            link_elem = container.select_one("a[href^='/status/']")
            tweet_id = link_elem.get("href", "").split("/")[-1] if link_elem else ""
            
            # Get engagement
            likes = container.select_one('[data-testid="like"]')
            retweets = container.select_one('[data-testid="retweet"]')
            
            tweets.append({
                "text": text[:500],
                "author": author_name,
                "tweet_id": tweet_id,
                "likes": likes.get_text(strip=True) if likes else "",
                "retweets": retweets.get_text(strip=True) if retweets else "",
                "query": query,
            })
        
        return tweets
    
    def _parse_tweet_detail(self, html: str, tweet_id: str) -> dict:
        """Parse individual tweet detail."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Tweet text
        text_elem = soup.select_one('[data-testid="tweetText"]')
        text = text_elem.get_text(strip=True) if text_elem else ""
        
        # Author
        author_elem = soup.select_one('[data-testid="User-Name"]')
        author = author_elem.get_text(strip=True) if author_elem else ""
        
        # Time
        time_elem = soup.select_one('time')
        time = time_elem.get("datetime", "") if time_elem else ""
        
        return {
            "tweet_id": tweet_id,
            "text": text,
            "author": author,
            "created_at": time,
        }
