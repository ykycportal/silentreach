#!/usr/bin/env python3
"""
Notification system for SilentReach
Uses Termux:API for push notifications
"""

import subprocess
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger("silentreach.notifications")

# Notification icons
ICON_URLS = {
    "info": "https://raw.githubusercontent.com/termux/termux-app/master/app/src/main/res/mipmap-hdpi/ic_launcher.png",
    "success": "https://raw.githubusercontent.com/termux/termux-app/master/app/src/main/res/mipmap-hdpi/ic_stat_notification.png",
    "error": "https://raw.githubusercontent.com/termux/termux-app/master/app/src/main/res/mipmap-hdpi/ic_launcher_red.png",
}


def notify(
    title: str,
    message: str,
    icon: str = "info",
    priority: str = "high",
    ticker: Optional[str] = None,
    when: Optional[int] = None,
) -> bool:
    """
    Send notification using Termux:API.
    
    Args:
        title: Notification title
        message: Notification body
        icon: Icon type (info, success, error)
        priority: Notification priority (low, normal, high, max)
        ticker: Scrolling text in status bar
        when: Timestamp in milliseconds since epoch
    
    Returns:
        True if notification sent successfully
    """
    try:
        # Check if termux-notification is available
        probe = subprocess.run(
            ["which", "termux-notification"],
            capture_output=True,
            text=True
        )
        
        if probe.returncode != 0:
            logger.warning("Termux:API not installed. Run: pkg install termux-api")
            return False
        
        # Build command
        cmd = ["termux-notification"]
        
        if title:
            cmd.extend(["--title", title])
        
        if message:
            cmd.extend(["--text", message[:1000]])  # Limit message length
        
        if icon in ICON_URLS:
            cmd.extend(["--icon", ICON_URLS[icon]])
        
        if priority:
            cmd.extend(["--priority", priority])
        
        if ticker:
            cmd.extend(["--ticker", ticker])
        
        if when:
            cmd.extend(["--when", str(when)])
        
        # Send notification
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.debug(f"Notification sent: {title}")
            return True
        else:
            logger.error(f"Notification failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Notification error: {e}")
        return False


def notify_success(title: str, message: str):
    """Send success notification."""
    return notify(title, message, icon="success")


def notify_error(title: str, message: str):
    """Send error notification."""
    return notify(title, message, icon="error")


def notify_info(title: str, message: str):
    """Send info notification."""
    return notify(title, message, icon="info")


class NotificationCenter:
    """Manages notification settings and queue."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".silentreach" / "notifications.yaml"
        self.enabled = self._load_config()
        self.queue = []
    
    def _load_config(self) -> bool:
        """Load notification configuration."""
        try:
            import yaml
            if self.config_path.exists():
                with open(self.config_path) as f:
                    config = yaml.safe_load(f)
                    return config.get("enabled", True)
        except:
            pass
        return True
    
    def enable(self):
        """Enable notifications."""
        self.enabled = True
        self._save_config()
        notify_info("SilentReach", "Notifications enabled")
    
    def disable(self):
        """Disable notifications."""
        self.enabled = False
        self._save_config()
        notify_info("SilentReach", "Notifications disabled")
    
    def _save_config(self):
        """Save notification configuration."""
        try:
            import yaml
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                yaml.dump({"enabled": self.enabled}, f)
        except:
            pass
    
    def send(self, title: str, message: str, icon: str = "info"):
        """Send notification if enabled."""
        if not self.enabled:
            return False
        return notify(title, message, icon=icon)
    
    def on_complete(self, platform: str, count: int, query: str):
        """Send completion notification."""
        if count > 0:
            self.send(
                f"🔍 {platform.capitalize()} Complete",
                f"Found {count} results for '{query}'",
                icon="success"
            )
        else:
            self.send(
                f"⚠️ No Results",
                f"Found 0 results for '{query}' on {platform}",
                icon="error"
            )
    
    def on_error(self, platform: str, error: str, query: str):
        """Send error notification."""
        self.send(
            f"❌ {platform.capitalize()} Error",
            f"Failed to scrape {query}: {error[:100]}",
            icon="error"
        )
    
    def on_schedule(self, job_name: str, cron_expr: str):
        """Send schedule confirmation."""
        self.send(
            "⏰ Scheduler Updated",
            f"Added cron job '{job_name}': {cron_expr}",
            icon="info"
        )
    
    def on_download(self, file_path: str, size_mb: float):
        """Send download complete notification."""
        self.send(
            "📥 Download Complete",
            f"Saved {size_mb:.1f}MB to {file_path}",
            icon="success"
        )


# Global notification center instance
_notification_center = None


def get_notification_center() -> NotificationCenter:
    """Get or create global notification center."""
    global _notification_center
    if _notification_center is None:
        _notification_center = NotificationCenter()
    return _notification_center


def notify_complete(platform: str, count: int, query: str):
    """Convenience function for completion notifications."""
    return get_notification_center().on_complete(platform, count, query)


def notify_error(platform: str, error: str, query: str):
    """Convenience function for error notifications."""
    return get_notification_center().on_error(platform, error, query)


def check_termux_api() -> dict:
    """Check if Termux:API is properly installed."""
    import shutil
    
    checks = {
        "termux-notification": shutil.which("termux-notification") is not None,
        "termux-wake-lock": shutil.which("termux-wake-lock") is not None,
        "termux-toast": shutil.which("termux-toast") is not None,
        "termux-vibrate": shutil.which("termux-vibrate") is not None,
    }
    
    all_available = all(checks.values())
    
    result = {
        "available": all_available,
        "components": checks,
        "recommendation": ""
    }
    
    if not all_available:
        missing = [k for k, v in checks.items() if not v]
        result["recommendation"] = f"Install missing components: pkg install termux-api"
    
    return result


if __name__ == "__main__":
    # Test notifications
    print("Testing SilentReach notifications...")
    
    api_status = check_termux_api()
    print(f"Termux:API status: {api_status['available']}")
    if api_status['recommendation']:
        print(f"Recommendation: {api_status['recommendation']}")
    
    # Test notifications
    notify_info("SilentReach Test", "Hello from SilentReach!")
    notify_success("Test Success", "This is a success notification")
    notify_error("Test Error", "This is an error notification")
    
    print("Notifications sent. Check your phone!")
