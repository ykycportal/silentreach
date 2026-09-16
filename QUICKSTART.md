# SilentReach

## Quick Install

```bash
# Termux setup
pkg update && pkg upgrade -y
pkg install python git chromium -y

# Clone and install
git clone https://github.com/ykycportal/silentreach.git
cd silentreach
pip install -e ".[all]"

# Run setup
silentreach setup
silentreach doctor
```

## Basic Usage

```bash
# Search Reddit
silentreach search "dropshipping tips" -p reddit

# Search all platforms
silentreach search "AI tools" -p all --limit 20

# Full intelligence report
silentreach intel "dropshipping 2024" --depth full

# Save results to file
silentreach search "shopify" -p reddit,youtube -o results.json
```

## Python API

```python
import asyncio
from scrapers.reddit import RedditScraper
from scrapers.youtube import YouTubeScraper
from services.output_fmt import OutputFormatter

async def main():
    # Reddit search
    reddit = RedditScraper()
    results = await reddit.search("dropshipping", limit=10)
    
    # YouTube search
    youtube = YouTubeScraper()
    videos = await youtube.search("dropshipping tutorial", limit=10)
    
    # Combine and save
    report = OutputFormatter.to_markdown({
        "reddit": results,
        "youtube": videos,
    }, "Research Report")
    
    print(report)

asyncio.run(main())
```

## Platforms

| Platform | Method | Auth Required |
|----------|--------|---------------|
| Reddit | agent-reach + nodriver | Yes |
| YouTube | agent-reach + yt-dlp | No |
| Twitter/X | nodriver | Yes |
| Instagram | nodriver | Yes |
| LinkedIn | nodriver + agent-reach | Yes |
| Bilibili | agent-reach + yt-dlp | No |
| V2EX | agent-reach | No |
| RSS | agent-reach | No |

## Stealth Features

- Randomized user agents and headers
- Rate limiting with exponential backoff
- Cookie persistence for authenticated sessions
- Platform-specific timing delays
- Proxy rotation support

## Configuration

Copy and customize:
```bash
cp config/settings.example.yaml ~/.silentreach/config.yaml
```

## License

MIT - Use responsibly.
