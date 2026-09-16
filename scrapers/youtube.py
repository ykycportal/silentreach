"""
YouTube Scraper for SilentReach
Uses agent-reach for public access, nodriver for authenticated search.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class YouTubeScraper:
    """YouTube content scraper using yt-dlp and agent-reach."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
    
    async def search(self, query: str, limit: int = 20) -> dict:
        """Search YouTube videos."""
        results = []
        
        # Try agent-reach first
        try:
            from agent_reach import AgentReach
            reach = AgentReach()
            
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            result = reach.read(url)
            
            if result:
                results.extend(self._parse_search_results(result.content, query))
        except Exception as e:
            logger.warning(f"Agent-reach YouTube search failed: {e}")
        
        # Fallback to yt-dlp
        if len(results) < limit:
            try:
                yt_results = await self._search_ytdlp(query, limit - len(results))
                results.extend(yt_results)
            except Exception as e:
                logger.warning(f"yt-dlp search failed: {e}")
        
        return {
            "query": query,
            "results": results[:limit],
            "total": len(results),
        }
    
    async def get_video_info(self, video_id: str) -> dict:
        """Get detailed video information."""
        try:
            import yt_dlp
            
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                return {
                    "id": info.get("id"),
                    "title": info.get("title"),
                    "description": info.get("description", "")[:500],
                    "duration": info.get("duration"),
                    "view_count": info.get("view_count"),
                    "channel": info.get("channel"),
                    "upload_date": info.get("upload_date"),
                    "thumbnail": info.get("thumbnail"),
                    "tags": info.get("tags", []),
                }
        except Exception as e:
            logger.error(f"Error fetching video info: {e}")
            return {"error": str(e)}
    
    def _parse_search_results(self, content: str, query: str) -> list:
        """Parse YouTube search results HTML."""
        from bs4 import BeautifulSoup
        
        results = []
        soup = BeautifulSoup(content, "html.parser")
        
        # YouTube search result containers
        video_containers = soup.select("ytd-grid-video-renderer, ytd-video-renderer, .yt-lockup")
        
        for container in video_containers[:20]:
            title_elem = container.select_one("a#video-title, .yt-lockup-title a, h3 a")
            if title_elem:
                title = title_elem.get_text(strip=True)
                video_id = title_elem.get("href", "").split("?v=")[-1].split("&")[0]
                
                channel = container.select_one(".yt-lockup-byline a, .video-owner a")
                
                results.append({
                    "title": title,
                    "video_id": video_id,
                    "channel": channel.get_text(strip=True) if channel else "",
                    "query": query,
                })
        
        return results
    
    async def _search_ytdlp(self, query: str, limit: int) -> list:
        """Search YouTube using yt-dlp."""
        try:
            import yt_dlp
            
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
            }
            
            results = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                for entry in info.get("entries", [])[:limit]:
                    results.append({
                        "title": entry.get("title"),
                        "video_id": entry.get("id"),
                        "channel": entry.get("channel"),
                        "duration": entry.get("duration"),
                        "view_count": entry.get("view_count"),
                    })
            
            return results
        except Exception as e:
            logger.error(f"yt-dlp search error: {e}")
            return []
