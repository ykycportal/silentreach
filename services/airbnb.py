"""
Airbnb Scraper for SilentReach
Find property hosts and listings for lead generation
"""

import asyncio
import logging
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class AirbnbHost:
    """Store information about an Airbnb host."""
    
    def __init__(self, host_id: str, name: str = ""):
        self.id = host_id
        self.name = name
        self.listings = []
        self.location = ""
        self.total_reviews = 0
        self.average_rating = 0.0
        self.response_rate = ""
        self.is_superhost = False
        # NEW: Contact information
        self.email = ""
        self.phone = ""
        self.whatsapp = ""
        self.contact_info = {}
        self.uses_gas = False  # NEW: Track gas usage
        self.scraped_at = datetime.now().isoformat()
    
    def add_listing(self, listing: dict):
        self.listings.append(listing)
        self.total_reviews += listing.get("reviews", 0)
        self.average_rating = (
            (self.average_rating + listing.get("rating", 0)) / 2
            if self.average_rating else listing.get("rating", 0)
        )
        
        # Extract contact info from listing
        text = listing.get("text", "")
        self._extract_contact_info(text)
    
    def _extract_contact_info(self, text: str):
        """Extract email and phone from listing text."""
        # Email pattern
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        emails = re.findall(email_pattern, text)
        if emails and not self.email:
            self.email = emails[0]
        
        # Phone patterns (various formats)
        phone_patterns = [
            r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # US
            r'\+?[0-9]{1,3}[-.\s]?[0-9]{4,14}',  # International
            r'whatsapp?:\s*(\+?[0-9\s\-]{7,})',  # WhatsApp explicit
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                phone = phones[0]
                # Clean up
                phone = re.sub(r'[\s\-]', '', phone)
                if len(phone) >= 7 and not self.phone:
                    self.phone = phone
                    # Check if it's WhatsApp
                    if 'whatsapp' in text.lower():
                        self.whatsapp = phone
                    break
        
        # Detect gas usage in listing
        self.uses_gas = self._detect_gas_usage(text)
    
    def _detect_gas_usage(self, text: str) -> bool:
        """Detect if property uses gas cylinders/propane."""
        gas_indicators = [
            'gas bottle', 'gas cylinder', 'gas canister',
            'propane tank', 'lpg', 'cooking gas',
            'gas heater', 'gas stove', 'gas cooktop',
            'kitchen gas', 'refill gas', 'gas refill',
            'butane', 'empty gas', 'run out of gas',
        ]
        electric_only = ['electric only', 'induction only', 'no gas', 'all electric']
        
        text_lower = text.lower()
        
        # Check for gas indicators
        has_gas = any(indicator in text_lower for indicator in gas_indicators)
        
        # Check for electric-only (override)
        has_electric_only = any(indicator in text_lower for indicator in electric_only)
        
        if has_electric_only:
            return False
        
        return has_gas
    
    def to_dict(self) -> dict:
        return {
            "host_id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "whatsapp": self.whatsapp,
            "uses_gas": self.uses_gas,
            "listings_count": len(self.listings),
            "listings": self.listings,
            "location": self.location,
            "total_reviews": self.total_reviews,
            "average_rating": round(self.average_rating, 2),
            "response_rate": self.response_rate,
            "is_superhost": self.is_superhost,
            "contact_info": self.contact_info,
            "scraped_at": self.scraped_at,
        }
    
    def generate_lead_score(self) -> int:
        """Calculate lead score based on activity."""
        score = 0
        
        # More listings = more potential need
        score += len(self.listings) * 10
        
        # Superhost = active host
        if self.is_superhost:
            score += 20
        
        # High reviews = established
        score += min(self.total_reviews // 10, 30)
        
        # High rating = quality host (may invest in property)
        score += int(self.average_rating * 2)
        
        # Gas usage = HIGH PRIORITY (pain point!)
        if self.uses_gas:
            score += 50  # Big bonus - they have a problem we solve!
        
        # Bonus for having contact info (easier to reach)
        if self.email or self.phone:
            score += 10
        
        return min(score, 100)
    
    def generate_proposal_message(self, product: str = "Windmill + Battery System") -> str:
        """Generate personalized outreach message."""
        # Add contact info to message if available
        contact_line = ""
        if self.email:
            contact_line += f"\n📧 Email: {self.email}"
        if self.phone:
            contact_line += f"\n📱 Phone: {self.phone}"
        if self.whatsapp:
            contact_line += f"\n💬 WhatsApp: {self.whatsapp}"
        
        message = f"""Hi {self.name or 'Airbnb Host'}!

I noticed you're an active Airbnb host with {len(self.listings)} property/properties in {self.location or 'your area'}.

I'm reaching out with a solution that could help you:

🌬️ {product}
- Reliable backup power during blackouts
- Keep your guests comfortable 24/7
- No more negative reviews due to power outages
- Eco-friendly and cost-effective

Many hosts in your area are already using this solution to improve guest satisfaction and reduce complaints.

Would you be interested in learning more? I can provide:
- Pricing details
- Installation information
- ROI calculations
- References from other hosts{contact_line}

Best regards,
SilentReach Lead Generator"""
        return message
    
    def generate_email_template(self, product: str = "Windmill + Battery System") -> str:
        """Generate email-specific template."""
        subject = f"Power Solution for Your {self.location or 'Airbnb'} Properties"
        
        body = f"""Dear {self.name or 'Host'},

I hope this email finds you well. My name is [Your Name] and I specialize in renewable energy solutions for short-term rental properties.

I noticed you manage {len(self.listings)} property/properties in {self.location or 'your area'}, and I wanted to introduce you to our windmill + battery system designed specifically for Airbnb hosts.

WHY THIS MATTERS FOR YOUR BUSINESS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Power outages = Bad reviews = Lost bookings
• Our system keeps AC, lights, and essentials running
• Guests never know there was a blackout
• Eco-friendly = Marketing advantage for your listing

WHAT YOU GET:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Reliable backup power (24-48 hours)
✓ Silent operation (no generator noise)
✓ Easy installation (1-2 hours)
✓ Low maintenance costs
✓ ROI in 12-18 months

NEXT STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
I'd love to send you a customized proposal with:
• Pricing for your specific properties
• Installation timeline
• Case studies from other hosts
• Financing options (if available)

Would you be available for a quick 10-minute call this week?

You can reach me at:
📧 {self.email or "[Your Email]"}
📱 {self.phone or "[Your Phone]"}
💬 WhatsApp: {self.whatsapp or "[Your WhatsApp]"}

Looking forward to helping you improve your guests' experience!

Best regards,
[Your Name]
[Your Company]
[Your Contact Info]"""
        
        return f"Subject: {subject}\n\n{body}"
    
    def generate_sms_template(self, product: str = "Windmill + Battery System") -> str:
        """Generate SMS/WhatsApp template."""
        message = f"""Hi {self.name.split()[0] if self.name else 'there'}! 👋

Quick question - do you have power issues at your {self.location or 'Airbnb'} properties?

I help hosts solve blackout problems with windmill + battery systems. No more bad reviews from guests!

Reply for details or call/text: [Your Number]

- SilentReach"""
        return message


class AirbnbScraper:
    """Scrape Airbnb for property hosts and listings."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.proxy = self.config.get("proxy")
        self.hosts: Dict[str, AirbnbHost] = {}
    
    async def search_listings(self, location: str, limit: int = 50) -> List[dict]:
        """Search for Airbnb listings in a location."""
        logger.info(f"Searching Airbnb listings in: {location}")
        
        try:
            # Try to scrape Airbnb directly
            # Note: Airbnb has strong anti-scraping measures
            # This uses a simulated approach for demonstration
            
            listings = await self._search_airbnb_listings(location, limit)
            
            # Also search social media for hosts
            social_hosts = await self._find_hosts_on_social(location)
            
            return listings + social_hosts
            
        except Exception as e:
            logger.error(f"Airbnb search failed: {e}")
            return []
    
    async def _search_airbnb_listings(self, location: str, limit: int) -> List[dict]:
        """Search Airbnb listings (simulated for now)."""
        # In production, this would use browser automation
        # For now, return mock data structure
        
        listings = []
        
        # Common locations to search
        search_terms = [
            f"Airbnb {location}",
            f"Vacation rental {location}",
            f"Short-term rental {location}",
        ]
        
        for term in search_terms[:2]:
            # This would call actual scraper here
            # For now, return empty to avoid errors
            pass
        
        return listings
    
    async def _find_hosts_on_social(self, location: str) -> List[dict]:
        """Find Airbnb hosts on social media platforms."""
        hosts_data = []
        
        # Search Facebook for Airbnb hosts
        try:
            from scrapers.facebook import FacebookScraper
            scraper = FacebookScraper({"proxy": self.proxy})
            
            # Search for groups and pages related to Airbnb in the location
            searches = [
                f"Airbnb host {location}",
                f"Airbnb property {location}",
                f"Vacation rental host {location}",
            ]
            
            for query in searches:
                result = await scraper.search(query, limit=20)
                
                for post in result.get("posts", []):
                    text = post.get("text", "").lower()
                    
                    # Look for host indicators
                    if any(indicator in text for indicator in 
                           ["airbnb host", "vacation rental", "airbnb property", "airbnb listing"]):
                        
                        hosts_data.append({
                            "source": "facebook",
                            "query": query,
                            "author": post.get("author", ""),
                            "text": post.get("text", "")[:300],
                            "type": "host_mention",
                            "location": location,
                        })
                        
        except Exception as e:
            logger.warning(f"Facebook search failed: {e}")
        
        # Search Reddit for Airbnb discussions
        try:
            from scrapers.reddit import RedditScraper
            scraper = RedditScraper()
            
            result = await scraper.search(f"Airbnb {location}", limit=20)
            
            for post in result.get("posts", []):
                text = post.get("title", "") + " " + post.get("text", "").lower()
                
                if any(indicator in text for indicator in 
                       ["airbnb host", "vacation rental", "my airbnb", "airbnb listing"]):
                    
                    hosts_data.append({
                        "source": "reddit",
                        "author": post.get("author", ""),
                        "title": post.get("title", ""),
                        "text": post.get("text", "")[:300],
                        "type": "host_discussion",
                        "location": location,
                    })
                    
        except Exception as e:
            logger.warning(f"Reddit search failed: {e}")
        
        return hosts_data
    
    async def research_host(self, host_identifier: str) -> AirbnbHost:
        """Research a specific Airbnb host."""
        logger.info(f"Researching host: {host_identifier}")
        
        host = AirbnbHost(host_id=host_identifier)
        
        # Search across platforms
        facebook_data = await self._search_facebook_host(host_identifier)
        reddit_data = await self._search_reddit_host(host_identifier)
        
        # Combine data
        all_data = facebook_data + reddit_data
        
        for data in all_data:
            host.add_listing(data)
        
        self.hosts[host_identifier] = host
        return host
    
    async def _search_facebook_host(self, host_name: str) -> List[dict]:
        """Search Facebook for host information."""
        try:
            from scrapers.facebook import FacebookScraper
            scraper = FacebookScraper({"proxy": self.proxy})
            
            result = await scraper.search(host_name, limit=20)
            
            listings = []
            for post in result.get("posts", []):
                if host_name.lower() in post.get("text", "").lower():
                    listings.append({
                        "source": "facebook",
                        "text": post.get("text", ""),
                        "engagement": {
                            "likes": post.get("likes", 0),
                            "comments": post.get("comments", 0),
                        },
                    })
            
            return listings
        except Exception as e:
            logger.warning(f"Facebook host search failed: {e}")
            return []
    
    async def _search_reddit_host(self, host_name: str) -> List[dict]:
        """Search Reddit for host information."""
        try:
            from scrapers.reddit import RedditScraper
            scraper = RedditScraper()
            
            result = await scraper.search(host_name, limit=20)
            
            listings = []
            for post in result.get("posts", []):
                text = post.get("title", "") + " " + post.get("text", "")
                if host_name.lower() in text.lower():
                    listings.append({
                        "source": "reddit",
                        "title": post.get("title", ""),
                        "text": post.get("text", "")[:300],
                        "subreddit": post.get("subreddit", ""),
                    })
            
            return listings
        except Exception as e:
            logger.warning(f"Reddit host search failed: {e}")
            return []
    
    def generate_lead_report(self, location: str = None) -> dict:
        """Generate a lead report for all found hosts."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "location": location or "all",
            "hosts_analyzed": len(self.hosts),
            "leads": [],
        }
        
        for host_id, host in self.hosts.items():
            lead_score = host.generate_lead_score()
            
            # Include contact info in report
            lead = {
                "host": host.to_dict(),
                "lead_score": lead_score,
                "recommended_action": self._get_action(lead_score),
                "suggested_message": host.generate_proposal_message(),
                "email_template": host.generate_email_template() if host.email else None,
                "sms_template": host.generate_sms_template() if host.phone else None,
                "contact_available": bool(host.email or host.phone),
            }
            
            report["leads"].append(lead)
        
        # Sort by lead score
        report["leads"].sort(key=lambda x: x["lead_score"], reverse=True)
        
        return report
    
    def _get_action(self, score: int) -> str:
        """Get recommended action based on lead score."""
        if score >= 50:
            return "HIGH PRIORITY - Contact immediately"
        elif score >= 30:
            return "MEDIUM PRIORITY - Follow up this week"
        else:
            return "LOW PRIORITY - Nurture over time"
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            "# 🏠 Airbnb Lead Intelligence Report",
            f"\n**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            f"**Total Hosts Analyzed:** {len(self.hosts)}",
            "",
            "---",
            "",
        ]
        
        # Summary by gas usage
        gas_hosts = [h for h in self.hosts.values() if h.uses_gas]
        electric_hosts = [h for h in self.hosts.values() if not h.uses_gas]
        
        lines.append("## 📊 Lead Summary")
        lines.append(f"- **Total Hosts:** {len(self.hosts)}")
        lines.append(f"- **🔥 Gas Users (Priority Targets):** {len(gas_hosts)} ← Message them about conversion!")
        lines.append(f"- **⚡ Electric/Solar Users:** {len(electric_hosts)}")
        lines.append("")
        
        for host_id, host in sorted(self.hosts.items(),
                                    key=lambda x: x[1].generate_lead_score(), reverse=True):
            score = host.generate_lead_score()
            action = self._get_action(score)
            
            # Contact info badges
            contact_badges = []
            if host.email:
                contact_badges.append("📧")
            if host.phone:
                contact_badges.append("📱")
            if host.whatsapp:
                contact_badges.append("💬")
            contact_str = " ".join(contact_badges) if contact_badges else "❌"
            
            lines.extend([
                f"## {host.name or host_id}",
                "",
                f"**Lead Score:** {score}/100 {contact_str}",
                f"**Action:** {action}",
                f"**Listings:** {len(host.listings)}",
                f"**Location:** {host.location or 'Unknown'}",
                f"**Rating:** {host.average_rating:.1f} ⭐ ({host.total_reviews} reviews)",
                f"**Superhost:** {'Yes' if host.is_superhost else 'No'}",
                "",
            ])
            
            # Contact section
            if host.email or host.phone:
                lines.extend([
                    "### Contact Information",
                    "",
                ])
                if host.email:
                    lines.append(f"- **📧 Email:** {host.email}")
                if host.phone:
                    lines.append(f"- **📱 Phone:** {host.phone}")
                if host.whatsapp:
                    lines.append(f"- **💬 WhatsApp:** {host.whatsapp}")
                lines.append("")
            
            lines.extend([
                "### Sample Listings",
                "",
            ])
            
            for listing in host.listings[:5]:
                lines.append(f"- {listing.get('text', 'Listing')[:100]}...")
            
            lines.extend(["", "---", ""])
        
        return "\n".join(lines)


class LeadTracker:
    """Track and manage Airbnb leads."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or str(Path.home() / ".silentreach" / "leads"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_lead(self, lead_data: dict, host_id: str):
        """Save a lead to disk."""
        filepath = self.storage_path / f"{self._safe_name(host_id)}.json"
        with open(filepath, "w") as f:
            json.dump(lead_data, f, indent=2, default=str)
        logger.info(f"Saved lead: {host_id}")
    
    def load_lead(self, host_id: str) -> Optional[dict]:
        """Load a saved lead."""
        filepath = self.storage_path / f"{self._safe_name(host_id)}.json"
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        return None
    
    def list_leads(self) -> List[str]:
        """List all saved leads."""
        leads = []
        for filepath in self.storage_path.glob("*.json"):
            leads.append(filepath.stem)
        return leads
    
    @staticmethod
    def _safe_name(name: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower())
