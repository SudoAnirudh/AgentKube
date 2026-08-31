import uuid
from typing import Dict, Optional
import redis
from app.models.execution import ExecutionState, ExecutionStatus
from app.utils.config import Settings, get_settings
from app.utils.logger import get_logger

logger = get_logger()


class RedisStateManager:
    """Redis-backed state manager for cross-process execution state tracking."""

    def __init__(self, redis_url: Optional[str] = None, ttl_seconds: int = 86400):
        settings = get_settings()
        self.redis_url = redis_url or settings.REDIS_URL
        self.ttl_seconds = ttl_seconds
        self.client = redis.Redis.from_url(self.redis_url, decode_responses=True)

    def ping(self) -> bool:
        try:
            return self.client.ping()
        except Exception as err:
            logger.error(f"Redis ping failed at {self.redis_url}: {err}")
            return False

    def create_state(self, task: str, context: Optional[Dict] = None) -> ExecutionState:
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        state = ExecutionState(
            execution_id=execution_id,
            task=task,
            context=context or {},
            status=ExecutionStatus.QUEUED,
        )
        self.save_state(state)
        return state

    def get_state(self, execution_id: str) -> Optional[ExecutionState]:
        key = f"execution:{execution_id}"
        raw_data = self.client.get(key)
        if not raw_data:
            return None
        try:
            return ExecutionState.model_validate_json(raw_data)
        except Exception as parse_err:
            logger.error(f"Failed to parse execution state for '{execution_id}': {parse_err}")
            return None

    def save_state(self, state: ExecutionState) -> None:
        key = f"execution:{state.execution_id}"
        json_data = state.model_dump_json()
        self.client.set(key, json_data, ex=self.ttl_seconds)
