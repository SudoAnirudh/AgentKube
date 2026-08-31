from celery import Celery
from app.utils.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ai_agent_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
)

celery_app.autodiscover_tasks(["app.workers"])
