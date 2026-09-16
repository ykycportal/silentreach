# SilentReach Architecture

Technical documentation for SilentReach framework.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SilentReach Framework                    │
├─────────────────────────────────────────────────────────────┤
│  CLI Layer (scripts/silentreach.py)                        │
│  ├─ Search/Intel Commands                                   │
│  ├─ Scheduler Management                                    │
│  ├─ Queue Management                                        │
│  ├─ Dashboard Server                                        │
│  └─ Notification Interface                                  │
├─────────────────────────────────────────────────────────────┤
│  Service Layer (services/)                                  │
│  ├─ StealthEngine    — Anti-detection, fingerprint random   │
│  ├─ CookieManager    — Session persistence & refresh        │
│  ├─ NotificationCenter — Termux:API integration             │
│  ├─ Scheduler        — Crontab management                   │
│  ├─ OfflineQueue     — Job queuing & retry logic            │
│  ├─ PluginRegistry   — Custom scraper discovery             │
│  └─ SheetsExporter   — Google Sheets integration            │
├─────────────────────────────────────────────────────────────┤
│  Scraper Layer (scrapers/)                                  │
│  ├─ RedditScraper      — rdt-cli + nodriver fallback        │
│  ├─ YouTubeScraper     — yt-dlp direct                      │
│  ├─ TwitterScraper     — twitter-cli + nodriver fallback    │
│  ├─ InstagramScraper   — nodriver (headful required)        │
│  ├─ LinkedInScraper    — Jina Reader + nodriver             │
│  ├─ FacebookScraper    — nodriver                           │
│  ├─ BilibiliScraper    — bili-cli + yt-dlp                  │
│  ├─ V2EXScraper        — agent-reach                        │
│  ├─ RSSScraper         — feedparser                         │
│  └─ XiaohongshuScraper — nodriver                           │
├─────────────────────────────────────────────────────────────┤
│  Utility Layer (utils/)                                     │
│  ├─ Fingerprint        — Browser fingerprint randomizer     │
│  ├─ Headers            — Realistic header generation        │
│  ├─ Proxies            — Proxy rotation manager             │
│  └─ Logging            — Structured logging                 │
├─────────────────────────────────────────────────────────────┤
│  External Dependencies                                      │
│  ├─ agent-reach        — CLI router for public platforms    │
│  ├─ nodriver           — Undetected browser automation      │
│  ├─ yt-dlp             — YouTube video metadata             │
│  ├─ twitter-cli        — Twitter search (cookie-based)      │
│  ├─ rdt-cli            — Reddit search (cookie-based)       │
│  ├─ bili-cli           — Bilibili search                    │
│  └─ xhs-cli            — Xiaohongshu search                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Search Operation
```
User Command
    ↓
CLI Parser (silentreach.py)
    ↓
Platform Router (determines scraper)
    ↓
Scraper.search(query, limit)
    ↓
┌──────────────────────────────────┐
│  Primary Method                  │
│  (rdt-cli / twitter-cli / yt-dlp)│
└──────────────────────────────────┘
    ↓ Success?
    ├─ Yes → Return results
    └─ No → Fallback
              ↓
        Secondary Method
        (nodriver with cookies)
              ↓
        Return results or error
    ↓
Output Formatter
    ↓
JSON / Markdown / CSV
    ↓
Notification (if enabled)
```

### Offline Queue Flow
```
User Adds Job
    ↓
Queue.add_job()
    ↓
Save to ~/.silentreach/queue/pending/
    ↓
[Wait for network]
    ↓
Queue.poll() detects network
    ↓
Queue.process_next()
    ↓
Move to running/
    ↓
Execute scraper
    ↓
Move to completed/ or failed/
    ↓
Retry if failed (max 3 times)
```

---

## Stealth Engine Details

### Fingerprint Randomization
```python
class StealthEngine:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
        "Mozilla/5.0 (X11; Linux x86_64)...",
        # ... 7 total variants
    ]
    
    def get_random_fingerprint(self):
        return Fingerprint(
            user_agent=random.choice(self.USER_AGENTS),
            accept_language=random.choice(self.LANGUAGES),
            platform=random.choice(self.PLATFORMS),
            viewport_width=random.choice([1366, 1440, 1920]),
            # ... etc
        )
```

### Timing Control
- Platform-specific delays (Reddit: 2-4s, Instagram: 4-6s)
- Randomized within range
- Exponential backoff on 429 responses
- Respects rate limits configured per platform

---

## Cookie Management

### Storage Format
```json
{
  "cookies": {
    "session_id": "...",
    "auth_token": "...",
    // ... all browser cookies
  },
  "saved_at": "2024-09-17T08:00:00Z",
  "metadata": {
    "username": "user_handle",
    "login_method": "browser"
  }
}
```

### Auto-Refresh
- Check cookie age on each use
- Refresh if older than configured interval (default: 12 hours)
- Notify user if refresh fails

---

## Plugin System

### Auto-Discovery
```python
class PluginRegistry:
    PLUGIN_DIRS = [
        Path.home() / ".silentreach" / "plugins",
        Path(__file__).parent.parent / "plugins",
    ]
    
    def discover_plugins(self):
        for plugin_dir in self.plugin_dirs:
            for plugin_file in plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue
                # Import and register
```

### Plugin Template
```python
class MyPlatformScraper(BaseScraper):
    platform = "myplatform"
    stealth_level = "medium"
    auth_required = False
    
    async def search(self, query, limit=20):
        # Implementation
        pass
```

---

## Scheduler Implementation

### Crontab Integration
```bash
# SilentReach adds to system crontab
# Format: minute hour day month weekday command

# Generated entry:
# # SilentReach:daily_monitor
0 8 * * * /data/data/com.termux/files/home/.silentreach/jobs/daily_monitor.sh
```

### Job Script Template
```bash
#!/data/data/com.termux/files/usr/bin/bash
# SilentReach Job: daily_monitor
# Generated: 2024-09-17T08:00:00Z

cd ~/silentreach
silentreach search "topic" -p all >> logs/cron.log 2>&1
```

---

## Notification System

### Termux:API Integration
```python
def notify(title, message, icon="info"):
    subprocess.run([
        "termux-notification",
        "--title", title,
        "--text", message,
        "--icon", ICON_URLS[icon],
    ])
```

### Notification Events
- Search completion
- Job scheduled
- Job failed
- Queue processed
- Dashboard started

---

## Web Dashboard

### Flask Application
```python
class SilentDashboard:
    @app.route('/')
    def index():
        results = self._load_results()
        stats = self._calculate_stats()
        return render_template(DASHBOARD_TEMPLATE, ...)
    
    @app.route('/api/results')
    def api_results():
        return jsonify(self._load_results())
```

### Auto-Refresh
- JavaScript auto-refresh every 30 seconds
- WebSocket support for real-time updates (future)

---

## Security Considerations

### Local Storage Only
- All cookies stored in `~/.silentreach/cookies/`
- Never transmitted to external servers
- Encrypted at rest (future feature)

### No Telemetry
- SilentReach does not phone home
- All data stays on device
- Open source for audit

---

## Performance Characteristics

### Typical Search Times (Termux on Pixel 6)
| Platform | Method | Time |
|----------|--------|------|
| Reddit | rdt-cli | ~2s |
| YouTube | yt-dlp | ~1.5s |
| Twitter | twitter-cli | ~3s |
| Instagram | nodriver | ~5s |
| LinkedIn | Jina Reader | ~2s |

### Memory Usage
- Base: ~50MB
- With nodriver: ~150MB
- Peak during scan: ~300MB

---

## Extending SilentReach

### Adding New Platform
1. Create `scrapers/myplatform.py`
2. Inherit from `BaseScraper`
3. Implement `search()`, `get_item()`, `get_profile()`
4. Register in `scrapers/__init__.py`
5. Add to CLI platform list

### Adding New Service
1. Create `services/myservice.py`
2. Implement service interface
3. Import in `scripts/silentreach.py`
4. Add CLI commands as needed

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_reddit.py -v

# Integration test (requires network)
pytest tests/test_integration.py -v --network
```

---

## Deployment Options

### Termux (Primary)
- Full feature set
- Mobile IP advantage
- Background execution via cron

### Linux Server
- Same codebase
- Use residential proxies for stealth
- Docker support (future)

### Windows/macOS
- Core functionality works
- Some Termux-specific features unavailable
- Use standard cron or task scheduler
