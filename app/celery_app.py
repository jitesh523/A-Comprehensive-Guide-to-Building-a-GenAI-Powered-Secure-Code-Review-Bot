"""
Celery Application Configuration
"""
from celery import Celery
from kombu import Queue
import os
from dotenv import load_dotenv

load_dotenv()

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Celery Application
celery_app = Celery(
    "secure_code_review_bot",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.scan_orchestrator"]
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="task.#"),
        Queue("scan_queue", routing_key="scan.#"),
        Queue("verification_queue", routing_key="verification.#"),
    ),
    task_routes={
        "app.tasks.scan_orchestrator.run_scan": {"queue": "scan_queue"},
        "app.tasks.scan_orchestrator.verify_finding": {"queue": "verification_queue"},
    }
)

if __name__ == "__main__":
    celery_app.start()
