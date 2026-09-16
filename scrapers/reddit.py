"""
Reddit Scraper for SilentReach
Uses rdt-cli (from agent-reach ecosystem) or nodriver with cookies.
"""

import asyncio
import logging
import subprocess
import json
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class RedditScraper:
    """Reddit scraper using rdt-cli or nodriver."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.cookie_path = Path.home() / ".silentreach" / "cookies" / "reddit.json"
    
    async def search(self, query: str, limit: int = 20, **kwargs) -> dict:
        """Search Reddit posts."""
        results = {"query": query, "posts": [], "total": 0}
        
        # Try rdt-cli first (primary method)
        rdt_result = await self._search_rdt(query, limit)
        if rdt_result and len(rdt_result.get("posts", [])) > 0:
            return rdt_result
        
        # Fallback to nodriver
        logger.info("rdt-cli failed, trying nodriver...")
        nr_result = await self._search_nodriver(query, limit)
        if nr_result:
            return nr_result
        
        return results
    
    async def _search_rdt(self, query: str, limit: int) -> dict:
        """Search Reddit using rdt-cli."""
        try:
            # Check if rdt-cli is installed
            probe = await asyncio.create_subprocess_exec(
                "rdt", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await probe.communicate()
            
            if probe.returncode != 0:
                logger.warning("rdt-cli not found or not configured")
                return {"query": query, "posts": []}
            
            # Run search
            proc = await asyncio.create_subprocess_exec(
                "rdt", "search", query, "--limit", str(limit),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0 and stdout:
                posts = self._parse_rdt_output(stdout.decode())
                return {
                    "query": query,
                    "posts": posts,
                    "total": len(posts),
                    "method": "rdt-cli",
                }
            
            return {"query": query, "posts": [], "error": stderr.decode() if stderr else "Unknown error"}
            
        except FileNotFoundError:
            logger.warning("rdt-cli not installed")
            return {"query": query, "posts": []}
        except Exception as e:
            logger.error(f"rdt-cli error: {e}")
            return {"query": query, "posts": [], "error": str(e)}
    
    async def _search_nodriver(self, query: str, limit: int) -> dict:
        """Search Reddit using nodriver."""
        try:
            import nodriver as uc
            
            browser = await uc.start(headless=True)
            
            # Load cookies if available
            if self.cookie_path.exists():
                try:
                    browser = await browser.load_cookies(self.cookie_path)
                except:
                    pass
            
            page = await browser.get(f"https://www.reddit.com/search/?q={query}")
            await asyncio.sleep(3)
            
            content = await page.get_content()
            posts = self._parse_html(content, query)
            
            await browser.stop()
            
            return {
                "query": query,
                "posts": posts[:limit],
                "total": len(posts),
                "method": "nodriver",
            }
            
        except Exception as e:
            logger.error(f"nodriver search failed: {e}")
            return {"query": query, "posts": [], "error": str(e)}
    
    def _parse_rdt_output(self, output: str) -> list:
        """Parse rdt-cli JSON output."""
        posts = []
        try:
            data = json.loads(output)
            if isinstance(data, list):
                for post in data[:20]:
                    posts.append({
                        "title": post.get("title", ""),
                        "author": post.get("author", ""),
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "url": post.get("url", ""),
                        "subreddit": post.get("subreddit", ""),
                        "created_utc": post.get("created_utc", ""),
                    })
        except json.JSONDecodeError:
            # Try to parse as individual lines
            for line in output.strip().split("\n"):
                if line.startswith("{"):
                    try:
                        post = json.loads(line)
                        posts.append({
                            "title": post.get("title", ""),
                            "author": post.get("author", ""),
                            "score": post.get("score", 0),
                        })
                    except:
                        pass
        return posts
    
    def _parse_html(self, html: str, query: str) -> list:
        """Parse Reddit HTML for posts."""
        from bs4 import BeautifulSoup
        
        posts = []
        soup = BeautifulSoup(html, "html.parser")
        
        # Reddit post containers
        post_containers = soup.select(".Post, article, [data-testid='post-container']")
        
        for container in post_containers[:30]:
            title_elem = container.select_one(".PostTitle, .title, h1, h2, a")
            if title_elem:
                title = title_elem.get_text(strip=True)
                link = title_elem.get("href", "")
                
                # Get metadata
                score_elem = container.select_one("[class*='score']")
                comments_elem = container.select_one("[class*='comments']")
                
                posts.append({
                    "title": title,
                    "link": link,
                    "score": score_elem.get_text() if score_elem else "",
                    "comments": comments_elem.get_text() if comments_elem else "",
                    "query": query,
                })
        
        return posts
    
    async def get_post(self, post_id: str) -> dict:
        """Get a specific Reddit post."""
        # Try rdt-cli
        try:
            proc = await asyncio.create_subprocess_exec(
                "rdt", "read", post_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0 and stdout:
                post = json.loads(stdout)
                return {"post_id": post_id, "post": post}
        except:
            pass
        
        # Fallback to direct URL
        try:
            import urllib.request
            url = f"https://www.reddit.com/comments/{post_id}.json"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                return {"post_id": post_id, "post": data}
        except Exception as e:
            return {"post_id": post_id, "error": str(e)}
