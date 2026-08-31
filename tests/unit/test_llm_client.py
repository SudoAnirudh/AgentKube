import pytest
from pydantic import BaseModel
from app.core.exceptions import InvalidLLMOutputError, TimeoutExecutionError
from app.llm.base import extract_json_from_text
from app.llm.mock import MockLLMClient


class SampleSchema(BaseModel):
    name: str
    count: int


def test_extract_json_from_text_variants():
    # Plain JSON
    res1 = extract_json_from_text('{"name": "test", "count": 1}')
    assert res1 == {"name": "test", "count": 1}

    # Markdown block JSON
    res2 = extract_json_from_text('Here is the output:\n```json\n{"name": "block", "count": 5}\n```')
    assert res2 == {"name": "block", "count": 5}

    # Malformed JSON
    with pytest.raises(InvalidLLMOutputError):
        extract_json_from_text("Invalid text string")


@pytest.mark.asyncio
async def test_mock_llm_structured_output():
    client = MockLLMClient(mode="success")
    # Generate structured output parsing schema
    res = await client.generate_structured(
        prompt="Get sample data",
        response_model=SampleSchema,
    )
    assert isinstance(res, SampleSchema)


@pytest.mark.asyncio
async def test_mock_llm_timeout_mode():
    client = MockLLMClient(mode="timeout")
    with pytest.raises(TimeoutExecutionError):
        await client.generate("Hello")
