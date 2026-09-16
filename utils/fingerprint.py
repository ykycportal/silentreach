"""
Browser fingerprint utilities.
"""

import random
import platform
from typing import Dict, Tuple


def get_random_user_agent() -> str:
    """Generate a random realistic user agent."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    ]
    return random.choice(user_agents)


def get_random_viewport() -> Tuple[int, int]:
    """Generate a random but realistic viewport size."""
    widths = [1366, 1440, 1536, 1920]
    heights = [768, 900, 1024, 1080]
    return random.choice(widths), random.choice(heights)


def get_random_platform() -> str:
    """Get a random platform string."""
    platforms = ["Windows", "Macintosh", "Linux x86_64"]
    return random.choice(platforms)


def get_random_timezone() -> str:
    """Get a random timezone."""
    timezones = [
        "America/New_York",
        "America/Chicago",
        "America/Los_Angeles",
        "Europe/London",
        "Europe/Berlin",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Australia/Sydney",
    ]
    return random.choice(timezones)
