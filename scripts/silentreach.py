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
    config = load_config()
    
    # Import scrapers dynamically
    scrapers = {
        "reddit": ("scrapers.reddit", "RedditScraper"),
        "youtube": ("scrapers.youtube", "YouTubeScraper"),
        "twitter": ("scrapers.twitter", "TwitterScraper"),
        "instagram": ("scrapers.instagram", "InstagramScraper"),
        "linkedin": ("scrapers.linkedin", "LinkedInScraper"),
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
        platforms = ["reddit", "youtube", "bilibili"]
    elif args.depth == "full":
        platforms = ["reddit", "youtube", "twitter", "linkedin", "bilibili"]
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
    notify_parser.set_defaults(func=cmd_notify)
    
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
    
    scheduler = get_scheduler()
    
    success = scheduler.add_job(
        name=args.name,
        cron_expr=args.cron,
        command=args.command,
        description=args.description or ""
    )
    
    if success:
        print(f"✅ Added job '{args.name}' with cron: {args.cron}")
        notify_success("Scheduler Updated", f"Added job: {args.name}")
    else:
        print(f"❌ Failed to add job '{args.name}'")
        notify_error("Scheduler Error", f"Failed to add job: {args.name}")


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
    
    api_status = check_termux_api()
    
    if not api_status["available"]:
        print("❌ Termux:API not installed")
        print("Install with: pkg install termux-api")
        return
    
    notify_success("SilentReach", args.message)
    print(f"✅ Notification sent: {args.message}")


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
        bundle = generator.generate_agent_bundle(args.topic)
        with open(args.output, "w") as f:
            import json
            json.dump(bundle, f, indent=2, default=str)
        print(f"\n💾 Saved to: {args.output}")
    else:
        # Print summary
        print(f"\n📊 Summary:")
        for name, entity in list(service._entities.items())[:10]:
            print(f"   • {name} ({entity.type}) - {len(entity.facts)} facts")
    
    # Show conflicts if any
    if report['conflicts_found'] > 0:
        print(f"\n⚠️  {report['conflicts_found']} conflict(s) detected!")
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


if __name__ == "__main__":
    main()
