"""
Platform detection utilities for SilentReach.
"""

import os
import platform
import shutil
import subprocess
from typing import Optional


def is_termux() -> bool:
    """
    Detect if running in Termux/Android environment.

    Termux sets TERMUX_VERSION env var and uses /data/data/com.termux as HOME.
    """
    return (
        "TERMUX_VERSION" in os.environ or
        "/data/data/com.termux" in os.environ.get("HOME", "") or
        "android" in platform.system().lower()
    )


def has_termux_x11() -> bool:
    """Check if Termux:X11 is available (not recommended — heavy/unstable)."""
    return os.path.exists("/data/data/com.termux/files/usr/bin/startx11")


def is_ubuntu_vps() -> bool:
    """Detect Ubuntu VPS environment from /etc/os-release."""
    try:
        with open("/etc/os-release") as f:
            content = f.read().lower()
            return "ubuntu" in content
    except (FileNotFoundError, PermissionError):
        return False


def is_linux() -> bool:
    """Detect generic Linux (includes VPS)."""
    return platform.system() == "Linux"


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_macos() -> bool:
    return platform.system() == "Darwin"


def get_platform() -> str:
    """
    Return platform identifier for engine selection.
    
    Returns: 'termux-android' | 'vps-ubuntu' | 'desktop-linux' | 'desktop-macos' | 'desktop-windows'
    """
    if is_termux():
        return "termux-android"
    elif is_ubuntu_vps():
        return "vps-ubuntu"
    elif is_windows():
        return "desktop-windows"
    elif is_macos():
        return "desktop-macos"
    elif is_linux():
        return "desktop-linux"
    return "unknown"


def has_chrome() -> bool:
    """Check if Chrome/Chromium is installed."""
    return get_chrome_path() is not None


def get_chrome_path() -> Optional[str]:
    """Find Chrome/Chromium binary path."""
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


def has_node() -> bool:
    """Check if Node.js/npm is available (needed for bwb-browser-termux)."""
    import shutil
    return shutil.which("node") is not None and shutil.which("npx") is not None


def has_playwright() -> bool:
    """Check if Playwright is installed."""
    try:
        import playwright
        return True
    except ImportError:
        return False


def has_termux_playwright() -> bool:
    """Check if termux-playwright is installed."""
    try:
        import termux_playwright
        return True
    except ImportError:
        return False


def has_nodriver() -> bool:
    """Check if nodriver is installed."""
    try:
        import nodriver
        return True
    except ImportError:
        return False


def get_recommended_engines() -> list:
    """
    Get ordered list of recommended browser engines for current platform.
    
    Returns list of engine names: 'bwb-browser', 'playwright-termux', 'nodriver', 'playwright'
    """
    platform_name = get_platform()
    
    if platform_name == "termux-android":
        engines = []
        if has_node():
            engines.append("bwb-browser")
        if has_termux_playwright():
            engines.append("playwright-termux")
        return engines
    
    elif platform_name == "vps-ubuntu":
        engines = []
        if has_chrome():
            engines.append("nodriver")
        if has_playwright():
            engines.append("playwright")
        return engines
    
    else:  # Desktop platforms
        engines = []
        if has_chrome():
            engines.append("nodriver")
        if has_playwright():
            engines.append("playwright")
        return engines


def get_browser_status() -> dict:
    """Get current browser availability status."""
    return {
        "platform": get_platform(),
        "termux": is_termux(),
        "ubuntu_vps": is_ubuntu_vps(),
        "chrome_installed": has_chrome(),
        "nodriver_installed": has_nodriver(),
        "playwright_installed": has_playwright(),
        "termux_playwright_installed": has_termux_playwright(),
        "node_available": has_node(),
        "recommended_engines": get_recommended_engines(),
    }
