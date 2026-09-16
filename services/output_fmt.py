"""
Output formatters for SilentReach.
Supports JSON, Markdown, CSV, and native formats.
"""

import json
import csv
import io
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Formats scraper results into various output formats."""
    
    @staticmethod
    def to_json(data: Dict, pretty: bool = True) -> str:
        """Convert data to JSON string."""
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)
    
    @staticmethod
    def to_markdown(data: Dict, title: str = "Results") -> str:
        """Convert data to Markdown format."""
        lines = [
            f"# {title}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    lines.append(f"## {key.capitalize()} ({len(value)} items)")
                    lines.append("")
                    
                    for i, item in enumerate(value[:50], 1):
                        if isinstance(item, dict):
                            # Get first few fields
                            preview = ", ".join(str(v) for v in list(item.values())[:3])
                            lines.append(f"{i}. {preview}")
                        else:
                            lines.append(f"{i}. {item}")
                    
                    lines.append("")
                else:
                    lines.append(f"**{key.capitalize()}**: {value}")
                    lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_csv(data: List[Dict], filename: str = None) -> str:
        """Convert data to CSV format."""
        if not data:
            return ""
        
        # Get all unique keys
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        keys = sorted(all_keys)
        
        # Write CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=keys, extrasaction='ignore')
        writer.writeheader()
        
        for item in data:
            if isinstance(item, dict):
                # Convert values to strings
                row = {k: str(v) if v is not None else "" for k, v in item.items()}
                writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        # Save to file if filename provided
        if filename:
            with open(filename, "w", newline="") as f:
                f.write(csv_content)
            logger.info(f"CSV saved to {filename}")
        
        return csv_content
    
    @staticmethod
    def to_text(data: List[Dict], max_length: int = 1000) -> str:
        """Convert data to plain text."""
        texts = []
        
        for item in data:
            if isinstance(item, dict):
                # Combine relevant fields
                text_parts = []
                for key in ["text", "content", "title", "name", "description"]:
                    if key in item and item[key]:
                        text_parts.append(str(item[key]))
                
                if text_parts:
                    texts.append(" ".join(text_parts)[:max_length])
            else:
                texts.append(str(item)[:max_length])
        
        return "\n\n".join(texts)
    
    @staticmethod
    def save_to_file(data: Any, filename: str, format: str = "auto") -> str:
        """
        Save data to file with automatic format detection.
        
        Returns:
            Path to saved file
        """
        path = filename if filename.endswith(".json") or filename.endswith(".md") or filename.endswith(".csv") else f"{filename}.json"
        
        fmt = format if format != "auto" else path.split(".")[-1]
        
        if fmt == "json":
            content = OutputFormatter.to_json(data)
        elif fmt == "md":
            content = OutputFormatter.to_markdown(data)
        elif fmt == "csv":
            content = OutputFormatter.to_csv(data)
        else:
            content = OutputFormatter.to_json(data)
        
        with open(path, "w") as f:
            f.write(content)
        
        logger.info(f"Data saved to {path}")
        return path
