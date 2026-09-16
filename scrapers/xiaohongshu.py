"""
Xiaohongshu (Little Red Book) Scraper for SilentReach
Chinese social media platform.
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class XiaohongshuScraper:
    """Xiaohongshu scraper using nodriver."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.cookie_path = Path.home() / ".silentreach" / "cookies" / "xiaohongshu.json"
    
    async def search(self, query: str, limit: int = 20) -> dict:
        """Search Xiaohongshu posts."""
        import nodriver as uc
        
        browser = await uc.start(headless=False)
        
        if self.cookie_path.exists():
            try:
                browser = await browser.load_cookies(self.cookie_path)
            except:
                pass
        
        try:
            # Xiaohongshu search URL
            encoded_query = query.replace(" ", "%20")
            page = await browser.get(f"https://www.xiaohongshu.com/search_result?keyword={encoded_query}")
            await asyncio.sleep(5)
            
            content = await page.get_content()
            notes = self._parse_notes(content, query)
            
            return {
                "query": query,
                "notes": notes[:limit],
                "total": len(notes),
            }
        except Exception as e:
            logger.error(f"Xiaohongshu search failed: {e}")
            return {"query": query, "notes": [], "error": str(e)}
        finally:
            await browser.stop()
    
    async def get_note(self, note_id: str) -> dict:
        """Get a specific Xiaohongshu note."""
        import nodriver as uc
        
        browser = await uc.start(headless=False)
        
        if self.cookie_path.exists():
            try:
                browser = await browser.load_cookies(self.cookie_path)
            except:
                pass
        
        try:
            page = await browser.get(f"https://www.xiaohongshu.com/explore/{note_id}")
            await asyncio.sleep(3)
            
            content = await page.get_content()
            note = self._parse_note_detail(content, note_id)
            
            return note
        except Exception as e:
            return {"note_id": note_id, "error": str(e)}
        finally:
            await browser.stop()
    
    def _parse_notes(self, content: str, query: str) -> list:
        """Parse Xiaohongshu search results."""
        from bs4 import BeautifulSoup
        
        notes = []
        soup = BeautifulSoup(content, "html.parser")
        
        # Note cards
        note_cards = soup.select("[class*='note-card'], .note-item")
        
        for card in note_cards[:30]:
            # Title
            title = card.select_one("h3, .title, [class*='title']")
            title_text = title.get_text(strip=True) if title else ""
            
            # Author
            author = card.select_one("a[class*='user'], [class*='author']")
            author_name = author.get_text(strip=True) if author else ""
            
            # Image
            img = card.select_one("img")
            image_url = img.get("src", "") if img else ""
            
            if title_text:
                notes.append({
                    "title": title_text,
                    "author": author_name,
                    "image": image_url,
                    "query": query,
                })
        
        return notes
    
    def _parse_note_detail(self, content: str, note_id: str) -> dict:
        """Parse individual note detail."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(content, "html.parser")
        
        # Note content
        content_elem = soup.select_one("[class*='content'], .note-content")
        note_content = content_elem.get_text(strip=True) if content_elem else ""
        
        # Title
        title_elem = soup.select_one("h1, [class*='title']")
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Stats
        likes = soup.select_one("[class*='like']")
        likes_text = likes.get_text() if likes else "0"
        
        return {
            "note_id": note_id,
            "title": title,
            "content": note_content[:1000],
            "likes": likes_text,
        }
