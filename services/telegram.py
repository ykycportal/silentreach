#!/usr/bin/env python3
"""
Telegram notification service for SilentReach
"""

import asyncio
import logging
import aiohttp
from typing import Optional, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger("silentreach.telegram")


class TelegramNotifier:
    """Send notifications via Telegram Bot API."""
    
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or self._load_config("telegram_token")
        self.chat_id = chat_id or self._load_config("telegram_chat_id")
        self.api_url = f"https://api.telegram.org/bot{self.token}" if self.token else None
    
    def _load_config(self, key: str) -> Optional[str]:
        """Load config from file or environment."""
        import os
        # Check environment first
        env_val = os.getenv(f"SILENTREACH_{key.upper()}")
        if env_val:
            return env_val
        
        # Check config file
        config_path = Path.home() / ".silentreach" / "config.yaml"
        if config_path.exists():
            try:
                import yaml
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                    return config.get("telegram", {}).get(key)
            except:
                pass
        return None
    
    async def send_message(self, message: str, parse_mode: str = "HTML", 
                          disable_notification: bool = False) -> bool:
        """Send a text message to Telegram."""
        if not self.token or not self.chat_id:
            logger.warning("Telegram not configured. Set telegram_token and telegram_chat_id in config.")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                    "disable_notification": disable_notification,
                }
                
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("ok", False)
                    else:
                        logger.error(f"Telegram API error: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """Send a photo with caption."""
        if not self.token or not self.chat_id:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendPhoto"
                with open(photo_path, "rb") as f:
                    files = {"photo": f}
                    data = {"chat_id": self.chat_id, "caption": caption}
                    async with session.post(url, data=data, files=files, 
                                          timeout=aiohttp.ClientTimeout(total=60)) as resp:
                        if resp.status == 200:
                            return True
                        logger.error(f"Telegram photo upload failed: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"Failed to send Telegram photo: {e}")
            return False
    
    async def send_document(self, doc_path: str, filename: str = None) -> bool:
        """Send a document (PDF, etc.)."""
        if not self.token or not self.chat_id:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendDocument"
                with open(doc_path, "rb") as f:
                    files = {"document": f}
                    data = {
                        "chat_id": self.chat_id,
                        "caption": f"📊 SilentReach Report: {filename or doc_path}"
                    }
                    async with session.post(url, data=data, files=files,
                                          timeout=aiohttp.ClientTimeout(total=60)) as resp:
                        if resp.status == 200:
                            return True
                        logger.error(f"Telegram document upload failed: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"Failed to send Telegram document: {e}")
            return False
    
    async def send_alert(self, title: str, message: str, level: str = "info") -> bool:
        """Send an alert with emoji based on level."""
        emojis = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
        }
        emoji = emojis.get(level, "📢")
        
        formatted_msg = f"""{emoji} <b>{title}</b>

{message}

<i>— SilentReach</i>"""
        
        return await self.send_message(formatted_msg)
    
    async def send_daily_report(self, report_data: Dict[str, Any]) -> bool:
        """Send a formatted daily intelligence report."""
        lines = [
            "🌅 <b>Daily Intelligence Report</b>",
            f"📅 <b>Date:</b> {report_data.get('date', 'N/A')}",
            "",
            "🔍 <b>Scraping Summary</b>",
        ]
        
        # Platform results
        for platform, count in report_data.get("platform_results", {}).items():
            status = "✅" if count > 0 else "❌"
            lines.append(f"{status} {platform.capitalize()}: {count} results")
        
        lines.append("")
        
        # Key insights
        if report_data.get("key_insights"):
            lines.append("💡 <b>Key Insights</b>")
            for insight in report_data["key_insights"][:5]:
                lines.append(f"• {insight}")
        
        # Competitor updates
        if report_data.get("competitor_updates"):
            lines.append("")
            lines.append("🏢 <b>Competitor Updates</b>")
            for comp in report_data["competitor_updates"][:3]:
                lines.append(f"• {comp['name']}: {comp['change']}")
        
        lines.append("")
        lines.append(f"📊 <b>Confidence:</b> {report_data.get('overall_confidence', 'N/A')}")
        lines.append("<i>— SilentReach Daily Report</i>")
        
        return await self.send_message("\n".join(lines))
    
    async def send_weekly_summary(self, summary: Dict[str, Any]) -> bool:
        """Send a weekly intelligence summary."""
        lines = [
            "📈 <b>Weekly Intelligence Summary</b>",
            f"📅 <b>Period:</b> {summary.get('week_start')} - {summary.get('week_end')}",
            "",
            "🎯 <b>Top Competitors Tracked</b>",
        ]
        
        for comp in summary.get("top_competitors", [])[:5]:
            lines.append(f"• {comp['name']}: {comp.get('supplier_count', 0)} suppliers, "
                        f"{comp.get('mention_count', 0)} mentions")
        
        lines.append("")
        lines.append("🔗 <b>Supply Chain Insights</b>")
        for insight in summary.get("supply_chain_insights", [])[:3]:
            lines.append(f"• {insight}")
        
        lines.append("")
        lines.append("📊 <b>Report Stats</b>")
        lines.append(f"• Platforms monitored: {summary.get('platforms_monitored', 0)}")
        lines.append(f"• Total insights: {summary.get('total_insights', 0)}")
        lines.append(f"• Conflicts detected: {summary.get('conflicts_detected', 0)}")
        
        lines.append("")
        lines.append("<i>— SilentReach Weekly Report</i>")
        
        return await self.send_message("\n".join(lines))
    
    async def send_report_file(self, file_path: str, report_type: str = "report") -> bool:
        """Send a report file via Telegram."""
        if not Path(file_path).exists():
            logger.error(f"Report file not found: {file_path}")
            return False
        
        # Determine file type
        ext = Path(file_path).suffix.lower()
        
        if ext == ".pdf":
            return await self.send_document(file_path, f"PDF Report: {report_type}")
        elif ext in [".md", ".txt"]:
            # Read content and send as message
            with open(file_path) as f:
                content = f.read()
            # Truncate if too long
            if len(content) > 4000:
                content = content[:4000] + "\n\n...[truncated]"
            return await self.send_message(
                f"📄 <b>{report_type.title()} Report</b>\n\n" + content,
                parse_mode="Markdown"
            )
        else:
            return await self.send_document(file_path, f"{report_type.title()} Report")


# Singleton instance
_telegram_instance = None


def get_telegram_notifier() -> TelegramNotifier:
    """Get or create Telegram notifier instance."""
    global _telegram_instance
    if _telegram_instance is None:
        _telegram_instance = TelegramNotifier()
    return _telegram_instance


async def notify_telegram(message: str, level: str = "info") -> bool:
    """Convenience function to send a Telegram notification."""
    notifier = get_telegram_notifier()
    return await notifier.send_alert("SilentReach", message, level)
