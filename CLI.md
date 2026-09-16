# SilentReach CLI Commands

## Setup & Health

```bash
# Interactive setup wizard
silentreach setup

# Check system status
silentreach doctor
```

## Searching

```bash
# Search a topic on all platforms
silentreach search "dropshipping" -p all

# Search specific platforms
silentreach search "AI tools" -p reddit,youtube,twitter

# Limit results
silentreach search "products" -p reddit --limit 50

# Output formats
silentreach search "topic" -p all -f json -o results.json
silentreach search "topic" -p all -f markdown -o report.md
```

## Intelligence Reports

```bash
# Quick intel (3 platforms)
silentreach intel "dropshipping 2024" --depth quick

# Full intel (6 platforms)
silentreach intel "AI marketing" --depth full

# Save report
silentreach intel "topic" --depth full -o report.md
```

## Authentication

```bash
# Login to Twitter (opens browser)
silentreach login twitter -u username -P password

# Login to Instagram (opens browser)
silentreach login instagram -u username -P password
```

## Python API

```python
import asyncio
from silentreach.scrapers.reddit import RedditScraper
from silentreach.scrapers.youtube import YouTubeScraper
from silentreach.services.output_fmt import OutputFormatter

async def search_all():
    # Reddit
    reddit = RedditScraper()
    results = await reddit.search("dropshipping", limit=20)
    
    # YouTube
    youtube = YouTubeScraper()
    videos = await youtube.search("dropshipping tutorial", limit=20)
    
    # Format output
    report = OutputFormatter.to_markdown({
        "reddit": results,
        "youtube": videos,
    }, "Research Report")
    
    print(report)

asyncio.run(search_all())
```

## Configuration

Edit `~/.silentreach/config.yaml`:

```yaml
global:
  headless: true
  default_delay: 2.0
  
rate_limit:
  enabled: true
  default_rpm: 30

platforms:
  reddit:
    primary: agent_reach
    stealth_level: high
  twitter:
    primary: nodriver
    stealth_level: very_high
```

## Output Formats

- **json**: Structured data for processing
- **markdown**: Human-readable reports
- **csv**: Spreadsheet-compatible

## Tips

1. Always run `silentreach setup` first
2. Use `--depth quick` for fast results
3. Login to platforms for authenticated access
4. Check `~/.silentreach/cookies/` for saved sessions
