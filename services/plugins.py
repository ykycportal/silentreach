#!/usr/bin/env python3
"""
Plugin system for SilentReach
Auto-discover and load custom scrapers
"""

import importlib
import logging
from typing import Optional, Dict, List, Type
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("silentreach.plugins")


class PluginRegistry:
    """Register and manage SilentReach plugins."""
    
    def __init__(self, plugin_dirs: Optional[List[Path]] = None):
        self.plugin_dirs = plugin_dirs or [
            Path.home() / ".silentreach" / "plugins",
            Path(__file__).parent.parent / "plugins",
        ]
        self._plugins: Dict[str, Type] = {}
        self._loaded = False
    
    def discover_plugins(self):
        """Auto-discover plugins in plugin directories."""
        if self._loaded:
            return
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
            
            for plugin_file in plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue
                
                plugin_name = plugin_file.stem
                try:
                    module = importlib.import_module(f"plugins.{plugin_name}")
                    
                    # Look for scraper classes
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        if (
                            isinstance(attr, type)
                            and hasattr(attr, 'platform')
                            and hasattr(attr, 'search')
                        ):
                            self.register(attr, plugin_name)
                            logger.info(f"Loaded plugin: {plugin_name} ({attr.platform})")
                    
                except Exception as e:
                    logger.warning(f"Failed to load plugin {plugin_name}: {e}")
        
        self._loaded = True
    
    def register(self, scraper_class: Type, plugin_name: str):
        """Register a scraper class as a plugin."""
        platform = getattr(scraper_class, 'platform', plugin_name)
        self._plugins[platform] = scraper_class
    
    def get_plugin(self, platform: str) -> Optional[Type]:
        """Get a registered plugin by platform name."""
        self.discover_plugins()
        return self._plugins.get(platform)
    
    def list_plugins(self) -> List[Dict]:
        """List all registered plugins."""
        self.discover_plugins()
        
        plugins = []
        for platform, scraper_class in self._plugins.items():
            plugins.append({
                "platform": platform,
                "class": scraper_class.__name__,
                "module": scraper_class.__module__,
                "description": getattr(scraper_class, '__doc__', ''),
            })
        
        return plugins
    
    def create_plugin_template(self, platform_name: str, output_dir: Optional[Path] = None) -> Path:
        """Generate a plugin template for a new platform."""
        output_dir = output_dir or Path.home() / ".silentreach" / "plugins"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        plugin_file = output_dir / f"{platform_name}.py"
        
        template = f'''"""
{platform_name.capitalize()} Scraper Plugin for SilentReach
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class {platform_name.capitalize()}Scraper:
    """{platform_name.capitalize()} scraper implementation."""
    
    platform = "{platform_name}"
    stealth_level = "medium"
    auth_required = False
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {{}}
    
    async def search(self, query: str, limit: int = 20, **kwargs) -> dict:
        """Search {platform_name} for content."""
        # Implement your scraping logic here
        results = []
        
        # Example: Make API call or web request
        # response = await self._fetch_data(query)
        # results = self._parse_response(response)
        
        return {{
            "query": query,
            "results": results,
            "total": len(results),
        }}
    
    async def get_item(self, item_id: str, **kwargs) -> dict:
        """Get specific item details."""
        # Implement item detail retrieval
        pass
    
    async def get_profile(self, username: str, **kwargs) -> dict:
        """Get user profile."""
        # Implement profile retrieval
        pass
    
    async def _fetch_data(self, query: str) -> any:
        """Fetch data from {platform_name}."""
        # Your implementation here
        pass
    
    def _parse_response(self, response: any) -> list:
        """Parse API/response data into structured results."""
        # Your parsing logic here
        pass
'''
        
        with open(plugin_file, "w") as f:
            f.write(template)
        
        logger.info(f"Created plugin template: {plugin_file}")
        return plugin_file


class PluginManager:
    """High-level plugin management."""
    
    def __init__(self):
        self.registry = PluginRegistry()
    
    def load_all(self):
        """Load all available plugins."""
        self.registry.discover_plugins()
    
    def get_available_platforms(self) -> List[str]:
        """Get list of all available platforms (built-in + plugins)."""
        self.load_all()
        
        # Built-in platforms
        builtins = ["reddit", "youtube", "twitter", "instagram", "linkedin", 
                    "facebook", "bilibili", "v2ex", "rss", "xiaohongshu"]
        
        # Plugin platforms
        plugins = [p["platform"] for p in self.registry.list_plugins()]
        
        return list(set(builtins + plugins))
    
    def create_new_plugin(self, platform_name: str) -> Path:
        """Create a new plugin template."""
        return self.registry.create_plugin_template(platform_name)
    
    def get_scraper(self, platform: str):
        """Get scraper class for platform (built-in or plugin)."""
        # Try built-in first
        builtins = {
            "reddit": "scrapers.reddit.RedditScraper",
            "youtube": "scrapers.youtube.YouTubeScraper",
            "twitter": "scrapers.twitter.TwitterScraper",
            "instagram": "scrapers.instagram.InstagramScraper",
            "linkedin": "scrapers.linkedin.LinkedInScraper",
            "facebook": "scrapers.facebook.FacebookScraper",
            "bilibili": "scrapers.bilibili.BilibiliScraper",
            "v2ex": "scrapers.v2ex.V2EXScraper",
            "rss": "scrapers.rss.RSSScraper",
            "xiaohongshu": "scrapers.xiaohongshu.XiaohongshuScraper",
        }
        
        if platform in builtins:
            module_path, class_name = builtins[platform].rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        
        # Try plugin
        self.registry.discover_plugins()
        scraper_class = self.registry.get_plugin(platform)
        if scraper_class:
            return scraper_class
        
        return None


# Global plugin manager instance
_plugin_manager = None


def get_plugin_manager() -> PluginManager:
    """Get or create global plugin manager."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def discover_plugins():
    """Discover and load all plugins."""
    get_plugin_manager().load_all()


def list_plugins() -> List[Dict]:
    """List all available plugins."""
    return get_plugin_manager().registry.list_plugins()


def create_plugin(platform_name: str) -> Path:
    """Create a new plugin template."""
    return get_plugin_manager().create_new_plugin(platform_name)


if __name__ == "__main__":
    # Test plugin system
    print("=== SilentReach Plugin System Test ===\n")
    
    manager = PluginManager()
    
    # List available platforms
    platforms = manager.get_available_platforms()
    print(f"Available platforms ({len(platforms)}):")
    for p in sorted(platforms):
        print(f"  - {p}")
    
    # Create a new plugin
    print("\nCreating new plugin template...")
    template_path = manager.create_new_plugin("my_custom_platform")
    print(f"Created: {template_path}")
    
    # List all plugins
    print("\nAll plugins:")
    for plugin in list_plugins():
        print(f"  - {plugin['platform']}: {plugin['class']}")
