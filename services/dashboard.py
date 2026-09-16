#!/usr/bin/env python3
"""
Web dashboard for SilentReach
Access results via browser on your phone
"""

import logging
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger("silentreach.dashboard")

try:
    from flask import Flask, render_template_string, jsonify, request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


# HTML Template for Dashboard
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SilentReach Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 20px;
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card { 
            background: #1e293b;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value { font-size: 2em; font-weight: bold; color: #667eea; }
        .stat-label { color: #94a3b8; font-size: 0.9em; }
        .results { 
            background: #1e293b;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .results h2 { margin-bottom: 15px; color: #667eea; }
        .result-item { 
            background: #0f172a;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .result-title { font-weight: bold; color: #f1f5f9; }
        .result-meta { color: #94a3b8; font-size: 0.85em; margin-top: 5px; }
        .platform-badge { 
            display: inline-block;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.75em;
            font-weight: bold;
            margin-right: 10px;
        }
        .reddit { background: #ff4500; }
        .youtube { background: #ff0000; }
        .twitter { background: #1da1f2; }
        .linkedin { background: #0077b5; }
        .loading { text-align: center; padding: 50px; color: #94a3b8; }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
        }
        .refresh-btn:hover { background: #5568d3; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔇 SilentReach</h1>
        <p>Mobile Web Intelligence Dashboard</p>
    </div>
    
    <div style="text-align: center; margin-bottom: 20px;">
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
    </div>
    
    <div class="stats">
        {% for stat in stats %}
        <div class="stat-card">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
        </div>
        {% endfor %}
    </div>
    
    {% for platform, data in results.items() %}
    <div class="results">
        <h2>{{ platform|capitalize }} ({{ data.total }} results)</h2>
        {% for item in data.items %}
        <div class="result-item">
            <span class="platform-badge {{ platform }}">{{ platform }}</span>
            <span class="result-title">{{ item.title or item.text or item.name or 'No title' }}</span>
            <div class="result-meta">
                {% if item.author %}👤 {{ item.author }} | {% endif %}
                {% if item.score %}⭐ {{ item.score }} | {% endif %}
                {% if item.created_at %}📅 {{ item.created_at }}{% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
    {% endfor %}
    
    {% if not results %}
    <div class="loading">
        <p>No results yet. Run a search to see results here.</p>
        <p style="margin-top: 10px; font-size: 0.9em;">
            Command: <code>silentreach search "topic" -p all</code>
        </p>
    </div>
    {% endif %}
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
'''


class SilentDashboard:
    """Web dashboard for SilentReach."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5000, results_dir: Optional[Path] = None):
        self.host = host
        self.port = port
        self.results_dir = results_dir or Path.home() / ".silentreach" / "results"
        self.app = None
        self._start_server()
    
    def _start_server(self):
        """Start the Flask server."""
        if not HAS_FLASK:
            logger.error("Flask not installed. Run: pip install flask")
            return
        
        self.app = Flask(__name__)
        
        @self.app.route('/')
        def index():
            return self._render_dashboard()
        
        @self.app.route('/api/results')
        def api_results():
            return jsonify(self._load_results())
        
        @self.app.route('/api/stats')
        def api_stats():
            return jsonify(self._calculate_stats())
        
        logger.info(f"Dashboard starting on http://{self.host}:{self.port}")
    
    def _render_dashboard(self) -> str:
        """Render the dashboard HTML."""
        results = self._load_results()
        stats = self._calculate_stats()
        
        return render_template_string(
            DASHBOARD_TEMPLATE,
            results=results,
            stats=stats
        )
    
    def _load_results(self) -> Dict:
        """Load recent results from JSON files."""
        results = {}
        
        if not self.results_dir.exists():
            return results
        
        # Load recent results (last 10 per platform)
        for platform_dir in self.results_dir.iterdir():
            if not platform_dir.is_dir():
                continue
            
            platform = platform_dir.name
            results[platform] = {"items": [], "total": 0}
            
            json_files = sorted(
                platform_dir.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:10]
            
            for json_file in json_files:
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                    
                    items = data.get("results", [])
                    results[platform]["items"].extend(items)
                    results[platform]["total"] += len(items)
                    
                except:
                    pass
        
        # Limit items per platform
        for platform in results:
            results[platform]["items"] = results[platform]["items"][:50]
        
        return results
    
    def _calculate_stats(self) -> List[Dict]:
        """Calculate dashboard statistics."""
        results = self._load_results()
        
        total_items = sum(r["total"] for r in results.values())
        platforms = len(results)
        
        # Count recent results (last 24 hours)
        recent_count = 0
        for platform, data in results.items():
            for item in data["items"]:
                created = item.get("created_at", item.get("timestamp", ""))
                if created:
                    try:
                        created_time = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        if (datetime.now() - created_time).total_seconds() < 86400:
                            recent_count += 1
                    except:
                        pass
        
        return [
            {"label": "Total Results", "value": total_items},
            {"label": "Platforms", "value": platforms},
            {"label": "Last 24h", "value": recent_count},
            {"label": "Status", "value": "🟢 Online"},
        ]
    
    def run(self, block: bool = True):
        """Run the dashboard server."""
        if self.app:
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
            )
        else:
            logger.error("Dashboard not initialized")


def start_dashboard(port: int = 5000, background: bool = False):
    """Start dashboard in background or foreground."""
    import threading
    
    dashboard = SilentDashboard(port=port)
    
    if background:
        thread = threading.Thread(target=dashboard.run, daemon=True)
        thread.start()
        logger.info(f"Dashboard started in background on port {port}")
        return dashboard
    else:
        dashboard.run()
        return dashboard


if __name__ == "__main__":
    print("=== SilentReach Dashboard ===\n")
    print("Starting dashboard...")
    print("Open http://localhost:5000 in your browser")
    print("\nPress Ctrl+C to stop\n")
    
    dashboard = start_dashboard(port=5000)
