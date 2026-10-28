import enum
from datetime import datetime
from typing import Dict, Optional
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
        self.job_id, self.filename = job_id, filename
        self.status = JobStatus.PENDING
        self.progress = 0.0
        self.stage = "در صف پردازش"
        self.created_at = datetime.now()
        self.result: Optional[SpeechResult] = None
        self.error_message: Optional[str] = None

class JobManager:
    def __init__(self): self._jobs: Dict[str, Job] = {}
    def create_job(self, job_id: str, filename: str) -> Job:
        job = Job(job_id, filename); self._jobs[job_id] = job
        jobs_logger.info("Job created: %s", job_id); return job
    def get_job(self, job_id: str) -> Optional[Job]: return self._jobs.get(job_id)
    def update_progress(self, job_id: str, progress: float, status: JobStatus = JobStatus.PROCESSING, stage: str = None):
        if job_id in self._jobs:
            job = self._jobs[job_id]; job.progress = max(0.0, min(99.0, float(progress))); job.status = status
            if stage: job.stage = stage
    def complete_job(self, job_id: str, result: SpeechResult):
        if job_id in self._jobs:
            job = self._jobs[job_id]; job.result = result; job.status = JobStatus.COMPLETED
            job.progress = 100.0; job.stage = "پردازش کامل شد"; jobs_logger.info("Job completed: %s", job_id)
    def fail_job(self, job_id: str, error: str):
        if job_id in self._jobs:
            job = self._jobs[job_id]; job.error_message = error; job.status = JobStatus.FAILED
            job.stage = "خطا در پردازش"; jobs_logger.error("Job failed: %s | %s", job_id, error)

job_manager = JobManager()
