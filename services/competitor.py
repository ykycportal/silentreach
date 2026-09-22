"""
Competitor Intelligence Module for SilentReach
Scrapes competitors by location, product, and supplier relationships
"""

import asyncio
import logging
import json
from typing import Optional, List, Dict, Set
from pathlib import Path
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class CompetitorProfile:
    """Stores extracted competitor information."""
    
    def __init__(self, name: str):
        self.name = name
        self.location: Optional[str] = None
        self.products: List[str] = []
        self.suppliers: List[Dict] = []
        self.social_media: Dict = {}
        self.founders: List[str] = []
        self.mentions: List[Dict] = []
        self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "location": self.location,
            "products": self.products,
            "suppliers": self.suppliers,
            "social_media": self.social_media,
            "founders": self.founders,
            "mentions": len(self.mentions),
            "scraped_at": self.scraped_at,
        }
    
    def add_supplier(self, supplier: str, confidence: float = 0.8):
        self.suppliers.append({
            "name": supplier,
            "confidence": confidence,
            "detected_at": datetime.now().isoformat(),
        })
    
    def add_product(self, product: str):
        if product not in self.products:
            self.products.append(product)
    
    def add_mention(self, source: str, text: str, context: str = ""):
        self.mentions.append({
            "source": source,
            "text": text[:500],
            "context": context,
            "timestamp": datetime.now().isoformat(),
        })


class CompetitorScraper:
    """Scrape competitor information from multiple sources."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.proxy = self.config.get("proxy")
        self.results: Dict[str, CompetitorProfile] = {}
    
    async def search_competitor(self, name: str, focus: str = "auto") -> CompetitorProfile:
        """Search for a competitor across all platforms."""
        logger.info(f"Searching competitor: {name}")
        
        profile = CompetitorProfile(name)
        
        # Scrape Facebook
        facebook_data = await self._scrape_facebook(name)
        self._extract_facebook_info(profile, facebook_data)
        
        # Scrape LinkedIn
        linkedin_data = await self._scrape_linkedin(name)
        self._extract_linkedin_info(profile, linkedin_data)
        
        # Scrape Reddit
        reddit_data = await self._scrape_reddit(name)
        self._extract_reddit_info(profile, reddit_data)
        
        # Scrape Twitter
        twitter_data = await self._scrape_twitter(name)
        self._extract_twitter_info(profile, twitter_data)
        
        self.results[name] = profile
        return profile
    
    async def _scrape_facebook(self, name: str) -> dict:
        """Scrape Facebook for competitor mentions."""
        try:
            from scrapers.facebook import FacebookScraper
            scraper = FacebookScraper({"proxy": self.proxy})
            
            # Search by name
            search_result = await scraper.search(name, limit=20)
            
            # Try to scrape official page
            page_result = await scraper.scrape_page(name, limit=20)
            
            return {
                "search": search_result,
                "page": page_result,
            }
        except Exception as e:
            logger.warning(f"Facebook scrape failed for {name}: {e}")
            return {}
    
    async def _scrape_linkedin(self, name: str) -> dict:
        """Scrape LinkedIn for competitor company info."""
        try:
            from scrapers.linkedin import LinkedInScraper
            scraper = LinkedInScraper()
            
            result = await scraper.search_public(name, limit=10)
            return result
        except Exception as e:
            logger.warning(f"LinkedIn scrape failed for {name}: {e}")
            return {}
    
    async def _scrape_reddit(self, name: str) -> dict:
        """Scrape Reddit for competitor discussions."""
        try:
            from scrapers.reddit import RedditScraper
            scraper = RedditScraper()
            
            result = await scraper.search(name, limit=20)
            return result
        except Exception as e:
            logger.warning(f"Reddit scrape failed for {name}: {e}")
            return {}
    
    async def _scrape_twitter(self, name: str) -> dict:
        """Scrape Twitter for competitor mentions."""
        try:
            from scrapers.twitter import TwitterScraper
            scraper = TwitterScraper()
            
            result = await scraper.search(name, limit=30)
            return result
        except Exception as e:
            logger.warning(f"Twitter scrape failed for {name}: {e}")
            return {}
    
    def _extract_facebook_info(self, profile: CompetitorProfile, data: dict):
        """Extract info from Facebook data."""
        # Check for official page
        if "page" in data and data["page"].get("posts"):
            profile.social_media["facebook"] = {
                "type": "page",
                "posts_scraped": len(data["page"]["posts"]),
                "url": f"https://facebook.com/{profile.name}",
            }
        
        # Look for supplier mentions
        for post in data.get("search", {}).get("posts", []):
            text = post.get("text", "").lower()
            
            # Supplier detection patterns
            supplier_patterns = [
                r'supplied\s+by\s+([^\.,\n]+)',
                r'manufactured\s+by\s+([^\.,\n]+)',
                r'made\s+by\s+([^\.,\n]+)',
                r'partner\s+with\s+([^\.,\n]+)',
                r'distributor\s+([^\.,\n]+)',
                r'sourced\s+from\s+([^\.,\n]+)',
                r'supplier:\s*([^\.,\n]+)',
            ]
            
            for pattern in supplier_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    supplier = match.group(1).strip()
                    if supplier and len(supplier) > 2:
                        profile.add_supplier(supplier, confidence=0.7)
            
            # Location detection
            location_patterns = [
                r'based\s+in\s+([^\.,\n]+)',
                r'located\s+in\s+([^\.,\n]+)',
                r'headquartered\s+in\s+([^\.,\n]+)',
                r'\sin\s+(United\s+States|California|New\s+York|London|China|Vietnam|Thailand)',
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and not profile.location:
                    profile.location = match.group(1).strip()
                    break
            
            # Product mentions
            if any(word in text for word in ["new product", "launching", "selling", "offering"]):
                # Extract product names from context
                products = re.findall(r'(?:product|item|thing)\s+[:\s]+([^\.,\n]{5,50})', text)
                for prod in products:
                    profile.add_product(prod.strip())
    
    def _extract_linkedin_info(self, profile: CompetitorProfile, data: dict):
        """Extract info from LinkedIn data."""
        if not data or "error" in data:
            return
        
        # Company info
        for post in data.get("results", [])[:5]:
            text = post.get("text", "")
            
            # Industry detection
            if "industry" in post:
                profile.add_mention("linkedin", f"Industry: {post['industry']}", "company_profile")
            
            # Employee count (size indicator)
            if "employees" in post:
                profile.add_mention("linkedin", f"Employees: {post['employees']}", "company_size")
    
    def _extract_reddit_info(self, profile: CompetitorProfile, data: dict):
        """Extract info from Reddit data."""
        if not data or "error" in data:
            return
        
        for post in data.get("posts", [])[:20]:
            title = post.get("title", "")
            text = post.get("text", "")
            full_text = f"{title} {text}".lower()
            
            # Supplier mentions in discussions
            supplier_patterns = [
                r'sold\s+by\s+([^\.,\n]+)',
                r'bought\s+from\s+([^\.,\n]+)',
                r'wholesale\s+from\s+([^\.,\n]+)',
                r'supplier\s+([^\.,\n]+)',
                r'sourcing\s+from\s+([^\.,\n]+)',
            ]
            
            for pattern in supplier_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    supplier = match.group(1).strip()
                    if supplier and len(supplier) > 2:
                        profile.add_supplier(supplier, confidence=0.6)
            
            # Add mention for context
            if "review" in full_text or "experience" in full_text:
                profile.add_mention("reddit", f"r/{post.get('subreddit', '')}: {title[:100]}", "user_discussion")
    
    def _extract_twitter_info(self, profile: CompetitorProfile, data: dict):
        """Extract info from Twitter data."""
        if not data or "error" in data:
            return
        
        for tweet in data.get("tweets", [])[:10]:
            text = tweet.get("text", "").lower()
            
            # Location from bio
            if "location" in text or "based" in text:
                loc_match = re.search(r'located?\s+in\s+([^\.,\n]+)', text)
                if loc_match and not profile.location:
                    profile.location = loc_match.group(1).strip()
    
    def get_supplier_network(self, min_confidence: float = 0.5) -> Dict[str, List[str]]:
        """Get all detected suppliers and which competitors use them."""
        supplier_map: Dict[str, List[str]] = {}
        
        for name, profile in self.results.items():
            for supplier_info in profile.suppliers:
                if supplier_info["confidence"] >= min_confidence:
                    supplier = supplier_info["name"]
                    if supplier not in supplier_map:
                        supplier_map[supplier] = []
                    supplier_map[supplier].append(name)
        
        return supplier_map
    
    def generate_report(self, format: str = "json") -> dict:
        """Generate competitor intelligence report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "competitors": len(self.results),
            "profiles": {name: p.to_dict() for name, p in self.results.items()},
            "supplier_network": self.get_supplier_network(),
        }
        return report


class CompetitorTracker:
    """Track competitors over time."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or str(Path.home() / ".silentreach" / "competitors"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_competitor(self, profile: CompetitorProfile):
        """Save competitor profile to disk."""
        filepath = self.storage_path / f"{self._safe_name(profile.name)}.json"
        with open(filepath, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)
        logger.info(f"Saved competitor: {profile.name}")
    
    def load_competitor(self, name: str) -> Optional[CompetitorProfile]:
        """Load saved competitor profile."""
        filepath = self.storage_path / f"{self._safe_name(name)}.json"
        if filepath.exists():
            with open(filepath) as f:
                data = json.load(f)
            profile = CompetitorProfile(data["name"])
            profile.__dict__.update(data)
            return profile
        return None
    
    def list_competitors(self) -> List[str]:
        """List all tracked competitors."""
        competitors = []
        for filepath in self.storage_path.glob("*.json"):
            competitors.append(filepath.stem)
        return competitors
    
    @staticmethod
    def _safe_name(name: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower())
