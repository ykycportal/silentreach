# SilentReach Termux Setup Guide

Complete guide for running SilentReach on Android via Termux.

## Why Termux + SilentReach?

Termux gives you a full Linux environment on Android. Combined with SilentReach:
- **Mobile IPs**: Harder to block than datacenter/VPS IPs
- **Always Connected**: Your phone is always on, perfect for scheduled scans
- **Zero Cost**: No VPS needed, runs entirely on your device
- **Portable**: Clone the repo, install deps, start scraping anywhere

---

## Prerequisites

### 1. Install Termux
Download from [F-Droid](https://f-droid.org/packages/com.termux/) (preferred) or GitHub releases.

### 2. Grant Storage Permission
```bash
termux-setup-storage
```

### 3. Update Packages
```bash
pkg update && pkg upgrade -y
```

---

## Installation

### Option A: One-Click Install (Recommended)
```bash
bash <(curl -s https://raw.githubusercontent.com/ykycportal/silentreach/main/install.sh)
```

### Option B: Manual Install
```bash
# Install system dependencies
pkg install python git chromium yt-dlp termux-api -y

# Clone repository
git clone https://github.com/ykycportal/silentreach.git
cd silentreach

# Install Python package
pip install -e ".[all]"

# Run setup
silentreach setup
silentreach doctor
```

---

## First Time Setup

### 1. Check Installation
```bash
silentreach doctor
```

Expected output:
```
👁️  SilentReach Doctor

✅ Python 3.11.7
✅ agent-reach installed
✅ nodriver installed
✅ yt-dlp installed
✅ Chrome/Chromium found
✅ Config at /data/data/com.termux/files/home/.silentreach/config.yaml
```

### 2. Enable Notifications
```bash
pkg install termux-api
silentreach notify "SilentReach is ready!"
```

### 3. Login to Platforms
Some platforms require authentication:

```bash
# Twitter/X (opens browser for login)
silentreach login twitter

# Instagram (opens browser for login)
silentreach login instagram
```

Cookies are saved to `~/.silentreach/cookies/`.

---

## Daily Usage

### Basic Search
```bash
# Search Reddit
silentreach search "dropshipping" -p reddit --limit 10

# Search multiple platforms
silentreach search "AI tools" -p reddit,youtube,twitter

# Full intelligence report
silentreach intel "ecommerce trends" --depth full
```

### Save Results

Export in **7 formats** for maximum flexibility:

```bash
# JSON format (API integration)
silentreach search "topic" -p all -f json -o results.json

# Markdown report (human-readable)
silentreach search "topic" -p all -f markdown -o report.md

# CSV export (spreadsheet import)
silentreach search "topic" -p reddit --limit 50 -f csv -o reddit_data.csv

# PDF report (email attachment)
silentreach search "competitors" -p all -f pdf -o report.pdf

# Excel analysis (data processing)
silentreach search "trends" -p all -f xlsx -o analysis.xlsx

# LibreOffice format (open standard)
silentreach search "research" -p all -f ods -o report.ods

# Auto-detect from extension
silentreach search "topic" -o output.pdf
silentreach search "topic" -o output.xlsx
```

---

## Background Operations

### Using Crontab (Persistent Across Reboots)
```bash
# Edit crontab
crontab -e

# Add job (runs daily at 8 AM)
0 8 * * * cd ~/silentreach && silentreach search "dropshipping" -p reddit,youtube >> logs/cron.log 2>&1

# Save and exit (:wq)
```

### Using Terminal Background (Session Only)
```bash
# Keep running after terminal closes
termux-wake-lock
nohup silentreach search "topic" -p all > output.log 2>&1 &

# Check status
jobs
```

### Using Scheduler Service
```bash
# Add scheduled job
silentreach schedule add daily_monitor "0 8 * * *" \
  --command "silentreach search 'dropshipping' -p all" \
  --description "Daily market research"

# List jobs
silentreach schedule list

# Run immediately
silentreach schedule run daily_monitor
```

---

## Offline Queue System

When you're on cellular data or have spotty connection:

```bash
# Queue jobs for later
silentreach queue add reddit "ecommerce trends" --priority 1
silentreach queue add youtube "product reviews" --priority 2

# Check queue status
silentreach queue show

# Process when WiFi available
silentreach queue process
```

Queue automatically retries failed jobs (up to 3 times with exponential backoff).

---

## Web Dashboard

Monitor your scrapes from any browser:

```bash
# Start dashboard
silentreach dashboard

# Access at http://localhost:5000
# Or from another device on same network:
# http://<your-phone-ip>:5000
```

Features:
- Real-time results display
- Auto-refresh every 30 seconds
- Statistics and platform breakdown
- Mobile-responsive design

---

## Battery Optimization

### Keep Termux Awake
```bash
# Prevent screen from sleeping during long scans
termux-wake-lock

# Check battery status
termux-battery-status
```

### Optimize Scans
Edit `~/.silentreach/config.yaml`:
```yaml
global:
  headless: true           # Faster, less battery
  default_delay: 1.0       # Shorter delays
  
rate_limit:
  default_rpm: 60          # Higher RPM for faster scans
```

---

## Storage Management

### Check Disk Usage
```bash
df -h
du -sh ~/.silentreach/
```

### Clean Up Old Data
```bash
# Clear completed queue items (older than 24 hours)
python -c "from services.queue import get_queue; print(f'Cleaned {get_queue().clear_completed()} items')"

# Clear old logs
find ~/.silentreach/logs -name "*.log" -mtime +7 -delete

# Clear old results
find ~/.silentreach/results -name "*.json" -mtime +30 -delete
```

---

## Troubleshooting

### "nodriver: command not found"
```bash
pkg install chromium
# Or use built-in browser
nodriver starts Chrome automatically
```

### "No module named 'agent_reach'"
```bash
pip install -e ".[all]" --force-reinstall
```

### YouTube Search Fails
```bash
# Install deno for JS runtime
pkg install deno

# Or configure yt-dlp
mkdir -p ~/.config/yt-dlp
echo "--js-runtimes node" >> ~/.config/yt-dlp/config
```

### Twitter/Instagram Login Issues
```bash
# Clear saved cookies
rm ~/.silentreach/cookies/twitter.json
rm ~/.silentreach/cookies/instagram.json

# Re-login
silentreach login twitter
```

### Notifications Not Working
```bash
# Check Termux:API
which termux-notification

# Reinstall if needed
pkg uninstall termux-api
pkg install termux-api

# Test
termux-notification --title "Test" --text "Hello"
```

---

## Advanced: Custom Monitoring Script

Create `~/.silentreach/daily_monitor.py`:

```python
#!/usr/bin/env python3
import asyncio
import json
from pathlib import Path
from scrapers.reddit import RedditScraper
from scrapers.youtube import YouTubeScraper
from services.notifications import notify_success

async def daily_check():
    topics = ["dropshipping", "ecommerce", "shopify"]
    all_results = {}
    
    for topic in topics:
        print(f"\n=== Checking: {topic} ===")
        
        # Reddit
        reddit = RedditScraper()
        reddit_data = await reddit.search(topic, limit=10)
        all_results[f"reddit_{topic}"] = reddit_data
        
        # YouTube
        youtube = YouTubeScraper()
        yt_data = await youtube.search(topic, limit=10)
        all_results[f"youtube_{topic}"] = yt_data
        
        # Save to file
        output_dir = Path.home() / ".silentreach" / "results" / "daily"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = asyncio.get_event_loop().time()
        with open(output_dir / f"{topic}_{timestamp}.json", "w") as f:
            json.dump(all_results, f, indent=2)
    
    # Send notification
    total = sum(
        len(r.get("posts", r.get("videos", [])))
        for r in all_results.values()
    )
    notify_success("Daily Research Complete", f"Found {total} results across {len(topics)} topics")

if __name__ == "__main__":
    asyncio.run(daily_check())
```

Make executable and schedule:
```bash
chmod +x ~/.silentreach/daily_monitor.py
silentreach schedule add daily_custom "0 9 * * *" \
  --command "python ~/.silentreach/daily_monitor.py"
```

---

## Useful Termux Commands

```bash
# Check disk space
df -h

# Monitor CPU usage
top

# Check battery
termux-battery-status

# Keep screen on
termux-wake-lock

# List packages
pkg list-installed

# Upgrade specific package
pkg upgrade python
```

---

## Data Privacy

SilentReach is designed with privacy in mind:
- All data stored locally in `~/.silentreach/`
- Cookies never uploaded anywhere
- No telemetry or phone-home
- Open source — audit the code yourself

---

## Need Help?

- **GitHub Issues**: https://github.com/ykycportal/silentreach/issues
- **Documentation**: See `README.md`, `CLI.md`, `QUICKREF.md`
- **Examples**: Check `examples/` directory
