"""
SilentReach CLI - Main entry point for the framework.
Usage: silentreach <command> [options]
"""

import asyncio
import argparse
import logging
import json
import sys
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("silentreach.log")
    ]
)
logger = logging.getLogger("silentreach")


def load_config() -> dict:
    """Load configuration from YAML file."""
    import yaml
    
    config_paths = [
        Path.home() / ".silentreach" / "config.yaml",
        Path(__file__).parent.parent / "config" / "settings.yaml",
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
    
    # Return default config
    return {
        "global": {
            "headless": True,
            "default_delay": 2.0,
            "max_retries": 3,
        },
        "rate_limit": {"enabled": True, "default_rpm": 30},
        "cookies": {"storage_path": str(Path.home() / ".silentreach" / "cookies")},
    }


async def cmd_search(args):
    """Execute a search across platforms."""
    config = load_config()
    
    scrapers = {
        "reddit": "scrapers.reddit.RedditScraper",
        "youtube": "scrapers.youtube.YouTubeScraper",
        "twitter": "scrapers.twitter.TwitterScraper",
        "instagram": "scrapers.instagram.InstagramScraper",
        "linkedin": "scrapers.linkedin.LinkedInScraper",
        "bilibili": "scrapers.bilibili.BilibiliScraper",
    }
    
    results = {}
    
    if args.platform == "all":
        platforms = list(scrapers.keys())
    else:
        platforms = args.platform.split(",")
    
    for platform in platforms:
        platform = platform.strip().lower()
        if platform not in scrapers:
            logger.warning(f"Unknown platform: {platform}")
            continue
        
        logger.info(f"Searching {platform} for: {args.query}")
        
        try:
            module_path, class_name = scrapers[platform].rsplit(".", 1)
            module = __import__(f"{module_path}", fromlist=[class_name])
            ScraperClass = getattr(module, class_name)
            
            scraper = ScraperClass(config)
            result = await scraper.search(args.query, limit=args.limit)
            
            results[platform] = result
            logger.info(f"Found {len(result.get('results', result.get('videos', [])))} items on {platform}")
        except Exception as e:
            logger.error(f"Error on {platform}: {e}")
            results[platform] = {"error": str(e)}
    
    # Output results
    if args.format == "json":
        output = {
            "query": args.query,
            "timestamp": datetime.now().isoformat(),
            "results": results,
        }
        print(json.dumps(output, indent=2))
    else:
        # Markdown format
        print(f"# SilentReach Results: {args.query}\n")
        for platform, data in results.items():
            print(f"## {platform.capitalize()}\n")
            if "error" in data:
                print(f"Error: {data['error']}\n")
            else:
                items = data.get("results", data.get("videos", data.get("tweets", [])))
                for i, item in enumerate(items[:10], 1):
                    if isinstance(item, dict):
                        title = item.get("title", item.get("text", item.get("name", "")))
                        print(f"{i}. {title}")
                    else:
                        print(f"{i}. {item}")
                print()
    
    # Save to file
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            "query": args.query,
            "timestamp": datetime.now().isoformat(),
            "results": results,
        }
        
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")


async def cmd_intel(args):
    """Run full intelligence report on a topic."""
    config = load_config()
    
    logger.info(f"Running intelligence report for: {args.topic}")
    logger.info(f"Depth: {args.depth}")
    
    all_results = {}
    
    # Platform order based on depth
    if args.depth == "quick":
        platforms = ["reddit", "youtube", "bilibili"]
    elif args.depth == "full":
        platforms = ["reddit", "youtube", "twitter", "linkedin", "bilibili"]
    else:
        platforms = list(["reddit", "youtube", "twitter", "instagram", "linkedin", "bilibili"])
    
    for platform in platforms:
        try:
            module_path, class_name = f"scrapers.{platform}.{platform.capitalize()}{platform.capitalize()}Scraper".rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            ScraperClass = getattr(module, class_name)
            
            scraper = ScraperClass(config)
            
            # Different methods for different platforms
            if platform == "twitter":
                result = await scraper.search(args.topic, limit=args.limit)
            elif platform == "instagram":
                result = await scraper.search(args.topic, limit=args.limit)
            else:
                result = await scraper.search(args.topic, limit=args.limit)
            
            all_results[platform] = result
            
            count = len(result.get("results", result.get("videos", result.get("tweets", []))))
            logger.info(f"{platform}: {count} results")
            
        except Exception as e:
            logger.error(f"Failed on {platform}: {e}")
            all_results[platform] = {"error": str(e)}
    
    # Generate report
    report = generate_intel_report(args.topic, all_results)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {output_path}")
    else:
        print(report)


def generate_intel_report(topic: str, results: dict) -> str:
    """Generate a markdown intelligence report."""
    lines = [
        f"# Intelligence Report: {topic}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
    ]
    
    total_items = 0
    for platform, data in results.items():
        if "error" not in data:
            count = len(data.get("results", data.get("videos", data.get("tweets", []))))
            total_items += count
            lines.append(f"- **{platform.capitalize()}**: {count} items")
        else:
            lines.append(f"- **{platform.capitalize()}**: Error - {data.get('error', 'Unknown')}")
    
    lines.extend([
        "",
        f"**Total items collected**: {total_items}",
        "",
        "---",
        "",
    ])
    
    # Detailed findings
    for platform, data in results.items():
        if "error" in data:
            continue
        
        items = data.get("results", data.get("videos", data.get("tweets", [])))
        if not items:
            continue
        
        lines.extend([
            f"## {platform.capitalize()}",
            "",
        ])
        
        for i, item in enumerate(items[:10], 1):
            if isinstance(item, dict):
                title = item.get("title", item.get("text", item.get("name", "")))
                lines.append(f"{i}. **{title}**")
            else:
                lines.append(f"{i}. {item}")
        
        lines.append("")
    
    return "\n".join(lines)


async def cmd_doctor(args):
    """Check system dependencies and configuration."""
    print("\n👁️  SilentReach Doctor\n")
    print("=" * 50)
    
    checks = []
    
    # Check Python version
    import sys
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 9):
        checks.append(("✅ Python", f"{python_version} (OK)", True))
    else:
        checks.append(("❌ Python", f"{python_version} (need 3.9+)", False))
    
    # Check agent-reach
    try:
        import agent_reach
        checks.append(("✅ agent-reach", agent_reach.__version__ if hasattr(agent_reach, '__version__') else "installed", True))
    except ImportError:
        checks.append(("❌ agent-reach", "not installed", False))
    
    # Check nodriver
    try:
        import nodriver
        checks.append(("✅ nodriver", "installed", True))
    except ImportError:
        checks.append(("❌ nodriver", "not installed", False))
    
    # Check yt-dlp
    try:
        import yt_dlp
        checks.append(("✅ yt-dlp", "installed", True))
    except ImportError:
        checks.append(("❌ yt-dlp", "not installed", False))
    
    # Check Chrome/Chromium
    import shutil
    chrome_paths = ["chrome", "chromium", "chromium-browser", "google-chrome"]
    chrome_found = any(shutil.which(p) for p in chrome_paths)
    checks.append(("✅ Chrome/Chromium", "found" if chrome_found else "not found", chrome_found))
    
    # Check config
    config_path = Path.home() / ".silentreach" / "config.yaml"
    if config_path.exists():
        checks.append(("✅ Config", str(config_path), True))
    else:
        checks.append(("⚠️  Config", "not found (using defaults)", True))
    
    # Check cookie storage
    cookie_path = Path.home() / ".silentreach" / "cookies"
    if cookie_path.exists():
        cookies = list(cookie_path.glob("*.json"))
        checks.append(("✅ Cookies", f"{len(cookies)} saved", True))
    else:
        checks.append(("⚠️  Cookies", "no cookies saved", True))
    
    # Print results
    ok_count = sum(1 for _, _, passed in checks if passed)
    total = len(checks)
    
    for name, status, passed in checks:
        icon = "✅" if passed else "❌"
        print(f"{icon} {name}: {status}")
    
    print("\n" + "=" * 50)
    print(f"Status: {ok_count}/{total} checks passed")
    
    if ok_count == total:
        print("✅ All systems operational!")
    else:
        print("⚠️  Some checks failed. Run 'silentreach setup' to configure.")


async def cmd_setup(args):
    """Interactive setup wizard."""
    from pathlib import Path
    
    print("\n🔧 SilentReach Setup Wizard\n")
    print("=" * 50)
    
    # Create directories
    dirs = [
        Path.home() / ".silentreach",
        Path.home() / ".silentreach" / "cookies",
        Path.home() / ".silentreach" / "logs",
        Path.home() / ".silentreach" / "config",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {d}")
    
    # Create config
    config_path = Path.home() / ".silentreach" / "config.yaml"
    if not config_path.exists():
        example_config = Path(__file__).parent.parent / "config" / "settings.example.yaml"
        if example_config.exists():
            import shutil
            shutil.copy(example_config, config_path)
            print(f"✅ Created config at {config_path}")
        else:
            print("⚠️  No example config found")
    else:
        print(f"ℹ️  Config already exists at {config_path}")
    
    # Check and install dependencies
    print("\nChecking dependencies...")
    
    deps = ["agent-reach", "nodriver", "beautifulsoup4", "yt-dlp"]
    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
            print(f"✅ {dep} installed")
        except ImportError:
            print(f"❌ {dep} not found - run: pip install {dep}")
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Run 'silentreach doctor' to verify everything works")
    print("2. For Twitter/Instagram, login first:")
    print("   python scripts/silentreach.py login twitter")
    print("   python scripts/silentreach.py login instagram")
    print("3. Start searching: silentreach search 'your topic'")


async def cmd_login(args):
    """Login to a platform and save cookies."""
    platform = args.platform.lower()
    
    login_methods = {
        "twitter": ("scrapers.twitter.TwitterScraper", "login"),
        "instagram": ("scrapers.instagram.InstagramScraper", "login"),
    }
    
    if platform not in login_methods:
        print(f"❌ Unsupported platform: {platform}")
        print(f"Supported: {', '.join(login_methods.keys())}")
        return
    
    module_path, class_name = login_methods[platform]
    module = __import__(module_path, fromlist=[class_name])
    ScraperClass = getattr(module, class_name)
    
    scraper = ScraperClass()
    
    print(f"\n🔐 Logging into {platform.capitalize()}...")
    print("Note: This will open a browser window for you to log in.\n")
    
    # Get credentials from args or prompt
    username = args.username or input(f"{platform.capitalize()} username: ").strip()
    password = args.password or input("password: ").strip()
    
    success = await scraper.login(username, password)
    
    if success:
        print(f"✅ Login successful! Cookies saved.")
    else:
        print("❌ Login failed. Please try again.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="silentreach",
        description="SilentReach - The ultimate undetected web intelligence framework",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", aliases=["run"], help="Search a topic")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--platform", "-p", default="all", 
                               help="Platform(s) to search (comma-separated or 'all')")
    search_parser.add_argument("--limit", "-l", type=int, default=20,
                               help="Max results per platform")
    search_parser.add_argument("--format", "-f", choices=["json", "markdown"], default="markdown",
                               help="Output format")
    search_parser.add_argument("--output", "-o", help="Save results to file")
    search_parser.set_defaults(func=cmd_search)
    
    # Intel command
    intel_parser = subparsers.add_parser("intel", help="Full intelligence report")
    intel_parser.add_argument("topic", help="Topic to research")
    intel_parser.add_argument("--depth", "-d", choices=["quick", "full"], default="full",
                              help="Research depth")
    intel_parser.add_argument("--limit", "-l", type=int, default=30,
                              help="Max results per platform")
    intel_parser.add_argument("--output", "-o", help="Save report to file")
    intel_parser.set_defaults(func=cmd_intel)
    
    # Doctor command
    doctor_parser = subparsers.add_parser("doctor", help="Check system status")
    doctor_parser.set_defaults(func=cmd_doctor)
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Interactive setup wizard")
    setup_parser.set_defaults(func=cmd_setup)
    
    # Login command
    login_parser = subparsers.add_parser("login", help="Login to a platform")
    login_parser.add_argument("platform", help="Platform to login to (twitter, instagram)")
    login_parser.add_argument("--username", "-u", help="Username")
    login_parser.add_argument("--password", "-P", help="Password")
    login_parser.set_defaults(func=cmd_login)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
