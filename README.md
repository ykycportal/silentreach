# SilentReach
# The ultimate undetected web intelligence framework — agent-reach + nodriver combined

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Termux](https://img.shields.io/badge/Termux-Ready-brightgreen)](https://termux.com)

## Overview
SilentReach combines agent-reach (public API access) with nodriver (undetected browser automation) for complete web intelligence without getting flagged. Invisible. Silent. Reach everywhere.

**Built for Termux/Android** — run your entire scraping pipeline from your phone. No VPS needed.

## Why Termux?
- **Run anywhere**: Your phone is your server
- **Always on**: Keep scripts running 24/7
- **Stealth**: Mobile IPs are less likely to be flagged as datacenter
- **Portable**: Clone the repo, install deps, start scraping

## Android-First Features ✨

| Feature | Command | Description |
|---------|---------|-------------|
| 🔔 **Notifications** | `silentreach notify "message"` | Push notifications via Termux:API |
| ⏰ **Scheduler** | `silentreach schedule add daily 0 8 * * * --command '...'` | Cron-based background jobs |
| 📥 **Offline Queue** | `silentreach queue add reddit "topic"` | Queue jobs when offline, sync when back |
| 🌐 **Web Dashboard** | `silentreach dashboard` | Monitor results from phone browser |
| 📊 **Sheets Export** | `export.py` | Push results to Google Sheets |
| 🔌 **Plugins** | `plugins.py` | Auto-discover custom scrapers |
| 📱 **One-Click Install** | `bash install.sh` | Automated Termux setup |
| 🎯 **Presets** | `silentreach presets` | Ready-to-use monitoring templates |

### Example Workflow

```bash
# 1. Install (one-time)
bash <(curl -s https://raw.githubusercontent.com/ykycportal/silentreach/main/install.sh)

# 2. Enable notifications
pkg install termux-api
silentreach notify "SilentReach ready!"

# 3. Schedule daily monitoring
silentreach schedule add dropshipping_daily 0 8 * * * \
  --command "silentreach search 'dropshipping' -p reddit,youtube,twitter"

# 4. Queue searches when offline
silentreach queue add reddit "ecommerce trends"
silentreach queue add youtube "product reviews"

# 5. Monitor via web dashboard
silentreach dashboard &
# Open http://localhost:5000 in your browser
```

### Background Operations

```bash
# Run scheduler in background (stays active after terminal closes)
termux-wake-lock
nohup silentreach schedule run daily_monitor > /dev/null 2>&1 &

# Or use cron (persistent across reboots)
crontab -e
# Add: 0 8 * * * cd ~/silentreach && silentreach search "topic" -p all >> logs/cron.log
```

## What's Included
- **Public Scrapers**: Reddit, YouTube, Bilibili, V2EX, RSS, Jina Reader
- **Authenticated Scrapers**: Twitter/X, Instagram, LinkedIn, Facebook, Xiaohongshu
- **Stealth Engine**: Fingerprint randomization, header rotation, timing control
- **Cookie Manager**: Persistent sessions, auto-refresh, secure storage
- **Output Formats**: JSON, Markdown, CSV, native Python objects

## Quick Start

```bash
# Install
pip install -e ".[all]"

# Run doctor check
python scripts/silentreach.py doctor

# Search a topic across platforms
python scripts/silentreach.py run --platform reddit --query "dropshipping"

# Full intelligence report
python scripts/silentreach.py intel --topic "AI tools" --depth full
```

## Platforms

| Platform | Agent-Reach | Nodriver | Stealth | Auth Required |
|----------|-------------|----------|---------|---------------|
| Reddit | ✅ | ✅ | High | Cookie/Session |
| YouTube | ✅ | ✅ | High | None |
| Twitter/X | ✅ | ✅ | Very High | Cookie |
| Instagram | ❌ | ✅ | Very High | Cookie/Session |
| LinkedIn | ✅ | ✅ | High | Cookie |
| Facebook | ❌ | ✅ | Very High | Cookie/Session |
| Bilibili | ✅ | ✅ | Medium | None |
| V2EX | ✅ | ✅ | High | None |
| RSS | ✅ | ✅ | Medium | None |
| Xiaohongshu | ✅ | ✅ | High | Cookie/Session |

## Architecture

```
silentreach/
├── scrapers/           # Platform-specific implementations
│   ├── base.py         # Abstract scraper interface
│   ├── reddit.py       # Reddit scraper (public + auth)
│   ├── youtube.py      # YouTube scraper
│   ├── twitter.py      # Twitter/X scraper
│   ├── instagram.py    # Instagram scraper
│   ├── linkedin.py     # LinkedIn scraper
│   ├── facebook.py     # Facebook scraper
│   └── bilibili.py     # Bilibili scraper
├── services/           # Core services
│   ├── stealth_engine.py  # Anti-detection logic
│   ├── cookie_mgr.py      # Session management
│   ├── rate_limiter.py    # Request throttling
│   └── output_fmt.py      # Response formatting
├── utils/              # Utilities
│   ├── fingerprint.py     # Browser fingerprint randomization
│   ├── headers.py         # Realistic header generation
│   ├── proxies.py         # Proxy rotation
│   └── logging.py         # Structured logging
├── config/             # Configuration
│   ├── settings.yaml      # Main config
│   ├── platforms/         # Per-platform settings
│   └── secrets.env        # API keys (gitignored)
├── scripts/            # CLI tools
│   ├── silentreach.py     # Main CLI
│   └── batch_run.py       # Batch operations
├── examples/           # Usage examples
└── tests/              # Test suite
```

## Stealth Features

### 1. Multi-Layer Anti-Detection
- **Browser Fingerprint Randomization**: Vary canvas, WebGL, audio context
- **Header Rotation**: Randomize User-Agent, Accept-Language, etc.
- **Timing Randomization**: Human-like delays between actions
- **Cookie Persistence**: Reuse real browser sessions
- **Proxy Rotation**: Residential proxies for sensitive targets

### 2. Platform-Specific Evasion
- **Twitter**: Uses OpenCLI/browser session reuse
- **Reddit**: Primary via OpenCLI, fallback to rdt-cli
- **Instagram**: Desktop-only via OpenCLI (real browser session)
- **LinkedIn**: Public pages via Jina, authenticated via browser

### 3. Rate Limiting & Scheduling
- Exponential backoff on 429s
- Configurable delay between requests
- Respectful cron-style scheduling

## Advanced Usage

### Custom Scraper Plugin
```python
from silentreach import BaseScraper, run_async

class MyScraper(BaseScraper):
    platform = "myplatform"
    
    async def search(self, query: str, limit: int = 20):
        # Your implementation
        return results

# Register and use
run_async(MyScraper().search("topic"))
```

### Multi-Platform Intel Report
```python
from silentreach import IntelReporter

report = IntelReporter()
report.add("reddit", "dropshipping", limit=50)
report.add("twitter", "dropshipping", limit=30)
report.add("youtube", "dropshipping tutorial", limit=20)

results = await report.run()
report.to_markdown("report.md")
```

## Installation

```bash
# Clone and install
git clone https://github.com/ykycportal/silentreach.git
cd silentreach
pip install -e ".[all]"

# Configure
python scripts/silentreach.py setup
```

## License
MIT - Use responsibly. Stay silent, reach everything.
