"""
Facebook Scraper for SilentReach
Uses nodriver with desktop browser session.
Features: proxy support, page/group targeting, JSON/CSV output
"""

import asyncio
import logging
import json
import csv
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class FacebookScraper:
    """Facebook scraper using nodriver with proxy support."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.cookie_path = Path.home() / ".silentreach" / "cookies" / "facebook.json"
        self.proxy = self.config.get("proxy")  # "http://IP:PORT" or "user:pass@ip:port"
        self.timeout = self.config.get("timeout", 300)  # seconds
        self.headless = self.config.get("headless", False)
        self.browser_type = self.config.get("browser", "chrome")
    
    async def search(self, query: str, limit: int = 20, output_format: str = "json") -> dict:
        """Search Facebook posts by query."""
        import nodriver as uc
        
        proxy_args = {"proxy": self.proxy} if self.proxy else {}
        browser = await uc.start(headless=self.headless, **proxy_args)
        
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
            
            result = {
                "query": query,
                "posts": posts[:limit],
                "total": len(posts),
                "source": "facebook_search",
                "timestamp": asyncio.get_event_loop().time(),
            }
            
            if output_format == "csv":
                return self._to_csv(result)
            return result
            
        except Exception as e:
            logger.error(f"Facebook search failed: {e}")
            return {"query": query, "posts": [], "error": str(e)}
        finally:
            await browser.stop()
    
    async def scrape_page(self, page_name: str, limit: int = 20, output_format: str = "json") -> dict:
        """Scrape a specific Facebook page by name."""
        import nodriver as uc
        
        proxy_args = {"proxy": self.proxy} if self.proxy else {}
        browser = await uc.start(headless=self.headless, **proxy_args)
        
        if self.cookie_path.exists():
            try:
                browser = await browser.load_cookies(self.cookie_path)
            except:
                pass
        
        try:
            # Navigate to page timeline
            page_url = f"https://www.facebook.com/{page_name}/posts"
            await browser.get(page_url)
            await asyncio.sleep(5)
            
            content = await browser.get_content()
            posts = self._parse_posts(content, page_name)
            
            result = {
                "page": page_name,
                "url": page_url,
                "posts": posts[:limit],
                "total": len(posts),
                "source": "facebook_page",
                "timestamp": asyncio.get_event_loop().time(),
            }
            
            if output_format == "csv":
                return self._to_csv(result)
            return result
            
        except Exception as e:
            logger.error(f"Facebook page scrape failed: {e}")
            return {"page": page_name, "posts": [], "error": str(e)}
        finally:
            await browser.stop()
    
    async def scrape_group(self, group_name: str, limit: int = 20, output_format: str = "json") -> dict:
        """Scrape a specific Facebook group."""
        import nodriver as uc
        
        proxy_args = {"proxy": self.proxy} if self.proxy else {}
        browser = await uc.start(headless=self.headless, **proxy_args)
        
        if self.cookie_path.exists():
            try:
                browser = await browser.load_cookies(self.cookie_path)
            except:
                pass
        
        try:
            # Navigate to group
            group_url = f"https://www.facebook.com/groups/{group_name}"
            await browser.get(group_url)
            await asyncio.sleep(5)
            
            content = await browser.get_content()
            posts = self._parse_posts(content, group_name)
            
            result = {
                "group": group_name,
                "url": group_url,
                "posts": posts[:limit],
                "total": len(posts),
                "source": "facebook_group",
                "timestamp": asyncio.get_event_loop().time(),
            }
            
            if output_format == "csv":
                return self._to_csv(result)
            return result
            
        except Exception as e:
            logger.error(f"Facebook group scrape failed: {e}")
            return {"group": group_name, "posts": [], "error": str(e)}
        finally:
            await browser.stop()
    
    async def login(self, email: str, password: str) -> bool:
        """Login to Facebook."""
        import nodriver as uc
        
        proxy_args = {"proxy": self.proxy} if self.proxy else {}
        browser = await uc.start(headless=False, **proxy_args)
        
        try:
            page = await browser.get("https://www.facebook.com/login")
            await asyncio.sleep(2)
            
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
    
    def _parse_posts(self, content: str, source: str) -> list:
        """Parse Facebook posts from HTML."""
        from bs4 import BeautifulSoup
        
        posts = []
        soup = BeautifulSoup(content, "html.parser")
        
        # Multiple selectors for different FB layouts
        selectors = [
            "div[class*='story']",
            "article",
            "div[data-content-type='timeline']",
            "div[class*='userContent']",
        ]
        
        for selector in selectors:
            containers = soup.select(selector)
            if containers:
                break
        
        for container in containers[:30]:
            # Post text - try multiple selectors
            text_elem = (
                container.select_one("div[class*='selectedText']") or
                container.select_one("p span") or
                container.select_one("div[class*='entryContent']") or
                container.select_one("div[data-block='true']")
            )
            text = text_elem.get_text(strip=True) if text_elem else ""
            
            # Author
            author = (
                container.select_one("a[href*='/profile.php']") or
                container.select_one("a[href*='/permalink.php']") or
                container.select_one("div[class*='senderName']")
            )
            author_name = author.get_text(strip=True) if author else ""
            
            # Timestamp
            time_elem = container.select_one("abbr[data-ctime]") or container.select_one("time")
            timestamp = time_elem.get("datetime", "") if time_elem else ""
            
            # Engagement (likes, comments)
            likes = self._extract_engagement(container, "like")
            comments = self._extract_engagement(container, "comment")
            
            if text:
                posts.append({
                    "text": text[:500],
                    "author": author_name,
                    "source": source,
                    "timestamp": timestamp,
                    "likes": likes,
                    "comments": comments,
                    "type": "post",
                })
        
        return posts
    
    def _extract_engagement(self, container, type_: str) -> int:
        """Extract engagement count from post."""
        # Look for numbers near like/comment labels
        import re
        text = container.get_text()
        
        patterns = {
            "like": r'(\d[\d,]*)\s*(?:likes|like)',
            "comment": r'(\d[\d,]*)\s*(?:comments|comment)',
        }
        
        match = re.search(patterns.get(type_, ''), text)
        if match:
            return int(match.group(1).replace(',', ''))
        return 0
    
    def _to_csv(self, data: dict) -> str:
        """Convert result to CSV string."""
        import io
        from datetime import datetime
        
        posts = data.get("posts", [])
        if not posts:
            return "No posts to export\n"
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "type", "source", "author", "text", "timestamp", 
            "likes", "comments", "url"
        ])
        
        # Posts
        for post in posts:
            writer.writerow([
                post.get("type", "post"),
                post.get("source", ""),
                post.get("author", ""),
                post.get("text", ""),
                post.get("timestamp", ""),
                post.get("likes", ""),
                post.get("comments", ""),
                data.get("url", ""),
            ])
        
        return output.getvalue()
    
    def save_to_file(self, data: dict, filename: str, output_format: str = "auto") -> str:
        """Save scraped data to file."""
        output_dir = Path.home() / ".silentreach" / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Auto-detect format
        if output_format == "auto":
            ext = Path(filename).suffix.lower()
            if ext == ".csv":
                output_format = "csv"
            else:
                output_format = "json"
        
        filepath = output_dir / filename
        
        if output_format == "csv":
            csv_content = self._to_csv(data) if isinstance(data, dict) else str(data)
            filepath.write_text(csv_content)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved to {filepath}")
        return str(filepath)
