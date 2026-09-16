"""
Example usage of SilentReach framework.
"""

import asyncio
import json
from pathlib import Path


async def example_basic_search():
    """Basic search example."""
    from scrapers.reddit import RedditScraper
    from scrapers.youtube import YouTubeScraper
    
    scraper = RedditScraper()
    result = await scraper.search("dropshipping", limit=10)
    
    print(f"Found {len(result.get('results', []))} Reddit posts")
    for post in result.get('results', [])[:5]:
        print(f"  - {post.get('title', 'No title')}")


async def example_twitter_login():
    """Twitter login and search example."""
    from scrapers.twitter import TwitterScraper
    
    scraper = TwitterScraper()
    
    # Login (requires actual credentials)
    # success = await scraper.login("your_username", "your_password")
    # if success:
    #     results = await scraper.search("AI tools", limit=20)
    #     print(f"Found {len(results.get('tweets', []))} tweets")


async def example_multi_platform():
    """Search across multiple platforms."""
    from scrapers.reddit import RedditScraper
    from scrapers.youtube import YouTubeScraper
    from scrapers.bilibili import BilibiliScraper
    
    query = "dropshipping"
    
    results = {}
    
    # Reddit
    reddit = RedditScraper()
    results["reddit"] = await reddit.search(query, limit=10)
    
    # YouTube
    youtube = YouTubeScraper()
    results["youtube"] = await youtube.search(query, limit=10)
    
    # Bilibili
    bilibili = BilibiliScraper()
    results["bilibili"] = await bilibili.search(query, limit=10)
    
    # Save combined results
    output = {
        "query": query,
        "timestamp": asyncio.get_event_loop().time(),
        "results": results,
    }
    
    output_path = Path.home() / ".silentreach" / "results" / f"{query}_multi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"Results saved to {output_path}")


async def example_intel_report():
    """Generate an intelligence report."""
    from scrapers.reddit import RedditScraper
    from scrapers.youtube import YouTubeScraper
    from scrapers.twitter import TwitterScraper
    from services.output_fmt import OutputFormatter
    
    topic = "AI marketing"
    
    # Gather data
    reddit = RedditScraper()
    reddit_data = await reddit.search(topic, limit=20)
    
    youtube = YouTubeScraper()
    youtube_data = await youtube.search(topic, limit=20)
    
    twitter = TwitterScraper()
    twitter_data = await twitter.search(topic, limit=20)
    
    # Compile report
    report_data = {
        "topic": topic,
        "reddit": reddit_data,
        "youtube": youtube_data,
        "twitter": twitter_data,
    }
    
    # Save as markdown
    report_md = OutputFormatter.to_markdown(report_data, f"Intel Report: {topic}")
    
    output_path = Path.home() / ".silentreach" / "reports" / f"{topic}_intel.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write(report_md)
    
    print(f"Report saved to {output_path}")


async def main():
    """Run all examples."""
    print("=== SilentReach Examples ===\n")
    
    print("1. Basic Reddit Search")
    await example_basic_search()
    print()
    
    print("2. Multi-Platform Search")
    await example_multi_platform()
    print()
    
    print("3. Intelligence Report")
    await example_intel_report()
    print()
    
    print("All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
