"""
Bilibili Scraper for SilentReach
Uses agent-reach for public content, nodriver for comments/subtitles.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BilibiliScraper:
    """Bilibili video scraper."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
    
    async def search(self, query: str, limit: int = 20) -> dict:
        """Search Bilibili videos."""
        try:
            from agent_reach import AgentReach
            reach = AgentReach()
            
            url = f"https://search.bilibili.com/all?keyword={query}"
            result = reach.read(url)
            
            if result:
                videos = self._parse_videos(result.content, query)
                return {
                    "query": query,
                    "videos": videos[:limit],
                    "total": len(videos),
                }
        except Exception as e:
            logger.warning(f"Bilibili search failed: {e}")
        
        return {"query": query, "videos": []}
    
    async def get_video(self, bvid: str) -> dict:
        """Get video details and comments."""
        try:
            import yt_dlp
            
            # Get video info
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.bilibili.com/video/{bvid}", download=False)
                
                return {
                    "bvid": bvid,
                    "title": info.get("title"),
                    "description": info.get("description", "")[:500],
                    "author": info.get("creator"),
                    "duration": info.get("duration"),
                    "view_count": info.get("view_count"),
                    "like_count": info.get("like_count"),
                    "upload_date": info.get("upload_date"),
                }
        except Exception as e:
            logger.error(f"Bilibili video fetch failed: {e}")
            return {"bvid": bvid, "error": str(e)}
    
    def _parse_videos(self, content: str, query: str) -> list:
        """Parse Bilibili search results."""
        from bs4 import BeautifulSoup
        
        videos = []
        soup = BeautifulSoup(content, "html.parser")
        
        # Bilibili video cards
        video_cards = soup.select(".bili-video-card, .video-item, [class*='video-item']")
        
        for card in video_cards[:20]:
            # Title
            title_elem = card.select_one("a, .title, .info-title")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Link
            link_elem = card.select_one("a[href]")
            link = link_elem.get("href", "") if link_elem else ""
            
            if title and link:
                videos.append({
                    "title": title,
                    "link": link,
                    "query": query,
                })
        
        return videos
