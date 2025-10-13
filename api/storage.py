"""
Job storage and management
Handles in-memory storage of jobs and results with TTL
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from threading import Lock
from models import JobStatus
from config import settings


class JobStorage:
    """
    In-memory job storage with TTL management

    For production, replace with Redis or database
    """

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def create_job(self, job_id: str, filename: str, file_path: str,
                   parsing_mode: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new parsing job"""
        with self._lock:
            job_data = {
                "job_id": job_id,
                "status": JobStatus.PENDING,
                "filename": filename,
                "file_path": file_path,
                "parsing_mode": parsing_mode,
                "options": options,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "completed_at": None,
                "error_message": None,
                "progress_percent": 0
            }
            self._jobs[job_id] = job_data
            return job_data

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        with self._lock:
            return self._jobs.get(job_id)

    def update_job_status(self, job_id: str, status: JobStatus,
                         progress_percent: Optional[int] = None,
                         error_message: Optional[str] = None):
        """Update job status"""
        with self._lock:
            if job_id not in self._jobs:
                return

            self._jobs[job_id]["status"] = status
            self._jobs[job_id]["updated_at"] = datetime.utcnow()

            if progress_percent is not None:
                self._jobs[job_id]["progress_percent"] = progress_percent

            if error_message is not None:
                self._jobs[job_id]["error_message"] = error_message

            if status == JobStatus.COMPLETED or status == JobStatus.FAILED:
                self._jobs[job_id]["completed_at"] = datetime.utcnow()

    def store_result(self, job_id: str, result_data: Dict[str, Any]):
        """Store parsing result"""
        with self._lock:
            result_data["stored_at"] = datetime.utcnow()
            result_data["expires_at"] = datetime.utcnow() + timedelta(
                seconds=settings.RESULTS_TTL_SECONDS
            )
            self._results[job_id] = result_data

    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get parsing result if not expired"""
        with self._lock:
            if job_id not in self._results:
                return None

            result = self._results[job_id]

            # Check if expired
            if datetime.utcnow() > result["expires_at"]:
                del self._results[job_id]
                return None

            return result

    def delete_result(self, job_id: str):
        """Delete result"""
        with self._lock:
            if job_id in self._results:
                del self._results[job_id]

    def cleanup_expired_results(self):
        """Clean up expired results"""
        with self._lock:
            now = datetime.utcnow()
            expired_ids = [
                job_id for job_id, result in self._results.items()
                if now > result["expires_at"]
            ]
            for job_id in expired_ids:
                del self._results[job_id]

    def get_all_jobs(self, status: Optional[JobStatus] = None) -> list:
        """Get all jobs, optionally filtered by status"""
        with self._lock:
            jobs = list(self._jobs.values())
            if status:
                jobs = [j for j in jobs if j["status"] == status]
            return jobs

    def count_jobs_by_status(self, status: JobStatus) -> int:
        """Count jobs with specific status"""
        with self._lock:
            return sum(1 for job in self._jobs.values() if job["status"] == status)


# Global storage instance
job_storage = JobStorage()
