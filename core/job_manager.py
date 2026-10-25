import enum
from typing import Dict, Optional
from datetime import datetime
from app.engines.schema import SpeechResult
from app.core.logger import jobs_logger

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Job:
    def __init__(self, job_id: str, filename: str):
        self.job_id = job_id
        self.filename = filename
        self.status = JobStatus.PENDING
        self.progress: float = 0.0
        self.created_at = datetime.now()
        self.result: Optional[SpeechResult] = None
        self.error_message: Optional[str] = None

class JobManager:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}

    def create_job(self, job_id: str, filename: str) -> Job:
        job = Job(job_id, filename)
        self._jobs[job_id] = job
        jobs_logger.info(f"Job created: {job_id} for file: {filename}")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def update_progress(self, job_id: str, progress: float, status: JobStatus = JobStatus.PROCESSING):
        if job_id in self._jobs:
            self._jobs[job_id].progress = progress
            self._jobs[job_id].status = status

    def complete_job(self, job_id: str, result: SpeechResult):
        if job_id in self._jobs:
            self._jobs[job_id].result = result
            self._jobs[job_id].status = JobStatus.COMPLETED
            self._jobs[job_id].progress = 100.0
            jobs_logger.info(f"Job completed successfully: {job_id}")

    def fail_job(self, job_id: str, error: str):
        if job_id in self._jobs:
            self._jobs[job_id].error_message = error
            self._jobs[job_id].status = JobStatus.FAILED
            jobs_logger.error(f"Job failed: {job_id} | Error: {error}")

job_manager = JobManager()