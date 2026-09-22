"""
SilentReach Browser Engine — Tiered Platform Detection

Tier 1: bwb-browser-termux (Android/Termux primary — hooks existing Chrome)
Tier 2: Playwright + termux-playwright (Android form-fill capability)
Tier 3: nodriver + system Chrome (Ubuntu VPS / desktop)
"""

import asyncio
import logging
import os
import shutil
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


def is_termux() -> bool:
    """Detect if running in Termux/Android environment."""
    return (
        "TERMUX_VERSION" in os.environ or
        "/data/data/com.termux" in os.environ.get("HOME", "") or
        os.uname().release.startswith("4.") and "Android" in os.uname().version
    )


def is_ubuntu_vps() -> bool:
    """Detect Ubuntu VPS environment."""
    try:
        with open("/etc/os-release") as f:
            content = f.read()
            return "Ubuntu" in content
    except (FileNotFoundError, PermissionError):
        return False


def get_chrome_path() -> Optional[str]:
    """Find Chrome/Chromium binary on system."""
    candidates = [
        "chromium-browser",
        "chromium",
        "google-chrome",
        "google-chrome-stable",
        "chrome",
    ]
    for cmd in candidates:
        path = shutil.which(cmd)
        if path:
            return path
    return None


class BrowserManager:
    """Unified browser manager with platform-aware engine selection."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.headless = self.config.get("headless", True)
        self.proxy = self.config.get("proxy")
        self.platform = self._detect_platform()
        self.engine = None
        self._ctx = None
        self._browser = None
        self._proc = None

    def _detect_platform(self) -> str:
        """Detect current platform and return engine priority list."""
        if is_ubuntu_vps():
            return "vps-ubuntu"
        elif is_termux():
            return "termux-android"
        else:
            # Desktop Linux/macOS/Windows
            return "desktop"

    @property
    def available_engines(self) -> list:
        """Get ordered list of available engines for this platform."""
        if self.platform == "termux-android":
            return ["bwb-browser", "playwright-termux"]
        elif self.platform == "vps-ubuntu":
            chrome = get_chrome_path()
            if chrome:
                return ["nodriver"]
            return []
        else:
            # Desktop — try nodriver first, then playwright
            engines = []
            if get_chrome_path():
                engines.append("nodriver")
            engines.append("playwright")
            return engines

    async def start(self) -> bool:
        """Start the best available browser engine."""
        for engine_name in self.available_engines:
            try:
                if engine_name == "bwb-browser":
                    success = await self._start_bwb()
                elif engine_name == "playwright-termux":
                    success = await self._start_playwright_termux()
                elif engine_name == "nodriver":
                    success = await self._start_nodriver()
                elif engine_name == "playwright":
                    success = await self._start_playwright()
                else:
                    continue

                if success:
                    logger.info(f"[{self.platform}] Using engine: {engine_name}")
                    self.engine = engine_name
                    return True
            except Exception as e:
                logger.debug(f"Engine {engine_name} failed: {e}")
                continue

        raise RuntimeError(
            f"No browser engine available for {self.platform}. "
            f"Try: pip install termux-playwright (Android) or "
            f"apt install chromium (VPS)"
        )

    async def _start_bwb(self) -> bool:
        """Start bwb-browser-termux (Android primary)."""
        # Check if npx/node available
        if not shutil.which("npx"):
            return False

        cmd = [
            "npx", "bwb-browser-termux",
            "--headless", str(self.headless).lower(),
        ]
        if self.proxy:
            cmd.extend(["--proxy", self.proxy])

        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for CDP to be ready
        await asyncio.sleep(3)

        # Verify connection
        try:
            import urllib.request
            resp = urllib.request.urlopen(
                "http://localhost:9222/json/version", timeout=5
            )
            if resp.status == 200:
                return True
        except Exception:
            pass

        # Cleanup on failure
        self._proc.terminate()
        return False

    async def _start_playwright_termux(self) -> bool:
        """Start Playwright via termux-playwright (Android form-fill)."""
        try:
            from termux_playwright import async_playwright_termux, launch
            import nest_asyncio
            nest_asyncio.apply()

            self._ctx = await async_playwright_termux().start()
            self._browser = await launch(
                self._ctx,
                headless=self.headless,
                proxy=self.proxy,
            )
            return True
        except ImportError:
            return False
        except Exception:
            return False

    async def _start_nodriver(self) -> bool:
        """Start nodriver with system Chrome (VPS/desktop)."""
        try:
            import nodriver as uc
            proxy_args = {"proxy": self.proxy} if self.proxy else {}
            self._browser = await uc.start(
                headless=self.headless,
                **proxy_args
            )
            return True
        except ImportError:
            return False
        except Exception:
            return False

    async def _start_playwright(self) -> bool:
        """Start Playwright with system Chrome (desktop fallback)."""
        try:
            from playwright.async_api import async_playwright
            self._ctx = await async_playwright().start()
            self._browser = await self._ctx.chromium.launch(
                headless=self.headless,
                channel="chrome" if get_chrome_path() else None,
            )
            return True
        except ImportError:
            return False
        except Exception:
            return False

    async def get_page(self, url: str) -> Any:
        """Navigate to URL and return page/tab handle."""
        if self.engine == "bwb-browser":
            return await self._bwb_goto(url)
        elif self.engine == "playwright-termux":
            page = await self._browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            return page
        elif self.engine == "nodriver":
            return await self._browser.get(url)
        elif self.engine == "playwright":
            page = await self._browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            return page

    async def _bwb_goto(self, url: str) -> str:
        """Use bwb CLI for navigation."""
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                ["npx", "bwb-browser-termux", "browser_goto", url],
                capture_output=True,
                text=True,
                timeout=30000
            )
        )
        return result.stdout

    async def close(self):
        """Cleanup browser resources."""
        try:
            if self.engine == "playwright-termux" and self._browser:
                await self._browser.close()
                if self._ctx:
                    await self._ctx.stop()
            elif self.engine == "nodriver" and self._browser:
                await self._browser.stop()
            elif self.engine == "playwright" and self._browser:
                await self._browser.close()
                if self._ctx:
                    await self._ctx.stop()
            elif self.engine == "bwb-browser" and self._proc:
                self._proc.terminate()
                self._proc.wait(timeout=5)
        except Exception as e:
            logger.warning(f"Browser cleanup error: {e}")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()


# Convenience functions
async def create_browser(config: Optional[Dict] = None) -> BrowserManager:
    """Create and start browser manager."""
    mgr = BrowserManager(config)
    await mgr.start()
    return mgr


async def browse(url: str, config: Optional[Dict] = None) -> Dict[str, Any]:
    """Quick browse helper."""
    mgr = await create_browser(config)
    try:
        page = await mgr.get_page(url)
        title = await page.title() if hasattr(page, 'title') else "N/A"
        return {
            "url": url,
            "title": title,
            "platform": mgr.platform,
            "engine": mgr.engine,
            "success": True
        }
    finally:
        await mgr.close()
