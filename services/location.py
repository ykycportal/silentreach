"""
Location Intelligence Module for SilentReach
Scrapes Facebook for activity in a specific geographic area
"""

import asyncio
import logging
from typing import Optional, List, Dict, Set
from pathlib import Path
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class LocationProfile:
    """Stores location intelligence data."""
    
    def __init__(self, location_name: str):
        self.name = location_name
        self.posts = []
        self.pages = []
        self.groups = []
        self.businesses = []
        self.events = []
        self.total_mentions = 0
        self.active_users: Set[str] = set()
        self.scraped_at = datetime.now().isoformat()
    
    def add_post(self, post: dict):
        self.posts.append(post)
        self.total_mentions += 1
        author = post.get("author", "")
        if author:
            self.active_users.add(author)
    
    def add_page(self, page: dict):
        self.pages.append(page)
    
    def add_group(self, group: dict):
        self.groups.append(group)
    
    def add_business(self, business: dict):
        self.businesses.append(business)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "scraped_at": self.scraped_at,
            "total_mentions": self.total_mentions,
            "unique_authors": len(self.active_users),
            "posts_count": len(self.posts),
            "pages_count": len(self.pages),
            "groups_count": len(self.groups),
            "businesses_count": len(self.businesses),
            "top_authors": list(self.active_users)[:20],
            "sample_posts": self.posts[:10],
        }


class LocationScraper:
    """Scrape Facebook for activity in a specific location."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.proxy = self.config.get("proxy")
        self.results: Dict[str, LocationProfile] = {}
    
    async def research_location(self, location: str, limit: int = 50) -> LocationProfile:
        """Research activity in a specific location."""
        logger.info(f"Researching location: {location}")
        
        profile = LocationProfile(location)
        
        # Search for posts mentioning the location
        posts = await self._search_posts(location, limit=limit)
        for post in posts:
            profile.add_post(post)
        
        # Search for local pages
        pages = await self._search_pages(location, limit=20)
        for page in pages:
            profile.add_page(page)
        
        # Search for local groups
        groups = await self._search_groups(location, limit=20)
        for group in groups:
            profile.add_group(group)
        
        # Search for local businesses
        businesses = await self._search_businesses(location, limit=20)
        for business in businesses:
            profile.add_business(business)
        
        self.results[location] = profile
        return profile
    
    async def _search_posts(self, location: str, limit: int = 50) -> List[dict]:
        """Search Facebook posts mentioning the location."""
        try:
            from scrapers.facebook import FacebookScraper
            scraper = FacebookScraper({"proxy": self.proxy})
            
            result = await scraper.search(location, limit=limit)
            
            posts = []
            for post in result.get("posts", [])[:limit]:
                text = post.get("text", "").lower()
                
                # Check for location indicators
                location_indicators = [
                    f"in {location.lower()}",
                    f"{location.lower()}",
                    "ambergris caye",
                    "amaici",  # Local name
                    "belize",
                    " Caye ",
                ]
                
                has_location = any(indicator in text for indicator in location_indicators)
                
                if has_location or True:  # Include all posts for now
                    posts.append({
                        "text": post.get("text", "")[:500],
                        "author": post.get("author", ""),
                        "timestamp": post.get("timestamp", ""),
                        "likes": post.get("likes", 0),
                        "comments": post.get("comments", 0),
                        "type": "post",
                    })
            
            return posts
        except Exception as e:
            logger.warning(f"Post search failed for {location}: {e}")
            return []
    
    async def _search_pages(self, location: str, limit: int = 20) -> List[dict]:
        """Search for Facebook pages in the location."""
        try:
            from scrapers.facebook import FacebookScraper
            scraper = FacebookScraper({"proxy": self.proxy})
            
            # Try different search terms
            search_terms = [
                f"{location} Belize",
                f"Ambergris Caye",
                f"Amaici",
                f"{location} business",
                f"{location} tourism",
            ]
            
            pages = []
            for term in search_terms[:3]:  # Limit searches
                result = await scraper.search(f"page {term}", limit=limit)
                for post in result.get("posts", []):
                    if "page" in post.get("text", "").lower():
                        pages.append({
                            "name": post.get("author", ""),
                            "type": "page",
                            "source": term,
                        })
            
            # Deduplicate
            seen = set()
            unique_pages = []
            for p in pages:
                if p["name"] not in seen:
                    seen.add(p["name"])
                    unique_pages.append(p)
            
            return unique_pages[:limit]
        except Exception as e:
            logger.warning(f"Page search failed for {location}: {e}")
            return []
    
    async def _search_groups(self, location: str, limit: int = 20) -> List[dict]:
        """Search for Facebook groups in the location."""
        try:
            from scrapers.facebook import FacebookScraper
            scraper = FacebookScraper({"proxy": self.proxy})
            
            groups = []
            search_terms = [
                f"group {location}",
                f"group Ambergris Caye",
                f"group amaici",
            ]
            
            for term in search_terms:
                result = await scraper.search(term, limit=limit)
                for post in result.get("posts", []):
                    if "group" in post.get("text", "").lower():
                        groups.append({
                            "name": post.get("author", ""),
                            "type": "group",
                            "source": term,
                        })
            
            return groups[:limit]
        except Exception as e:
            logger.warning(f"Group search failed for {location}: {e}")
            return []
    
    async def _search_businesses(self, location: str, limit: int = 20) -> List[dict]:
        """Search for local businesses."""
        try:
            from scrapers.facebook import FacebookScraper
            scraper = FacebookScraper({"proxy": self.proxy})
            
            businesses = []
            search_terms = [
                f"restaurant {location}",
                f"hotel {location}",
                f"tour {location}",
                f"shop {location}",
                f"bar {location}",
            ]
            
            for term in search_terms:
                result = await scraper.search(term, limit=limit)
                for post in result.get("posts", []):
                    text = post.get("text", "").lower()
                    if any(word in text for word in ["open", "hours", "menu", "book", "visit"]):
                        businesses.append({
                            "name": post.get("author", ""),
                            "type": "business",
                            "source": term,
                            "text": post.get("text", "")[:200],
                        })
            
            return businesses[:limit]
        except Exception as e:
            logger.warning(f"Business search failed for {location}: {e}")
            return []
    
    def generate_report(self, format: str = "json") -> dict:
        """Generate location intelligence report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "locations": {name: p.to_dict() for name, p in self.results.items()},
        }
        return report
    
    def to_markdown(self, location: str = None) -> str:
        """Generate human-readable report."""
        if location and location in self.results:
            profiles = {location: self.results[location]}
        else:
            profiles = self.results
        
        lines = [
            "# 📍 Location Intelligence Report",
            f"\n**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            "",
            "---",
            "",
        ]
        
        for loc_name, profile in profiles.items():
            lines.extend([
                f"## {profile.name}",
                "",
                f"**Scraped:** {profile.scraped_at[:19]}",
                f"**Total Post Mentions:** {profile.total_mentions}",
                f"**Unique Authors:** {len(profile.active_users)}",
                f"**Facebook Pages Found:** {len(profile.pages)}",
                f"**Facebook Groups Found:** {len(profile.groups)}",
                f"**Local Businesses:** {len(profile.businesses)}",
                "",
                "### Sample Posts",
                "",
            ])
            
            for post in profile.posts[:10]:
                lines.append(f"- **{post.get('author', 'Unknown')}**: {post.get('text', '')[:100]}...")
                lines.append(f"  👍 {post.get('likes', 0)} | 💬 {post.get('comments', 0)}")
            
            lines.extend(["", "### Top Authors", ""])
            for author in list(profile.active_users)[:10]:
                lines.append(f"- {author}")
            
            lines.extend(["", "---", ""])
        
        return "\n".join(lines)


class LocationTracker:
    """Track location intelligence over time."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or str(Path.home() / ".silentreach" / "locations"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_location(self, profile: LocationProfile):
        """Save location profile to disk."""
        filepath = self.storage_path / f"{self._safe_name(profile.name)}.json"
        with open(filepath, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)
        logger.info(f"Saved location: {profile.name}")
    
    def load_location(self, name: str) -> Optional[LocationProfile]:
        """Load saved location profile."""
        filepath = self.storage_path / f"{self._safe_name(name)}.json"
        if filepath.exists():
            with open(filepath) as f:
                data = json.load(f)
            profile = LocationProfile(data["name"])
            profile.__dict__.update(data)
            return profile
        return None
    
    def list_locations(self) -> List[str]:
        """List all tracked locations."""
        locations = []
        for filepath in self.storage_path.glob("*.json"):
            locations.append(filepath.stem)
        return locations
    
    @staticmethod
    def _safe_name(name: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower())
