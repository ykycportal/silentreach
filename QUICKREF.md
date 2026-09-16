# SilentReach Quick Reference

## Installation
```bash
pkg install python git chromium yt-dlp termux-api -y
git clone https://github.com/ykycportal/silentreach.git
cd silentreach
pip install -e ".[all]"
silentreach setup
```

## Basic Commands
```bash
# Search
silentreach search "topic" -p reddit,youtube,twitter
silentreach search "topic" -p all --limit 50

# Intelligence report
silentreach intel "topic" --depth full

# Check status
silentreach doctor
```

## Android Features
```bash
# Notifications
silentreach notify "message"

# Schedule jobs
silentreach schedule add name "0 8 * * *" --command "silentreach search 'topic' -p all"
silentreach schedule list
silentreach schedule run name

# Offline queue
silentreach queue add reddit "topic"
silentreach queue show
silentreach queue process

# Web dashboard
silentreach dashboard
# Access at http://localhost:5000

# Presets
silentreach presets
```

## Use Cases
```bash
# Daily monitoring
silentreach schedule add daily 0 8 * * * \
  --command "silentreach search 'dropshipping' -p reddit,youtube"

# Competitor tracking
silentreach schedule add competitor */6 * * * * \
  --command "silentreach search 'shopify stores' -p twitter,reddit"

# Viral content
silentreach queue add youtube "viral products"
silentreach queue add reddit "product launches"
```

## Data Locations
```
~/.silentreach/
├── config.yaml          # Configuration
├── cookies/             # Browser sessions
├── jobs/                # Scheduled jobs
├── queue/               # Offline queue
│   ├── pending/
│   ├── running/
│   ├── completed/
│   └── failed/
├── results/             # Saved searches
└── logs/                # Application logs
```

## Troubleshooting
```bash
# Check Termux:API
which termux-notification

# Clear cache
rm ~/.silentreach/cookies/*.json

# Reinstall
pip install -e ".[all]" --force-reinstall
```
