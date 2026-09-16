"""
YouTube Scraper for SilentReach
Uses yt-dlp directly for video info and search.
"""

import asyncio
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class YouTubeScraper:
    """YouTube scraper using yt-dlp."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
    
    async def search(self, query: str, limit: int = 20) -> dict:
        """Search YouTube videos."""
        try:
            import yt_dlp
            
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "extract_flat": False,
            }
            
            videos = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                for entry in info.get("entries", [])[:limit]:
                    videos.append({
                        "title": entry.get("title"),
                        "video_id": entry.get("id"),
                        "channel": entry.get("channel"),
                        "duration": entry.get("duration"),
                        "view_count": entry.get("view_count"),
                        "upload_date": entry.get("upload_date"),
                        "description": entry.get("description", "")[:200],
                        "thumbnail": entry.get("thumbnail"),
                    })
            
            return {
                "query": query,
                "videos": videos,
                "total": len(videos),
                "method": "yt-dlp",
            }
            
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
            return {"query": query, "videos": [], "error": str(e)}
    
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
                    "description": info.get("description", "")[:1000],
                    "duration": info.get("duration"),
                    "view_count": info.get("view_count"),
                    "like_count": info.get("like_count"),
                    "channel": info.get("channel"),
                    "channel_id": info.get("channel_id"),
                    "upload_date": info.get("upload_date"),
                    "thumbnail": info.get("thumbnail"),
                    "tags": info.get("tags", []),
                    "categories": info.get("categories", []),
                    "subtitles": self._get_subtitles(info),
                }
                
        except Exception as e:
            logger.error(f"YouTube video info failed: {e}")
            return {"video_id": video_id, "error": str(e)}
    
    def _get_subtitles(self, info: dict) -> dict:
        """Extract subtitle information."""
        subtitles = {}
        
        if "requested_subtitles" in info:
            for lang, url in info["requested_subtitles"].items():
                subtitles[lang] = url
        
        # Also check automatic captions
        if "automatic_captions" in info:
            for lang, urls in info["automatic_captions"].items():
                if lang not in subtitles:
                    subtitles[f"{lang}_auto"] = urls[0].get("url", "")
        
        return subtitles
    
    async def get_channel_info(self, channel_id: str) -> dict:
        """Get YouTube channel information."""
        try:
            import yt_dlp
            
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/channel/{channel_id}", download=False)
                
                return {
                    "channel_id": channel_id,
                    "name": info.get("name"),
                    "description": info.get("description", "")[:500],
                    "subscriber_count": info.get("subscriber_count"),
                    "video_count": info.get("video_count"),
                    "thumbnail": info.get("thumbnail"),
                }
                
        except Exception as e:
            return {"channel_id": channel_id, "error": str(e)}
    
    async def download_subtitle(self, video_id: str, lang: str = "en") -> Optional[str]:
        """Download video subtitles."""
        try:
            import yt_dlp
            
            ydl_opts = {
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": [lang],
                "subtitlesformat": "srv1/txt/vtt/json",
                "outtmpl": f"/tmp/subtitle_{video_id}.%(ext)s",
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                # Find subtitle file
                if "requested_subtitles" in info:
                    for l, data in info["requested_subtitles"].items():
                        if l == lang or lang in l:
                            return data.get("url")
                
                return None
                
        except Exception as e:
            logger.error(f"Subtitle download failed: {e}")
            return None
