# SilentReach

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Termux](https://img.shields.io/badge/Termux-Ready-brightgreen)](https://termux.com)
[![GitHub stars](https://img.shields.io/github/stars/ykycportal/silentreach?style=social)](https://github.com/ykycportal/silentreach)

## 📱 The Ultimate Android-First Web Scraper

**SilentReach** combines agent-reach (public APIs) + nodriver (undetected browser automation) into a complete web intelligence framework — **built specifically for Termux/Android**.

Run your entire scraping pipeline from your phone. No VPS. No cloud. Just you, your mobile IP, and 12 platforms.

---

## 🚀 Why SilentReach?

| Feature | Description |
|---------|-------------|
| **📱 Mobile-Native** | Designed for Termux from day one |
| **🔒 Stealth** | Mobile IPs are harder to flag than datacenters |
| **⏰ Background Jobs** | Run 24/7 with cron, survive terminal close |
| **🔔 Push Notifications** | Get alerts on your phone when scans complete |
| **📥 Offline Queue** | Queue jobs when offline, auto-sync when back |
| **🌐 Web Dashboard** | Monitor results from any browser |
| **🔌 Plugins** | Extend with custom platform scrapers |
| **📊 Export** | Push to Google Sheets automatically |

---

## 📦 What's Inside

### 12 Platform Scrapers

| Platform | Method | Stealth | Auth | Status |
|----------|--------|---------|------|--------|
| Reddit | rdt-cli + nodriver | High | Cookie | ✅ |
| YouTube | yt-dlp | High | None | ✅ |
| Twitter/X | twitter-cli + nodriver | Very High | Cookie | ✅ |
| Instagram | nodriver (headful) | Very High | Cookie | ✅ |
| LinkedIn | Jina Reader + nodriver | High | Cookie | ✅ |
| Facebook | nodriver | Very High | Cookie | ✅ |
| Bilibili | bili-cli + yt-dlp | Medium | None | ✅ |
| V2EX | agent-reach | High | None | ✅ |
| RSS | feedparser | Medium | None | ✅ |
| Xiaohongshu | nodriver | High | Cookie | ✅ |
| Google Search | Exa API | High | None | ✅ |
| Any Website | Jina Reader | Medium | None | ✅ |

### Core Services

- **StealthEngine**: Fingerprint randomization, header rotation, timing control
- **CookieManager**: Persistent sessions with auto-refresh
- **NotificationCenter**: Termux:API push notifications
- **Scheduler**: Cron-based background job management
- **OfflineQueue**: Queue jobs when offline, process when back online
- **PluginRegistry**: Auto-discover custom scrapers
- **SheetsExporter**: Push results to Google Sheets
- **WebDashboard**: Browser-based monitoring UI

---

## ⚡ Quick Start (30 Seconds)

```bash
# One-click install
bash <(curl -s https://raw.githubusercontent.com/ykycportal/silentreach/main/install.sh)

# Verify installation
silentreach doctor

# Run your first search
silentreach search "dropshipping" -p reddit,youtube --limit 10
```

### First Time Setup

```bash
# 1. Install Termux:API for notifications
pkg install termux-api

# 2. Test notifications
silentreach notify "Hello from SilentReach!"

# 3. Login to platforms (one-time)
silentreach login twitter
silentreach login instagram

# 4. Schedule your first job
silentreach schedule add daily_monitor "0 8 * * *" \
  --command "silentreach search 'dropshipping' -p reddit,youtube,twitter"
```

---

## 🎯 Use Cases

### 1. Daily Monitoring
```bash
# Set up daily dropshipping research
silentreach schedule add dropshipping_daily "0 8 * * *" \
  --command "silentreach search 'dropshipping' -p reddit,youtube,twitter" \
  --description "Daily market research"

# Run now to test
silentreach schedule run dropshipping_daily
```

### 2. Competitor Tracking
```bash
# Track competitor mentions every 6 hours
silentreach schedule add competitor_watch "0 */6 * * *" \
  --command "silentreach search 'shopify stores' -p twitter,reddit"
```

### 3. Offline-First Workflow
```bash
# Queue searches while on cellular
silentreach queue add reddit "ecommerce trends" --priority 1
silentreach queue add youtube "product reviews" --priority 2

# Process when WiFi available
silentreach queue process
```

### 4. Web Dashboard
```bash
# Start monitoring UI
silentreach dashboard

# Open in browser: http://localhost:5000
# Auto-refreshes every 30 seconds
```

---

## 📋 Complete CLI Reference

### Search Commands
```bash
# Search across platforms
silentreach search "topic" -p reddit,youtube,twitter
silentreach search "topic" -p all --limit 50

# Save results
silentreach search "topic" -p all -f json -o results.json
silentreach search "topic" -p all -f markdown -o report.md
```

### Intelligence Reports
```bash
# Quick scan (3 platforms)
silentreach intel "topic" --depth quick

# Full analysis (6 platforms)
silentreach intel "topic" --depth full
```

### Scheduler
```bash
# List jobs
silentreach schedule list

# Add job
silentreach schedule add my_job "0 8 * * *" \
  --command "silentreach search 'topic' -p all"

# Remove job
silentreach schedule remove my_job

# Run now
silentreach schedule run my_job
```

### Notifications
```bash
# Send test notification
silentreach notify "Test message"

# Check Termux:API status
silentreach doctor  # Shows API availability
```

### Offline Queue
```bash
# Add to queue
silentreach queue add reddit "products"

# View queue status
silentreach queue show

# Process next job
silentreach queue process
```

### Dashboard
```bash
# Start web UI
silentreach dashboard

# Custom port
silentreach dashboard --port 8080

# Run in background
silentreach dashboard --background
```

### Presets
```bash
# View ready-made templates
silentreach presets

# Use a preset
silentreach schedule add $(silentreach presets | grep dropshipping | head -1) \
  --cron "0 8 * * *" \
  --command "silentreach search 'dropshipping' -p reddit,youtube"
```

---

## 🔧 Python API

```python
import asyncio
from scrapers.reddit import RedditScraper
from scrapers.youtube import YouTubeScraper
from services.notifications import notify_success
from services.scheduler import get_scheduler

async def research():
    # Multi-platform search
    results = {}
    
    reddit = RedditScraper()
    results["reddit"] = await reddit.search("dropshipping", limit=20)
    
    youtube = YouTubeScraper()
    results["youtube"] = await youtube.search("dropshipping tutorial", limit=20)
    
    # Send notification when done
    total = sum(len(r.get("posts", r.get("videos", []))) for r in results.values())
    notify_success("Research Complete", f"Found {total} results")
    
    return results

# Schedule daily
scheduler = get_scheduler()
scheduler.add_job(
    name="daily_research",
    cron_expr="0 8 * * *",
    command="python my_script.py"
)

asyncio.run(research())
```

---

## 🌐 Plugin System

Create custom scrapers:

```bash
# Generate template
silentreach plugins create my_platform

# Edit the generated file
nano ~/.silentreach/plugins/my_platform.py
```

```python
# ~/.silentreach/plugins/my_platform.py
from scrapers.base import BaseScraper

class MyPlatformScraper(BaseScraper):
    platform = "myplatform"
    stealth_level = "high"
    
    async def search(self, query, limit=20):
        # Your implementation
        return {"query": query, "results": [...], "total": len([...])}
```

Auto-discovered on next run:
```bash
silentreach presets  # Shows your new platform
```

---

## 📊 Data Storage

All data stays local on your device:

```
~/.silentreach/
├── config.yaml              # Configuration
├── cookies/                 # Browser sessions (encrypted locally)
│   ├── twitter.json
│   ├── instagram.json
│   └── ...
├── jobs/                    # Scheduled job scripts
├── queue/                   # Offline queue
│   ├── pending/
│   ├── running/
│   ├── completed/
│   └── failed/
├── results/                 # Saved searches
│   ├── reddit/
│   ├── youtube/
│   └── ...
├── logs/                    # Application logs
└── plugins/                 # Custom scrapers
```

---

## 🔒 Stealth Features

### Multi-Layer Anti-Detection
- **Fingerprint Randomization**: Rotates User-Agent, viewport, platform
- **Header Rotation**: Realistic browser headers with natural variation
- **Timing Control**: Platform-specific delays (Reddit: 2-4s, Instagram: 4-6s)
- **Cookie Persistence**: Reuse real browser sessions
- **Rate Limiting**: Exponential backoff on 429s

### Mobile IP Advantage
- Mobile carriers use CGNAT — IPs shared with thousands of users
- Less likely to be flagged as "datacenter" vs VPS/proxy IPs
- Geographic diversity changes naturally as you move

---

## ⚙️ Configuration

```yaml
# ~/.silentreach/config.yaml
global:
  headless: true           # False for login flows
  default_delay: 2.0       # Seconds between requests
  max_retries: 3
  timeout: 30

rate_limit:
  enabled: true
  default_rpm: 30

notifications:
  enabled: true
  termux_api: true

queue:
  auto_process: true
  max_retries: 3
  retry_delay_minutes: 5

cookies:
  storage_path: ~/.silentreach/cookies/
  auto_refresh: true
  refresh_interval_hours: 12
```

---

## 🐛 Troubleshooting

### Termux:API Not Working
```bash
pkg install termux-api
silentreach notify "test"
```

### nodriver Chrome Error
```bash
pkg install chromium
chromium --version
```

### YouTube/Network Issues
```bash
# DNS check
nslookup youtube.com

# Try with proxy if blocked
export HTTP_PROXY=http://your-proxy:port
```

### Clear Cookies & Re-login
```bash
rm ~/.silentreach/cookies/*.json
silentreach login twitter
```

---

## 📚 Documentation

- **Quick Reference**: `QUICKREF.md`
- **Termux Setup**: `TERMUX.md`
- **CLI Commands**: `CLI.md`
- **Examples**: `examples/`
- **API Docs**: `docs/api/`

---

## 🤝 Contributing

```bash
git clone https://github.com/ykycportal/silentreach.git
cd silentreach
pip install -e ".[dev]"
pytest tests/ -v
```

---

## 📄 License

MIT License — Use responsibly. Stay silent, reach everything.

---

**Built for Android by [y Kycportal](https://github.com/ykycportal)**
