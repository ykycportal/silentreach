# SilentReach

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Termux](https://img.shields.io/badge/Termux-Optimized-brightgreen)](https://termux.com)
[![Windows](https://img.shields.io/badge/Windows-Supported-0078D6?logo=windows)](https://microsoft.com/windows)
[![macOS](https://img.shields.io/badge/macOS-Supported-333333?logo=apple)](https://apple.com/macos)
[![Linux](https://img.shields.io/badge/Linux-Supported-FCC624?logo=linux)](https://linux.org)

## 🌐 Cross-Platform Web Intelligence Framework

**SilentReach** combines **agent-reach** (public APIs) + **nodriver** (undetected browser automation) into a complete web scraping and research framework.

Built for **Termux/Android** with mobile-first features — but runs identically on **Windows, macOS, and Linux**.

> One codebase. Seven export formats. Twelve platforms. Zero cloud required.

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

| Feature | Description |
|---------|-------------|
| **🔔 Push Notifications** | Get alerts on your phone when scans complete (via Termux:API) |
| **⏰ Persistent Background Jobs** | Cron jobs survive terminal close and reboots |
| **📥 Offline Queue** | Queue searches while on cellular, auto-process when WiFi returns |
| **🔋 Battery Optimization** | Built-in wake-lock and power management |
| **📊 Web Dashboard** | Monitor from any browser on your network |

### Enable Notifications (Termux Only)

```bash
pkg install termux-api
silentreach notify "Hello from SilentReach!"
```

### Schedule Background Jobs (Termux Only)

```bash
# Add daily job (survives terminal close)
silentreach schedule add daily_monitor "0 8 * * *" \
  --command "silentreach search 'dropshipping' -p reddit,youtube"

# Jobs run automatically even when terminal is closed
silentreach schedule list
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

## 📦 Platform Support Matrix

| Feature | Android/Termux | Windows | macOS | Linux |
|---------|---------------|---------|-------|-------|
| **Core Scrapers** | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **Output Formats** | ✅ 7 formats | ✅ 7 formats | ✅ 7 formats | ✅ 7 formats |
| **Stealth Browser** | ✅ nodriver | ✅ nodriver | ✅ nodriver | ✅ nodriver |
| **Notifications** | ✅ Termux:API | ❌ Skip | ❌ Skip | ❌ Skip |
| **Background Cron** | ✅ Native | ⚠️ Task Scheduler | ⚠️ launchd | ✅ cron/systemd |
| **Offline Queue** | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **Web Dashboard** | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **One-Click Install** | ✅ `install.sh` | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual |

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
