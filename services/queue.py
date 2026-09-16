#!/usr/bin/env python3
"""
Offline queue system for SilentReach
Queues jobs when offline, syncs when back online
"""

import asyncio
import json
import logging
import time
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("silentreach.queue")


class SilentQueue:
    """Queue management for offline scraping."""
    
    def __init__(self, queue_dir: Optional[Path] = None):
        self.queue_dir = queue_dir or Path.home() / ".silentreach" / "queue"
        self.pending_dir = self.queue_dir / "pending"
        self.running_dir = self.queue_dir / "running"
        self.completed_dir = self.queue_dir / "completed"
        self.failed_dir = self.queue_dir / "failed"
        
        # Create directories
        for d in [self.pending_dir, self.running_dir, self.completed_dir, self.failed_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def add_job(
        self,
        platform: str,
        query: str,
        limit: int = 20,
        priority: int = 0,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Add a job to the queue."""
        job_id = self._generate_id()
        
        job = {
            "id": job_id,
            "platform": platform,
            "query": query,
            "limit": limit,
            "priority": priority,
            "metadata": metadata or {},
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "retries": 0,
            "max_retries": 3,
        }
        
        # Save to pending
        job_path = self.pending_dir / f"{job_id}.json"
        with open(job_path, "w") as f:
            json.dump(job, f, indent=2)
        
        logger.info(f"Added job {job_id} to queue: {platform} - {query}")
        return job_id
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from queue."""
        job_path = self.pending_dir / f"{job_id}.json"
        
        if job_path.exists():
            job_path.unlink()
            logger.info(f"Removed job {job_id} from queue")
            return True
        
        return False
    
    def get_next_job(self) -> Optional[Dict]:
        """Get next job to process (by priority, then creation time)."""
        pending_files = list(self.pending_dir.glob("*.json"))
        
        if not pending_files:
            return None
        
        # Load and sort by priority
        jobs = []
        for job_path in pending_files:
            with open(job_path) as f:
                job = json.load(f)
                jobs.append(job)
        
        # Sort by priority (higher first), then by creation time (older first)
        jobs.sort(key=lambda x: (-x.get("priority", 0), x.get("created_at", "")))
        
        if jobs:
            return jobs[0]
        
        return None
    
    def start_job(self, job_id: str) -> bool:
        """Move job from pending to running."""
        job_path = self.pending_dir / f"{job_id}.json"
        running_path = self.running_dir / f"{job_id}.json"
        
        if not job_path.exists():
            return False
        
        # Move file
        import shutil
        shutil.move(str(job_path), str(running_path))
        
        # Update status
        with open(running_path) as f:
            job = json.load(f)
        
        job["status"] = "running"
        job["started_at"] = datetime.now().isoformat()
        
        with open(running_path, "w") as f:
            json.dump(job, f, indent=2)
        
        logger.info(f"Started job {job_id}")
        return True
    
    def complete_job(self, job_id: str, result: Dict) -> bool:
        """Mark job as completed."""
        running_path = self.running_dir / f"{job_id}.json"
        completed_path = self.completed_dir / f"{job_id}.json"
        
        if not running_path.exists():
            return False
        
        # Load job
        with open(running_path) as f:
            job = json.load(f)
        
        # Update status
        job["status"] = "completed"
        job["completed_at"] = datetime.now().isoformat()
        job["result"] = result
        
        # Save to completed
        with open(completed_path, "w") as f:
            json.dump(job, f, indent=2)
        
        # Remove from running
        running_path.unlink()
        
        logger.info(f"Completed job {job_id}: {len(result.get('data', []))} items")
        return True
    
    def fail_job(self, job_id: str, error: str) -> bool:
        """Mark job as failed."""
        running_path = self.running_dir / f"{job_id}.json"
        failed_path = self.failed_dir / f"{job_id}.json"
        
        if not running_path.exists():
            return False
        
        # Load job
        with open(running_path) as f:
            job = json.load(f)
        
        # Update status
        job["status"] = "failed"
        job["failed_at"] = datetime.now().isoformat()
        job["error"] = error
        job["retries"] = job.get("retries", 0) + 1
        
        # Check if should retry
        if job["retries"] < job.get("max_retries", 3):
            # Move back to pending with delay
            job["status"] = "pending"
            job["next_retry"] = (
                datetime.now().timestamp() + (2 ** job["retries"]) * 60
            )
            
            retry_path = self.pending_dir / f"{job_id}.json"
            with open(retry_path, "w") as f:
                json.dump(job, f, indent=2)
            
            running_path.unlink()
            logger.warning(f"Job {job_id} failed, will retry in {2 ** job['retries']} minutes")
            return True
        else:
            # Max retries exceeded, move to failed
            with open(failed_path, "w") as f:
                json.dump(job, f, indent=2)
            
            running_path.unlink()
            logger.error(f"Job {job_id} failed permanently after {job['retries']} retries")
            return False
    
    def get_stats(self) -> Dict:
        """Get queue statistics."""
        return {
            "pending": len(list(self.pending_dir.glob("*.json"))),
            "running": len(list(self.running_dir.glob("*.json"))),
            "completed": len(list(self.completed_dir.glob("*.json"))),
            "failed": len(list(self.failed_dir.glob("*.json"))),
        }
    
    def clear_completed(self, max_age_hours: int = 24) -> int:
        """Clear completed jobs older than max_age_hours."""
        count = 0
        now = time.time()
        
        for job_path in self.completed_dir.glob("*.json"):
            with open(job_path) as f:
                job = json.load(f)
            
            completed_at = job.get("completed_at", "")
            if completed_at:
                try:
                    completed_time = datetime.fromisoformat(completed_at).timestamp()
                    if now - completed_time > max_age_hours * 3600:
                        job_path.unlink()
                        count += 1
                except:
                    pass
        
        logger.info(f"Cleared {count} completed jobs")
        return count
    
    def clear_failed(self) -> int:
        """Clear all failed jobs."""
        count = 0
        for job_path in self.failed_dir.glob("*.json"):
            job_path.unlink()
            count += 1
        
        logger.info(f"Cleared {count} failed jobs")
        return count
    
    def _generate_id(self) -> str:
        """Generate unique job ID."""
        return f"{int(time.time())}_{hash(time.monotonic()) % 10000:04d}"


def get_queue() -> SilentQueue:
    """Get or create global queue instance."""
    return SilentQueue()


async def sync_when_online(queue: SilentQueue, check_interval: int = 30):
    """
    Monitor network and process queued jobs when online.
    Run this in background.
    """
    import aiohttp
    
    while True:
        try:
            # Check if online
            async with aiohttp.ClientSession() as session:
                async with session.get("https://www.google.com", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        # Online - process queue
                        await _process_queue(queue)
        except:
            # Offline - wait and retry
            pass
        
        await asyncio.sleep(check_interval)


async def _process_queue(queue: SilentQueue):
    """Process pending jobs in queue."""
    job = queue.get_next_job()
    
    if not job:
        return
    
    job_id = job["id"]
    platform = job["platform"]
    query = job["query"]
    limit = job.get("limit", 20)
    
    logger.info(f"Processing queued job: {platform} - {query}")
    
    # Start job
    queue.start_job(job_id)
    
    # Import and run scraper
    try:
        module_name = f"scrapers.{platform}"
        module = __import__(module_name, fromlist=["Scraper"])
        ScraperClass = getattr(module, f"{platform.capitalize()}Scraper")
        
        scraper = ScraperClass()
        result = await scraper.search(query, limit=limit)
        
        # Complete job
        queue.complete_job(job_id, result)
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        queue.fail_job(job_id, str(e))


if __name__ == "__main__":
    # Test queue
    queue = SilentQueue()
    
    print("=== SilentReach Queue Test ===\n")
    
    # Add test jobs
    job1 = queue.add_job("reddit", "dropshipping", limit=10, priority=1)
    job2 = queue.add_job("youtube", "ecommerce", limit=20, priority=2)
    job3 = queue.add_job("twitter", "shopify", limit=15, priority=1)
    
    print(f"Added 3 jobs to queue")
    print(f"Stats: {queue.get_stats()}")
    
    # Get next job
    next_job = queue.get_next_job()
    if next_job:
        print(f"\nNext job: {next_job['platform']} - {next_job['query']} (priority: {next_job['priority']})")
    
    # Complete a job
    if next_job:
        queue.start_job(next_job["id"])
        queue.complete_job(next_job["id"], {"data": [{"test": "data"}]})
        print(f"\nCompleted job {next_job['id']}")
    
    print(f"\nFinal stats: {queue.get_stats()}")
