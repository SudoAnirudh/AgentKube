import pytest
from httpx import ASGITransport, AsyncClient
from app.api.routes import get_state_manager
from app.llm.mock import MockLLMClient
from app.main import app
from app.storage.redis import RedisStateManager
from app.utils.config import Settings
from app.workers.celery_app import celery_app


@pytest.fixture(autouse=True)
def configure_celery_eager():
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )


@pytest.fixture
def test_settings():
    return Settings(
        LLM_PROVIDER="mock",
        LLM_MODEL="mock-model",
        MAX_RETRIES=2,
        AGENT_TIMEOUT_SECONDS=5.0,
        CELERY_TASK_ALWAYS_EAGER=True,
        LOG_LEVEL="DEBUG",
    )


@pytest.fixture
def mock_llm_client():
    return MockLLMClient(mode="success")


@pytest.fixture
def redis_state_manager(test_settings):
    return RedisStateManager(redis_url=test_settings.REDIS_URL)


@pytest.fixture
async def async_client(redis_state_manager):
    app.dependency_overrides[get_state_manager] = lambda: redis_state_manager
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
