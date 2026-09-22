# Nodriver / Anti-Bot Browser Automation

## What is nodriver?
nodriver (formerly undetected-chromedriver) is the gold standard for undetected browser automation in Python. It communicates directly with Chrome/Chromium via raw CDP (Chrome DevTools Protocol) — no ChromeDriver binary, no Selenium, no WebDriver artifacts.

### Why it matters for scraping
Modern anti-bot systems (Cloudflare, DataDome, PerimeterX, Akamai) detect automation through:
- `navigator.webdriver = true` — nodriver never sets this
- CDP handshake patterns — nodriver bypasses Playwright/Selenium shims
- TLS fingerprints — nodriver uses real Chrome's TLS signature
- Behavioral signals — fresh profiles, no automation flags

### 2026 Benchmark Results
Ian Patterson's benchmark (651 verdicts across 31 targets):
- **nodriver**: 28 OK, 0 blocked — only tool with zero hard blocks
- Playwright: multiple blocks
- Camoufox: middle of the pack
- Patchright: similar to Playwright

Source: https://ianlpaterson.com/blog/anti-detect-browser-benchmark-patchright-nodriver-curl-cffi/

## Installation

```bash
# Core package
pip install nodriver

# Requires: Chrome or Chromium installed on system
# nodriver auto-detects browser path
```

## Key Features
- Async-first API
- Fresh profile per session (auto-cleanup)
- Cookie save/load from JSON file
- Direct CDP communication
- No chromedriver binary dependency
- Works with Chrome, Chromium, Edge, Brave

## Usage Pattern

```python
import nodriver as uc

async def main():
    browser = await uc.start(headless=True)
    page = await browser.get('https://example.com')
    await page.sleep(2)
    content = await page.get_content()
    await browser.stop()

uc.loop().run_until_complete(main())
```

---

# Platform-Aware Browser Engine Selection

SilentReach uses a tiered browser engine system that auto-selects the best engine for the current platform.

## Engine Tiers

| Tier | Engine | Platform | Size | Use Case |
|------|--------|----------|------|----------|
| 1 | bwb-browser-termux | Android/Termux | ~2MB | Primary on mobile, hooks existing Chrome |
| 2 | termux-playwright | Android/Termux | ~200MB | Form-fill, CAPTCHA handling |
| 3 | nodriver | VPS/Desktop | ~5MB | Stealth champion, zero blocks |
| 4 | playwright | Any | ~250MB | Fallback with full feature set |

## Platform Detection

```python
from services.platform_detect import get_platform, is_termux, is_ubuntu_vps

platform = get_platform()
# Returns: 'termux-android' | 'vps-ubuntu' | 'desktop-linux' | 'desktop-macos' | 'desktop-windows'
```

## Automatic Selection Logic

```
Is running on Termux/Android?
├── YES → Try bwb-browser-termux first
│         └── Need form-fill? → Escalate to termux-playwright
└── NO → Is Ubuntu VPS or Desktop?
         └── Try nodriver first (stealth champion)
                 └── Fallback: playwright
```

## Installation Commands by Platform

### Termux/Android
```bash
# Option 1: bwb-browser-termux (recommended, lightweight)
npm install -g bwb-browser-termux
# Requires: pkg install chromium (from x11-repo)

# Option 2: termux-playwright (full feature set)
pkg install x11-repo
pkg install chromium
pip install termux-playwright && termux-playwright-install
```

### Ubuntu VPS
```bash
# Option 1: nodriver (recommended, stealth champion)
apt install chromium-browser
pip install nodriver

# Option 2: Playwright
apt install chromium-browser
pip install playwright
playwright install chromium
```

### Desktop (Linux/macOS/Windows)
```bash
# Option 1: nodriver
# Chrome/Chromium must be installed
pip install nodriver

# Option 2: Playwright
pip install playwright
playwright install chromium
```

## BrowserManager API

```python
from services.browser_engine import BrowserManager, create_browser, browse

# Async context manager (recommended)
async with BrowserManager() as browser:
    page = await browser.get_page("https://example.com")
    # Use page object...
    # Auto-cleanup on exit

# Or manual lifecycle
browser = await create_browser()
try:
    page = await browser.get_page(url)
    result = await page.get_content()
finally:
    await browser.close()

# Quick one-liner
result = await browse("https://example.com")
# Returns: {"url": "...", "title": "...", "engine": "bwb-browser", "success": True}
```

## Why This Architecture

1. **bwb-browser-termux on Android**: Hooks into phone's existing Chrome, no 200MB download, survives OOM killer
2. **termux-playwright when needed**: Full Playwright API for complex form-filling and interactions
3. **nodriver on VPS**: Zero CDP leaks, 0/31 blocked in benchmarks, pure stealth
4. **Playwright fallback**: Universal compatibility when other engines fail

## Doctor Output

```
🌐 bwb-browser-termux: available      ← Termux primary
🌐 termux-playwright: not installed
🌐 nodriver: not installed
🎯 Recommended Engine: bwb-browser
```

On VPS:
```
🌐 bwb-browser-termux: N/A (non-Termux)
🌐 termux-playwright: not installed
🌐 nodriver: installed            ← VPS primary
✅ Chrome/Chromium: found
🎯 Recommended Engine: nodriver
```

## Integration with SilentReach Scrapers

The `BaseScraper` class now has `_get_browser()` and `_close_browser()` helpers:

```python
class FacebookScraper:
    async def search(self, query, limit=20):
        browser_handle = await self._get_browser()
        try:
            page = await browser_handle["browser"].get(url)
            # ... scraping logic ...
        finally:
            await self._close_browser(browser_handle)
```

Engine selection happens automatically based on platform and availability.
