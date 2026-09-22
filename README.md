# SilentReach

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Termux](https://img.shields.io/badge/Termux-Optimized-brightgreen)](https://termux.com)
[![Windows](https://img.shields.io/badge/Windows-Supported-0078D6?logo=windows)](https://microsoft.com/windows)
[![macOS](https://img.shields.io/badge/macOS-Supported-333333?logo=apple)](https://apple.com/macos)
[![Linux](https://img.shields.io/badge/Linux-Supported-FCC624?logo=linux)](https://linux.org)

## 🌐 The Most Powerful Intelligence Stack for Marketing Departments

**SilentReach + Semantica = The most powerful combination for marketing departments and marketing agents.**

SilentReach provides the scraping engine (12 platforms, stealth browser, mobile IP advantage). Semantica provides the intelligence layer (entity extraction, knowledge graphs, conflict detection, provenance tracking). Together, they transform raw web data into structured marketing intelligence that humans can read and AI agents can consume.

> **One stack. Infinite intelligence.** Built for Termux/Android — works on Windows, macOS, and Linux too.

---

## 🚀 Quick Start

### Android/Termux (Recommended — One-Click Install)

```bash
# Install everything in one command
bash <(curl -s https://raw.githubusercontent.com/ykycportal/silentreach/main/install.sh)

# Verify installation
silentreach doctor

# Run your first search
silentreach search "dropshipping" -p reddit,youtube --limit 10
```

**Why Termux?** Mobile IPs are harder to block, background jobs run 24/7, and you get push notifications directly to your phone.

### Build Marketing Intelligence (The Power Combo)

```bash
# Install with Semantica for full power
pip install "silentreach[kg]"

# Build a knowledge graph — the most powerful combo for marketing
silentreach kg build "AI marketing tools" -p reddit,linkedin,twitter

# Export for your team and agents
silentreach kg export --format markdown   # For marketing department
silentreach kg export --format json       # For marketing agents
```

**Result:** A complete intelligence report with entities (Shopify, HubSpot, etc.), relations (X uses Y, A vs B), conflicts (sources disagree), and executive recommendations — all automatically generated.

### Windows

```cmd
# Install Python 3.9+ from python.org
# Then open Command Prompt or PowerShell:
git clone https://github.com/ykycportal/silentreach.git
cd silentreach
pip install -e ".[all]"

# Run
silentreach search "dropshipping" -p reddit,youtube --limit 10
```

### macOS

```bash
# Install Homebrew if needed: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.12 git chromium

git clone https://github.com/ykycportal/silentreach.git
cd silentreach
pip install -e ".[all]"

# Run
silentreach search "dropshipping" -p reddit,youtube --limit 10
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip git chromium-browser -y

git clone https://github.com/ykycportal/silentreach.git
cd silentreach
pip install -e ".[all]"

# Run
silentreach search "dropshipping" -p reddit,youtube --limit 10
```

---

## 📱 Termux-Exclusive Features

These features only work on Android/Termux:

|| Feature | Description |
||---------|-------------|
|| **🔔 Telegram Alerts** | Get real-time notifications on your phone via Telegram bot |
|| **⏰ Scheduled Reports** | Daily/weekly automated intelligence reports |
|| **📥 Offline Queue** | Queue searches while on cellular, auto-process when WiFi returns |
|| **🔋 Battery Optimization** | Built-in wake-lock and power management |
|| **📊 Web Dashboard** | Monitor from any browser on your network |

### Setup Telegram Notifications (Termux + Any Device)

```bash
# Get a bot token from @BotFather on Telegram
# Then configure:
silentreach telegram setup --token YOUR_BOT_TOKEN --chat-id YOUR_CHAT_ID

# Test it works:
silentreach telegram test

# Receive daily reports automatically
silentreach schedule add daily
```

### Automated Daily Reports

```bash
# Preset schedules (run automatically)
silentreach schedule add daily       # Every day at 8am
silentreach schedule add weekly      # Every Monday at 9am
silentreach schedule add competitor_daily  # Daily competitor tracking

# Or create custom schedule
silentreach schedule add "my-research" "0 9 * * *" \
  --command "silentreach search 'dropshipping' -p reddit,twitter"

# View and manage
silentreach schedule list
silentreach schedule run daily       # Run now
```

---

## 🎯 What Works Everywhere

All platforms get these features:

```
✓ 12 Platform Scrapers (Reddit, YouTube, Twitter, Instagram, etc.)
✓ 7 Export Formats (JSON, MD, CSV, TXT, PDF, Excel, ODS)
✓ Stealth Browser Automation (nodriver)
✓ Cookie Management & Session Persistence
✓ Rate Limiting & Exponential Backoff
✓ Plugin System for Custom Platforms
✓ Google Sheets Export
✓ Web Dashboard (port 5000)
```

---

## 📦 Supported Platforms

SilentReach supports **11 platforms** with full scraping, stealth features, and cross-platform compatibility:

| Platform | API Method | Browser Fallback | Auth Required | Best For |
|----------|------------|------------------|---------------|----------|
| **Reddit** | rdt-cli + API | ✅ nodriver | Optional | Community sentiment, trends |
| **YouTube** | yt-dlp direct | ❌ N/A | No | Video content analysis |
| **Twitter/X** | twitter-cli + API | ✅ nodriver | Required | Real-time buzz, influencer tracking |
| **Instagram** | Node browser only | ✅ nodriver (headful) | Required | Visual content, influencer marketing |
| **LinkedIn** | Jina Reader + API | ✅ nodriver | Required | B2B insights, professional trends |
| **Facebook** | Browser automation | ✅ nodriver | Required | Group sentiment, ad research, community monitoring |
| **Bilibili** | bili-cli + yt-dlp | ❌ N/A | Optional | Chinese market, Asian trends |
| **V2EX** | agent-reach | ❌ N/A | No | Tech community, developer insights |
| **Xiaohongshu** | Node browser only | ✅ nodriver (headful) | Required | Chinese lifestyle, reviews |
| **RSS Feeds** | feedparser | ❌ N/A | No | News aggregation, curated sources |

### Platform Status Legend

- ✅ **Full Support** — Works on all platforms (Android, Windows, macOS, Linux)
- ⚠️ **Partial Support** — Some features limited on certain platforms
- ❌ **Not Available** — Not applicable for this platform type

### Platform-Specific Notes

**Mobile-Optimized Platforms (Termux):**
- Reddit, Twitter, YouTube — Highest success rate on mobile IPs
- Instagram — Requires headful browser (opens Chrome window)
- Xiaohongshu — Chinese platform, best accessed from Asian IPs

**Desktop-Optimized:**
- LinkedIn — Higher rate limits, needs professional context
- Bilibili — Chinese platform, benefits from regional proxies

### How to Use

```bash
# Search all platforms
silentreach search "dropshipping" -p all

# Specific platforms
silentreach search "AI tools" -p reddit,twitter,youtube

# With exports
silentreach kg build "marketing trends" -p reddit,linkedin,twitter
```

---

## 🔔 Real-Time Alerts & Automation

### Telegram Notifications

Get instant alerts delivered to your Telegram when:
- Scraping jobs complete
- Competitor changes detected
- Daily/weekly reports ready
- Conflicts found in intelligence

```bash
# One-time setup (requires @BotFather token)
silentreach telegram setup --token BOT_TOKEN --chat-id CHAT_ID

# Test the connection
silentreach telegram test

# Send custom alerts
silentreach notify "New competitor alert!" --platform telegram
```

### Scheduled Intelligence Reports

Automate your marketing research with cron-based scheduling:

| Preset | Schedule | What It Does |
|--------|----------|--------------|
| `daily` | 8:00 AM daily | Quick trend scan across Reddit, YouTube, Twitter |
| `weekly` | 9:00 AM Monday | Full intelligence report with deep analysis |
| `competitor_daily` | 7:00 AM daily | Monitor competitors for supplier changes |

```bash
# Activate a preset
silentreach schedule add daily

# Or create custom schedule
silentreach schedule add "hourly-check" "0 * * * *" \
  --command "silentreach search 'new products' -p reddit,twitter"

# Manage your jobs
silentreach schedule list          # See all scheduled jobs
silentreach schedule run daily     # Run immediately
silentreach schedule remove daily  # Cancel schedule
```

### Delivery Options

Reports are sent via:
- **Telegram** — Instant messages with summary
- **Email** — PDF attachments (coming soon)
- **Local Files** — Saved to `~/.silentreach/reports/`

---

## 🧠 Knowledge Graph (KG) Integration

**The most powerful combination for marketing departments and marketing agents.**

SilentReach's scraping power meets Semantica's intelligence layer — creating a complete marketing intelligence pipeline from raw data to actionable insights.

### Why This Combo Wins

| SilentReach Alone | + Semantica |
|-------------------|-------------|
| Raw posts/articles | Structured knowledge graph |
| "Here's what I found" | "Here's what we know, and who said it" |
| No cross-platform correlation | Detects conflicts across Reddit, Twitter, LinkedIn |
| Can't ask complex questions | SPARQL/graph queries over all data |
| One-shot searches | Persistent context you build over time |

**For Marketing Departments:** Get campaign briefs, competitive analysis, and trend reports in minutes, not hours.

**For Marketing Agents:** Get structured JSON bundles with entities, relations, conflicts, and executive summaries ready for automated workflows.

### Quick Start

```bash
# Install KG extras
pip install "silentreach[kg]"

# Build a knowledge graph from a topic
silentreach kg build "AI regulation" -p reddit,linkedin,twitter

# Query your knowledge graph
silentreach kg query --search "AI"

# Find conflicts across sources
silentreach kg conflicts --entity "AI regulation"

# Export for your marketing agents
silentreach kg export --format json --output intelligence.json
```

### Output Formats

| Format | Use Case |
|--------|----------|
| `json` | Agent consumption (default) |
| `markdown` | Human-readable campaign briefs |
| `csv` | Spreadsheet analysis |

### File Structure

All KG data stored locally:
```
~/.silentreach/
├── kg/
│   ├── graphs/        # Saved sessions (JSON)
│   ├── reports/       # Generated reports
│   └── agents/        # Agent-ready bundles
└── config/
    └── kg_settings.yaml
```

---

## 📋 CLI Commands

### Search

```bash
# Basic search
silentreach search "topic" -p reddit,youtube,twitter

# All platforms
silentreach search "topic" -p all --limit 50

# Save to specific format
silentreach search "topic" -p all -f pdf -o report.pdf
silentreach search "topic" -p all -f xlsx -o data.xlsx
silentreach search "topic" -p all -f json -o data.json

# Auto-detect format from extension
silentreach search "topic" -o output.pdf
```

### Intelligence Reports

```bash
# Quick scan (3 platforms)
silentreach intel "topic" --depth quick

# Full analysis (all platforms)
silentreach intel "topic" --depth full
```

### Scheduler (Cross-Platform)

```bash
# Add job
silentreach schedule add my_job "0 8 * * *" \
  --command "silentreach search 'topic' -p all"

# List, run, remove
silentreach schedule list
silentreach schedule run my_job
silentreach schedule remove my_job
```

### Dashboard

```bash
# Start web UI
silentreach dashboard

# Access at http://localhost:5000
```

---

## 📊 Output Formats

SilentReach exports to **7 formats**:

| Format | Extension | Use Case |
|--------|-----------|----------|
| JSON | `.json` | API integration, scripts |
| Markdown | `.md` | Readable reports (default) |
| CSV | `.csv` | Spreadsheet import |
| TXT | `.txt` | Plain text, logs |
| **PDF** | `.pdf` | Email attachments, printing |
| **Excel** | `.xlsx` | Data analysis |
| **ODS** | `.ods` | LibreOffice |

### Example: Send PDF Report via Email

```bash
# Generate report
silentreach search "competitors" -p all -f pdf -o report.pdf

# Email (Linux/macOS/Windows with proper mail setup)
mailto:?subject="Research Report"&body=Check%20attached...&attachment=report.pdf
```

---

## 🔧 Installation Details

### Minimum Requirements

- Python 3.9+
- Git
- Chromium/Chrome browser (for nodriver)

### Dependencies

```bash
# Core (all platforms)
pip install -e ".[all]"

# Extra libraries for full features
pip install reportlab openpyxl odfpy gspread google-auth redis
```

### System Packages (Linux/macOS/Windows)

```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip git chromium-browser

# macOS
brew install python@3.12 git chromium

# Windows
# Download Chrome from google.com/chrome
# Python from python.org
```

---

## 🔒 Stealth Features

- **Fingerprint Randomization**: Rotates User-Agent, viewport, platform
- **Header Rotation**: Realistic browser headers with natural variation
- **Timing Control**: Platform-specific delays
- **Cookie Persistence**: Reuse real browser sessions
- **Rate Limiting**: Exponential backoff on 429s

### Mobile IP Advantage (Termux Only)

Mobile carriers use CGNAT — IPs shared with thousands of users. Much harder to flag as "datacenter" vs VPS/proxy IPs.

---

## 🌐 Plugin System

Extend with custom scrapers:

```bash
# Create template
silentreach plugins create my_platform

# Edit and use
nano ~/.silentreach/plugins/my_platform.py
```

---

## 📁 Data Storage

All data stays local:

```
~/.silentreach/
├── config.yaml
├── cookies/
├── jobs/
├── queue/
├── results/
├── logs/
└── plugins/
```

---

## 🐛 Troubleshooting

### nodriver Chrome Error

```bash
# Linux
sudo apt install chromium-browser

# macOS
brew install --cask chromium

# Windows
# Download Chrome from google.com/chrome
```

### Agent-Reach Issues

```bash
# Reinstall from GitHub (PyPI version is outdated)
pip install "agent-reach @ git+https://github.com/Panniantong/agent-reach.git@v1.5.0"
```

---

## 📚 Documentation

- **Quick Reference**: `QUICKREF.md`
- **Termux Setup**: `TERMUX.md`
- **CLI Commands**: `CLI.md`
- **Architecture**: `ARCHITECTURE.md`
- **Examples**: `examples/`

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

**Built for everyone, optimized for Android** — [y Kycportal](https://github.com/ykycportal)
