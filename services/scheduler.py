#!/usr/bin/env python3
"""
Background scheduler for SilentReach
Uses system crontab for reliable scheduling
"""

import subprocess
import logging
import re
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("silentreach.scheduler")

CRONTAB_HEADER = """# SilentReach Scheduler - Generated on {}
# DO NOT EDIT - Use 'silentreach schedule' commands instead
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class SilentScheduler:
    """Manage background scraping jobs via crontab."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".silentreach" / "scheduler.yaml"
        self.jobs_dir = Path.home() / ".silentreach" / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
    
    def list_jobs(self) -> List[Dict]:
        """List all scheduled jobs."""
        jobs = []
        
        # Read from crontab
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("# SilentReach") or "silentreach" in line:
                        jobs.append(self._parse_cron_line(line))
        except:
            pass
        
        # Read from config file
        if self.config_path.exists():
            import yaml
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
                for job_name, job_config in config.get("jobs", {}).items():
                    job_config["name"] = job_name
                    if job_config not in jobs:
                        jobs.append(job_config)
        
        return jobs
    
    def add_job(
        self,
        name: str,
        cron_expr: str,
        command: str,
        description: str = "",
        enabled: bool = True,
    ) -> bool:
        """Add a new scheduled job."""
        # Validate cron expression
        if not self._validate_cron(cron_expr):
            logger.error(f"Invalid cron expression: {cron_expr}")
            return False
        
        # Create job script
        job_script = self._create_job_script(name, command)
        
        # Add to crontab
        cron_line = f"{cron_expr} {job_script}"
        
        try:
            # Get existing crontab
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True
            )
            
            existing = result.stdout if result.returncode == 0 else ""
            
            # Remove old version of this job if exists
            lines = existing.split("\n")
            lines = [l for l in lines if f"silentreach:{name}" not in l]
            
            # Add new job
            lines.append(f"# SilentReach:{name}")
            lines.append(cron_line)
            lines.append("")
            
            # Write back
            new_crontab = "\n".join(lines)
            proc = subprocess.Popen(
                ["crontab", "-"],
                stdin=subprocess.PIPE,
                text=True
            )
            proc.communicate(input=new_crontab)
            
            # Save to config
            self._save_job_config(name, cron_expr, command, description, enabled)
            
            logger.info(f"Added job: {name} ({cron_expr})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add job: {e}")
            return False
    
    def remove_job(self, name: str) -> bool:
        """Remove a scheduled job."""
        try:
            # Get existing crontab
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                
                # Remove job lines
                filtered = []
                skip_next = False
                for line in lines:
                    if f"SilentReach:{name}" in line:
                        skip_next = True
                        continue
                    if skip_next:
                        skip_next = False
                        continue
                    filtered.append(line)
                
                # Write back
                new_crontab = "\n".join(filtered)
                proc = subprocess.Popen(
                    ["crontab", "-"],
                    stdin=subprocess.PIPE,
                    text=True
                )
                proc.communicate(input=new_crontab)
            
            # Remove config
            self._remove_job_config(name)
            
            logger.info(f"Removed job: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove job: {e}")
            return False
    
    def run_now(self, name: str) -> bool:
        """Run a job immediately."""
        jobs = self.list_jobs()
        
        for job in jobs:
            if job.get("name") == name:
                command = job.get("command", "")
                logger.info(f"Running job '{name}' now: {command}")
                
                # Run in background
                subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                
                return True
        
        logger.error(f"Job not found: {name}")
        return False
    
    def status(self) -> Dict:
        """Get scheduler status."""
        import shutil
        
        has_cron = shutil.which("crontab") is not None
        has_job = len(self.list_jobs()) > 0
        
        return {
            "enabled": has_cron,
            "jobs_count": len(self.list_jobs()),
            "jobs": self.list_jobs(),
            "last_run": self._get_last_run(),
        }
    
    def _parse_cron_line(self, line: str) -> Optional[Dict]:
        """Parse a crontab line into job config."""
        # Match: minute hour day month weekday command
        match = re.match(
            r"(\d+|\*)\s+(\d+|\*)\s+(\d+|\*)\s+(\d+|\*)\s+(\d+|\*)\s+(.+)",
            line
        )
        
        if not match:
            return None
        
        cron_expr = f"{match.group(1)} {match.group(2)} {match.group(3)} {match.group(4)} {match.group(5)}"
        command = match.group(6).strip()
        
        # Extract job name from comment
        name = "unknown"
        comment_match = re.search(r"SilentReach:(\w+)", line)
        if comment_match:
            name = comment_match.group(1)
        
        return {
            "name": name,
            "cron": cron_expr,
            "command": command,
            "enabled": True,
        }
    
    def _validate_cron(self, expr: str) -> bool:
        """Validate cron expression."""
        parts = expr.split()
        
        if len(parts) != 5:
            return False
        
        # Basic validation
        for i, part in enumerate(parts):
            if part == "*":
                continue
            
            # Check for numbers and ranges
            if not re.match(r"^(\d+(-\d+)?(,\d+(-\d+)?)*)?$", part):
                return False
        
        return True
    
    def _create_job_script(self, name: str, command: str) -> str:
        """Create a wrapper script for a job."""
        script_path = self.jobs_dir / f"{name}.sh"
        
        script_content = f"""#!/data/data/com.termux/files/usr/bin/bash
# SilentReach Job: {name}
# Generated: {datetime.now().isoformat()}

cd ~/silentreach
{command}
"""
        
        with open(script_path, "w") as f:
            f.write(script_content)
        
        subprocess.run(["chmod", "+x", script_path])
        
        return f"/data/data/com.termux/files/home/.silentreach/jobs/{name}.sh"
    
    def _save_job_config(
        self,
        name: str,
        cron_expr: str,
        command: str,
        description: str,
        enabled: bool,
    ):
        """Save job configuration."""
        import yaml
        
        config = {}
        if self.config_path.exists():
            with open(self.config_path) as f:
                config = yaml.safe_load(f) or {}
        
        if "jobs" not in config:
            config["jobs"] = {}
        
        config["jobs"][name] = {
            "cron": cron_expr,
            "command": command,
            "description": description,
            "enabled": enabled,
            "created": datetime.now().isoformat(),
        }
        
        with open(self.config_path, "w") as f:
            yaml.dump(config, f)
    
    def _remove_job_config(self, name: str):
        """Remove job configuration."""
        if not self.config_path.exists():
            return
        
        import yaml
        with open(self.config_path) as f:
            config = yaml.safe_load(f) or {}
        
        if "jobs" in config and name in config["jobs"]:
            del config["jobs"][name]
        
        with open(self.config_path, "w") as f:
            yaml.dump(config, f)
    
    def _get_last_run(self) -> Optional[str]:
        """Get last successful run time."""
        log_file = Path.home() / ".silentreach" / "logs" / "scheduler.log"
        
        if not log_file.exists():
            return None
        
        try:
            with open(log_file) as f:
                lines = f.readlines()
                if lines:
                    return lines[-1].strip()
        except:
            pass
        
        return None


def get_scheduler() -> SilentScheduler:
    """Get or create global scheduler instance."""
    return SilentScheduler()


def preset_commands():
    """Return preset command templates."""
    return {
        "dropshipping_daily": {
            "name": "dropshipping_daily",
            "cron": "0 8 * * *",
            "command": "silentreach search 'dropshipping' -p reddit,youtube,twitter --limit 20",
            "description": "Daily dropshipping monitoring",
        },
        "ecommerce_weekly": {
            "name": "ecommerce_weekly",
            "cron": "0 9 * * 1",
            "command": "silentreach search 'ecommerce trends' -p all --depth full",
            "description": "Weekly ecommerce trends report",
        },
        "competitor_monitor": {
            "name": "competitor_monitor",
            "cron": "0 */6 * * *",
            "command": "silentreach search 'shopify stores' -p reddit,twitter --limit 30",
            "description": "Competitor monitoring every 6 hours",
        },
        "viral_content": {
            "name": "viral_content",
            "cron": "0 10,16 * * *",
            "command": "silentreach search 'viral products' -p youtube,tiktok --limit 50",
            "description": "Viral content discovery twice daily",
        },
    }


if __name__ == "__main__":
    # Test scheduler
    scheduler = SilentScheduler()
    
    print("=== SilentReach Scheduler Test ===\n")
    
    # List jobs
    jobs = scheduler.list_jobs()
    print(f"Current jobs: {len(jobs)}")
    for job in jobs:
        print(f"  - {job.get('name')}: {job.get('cron')}")
    
    # Add test job
    print("\nAdding test job...")
    success = scheduler.add_job(
        name="test_job",
        cron_expr="*/5 * * * *",  # Every 5 minutes
        command="silentreach search 'test' -p reddit --limit 5",
        description="Test job every 5 minutes"
    )
    
    if success:
        print("✅ Job added successfully")
        jobs = scheduler.list_jobs()
        print(f"Total jobs: {len(jobs)}")
    else:
        print("❌ Failed to add job")
    
    print("\nTo remove: silentreach schedule remove test_job")
