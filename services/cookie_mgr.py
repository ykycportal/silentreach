"""
Cookie Manager for SilentReach.
Handles persistent browser sessions and cookie storage.
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CookieManager:
    """
    Manages browser cookies for persistent sessions.
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else Path.home() / ".silentreach" / "cookies"
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def save_cookies(self, platform: str, cookies: Dict, metadata: Optional[Dict] = None):
        """
        Save cookies for a platform with metadata.
        
        Args:
            platform: Platform name (twitter, instagram, etc.)
            cookies: Dictionary of cookies
            metadata: Optional metadata (login time, username, etc.)
        """
        filename = self.storage_path / f"{platform}.json"
        
        data = {
            "cookies": cookies,
            "saved_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {len(cookies)} cookies for {platform}")
        return filename
    
    async def load_cookies(self, platform: str) -> Optional[Dict]:
        """
        Load cookies for a platform.
        
        Returns:
            Cookie dictionary or None if not found
        """
        filename = self.storage_path / f"{platform}.json"
        
        if not filename.exists():
            return None
        
        try:
            with open(filename) as f:
                data = json.load(f)
            
            cookies = data.get("cookies", {})
            
            # Check if cookies are expired
            saved_at = datetime.fromisoformat(data.get("saved_at"))
            if self._is_expired(saved_at):
                logger.warning(f"Cookies for {platform} may be expired")
                # Still return them - the platform will tell us if they're invalid
            
            return cookies
        except Exception as e:
            logger.error(f"Failed to load cookies for {platform}: {e}")
            return None
    
    async def delete_cookies(self, platform: str) -> bool:
        """Delete cookies for a platform."""
        filename = self.storage_path / f"{platform}.json"
        
        if filename.exists():
            filename.unlink()
            logger.info(f"Deleted cookies for {platform}")
            return True
        
        return False
    
    async def list_cookies(self) -> Dict[str, Dict]:
        """List all saved cookies with their metadata."""
        cookies = {}
        
        for filename in self.storage_path.glob("*.json"):
            platform = filename.stem
            
            try:
                with open(filename) as f:
                    data = json.load(f)
                
                saved_at = data.get("saved_at", "unknown")
                metadata = data.get("metadata", {})
                
                cookies[platform] = {
                    "exists": True,
                    "saved_at": saved_at,
                    "num_cookies": len(data.get("cookies", {})),
                    "metadata": metadata,
                }
            except Exception as e:
                cookies[platform] = {
                    "exists": False,
                    "error": str(e),
                }
        
        return cookies
    
    def _is_expired(self, saved_at: datetime, max_age_hours: int = 48) -> bool:
        """Check if cookies are likely expired."""
        age = datetime.now() - saved_at
        return age > timedelta(hours=max_age_hours)
    
    async def refresh_if_needed(self, platform: str, scraper) -> bool:
        """
        Check if cookies need refresh and trigger re-login if needed.
        
        Args:
            platform: Platform name
            scraper: Scraper instance with login method
            
        Returns:
            True if cookies are valid, False if refresh needed
        """
        cookies = await self.load_cookies(platform)
        
        if cookies is None:
            logger.info(f"No cookies found for {platform}, login required")
            return False
        
        # Try to use cookies
        # If they fail, return False to trigger refresh
        return True
