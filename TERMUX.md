# SilentReach Termux Setup Guide

## Prerequisites

Make sure you have Termux installed and updated:
```bash
termux-setup-storage
pkg update && pkg upgrade -y
```

## Install Dependencies

```bash
# Install system packages
pkg install python git chromium -y

# Clone the repo
git clone https://github.com/ykycportal/silentreach.git
cd silentreach

# Install Python dependencies
pip install -e ".[all]"

# Verify installations
python -c "import nodriver; print('nodriver OK')"
python -c "import agent_reach; print('agent-reach OK')"
which chromium-browser
```

## First Run

```bash
# Setup SilentReach
silentreach setup

# Check your environment
silentreach doctor

# Test a search
silentreach search "dropshipping" -p reddit --limit 5
```

## Tips for Termux

### 1. Keep Background Processes Running
Use `Termux:WakeLock` or keep terminal open:
```bash
# Run in background
nohup silentreach search "topic" -p all > output.log &
```

### 2. Storage Access
Grant storage permission for saving results:
```bash
termux-setup-storage
# Results save to ~/.silentreach/ by default
```

### 3. Headless Mode vs Desktop
- **Headless**: Faster, but some sites detect it
- **Desktop**: Requires screen/display, more stealth
- **Recommendation**: Use headless for testing, desktop for sensitive platforms

### 4. Battery Optimization
Disable battery optimization for Termux:
```bash
termux-wake-lock
```

## Troubleshooting

### Chrome Not Found
```bash
pkg install chromium
# Or use built-in browser
nodriver starts Chrome automatically
```

### Python Package Issues
```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Reinstall
pip install -e ".[all]" --force-reinstall
```

###nodriver Connection Errors
```bash
# Ensure Chrome is installed
chromium --version

# Try headful mode for login
nodriver starts with --headless by default, remove for login flows
```

## Storage Locations

All SilentReach data is stored in your home directory:
```
~/.silentreach/
├── config.yaml        # Your configuration
├── cookies/           # Saved browser sessions
│   ├── twitter.json
│   ├── instagram.json
│   └── ...
├── logs/              # Application logs
└── results/           # Saved search results
```

## Example: Daily Monitoring Script

Create `~/.silentreach/daily_monitor.py`:
```python
#!/usr/bin/env python3
import asyncio
from scrapers.reddit import RedditScraper
from scrapers.youtube import YouTubeScraper

async def daily_check():
    topics = ["dropshipping", "ecommerce", "shopify"]
    
    for topic in topics:
        print(f"\n=== Checking: {topic} ===")
        
        reddit = RedditScraper()
        reddit_data = await reddit.search(topic, limit=10)
        
        youtube = YouTubeScraper()
        yt_data = await youtube.search(topic, limit=10)
        
        print(f"Reddit: {len(reddit_data.get('results', []))} posts")
        print(f"YouTube: {len(yt_data.get('results', []))} videos")

if __name__ == "__main__":
    asyncio.run(daily_check())
```

Run it:
```bash
python ~/.silentreach/daily_monitor.py
```

## Useful Termux Commands

```bash
# Check disk space
df -h

# Monitor battery
termux-battery-status

# Check CPU usage
top

# Keep screen on during long runs
termux-wake-lock

# Schedule tasks with cron
pkg install cronie
crontab -e
```
