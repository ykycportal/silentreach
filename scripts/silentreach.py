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
_log_dir = Path.home() / ".silentreach"
_log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(_log_dir / "silentreach.log"))
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
    return asyncio.run(_cmd_search_impl(args))


async def _cmd_search_impl(args):
    """Implementation of search command."""
    config = load_config()
    
    # Import scrapers dynamically
    scrapers = {
        "reddit": ("scrapers.reddit", "RedditScraper"),
        "youtube": ("scrapers.youtube", "YouTubeScraper"),
        "twitter": ("scrapers.twitter", "TwitterScraper"),
        "instagram": ("scrapers.instagram", "InstagramScraper"),
        "linkedin": ("scrapers.linkedin", "LinkedInScraper"),
        "facebook": ("scrapers.facebook", "FacebookScraper"),
        "bilibili": ("scrapers.bilibili", "BilibiliScraper"),
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
            module_name, class_name = scrapers[platform]
            module = __import__(module_name, fromlist=[class_name])
            ScraperClass = getattr(module, class_name)
            
            scraper = ScraperClass(config)
            
            # Call search with correct signature
            if hasattr(scraper, 'search'):
                result = await scraper.search(args.query, limit=args.limit)
            else:
                result = {"error": f"{platform} scraper has no search method"}
            
            results[platform] = result
            count = len(result.get("posts", result.get("videos", result.get("tweets", []))))
            logger.info(f"Found {count} items on {platform}")
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
    elif args.format == "csv":
        from services.output_fmt import OutputFormatter
        print(OutputFormatter.to_csv(results))
    elif args.format == "pdf":
        from services.output_fmt import OutputFormatter
        pdf_bytes = OutputFormatter.to_pdf(results, title=f"SilentReach: {args.query}")
        if pdf_bytes:
            output_path = Path(args.output) if args.output else None
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                print(f"[✓] PDF saved to: {output_path}")
            else:
                # Print first page preview
                print("[PDF generated - use -o flag to save]")
        else:
            print("[!] PDF generation failed (install reportlab)")
    elif args.format == "xlsx":
        from services.output_fmt import OutputFormatter
        xlsx_bytes = OutputFormatter.to_excel(results, title=f"SilentReach: {args.query}")
        if xlsx_bytes:
            output_path = Path(args.output) if args.output else None
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(xlsx_bytes)
                print(f"[✓] Excel saved to: {output_path}")
            else:
                print("[Excel generated - use -o flag to save]")
        else:
            print("[!] Excel generation failed (install openpyxl)")
    elif args.format == "ods":
        from services.output_fmt import OutputFormatter
        ods_bytes = OutputFormatter.to_odf(results, title=f"SilentReach: {args.query}")
        if ods_bytes:
            output_path = Path(args.output) if args.output else None
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(ods_bytes)
                print(f"[✓] ODS saved to: {output_path}")
            else:
                print("[ODS generated - use -o flag to save]")
        else:
            print("[!] ODS generation failed (install odfpy)")
    else:
        # Markdown format
        print(f"# SilentReach Results: {args.query}\n")
        print(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}")
        print(f"**Platforms:** {', '.join(results.keys())}\n")
        print("---\n")
        
        for platform, data in results.items():
            print(f"## {platform.capitalize()}\n")
            if "error" in data:
                print(f"*Error: {data['error']}*\n")
            else:
                items = data.get("results", data.get("videos", data.get("tweets", [])))
                if items:
                    print(f"**Found {len(items)} results:**\n")
                    for i, item in enumerate(items[:10], 1):
                        if isinstance(item, dict):
                            title = item.get("title", item.get("text", item.get("name", "")))
                            author = item.get("author", "")
                            date = item.get("created_at", item.get("timestamp", ""))
                            print(f"{i}. **{title[:80]}**")
                            if author:
                                print(f"   By: {author}")
                            if date:
                                print(f"   Date: {date[:10]}")
                            print()
                else:
                    print("*No results found*\n")
    
    # Save to file
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine format from extension or argument
        fmt = args.format if args.format != 'md' else output_path.suffix.lstrip('.')
        if fmt == '':
            fmt = 'md'

        # Format data for output
        output_data = {
            "query": args.query,
            "timestamp": datetime.now().isoformat(),
            "results": results,
        }

        # Use OutputFormatter for all formats
        from services.output_fmt import OutputFormatter
        OutputFormatter.save_to_file(output_data, str(output_path), fmt)

        logger.info(f"Results saved to {output_path}")


async def cmd_intel(args):
    """Run full intelligence report on a topic."""
    config = load_config()
    
    logger.info(f"Running intelligence report for: {args.topic}")
    logger.info(f"Depth: {args.depth}")
    
    all_results = {}
    
    # Platform order based on depth
    if args.depth == "quick":
        platforms = ["reddit", "youtube", "bilibili", "facebook"]
    elif args.depth == "full":
        platforms = ["reddit", "youtube", "twitter", "linkedin", "bilibili", "facebook"]
    else:
        platforms = list(["reddit", "youtube", "twitter", "instagram", "linkedin", "bilibili"])
    
    for platform in platforms:
        try:
            # Scrapers live at scrapers.XXX, not scrapers.XXX.XXXScraper
            module = __import__(f"scrapers.{platform}", fromlist=["Scraper"])
            class_name = f"{platform.capitalize()}Scraper"
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
    
    # Also show summary
    print(report)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Auto-detect format from extension
        fmt = output_path.suffix.lstrip('.')
        if fmt in ['pdf']:
            from services.output_fmt import OutputFormatter
            pdf_bytes = OutputFormatter.to_pdf(all_results, title=f"Intelligence Report: {args.topic}")
            if pdf_bytes:
                with open(output_path, "wb") as f:
                    f.write(pdf_bytes)
                print(f"\n💾 PDF saved to: {output_path}")
        else:
            with open(output_path, "w") as f:
                f.write(report)
            print(f"\n💾 Report saved to: {output_path}")
    else:
        print(f"\n💡 Use -o flag to save report to file")


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

    scraper = ScraperClass(config=load_config())
    
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
        description="SilentReach - Ultimate undetected web intelligence framework, platform-agnostic combining agent-reach + nodriver for social media with extra skillsets for excellent results. Published in different formats.",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", aliases=["run"], help="Search a topic")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--platform", "-p", default="all", 
                               help="Platform(s) to search (comma-separated or 'all')")
    search_parser.add_argument("--limit", "-l", type=int, default=20,
                               help="Max results per platform")
    search_parser.add_argument("--format", "-f", choices=["json", "md", "csv", "txt", "pdf", "xlsx", "ods"], default="md",
                               help="Output format (default: markdown)")
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
    
    # Schedule command
    schedule_parser = subparsers.add_parser("schedule", help="Manage scheduled jobs")
    schedule_sub = schedule_parser.add_subparsers(dest="schedule_action")
    
    # List jobs
    list_parser = schedule_sub.add_parser("list", help="List scheduled jobs")
    list_parser.set_defaults(func=cmd_schedule_list)
    
    # Add job
    add_parser = schedule_sub.add_parser("add", help="Add a scheduled job")
    add_parser.add_argument("name", help="Job name")
    add_parser.add_argument("cron", help="Cron expression (e.g., '0 8 * * *')")
    add_parser.add_argument("--command", "-c", required=True, help="Command to run")
    add_parser.add_argument("--description", "-d", help="Job description")
    add_parser.set_defaults(func=cmd_schedule_add)
    
    # Remove job
    remove_parser = schedule_sub.add_parser("remove", help="Remove a scheduled job")
    remove_parser.add_argument("name", help="Job name to remove")
    remove_parser.set_defaults(func=cmd_schedule_remove)
    
    # Run now
    run_parser = schedule_sub.add_parser("run", help="Run a job immediately")
    run_parser.add_argument("name", help="Job name to run")
    run_parser.set_defaults(func=cmd_schedule_run)
    
    # Notify command
    notify_parser = subparsers.add_parser("notify", help="Send test notification")
    notify_parser.add_argument("message", nargs="?", default="SilentReach is working!", help="Notification message")
    notify_parser.add_argument("--platform", "-p", choices=["telegram", "termux", "both"], default="both",
                               help="Notification platform")
    notify_parser.set_defaults(func=cmd_notify)
    
    # Telegram setup command
    telegram_parser = subparsers.add_parser("telegram", help="Configure Telegram notifications")
    telegram_sub = telegram_parser.add_subparsers(dest="telegram_action")
    
    # Setup Telegram
    setup_parser = telegram_sub.add_parser("setup", help="Setup Telegram bot")
    setup_parser.add_argument("--token", "-t", required=True, help="Bot token from @BotFather")
    setup_parser.add_argument("--chat-id", "-c", required=True, help="Your chat ID")
    setup_parser.set_defaults(func=cmd_telegram_setup)
    
    # Test Telegram
    test_parser = telegram_sub.add_parser("test", help="Send test message")
    test_parser.set_defaults(func=cmd_telegram_test)
    
    # Competitor command
    competitor_parser = subparsers.add_parser("competitor", help="Competitor intelligence scraping")
    competitor_parser.add_argument("name", help="Competitor name to research")
    competitor_parser.add_argument("--location", "-l", help="Filter by location (e.g., 'China', 'USA')")
    competitor_parser.add_argument("--product", "-p", help="Filter by product category")
    competitor_parser.add_argument("--save", "-s", action="store_true", help="Save to competitor database")
    competitor_parser.add_argument("--report", "-r", choices=["json", "md", "pdf", "docx"], default="json",
                                   help="Output format for report")
    competitor_parser.add_argument("--output", "-o", help="Save report to file")
    competitor_parser.set_defaults(func=cmd_competitor)
    
    # List competitors command
    list_parser = subparsers.add_parser("list-competitors", help="List saved competitors")
    list_parser.set_defaults(func=cmd_list_competitors)
    
    # Location command
    location_parser = subparsers.add_parser("location", help="Location intelligence scraping")
    location_parser.add_argument("name", help="Location name (e.g., 'Ambergris Caye')")
    location_parser.add_argument("--limit", "-l", type=int, default=50,
                                 help="Max results per platform")
    location_parser.add_argument("--save", "-s", action="store_true", help="Save to location database")
    location_parser.add_argument("--report", "-r", choices=["json", "md"], default="json",
                                 help="Output format for report")
    location_parser.add_argument("--output", "-o", help="Save report to file")
    location_parser.set_defaults(func=cmd_location)
    
    # List locations command
    list_locations_parser = subparsers.add_parser("list-locations", help="List saved locations")
    list_locations_parser.set_defaults(func=cmd_list_locations)
    
    # Airbnb command
    airbnb_parser = subparsers.add_parser("airbnb", help="Airbnb host lead generation")
    airbnb_parser.add_argument("location", help="Location to search (e.g., 'Ambergris Caye')")
    airbnb_parser.add_argument("--limit", "-l", type=int, default=50,
                               help="Max results per platform")
    airbnb_parser.add_argument("--save", "-s", action="store_true", help="Save leads to database")
    airbnb_parser.add_argument("--report", "-r", choices=["json", "md"], default="json",
                               help="Output format for report")
    airbnb_parser.add_argument("--output", "-o", help="Save report to file")
    airbnb_parser.set_defaults(func=cmd_airbnb)
    
    # List leads command
    list_leads_parser = subparsers.add_parser("list-leads", help="List saved Airbnb leads")
    list_leads_parser.set_defaults(func=cmd_list_leads)
    
    # Energy ROI calculator
    energy_parser = subparsers.add_parser("energy", help="Energy ROI calculator for wind+battery+miner")
    electric_sub = electric_parser.add_subparsers(dest="electric_action")
    
    # Calculate savings
    calc_parser = electric_sub.add_parser("calculate", help="Calculate gas-to-electric savings")
    calc_parser.add_argument("--type", "-t", choices=["studio", "1bed", "2bed", "3bed", "large"],
                             default="standard", help="Property type")
    calc_parser.add_argument("--output", "-o", help="Save report to file")
    calc_parser.set_defaults(func=cmd_electric_calculate)
    
    # Generate proposal
    proposal_parser = electric_sub.add_parser("proposal", help="Generate conversion proposal")
    proposal_parser.add_argument("--host-name", "-n", required=True, help="Host name")
    proposal_parser.add_argument("--type", "-t", choices=["studio", "1bed", "2bed", "3bed", "large"],
                                  default="standard", help="Property type")
    proposal_parser.add_argument("--output", "-o", help="Save proposal to file")
    proposal_parser.set_defaults(func=cmd_electric_proposal)
    
    # Package deal (wind + battery + electric)
    package_parser = electric_sub.add_parser("package", help="Complete energy package (wind+battery+electric)")
    package_parser.add_argument("location", help="Location name")
    package_parser.add_argument("--host-name", "-n", required=True, help="Host name")
    package_parser.add_argument("--properties", "-p", type=int, default=1, help="Number of properties")
    package_parser.add_argument("--output", "-o", help="Save proposal to file")
    package_parser.set_defaults(func=cmd_electric_package)
    energy_sub = energy_parser.add_subparsers(dest="energy_action")
    
    # Calculate ROI
    calc_parser = energy_sub.add_parser("calculate", help="Calculate ROI for a location")
    calc_parser.add_argument("location", help="Location name (e.g., 'Ambergris Caye')")
    calc_parser.add_argument("--properties", "-p", type=int, default=1,
                             help="Number of properties")
    calc_parser.add_argument("--output", "-o", help="Save report to file")
    calc_parser.set_defaults(func=cmd_energy_calculate)
    
    # Generate proposal
    proposal_parser = energy_sub.add_parser("proposal", help="Generate sales proposal")
    proposal_parser.add_argument("location", help="Location name")
    proposal_parser.add_argument("--host-name", "-n", required=True, help="Host name")
    proposal_parser.add_argument("--output", "-o", help="Save proposal to file")
    proposal_parser.set_defaults(func=cmd_energy_proposal)
    
    # Queue command
    queue_parser = subparsers.add_parser("queue", help="Manage offline queue")
    queue_sub = queue_parser.add_subparsers(dest="queue_action")
    
    # Add to queue
    q_add = queue_sub.add_parser("add", help="Add job to queue")
    q_add.add_argument("platform", help="Platform")
    q_add.add_argument("query", help="Search query")
    q_add.add_argument("--limit", "-l", type=int, default=20)
    q_add.add_argument("--priority", "-p", type=int, default=0)
    q_add.set_defaults(func=cmd_queue_add)
    
    # Show queue
    q_show = queue_sub.add_parser("show", help="Show queue status")
    q_show.set_defaults(func=cmd_queue_show)
    
    # Process queue
    q_process = queue_sub.add_parser("process", help="Process next job in queue")
    q_process.set_defaults(func=cmd_queue_process)
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start web dashboard")
    dashboard_parser.add_argument("--port", "-p", type=int, default=5000, help="Port number")
    dashboard_parser.add_argument("--background", "-b", action="store_true", help="Run in background")
    dashboard_parser.set_defaults(func=cmd_dashboard)
    
    # Presets command
    presets_parser = subparsers.add_parser("presets", help="List preset monitoring templates")
    presets_parser.set_defaults(func=cmd_presets)
    
    # ============================================================
    # Knowledge Graph Commands (KG Integration)
    # ============================================================
    kg_parser = subparsers.add_parser("kg", help="Knowledge graph operations for marketing intelligence")
    kg_sub = kg_parser.add_subparsers(dest="kg_command", help="KG subcommands")
    
    # kg build - search and build KG
    kg_build = kg_sub.add_parser("build", help="Build knowledge graph from topic research")
    kg_build.add_argument("topic", help="Research topic")
    kg_build.add_argument("--platform", "-p", default="all", help="Platform(s) to search")
    kg_build.add_argument("--depth", "-d", choices=["quick", "full"], default="full", help="Research depth")
    kg_build.add_argument("--limit", "-l", type=int, default=30, help="Max results per platform")
    kg_build.add_argument("--output", "-o", help="Save report to file")
    kg_build.set_defaults(func=cmd_kg_build)
    
    # kg query - search entities
    kg_query = kg_sub.add_parser("query", help="Query the knowledge graph")
    kg_query.add_argument("--search", "-s", help="Search entities by name")
    kg_query.add_argument("--type", "-t", choices=["Company", "Product", "Person", "Trend", "Concept", "Platform"], help="Filter by entity type")
    kg_query.set_defaults(func=cmd_kg_query)
    
    # kg conflicts - find contradictions
    kg_conflicts = kg_sub.add_parser("conflicts", help="Find conflicting intelligence across sources")
    kg_conflicts.add_argument("--entity", "-e", help="Check specific entity for conflicts")
    kg_conflicts.set_defaults(func=cmd_kg_conflicts)
    
    # kg sessions - list saved sessions
    kg_sessions = kg_sub.add_parser("sessions", help="List saved knowledge graph sessions")
    kg_sessions.set_defaults(func=cmd_kg_sessions)
    
    # kg load - load a session
    kg_load = kg_sub.add_parser("load", help="Load a previous KG session")
    kg_load.add_argument("session_id", nargs="?", help="Session ID (defaults to latest)")
    kg_load.set_defaults(func=cmd_kg_load)
    
    # kg export - export as agent bundle
    kg_export = kg_sub.add_parser("export", help="Export intelligence bundle for agents")
    kg_export.add_argument("--topic", "-t", help="Topic name")
    kg_export.add_argument("--format", "-f", choices=["json", "markdown", "csv"], default="json", help="Export format")
    kg_export.add_argument("--output", "-o", help="Output file path")
    kg_export.set_defaults(func=cmd_kg_export)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    asyncio.run(args.func(args))


# Schedule commands
async def cmd_schedule_list(args):
    """List scheduled jobs."""
    from services.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    jobs = scheduler.list_jobs()
    
    print("\n=== SilentReach Scheduled Jobs ===\n")
    
    if not jobs:
        print("No scheduled jobs found.")
        print("Use: silentreach schedule add <name> <cron> --command '<cmd>'")
        return
    
    for job in jobs:
        status = "✅" if job.get("enabled") else "❌"
        print(f"{status} {job.get('name', 'unknown')}")
        print(f"   Cron: {job.get('cron', 'N/A')}")
        print(f"   Command: {job.get('command', 'N/A')}")
        if job.get("description"):
            print(f"   Description: {job.get('description')}")
        print()


async def cmd_schedule_add(args):
    """Add a scheduled job."""
    from services.scheduler import get_scheduler
    from services.notifications import notify_success, notify_error
    from services.telegram import notify_telegram
    import asyncio
    
    scheduler = get_scheduler()
    
    # Check for preset names
    presets = {
        "daily": ("0 8 * * *", "silentreach intel daily-trends --depth quick -o ~/silentreach/reports/daily.md", "Daily intelligence summary"),
        "weekly": ("0 9 * * 1", "silentreach intel weekly-summary --depth full -o ~/silentreach/reports/weekly.md", "Weekly deep-dive report"),
        "competitor_daily": ("0 7 * * *", "silentreach competitor daily-check --save", "Daily competitor monitoring"),
    }
    
    if args.name in presets:
        cron, command, desc = presets[args.name]
        print(f"ℹ️  Using preset '{args.name}'")
        print(f"   Cron: {cron}")
        print(f"   Command: {command}")
        args.cron = cron
        args.command = command
        args.description = desc
    
    success = scheduler.add_job(
        name=args.name,
        cron_expr=args.cron,
        command=args.command,
        description=args.description or "",
    )
    
    if success:
        print(f"✅ Added job '{args.name}' with cron: {args.cron}")
        print(f"   Command: {args.command}")
        if args.description:
            print(f"   Description: {args.description}")
        
        # Send Telegram notification if configured
        asyncio.run(notify_telegram(f"📅 Scheduled job added: {args.name}\n{args.cron} - {args.command}"))
    else:
        print(f"❌ Failed to add job '{args.name}'")


async def cmd_schedule_remove(args):
    """Remove a scheduled job."""
    from services.scheduler import get_scheduler
    from services.notifications import notify_info
    
    scheduler = get_scheduler()
    
    success = scheduler.remove_job(args.name)
    
    if success:
        print(f"✅ Removed job '{args.name}'")
        notify_info("Scheduler Updated", f"Removed job: {args.name}")
    else:
        print(f"❌ Job '{args.name}' not found")


async def cmd_schedule_run(args):
    """Run a job immediately."""
    from services.scheduler import get_scheduler
    from services.notifications import notify_info, notify_error
    
    scheduler = get_scheduler()
    
    success = scheduler.run_now(args.name)
    
    if success:
        print(f"✅ Started job '{args.name}' in background")
        notify_info("Job Started", f"Running job: {args.name}")
    else:
        print(f"❌ Job '{args.name}' not found")
        notify_error("Job Error", f"Job not found: {args.name}")


# Notify command
async def cmd_notify(args):
    """Send test notification."""
    from services.notifications import notify_success, check_termux_api
    from services.telegram import get_telegram_notifier
    import asyncio
    
    platform = getattr(args, 'platform', 'both')
    
    # Termux notification
    if platform in ["termux", "both"]:
        api_status = check_termux_api()
        if api_status["available"]:
            notify_success("SilentReach", args.message)
            print(f"✅ Termux notification sent: {args.message}")
        else:
            print("⚠️  Termux:API not installed. Use --platform telegram instead.")
    
    # Telegram notification
    if platform in ["telegram", "both"]:
        tg = get_telegram_notifier()
        success = asyncio.run(tg.send_alert("SilentReach", args.message))
        if success:
            print(f"✅ Telegram notification sent: {args.message}")
        else:
            print(f"⚠️  Telegram not configured. Use: silentreach telegram setup")


async def cmd_telegram_setup(args):
    """Setup Telegram notifications."""
    from services.telegram import TelegramNotifier
    from pathlib import Path
    import yaml
    
    # Save config
    config_path = Path.home() / ".silentreach" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        except:
            config = {}
    
    if "telegram" not in config:
        config["telegram"] = {}
    
    config["telegram"]["token"] = args.token
    config["telegram"]["chat_id"] = args.chat_id
    
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    print("✅ Telegram configured!")
    print(f"   Token: {args.token[:10]}...")
    print(f"   Chat ID: {args.chat_id}")
    print("\n💡 Test with: silentreach telegram test")


async def cmd_telegram_test(args):
    """Send test Telegram message."""
    from services.telegram import get_telegram_notifier
    import asyncio
    
    tg = get_telegram_notifier()
    success = await tg.send_alert("SilentReach", "🎉 Telegram notifications are working!")
    
    if success:
        print("✅ Test message sent to Telegram!")
    else:
        print("❌ Failed to send test message.")
        print("   Configure with: silentreach telegram setup --token <TOKEN> --chat-id <CHAT_ID>")


# Queue commands
async def cmd_queue_add(args):
    """Add job to offline queue."""
    from services.queue import get_queue
    from services.notifications import notify_info
    
    queue = get_queue()
    job_id = queue.add_job(
        platform=args.platform,
        query=args.query,
        limit=args.limit,
        priority=args.priority
    )
    
    print(f"✅ Added to queue: {args.platform} - {args.query}")
    print(f"   Job ID: {job_id}")
    print(f"   Stats: {queue.get_stats()}")
    
    notify_info("Queue Updated", f"Added {args.platform} search to queue")


async def cmd_queue_show(args):
    """Show queue status."""
    from services.queue import get_queue
    
    queue = get_queue()
    stats = queue.get_stats()
    
    print("\n=== SilentReach Queue Status ===\n")
    print(f"Pending:   {stats['pending']}")
    print(f"Running:   {stats['running']}")
    print(f"Completed: {stats['completed']}")
    print(f"Failed:    {stats['failed']}")
    print()


async def cmd_queue_process(args):
    """Process next job in queue."""
    from services.queue import get_queue
    from services.notifications import notify_complete, notify_error
    
    queue = get_queue()
    job = queue.get_next_job()
    
    if not job:
        print("Queue is empty")
        return
    
    print(f"Processing: {job['platform']} - {job['query']}")
    
    # Start job
    queue.start_job(job["id"])
    
    # Import and run scraper
    try:
        module_name = f"scrapers.{job['platform']}"
        module = __import__(module_name, fromlist=["Scraper"])
        ScraperClass = getattr(module, f"{job['platform'].capitalize()}Scraper")

        scraper = ScraperClass(config=load_config())
        result = await scraper.search(job["query"], limit=job.get("limit", 20))
        
        # Complete job
        queue.complete_job(job["id"], result)
        
        count = len(result.get("data", result.get("posts", result.get("videos", []))))
        print(f"✅ Completed: {count} results")
        notify_complete(job["platform"], count, job["query"])
        
    except Exception as e:
        queue.fail_job(job["id"], str(e))
        print(f"❌ Failed: {e}")
        notify_error(job["platform"], str(e), job["query"])


# Dashboard command
async def cmd_dashboard(args):
    """Start web dashboard."""
    from services.dashboard import start_dashboard
    from services.notifications import notify_info
    
    print(f"\n🌐 Starting SilentReach Dashboard...")
    print(f"   Access at: http://localhost:{args.port}")
    print(f"   Press Ctrl+C to stop\n")
    
    notify_info("Dashboard Started", f"Access at http://localhost:{args.port}")
    
    dashboard = start_dashboard(port=args.port, background=args.background)


# Presets command
async def cmd_presets(args):
    """List preset monitoring templates."""
    from services.scheduler import preset_commands
    
    presets = preset_commands()
    
    print("\n=== SilentReach Preset Templates ===\n")
    
    for name, preset in presets.items():
        print(f"📋 {name.replace('_', ' ').title()}")
        print(f"   Cron: {preset['cron']}")
        print(f"   Command: {preset['command']}")
        print(f"   Description: {preset['description']}")
        print()
    
    print("To use a preset:")
    print("  silentreach schedule add <name> <cron> --command '<command>'")


# ============================================================
# Knowledge Graph Commands
# ============================================================

async def cmd_kg_build(args):
    """Build knowledge graph from topic research."""
    from services.kg_service import KGService, KGConfig
    from services.report_generator import MarketingReportGenerator
    
    # First run the search
    print(f"\n🔍 Searching for: {args.topic}")
    print("=" * 50)
    
    # Run search first to get results
    search_args = type('obj', (object,), {
        'query': args.topic,
        'platform': args.platform,
        'limit': args.limit,
        'format': 'json',
        'output': None,
    })()
    
    # Execute search
    search_results = {}
    scrapers = {
        "reddit": ("scrapers.reddit", "RedditScraper"),
        "youtube": ("scrapers.youtube", "YouTubeScraper"),
        "twitter": ("scrapers.twitter", "TwitterScraper"),
        "instagram": ("scrapers.instagram", "InstagramScraper"),
        "linkedin": ("scrapers.linkedin", "LinkedInScraper"),
    }
    
    if args.platform == "all":
        platforms = list(scrapers.keys())
    else:
        platforms = args.platform.split(",")
    
    config = {"global": {"headless": True, "default_delay": 2.0}}
    
    for platform in platforms:
        platform = platform.strip().lower()
        if platform not in scrapers:
            continue
        try:
            module_name, class_name = scrapers[platform]
            module = __import__(module_name, fromlist=[class_name])
            ScraperClass = getattr(module, class_name)
            scraper = ScraperClass(config)
            result = await scraper.search(args.topic, limit=args.limit)
            search_results[platform] = result
        except Exception as e:
            print(f"⚠️  {platform}: {e}")
            search_results[platform] = {"error": str(e)}
    
    # Now build the KG
    print(f"\n🧠 Building knowledge graph...")
    print("=" * 50)
    
    service = KGService()
    report = await service.ingest_results(search_results, topic=args.topic)
    
    print(f"\n✅ Knowledge Graph Built")
    print(f"   Entities: {report['entities_extracted']}")
    print(f"   Relations: {report['relations_extracted']}")
    print(f"   Conflicts: {report['conflicts_found']}")
    print(f"   Platforms: {', '.join(report['platforms_processed'])}")
    
    # Generate and save report
    generator = MarketingReportGenerator(service)
    
    if args.output:
        # Auto-detect format from extension
        ext = Path(args.output).suffix.lstrip('.')
        
        if ext == 'pdf':
            from services.output_fmt import OutputFormatter
            pdf_bytes = OutputFormatter.to_pdf(
                {"entities": list(service._entities.values())},
                title=f"Knowledge Graph Report: {args.topic}"
            )
            if pdf_bytes:
                with open(args.output, "wb") as f:
                    f.write(pdf_bytes)
                print(f"\n💾 PDF saved to: {args.output}")
        elif ext == 'md':
            report = generator.generate_campaign_brief(args.topic)
            with open(args.output, "w") as f:
                f.write(report)
            print(f"\n💾 Markdown report saved to: {args.output}")
        else:
            bundle = generator.generate_agent_bundle(args.topic)
            with open(args.output, "w") as f:
                import json
                json.dump(bundle, f, indent=2, default=str)
            print(f"\n💾 Agent bundle saved to: {args.output}")
    else:
        # Print human-readable summary
        report = generator.generate_campaign_brief(args.topic)
        print("\n" + "=" * 60)
        print("📊 HUMAN-READABLE INTELLIGENCE REPORT")
        print("=" * 60)
        print(report)
    
    # Show conflicts if any
    conflicts = service.detect_conflicts()
    if conflicts:
        print(f"\n⚠️  {len(conflicts)} conflict(s) detected!")
        print("   Use: silentreach kg conflicts --entity <name>")


async def cmd_kg_query(args):
    """Query the knowledge graph."""
    from services.kg_service import KGService
    
    service = KGService()
    
    # Load latest session if exists
    if not service.load_session():
        print("❌ No knowledge graph sessions found. Run 'kg build' first.")
        return
    
    # Query entities
    results = service.query_entities(
        search_term=args.search,
        entity_type=args.type
    )
    
    if not results:
        print("No entities found matching your criteria.")
        return
    
    print(f"\n📊 Found {len(results)} entities:\n")
    
    for entity in results:
        print(f"• {entity['name']} ({entity['type']})")
        print(f"  Sources: {', '.join(set(entity['sources']))}")
        print(f"  Facts: {entity['fact_count']}")
        if entity.get('sample_facts'):
            for fact in entity['sample_facts'][:2]:
                print(f"    - {fact['predicate']}: {fact['object']}")
        print()


async def cmd_kg_conflicts(args):
    """Find conflicts in the knowledge graph."""
    from services.kg_service import KGService
    
    service = KGService()
    
    if not service.load_session():
        print("❌ No knowledge graph sessions found. Run 'kg build' first.")
        return
    
    if args.entity:
        # Check specific entity
        conflicts = service.detect_conflicts()
        entity_conflicts = [c for c in conflicts if c.entity.lower() == args.entity.lower()]
        
        if not entity_conflicts:
            print(f"✅ No conflicts found for '{args.entity}'")
            return
        
        print(f"\n⚠️  Conflicts for '{args.entity}':\n")
        for conflict in entity_conflicts:
            print(f"  Claim 1: {conflict.fact_1} (from {conflict.source_1})")
            print(f"  Claim 2: {conflict.fact_2} (from {conflict.source_2})")
            print(f"  Confidence: {conflict.confidence:.0%}")
            print()
    else:
        # Show all conflicts
        conflicts = service.detect_conflicts()
        
        if not conflicts:
            print("✅ No conflicts detected across sources.")
            return
        
        print(f"\n⚠️  Found {len(conflicts)} conflicts:\n")
        for conflict in conflicts[:10]:
            print(f"• {conflict.entity}")
            print(f"  '{conflict.fact_1}' vs '{conflict.fact_2}'")
            print(f"  Sources: {conflict.source_1} vs {conflict.source_2}")
            print()


async def cmd_kg_sessions(args):
    """List saved KG sessions."""
    from services.kg_service import KGService
    
    service = KGService()
    sessions = service.list_sessions()
    
    if not sessions:
        print("No saved knowledge graph sessions found.")
        print("Run: silentreach kg build <topic>")
        return
    
    print(f"\n📚 Knowledge Graph Sessions ({len(sessions)}):\n")
    
    for session in sessions:
        print(f"• {session['id']}")
        print(f"  Topic: {session['topic']}")
        print(f"  Entities: {session['entities']} | Relations: {session['relations']}")
        print(f"  Saved: {session['timestamp']}")
        print()


async def cmd_kg_load(args):
    """Load a KG session."""
    from services.kg_service import KGService
    
    service = KGService()
    
    if args.session_id:
        success = service.load_session(args.session_id)
    else:
        success = service.load_session()  # Load latest
    
    if not success:
        print("❌ Session not found. Run 'silentreach kg sessions' to see available sessions.")
        return
    
    print("✅ Loaded knowledge graph session.")
    print(f"   Use 'kg query' to explore entities")
    print(f"   Use 'kg conflicts' to find contradictions")
    print(f"   Use 'kg export' to save as agent bundle")


async def cmd_kg_export(args):
    """Export knowledge graph as agent bundle."""
    from services.kg_service import KGService
    from services.report_generator import MarketingReportGenerator
    
    service = KGService()
    
    if not service.load_session():
        print("❌ No knowledge graph sessions found. Run 'kg build' first.")
        return
    
    generator = MarketingReportGenerator(service)
    
    # Generate bundle
    topic = args.topic or "market_intelligence"
    bundle = generator.generate_agent_bundle(topic)
    
    # Determine output
    if args.output:
        output_path = args.output
    elif args.format == "markdown":
        output_path = f"{topic}_report.md"
    else:
        output_path = f"{topic}_agent_bundle.json"
    
    # Write output
    if args.format == "markdown":
        report = generator.generate_campaign_brief(topic)
        with open(output_path, "w") as f:
            f.write(report)
    elif args.format == "csv":
        csv_data = service.to_csv()
        with open(output_path, "w") as f:
            f.write(csv_data)
    else:
        import json
        with open(output_path, "w") as f:
            json.dump(bundle, f, indent=2, default=str)
    
    print(f"💾 Exported to: {output_path}")
    print(f"   Entities: {len(bundle['entities'])}")
    print(f"   Relations: {len(bundle['relations'])}")
    print(f"   Conflicts: {len(bundle['conflicts'])}")


async def cmd_competitor(args):
    """Run competitor intelligence scraping."""
    from services.competitor import CompetitorScraper, CompetitorTracker
    
    print(f"\n🎯 Competitor Intelligence: {args.name}")
    print("=" * 50)
    
    scraper = CompetitorScraper()
    
    # Run competitor search
    profile = await scraper.search_competitor(args.name)
    
    # Apply filters if specified
    if hasattr(args, 'location') and args.location:
        if args.location.lower() not in str(profile.to_dict()).lower():
            print(f"⚠️  No mention of location '{args.location}' found")
    
    if hasattr(args, 'product') and args.product:
        products = [p for p in profile.products if args.product.lower() in p.lower()]
        if not products:
            print(f"⚠️  No products matching '{args.product}' found")
    
    # Generate report
    report_format = getattr(args, 'report', 'json')
    
    print("\n📊 Competitor Profile:")
    print(f"   Name: {profile.name}")
    print(f"   Location: {profile.location or 'Not detected'}")
    print(f"   Products: {len(profile.products)} found")
    print(f"   Suppliers: {len(profile.suppliers)} detected")
    print(f"   Mentions: {len(profile.mentions)} across platforms")
    
    # Format output
    if report_format == "json":
        report = scraper.generate_report(format="json")
        print("\n" + json.dumps(report, indent=2))
    elif report_format == "md":
        markdown = scraper.to_markdown()
        print("\n" + markdown)
    elif report_format == "pdf":
        pdf_bytes = scraper.to_pdf()
        if pdf_bytes:
            print(f"\n[✓] PDF generated ({len(pdf_bytes)} bytes)")
            print("[i] Use -o flag to save to file")
        else:
            print("\n[!] PDF generation failed")
    
    # Save to database if requested
    if getattr(args, 'save', False):
        tracker = CompetitorTracker()
        tracker.save_competitor(profile)
        print(f"\n[✓] Saved to competitor database")
    
    # Save to file if requested
    if hasattr(args, 'output') and args.output:
        filepath = Path(args.output)
        if report_format == "json":
            with open(filepath, "w") as f:
                json.dump(scraper.generate_report(), f, indent=2, default=str)
        elif report_format == "md":
            with open(filepath, "w") as f:
                f.write(scraper.to_markdown())
        elif report_format == "pdf":
            pdf_bytes = scraper.to_pdf()
            if pdf_bytes:
                with open(filepath, "wb") as f:
                    f.write(pdf_bytes)
                print(f"[✓] PDF saved to {filepath}")
        print(f"[✓] Report saved to {filepath}")


async def cmd_list_competitors(args):
    """List all saved competitors."""
    from services.competitor import CompetitorTracker
    
    tracker = CompetitorTracker()
    competitors = tracker.list_competitors()
    
    if not competitors:
        print("No competitors saved yet. Use `silentreach competitor <name> --save`")
        return
    
    print(f"\n📋 Saved Competitors ({len(competitors)})")
    print("=" * 50)
    for name in competitors:
        profile = tracker.load_competitor(name)
        if profile:
            print(f"- {profile.name} (scraped: {profile.scraped_at[:10]})")


async def cmd_location(args):
    """Research activity in a specific location."""
    from services.location import LocationScraper, LocationTracker
    
    print(f"\n📍 Location Intelligence: {args.name}")
    print("=" * 50)
    
    scraper = LocationScraper()
    
    # Run location research
    profile = await scraper.research_location(args.name, limit=args.limit)
    
    # Generate report
    print("\n📊 Location Profile:")
    print(f"   Name: {profile.name}")
    print(f"   Total Post Mentions: {profile.total_mentions}")
    print(f"   Unique Authors: {len(profile.active_users)}")
    print(f"   Pages Found: {len(profile.pages)}")
    print(f"   Groups Found: {len(profile.groups)}")
    print(f"   Businesses Found: {len(profile.businesses)}")
    
    # Format output
    if args.report == "json":
        report = scraper.generate_report()
        print("\n" + json.dumps(report, indent=2))
    elif args.report == "md":
        markdown = scraper.to_markdown()
        print("\n" + markdown)
    
    # Save to database if requested
    if getattr(args, 'save', False):
        tracker = LocationTracker()
        tracker.save_location(profile)
        print(f"\n[✓] Saved to location database")
    
    # Save to file if requested
    if hasattr(args, 'output') and args.output:
        filepath = Path(args.output)
        if args.report == "json":
            with open(filepath, "w") as f:
                json.dump(scraper.generate_report(), f, indent=2, default=str)
        else:
            with open(filepath, "w") as f:
                f.write(scraper.to_markdown())
        print(f"[✓] Report saved to {filepath}")


async def cmd_list_locations(args):
    """List all saved locations."""
    from services.location import LocationTracker
    
    tracker = LocationTracker()
    locations = tracker.list_locations()
    
    if not locations:
        print("No locations saved yet. Use `silentreach location <name> --save`")
        return
    
    print(f"\n📍 Saved Locations ({len(locations)})")
    print("=" * 50)
    for name in locations:
        profile = tracker.load_location(name)
        if profile:
            print(f"- {profile.name} ({profile.total_mentions} mentions)")


async def cmd_airbnb(args):
    """Generate leads from Airbnb hosts in a location."""
    from services.airbnb import AirbnbScraper, LeadTracker
    
    print(f"\n🏠 Airbnb Lead Generation: {args.location}")
    print("=" * 50)
    
    scraper = AirbnbScraper()
    
    # Search for hosts
    print(f"\n🔍 Searching for Airbnb hosts in: {args.location}")
    listings = await scraper.search_listings(args.location, limit=args.limit)
    
    print(f"   Found {len(listings)} potential leads")
    
    # Generate report
    report = scraper.generate_lead_report(args.location)
    
    # Print summary
    print("\n📊 Lead Summary:")
    print(f"   Total Leads: {len(report['leads'])}")
    
    high_priority = [l for l in report['leads'] if l['lead_score'] >= 50]
    medium_priority = [l for l in report['leads'] if 30 <= l['lead_score'] < 50]
    low_priority = [l for l in report['leads'] if l['lead_score'] < 30]
    
    print(f"   High Priority: {len(high_priority)}")
    print(f"   Medium Priority: {len(medium_priority)}")
    print(f"   Low Priority: {len(low_priority)}")
    
    # Format output
    if args.report == "json":
        print("\n" + json.dumps(report, indent=2))
    elif args.report == "md":
        markdown = scraper.to_markdown()
        print("\n" + markdown)
    
    # Save leads if requested
    if getattr(args, 'save', False):
        tracker = LeadTracker()
        for lead in report['leads']:
            host_id = lead['host']['host_id']
            tracker.save_lead(lead, host_id)
        print(f"\n[✓] Saved {len(report['leads'])} leads to database")
    
    # Save to file if requested
    if hasattr(args, 'output') and args.output:
        filepath = Path(args.output)
        if args.report == "json":
            with open(filepath, "w") as f:
                json.dump(report, f, indent=2, default=str)
        else:
            with open(filepath, "w") as f:
                f.write(scraper.to_markdown())
        print(f"[✓] Report saved to {filepath}")


async def cmd_list_leads(args):
    """List all saved Airbnb leads."""
    from services.airbnb import LeadTracker
    
    tracker = LeadTracker()
    leads = tracker.list_leads()
    
    if not leads:
        print("No leads saved yet. Use `silentreach airbnb <location> --save`")
        return
    
    print(f"\n🏠 Saved Airbnb Leads ({len(leads)})")
    print("=" * 50)
    for name in leads:
        lead = tracker.load_lead(name)
        if lead:
            host = lead.get('host', {})
            score = lead.get('lead_score', 0)
            print(f"- {host.get('name', name)} (Score: {score}, Listings: {host.get('listings_count', 0)})")


async def cmd_electric_calculate(args):
    """Calculate gas-to-electric conversion savings."""
    from services.electric_conversion import GasToElectricConverter
    
    print(f"\n🔥 Gas to Electric Conversion Calculator")
    print("=" * 60)
    
    converter = GasToElectricConverter(property_type=args.type)
    savings = converter.calculate_savings()
    safety = converter.calculate_safety_benefits()
    
    print(f"\n📊 Property Type: {args.type.capitalize()}")
    print()
    print("💰 MONTHLY SAVINGS:")
    print(f"   Current Gas Cost:      ${savings['monthly_gas_cost']:,.2f}")
    print(f"   New Electric Cost:     ${savings['monthly_electric_cost']:,.2f}")
    print(f"   ─────────────────────────────")
    print(f"   MONTHLY SAVINGS:       ${savings['monthly_savings']:,.2f}")
    print(f"   ANNUAL SAVINGS:        ${savings['annual_savings']:,.2f}")
    print()
    print("🛡️ SAFETY IMPROVEMENTS:")
    print(f"   Fire Risk Reduction:   {safety['fire_risk_reduction']}")
    print(f"   CO Risk:               {safety['co_poisoning_risk']}")
    print(f"   Guest Safety Score:    {safety['guest_safety']['before']} → {safety['guest_safety']['after']}/100")
    print()
    print("💰 INVESTMENT:")
    print(f"   Conversion Cost:       ${savings['conversion_cost']:,.0f}")
    print(f"   Payback Period:        {savings['payback_years']:.1f} years ({savings['payback_months']:.0f} months)")
    print()
    print(f"📈 5-Year Projection:")
    print(f"   Total Savings:         ${savings['annual_savings'] * 5 - savings['conversion_cost']:,.0f}")
    
    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump({**savings, **safety}, f, indent=2)
        print(f"\n💾 Saved to: {args.output}")


async def cmd_electric_proposal(args):
    """Generate gas-to-electric conversion proposal."""
    from services.electric_conversion import GasToElectricConverter
    
    print(f"\n📝 Generating Proposal for: {args.host_name}")
    print("=" * 60)
    
    converter = GasToElectricConverter(property_type=args.type)
    proposal = converter.generate_proposal(args.host_name)
    
    print(proposal)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(proposal)
        print(f"\n💾 Proposal saved to: {args.output}")


async def cmd_electric_package(args):
    """Generate complete energy package proposal."""
    from services.energy_roi import LocationEnergyCalculator, EnergySystem
    from services.electric_conversion import GasToElectricConverter
    
    print(f"\n📝 Generating Complete Energy Package for: {args.host_name}")
    print("=" * 60)
    
    # Get energy calculations
    energy_calc = LocationEnergyCalculator(args.location)
    energy_result = energy_calc.calculate_for_location(property_count=args.properties)
    
    # Get electric conversion calculations
    converter = GasToElectricConverter(property_type="2bed")
    electric_savings = converter.calculate_savings()
    
    # Combined benefits
    combined_monthly = energy_result['monthly_total']['total'] + electric_savings['monthly_savings']
    combined_annual = combined_monthly * 12
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           🌬️ COMPLETE ENERGY SOLUTION PACKAGE               ║
║        Wind + Battery + BTC Miner + Induction Cooking        ║
╚══════════════════════════════════════════════════════════════╝

📍 Location: {args.location}
🏘️  Properties: {args.properties}
👤 Host: {args.host_name}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 COMBINED MONTHLY BENEFITS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

From Wind + Battery + Miner:
   Energy Savings:        ${energy_result['monthly_total']['savings']:,.2f}
   USDT Earnings:         ${energy_result['monthly_total']['usdt_earnings']:,.2f}

From Gas-to-Electric:
   Cooking Savings:       ${electric_savings['monthly_savings']:,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 TOTAL COMBINED BENEFITS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Monthly Total:         ${combined_monthly:,.2f}
   Annual Total:          ${combined_annual:,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BENEFITS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 For Each Property:
   • Zero electricity bills (connection fee only)
   • Reliable power 24/7 (no blackouts)
   • Safe induction cooking (no gas cylinders)
   • Passive income from USDT exports
   • Extended battery life (25-80% regulation)

📊 Financial:
   • Payback: {energy_result['roi']['payback_years']:.1f} years (energy)
   • Electric payback: {electric_savings['payback_years']:.1f} years
   • 5-Year ROI: {energy_result['roi']['roi_5year_percent']:.1f}%

🎯 Market Advantage:
   • "Eco-friendly" listing badge
   • Higher guest safety scores
   • Modern induction cooking
   • Can charge premium rates

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Site survey (free)
2. System design (custom sizing)
3. Combined installation (1-2 days)
4. Monitoring setup (mobile app)
5. Guest certification (safety)

📞 Contact us for a bundled quote!
""")
    
    if args.output:
        import json
        combined = {
            "location": args.location,
            "host_name": args.host_name,
            "property_count": args.properties,
            "energy": energy_result,
            "electric_conversion": electric_savings,
            "combined_monthly": combined_monthly,
            "combined_annual": combined_annual,
        }
        with open(args.output, "w") as f:
            json.dump(combined, f, indent=2)
        print(f"\n💾 Saved to: {args.output}")


if __name__ == "__main__":
    main()
