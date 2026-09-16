# SilentReach CLI Reference

Complete command reference for SilentReach.

---

## Setup & Health

```bash
# Interactive setup wizard
silentreach setup

# Check system status and dependencies
silentreach doctor

# View configuration
silentreach config show
```

---

## Search Commands

### Basic Search
```bash
# Search a topic
silentreach search "dropshipping" -p reddit

# Search multiple platforms
silentreach search "AI tools" -p reddit,youtube,twitter

# Search all platforms
silentreach search "topic" -p all

# Limit results
silentreach search "products" -p reddit --limit 50
```

### Output Options

SilentReach supports **7 export formats**:

| Flag | Format | Use Case |
|------|--------|----------|
| `-f json` | JSON | API integration, scripts |
| `-f md` | Markdown | Readable reports (default) |
| `-f csv` | CSV | Spreadsheet import |
| `-f txt` | TXT | Plain text output |
| `-f pdf` | PDF | Email attachments, printing |
| `-f xlsx` | Excel | Data analysis in Excel |
| `-f ods` | ODS | LibreOffice spreadsheets |

```bash
# JSON output (structured data)
silentreach search "topic" -p all -f json

# Markdown report (human-readable)
silentreach search "topic" -p all -f markdown

# CSV for spreadsheet import
silentreach search "topic" -p all -f csv -o data.csv

# PDF for email/print
silentreach search "topic" -p all -f pdf -o report.pdf

# Excel for analysis
silentreach search "topic" -p all -f xlsx -o analysis.xlsx

# LibreOffice format
silentreach search "topic" -p all -f ods -o report.ods

# Auto-detect from file extension
silentreach search "topic" -o results.pdf
```

### Advanced Search
```bash
# Deep search (more results, slower)
silentreach search "topic" -p all --depth deep

# Quick search (fewer results, faster)
silentreach search "topic" -p reddit --depth quick

# Specific limit per platform
silentreach search "topic" -p reddit,youtube --limit 100
```

---

## Intelligence Reports

```bash
# Quick intel (3 platforms, fast)
silentreach intel "topic" --depth quick

# Full intel (6 platforms, thorough)
silentreach intel "topic" --depth full

# Save report
silentreach intel "topic" --depth full -o intel_report.md
```

---

## Authentication

```bash
# Login to Twitter/X
silentreach login twitter

# Login to Instagram
silentreach login instagram

# Check saved sessions
silentreach doctor  # Shows which platforms have cookies
```

---

## Scheduler

### List Jobs
```bash
silentreach schedule list
```

### Add Job
```bash
# Basic syntax
silentreach schedule add <name> <cron> --command "<cmd>"

# Examples
silentreach schedule add daily_monitor "0 8 * * *" \
  --command "silentreach search 'dropshipping' -p reddit,youtube"

silentreach schedule add hourly_check "0 * * * *" \
  --command "silentreach search 'ecommerce trends' -p twitter" \
  --description "Hourly market monitoring"

silentreach schedule add weekly_report "0 9 * * 1" \
  --command "silentreach intel 'AI tools' --depth full" \
  --description "Weekly intelligence report"
```

### Cron Syntax
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6, Sunday = 0)
│ │ │ │ │
* * * * *
```

### Common Patterns
```bash
# Every minute
* * * * *

# Every hour
0 * * * *

# Every 6 hours
0 */6 * * *

# Daily at 8 AM
0 8 * * *

# Weekly on Monday at 9 AM
0 9 * * 1

# Monthly on 1st at midnight
0 0 1 * *
```

### Manage Jobs
```bash
# Remove a job
silentreach schedule remove daily_monitor

# Run a job immediately
silentreach schedule run daily_monitor
```

---

## Notifications

```bash
# Send test notification
silentreach notify "Hello from SilentReach!"

# Send with custom title
silentreach notify --title "Custom Title" "Message body"

# Check Termux:API status
silentreach doctor  # Shows if termux-notification is available
```

---

## Offline Queue

### Add to Queue
```bash
# Basic queue add
silentreach queue add <platform> <query>

# Examples
silentreach queue add reddit "dropshipping tips"
silentreach queue add youtube "ecommerce tutorial"
silentreach queue add twitter "shopify stores"

# With priority (higher = processed first)
silentreach queue add reddit "urgent topic" --priority 10
silentreach queue add youtube "normal topic" --priority 5
```

### Queue Management
```bash
# View queue status
silentreach queue show

# Process next job
silentreach queue process

# Clear completed jobs (older than 24h)
silentreach queue clean --completed

# Clear all failed jobs
silentreach queue clean --failed
```

---

## Web Dashboard

```bash
# Start dashboard (default port 5000)
silentreach dashboard

# Custom port
silentreach dashboard --port 8080

# Run in background
silentreach dashboard --background

# Access the dashboard
# On phone: http://localhost:5000
# From computer: http://<phone-ip>:5000
```

---

## Presets

```bash
# View available preset templates
silentreach presets

# Output:
# 📋 Dropshipping Daily
#    Cron: 0 8 * * *
#    Command: silentreach search 'dropshipping' -p reddit,youtube,twitter
#    Description: Daily dropshipping market monitoring
#
# 📋 Ecommerce Weekly
#    Cron: 0 9 * * 1
#    Command: silentreach intel 'ecommerce trends' --depth full
#    Description: Weekly ecommerce intelligence report
#
# 📋 Competitor Monitor
#    Cron: 0 */6 * * *
#    Command: silentreach search 'shopify stores' -p reddit,twitter
#    Description: Track competitor activity every 6 hours
#
# 📋 Viral Content
#    Cron: 0 10,16 * * *
#    Command: silentreach search 'viral products' -p youtube,tiktok
#    Description: Viral content discovery twice daily
```

---

## Configuration

```bash
# View current config
silentreach config show

# Edit config file
nano ~/.silentreach/config.yaml
```

### Config File Location
```
~/.silentreach/config.yaml
```

### Example Configuration
```yaml
global:
  headless: true
  default_delay: 2.0
  max_retries: 3
  timeout: 30

logging:
  level: INFO
  file: logs/silentreach.log

rate_limit:
  enabled: true
  default_rpm: 30

notifications:
  enabled: true
  on_complete: true
  on_error: true

queue:
  auto_process: false
  max_retries: 3

platforms:
  reddit:
    stealth_level: high
  twitter:
    stealth_level: very_high
```

---

## Platform-Specific Options

### Reddit
```bash
# Search Reddit
silentreach search "topic" -p reddit

# Get specific post
silentreach get reddit <post_id>
```

### YouTube
```bash
# Search YouTube
silentreach search "topic" -p youtube

# Get video info
silentreach get youtube <video_id>
```

### Twitter/X
```bash
# Search tweets
silentreach search "topic" -p twitter

# Get specific tweet
silentreach get twitter <tweet_id>

# Get timeline
silentreach get twitter --username <username>
```

### Instagram
```bash
# Search posts
silentreach search "topic" -p instagram

# Get profile
silentreach get instagram --username <username>
```

---

## Batch Operations

```bash
# Search multiple topics
for topic in "dropshipping" "ecommerce" "shopify"; do
    silentreach search "$topic" -p reddit,youtube -o "results_$topic.json"
done

# Search across time periods
for day in $(seq -w 1 7); do
    silentreach search "topic_$day" -p reddit --limit 10 -o "daily/$day.json"
done
```

---

## Python API

```python
import asyncio
from scrapers.reddit import RedditScraper
from scrapers.youtube import YouTubeScraper
from services.notifications import notify_success
from services.scheduler import get_scheduler

async def research():
    results = {}
    
    reddit = RedditScraper()
    results["reddit"] = await reddit.search("dropshipping", limit=20)
    
    youtube = YouTubeScraper()
    results["youtube"] = await youtube.search("dropshipping tutorial", limit=20)
    
    notify_success("Research Complete", f"Found {sum(len(r.get('posts', r.get('videos', []))) for r in results.values())} results")
    
    return results

asyncio.run(research())
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Missing dependencies |
| 3 | Network error |
| 4 | Auth error (cookies invalid) |
| 5 | Rate limited |

---

## Help

```bash
# Show all commands
silentreach --help

# Show command help
silentreach search --help
silentreach schedule --help
silentreach queue --help
```
