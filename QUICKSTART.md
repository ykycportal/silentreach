# SilentReach — Quick Start

## Install (Pick Your Platform)

### Android / Termux
```bash
bash <(curl -s https://raw.githubusercontent.com/ykycportal/silentreach/main/install.sh)
silentreach doctor
```

### Windows
```powershell
git clone https://github.com/ykycportal/silentreach.git
cd silentreach
pip install -e ".[all]"
```

### macOS / Linux
```bash
brew install python git chromium  # macOS
# OR: sudo apt install python3 git chromium-browser  # Linux
git clone https://github.com/ykycportal/silentreach.git
cd silentreach
pip install -e ".[all]"
```

---

## Run Your First Search

```bash
# Cross-platform — same command everywhere
silentreach search "dropshipping" -p reddit,youtube --limit 10

# Save as PDF (email-ready)
silentreach search "products" -p all -f pdf -o report.pdf

# Save as Excel (data analysis)
silentreach search "trends" -p reddit,youtube,twitter -f xlsx -o data.xlsx
```

---

## What You Get

- **12 platforms**: Reddit, YouTube, Twitter/X, Instagram, LinkedIn, Facebook, Bilibili, V2EX, RSS, Xiaohongshu, Google Search, Any Website
- **7 export formats**: JSON, Markdown, CSV, TXT, PDF, Excel (.xlsx), LibreOffice (.ods)
- **Stealth**: Mobile-quality IPs, fingerprint randomization, realistic timing
- **Offline queue**: Queue searches, process when online
- **Web dashboard**: Monitor from any browser at http://localhost:5000

---

## Termux Extras (Android Only)

```bash
# Push notifications to your phone
pkg install termux-api
silentreach notify "Scan complete!"

# Background jobs that survive reboots
silentreach schedule add daily "0 8 * * *" --command "silentreach search 'topic' -p all"
```

---

GitHub: https://github.com/ykycportal/silentreach
