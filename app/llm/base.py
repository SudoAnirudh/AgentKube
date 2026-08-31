import abc
import json
import re
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
from app.core.exceptions import InvalidLLMOutputError, LLMProviderError

T = TypeVar("T", bound=BaseModel)


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Utility to safely extract and parse JSON object from LLM response text."""
    if not text:
        raise InvalidLLMOutputError("Received empty response from LLM provider")

    cleaned = text.strip()
    # Handle markdown code blocks e.g. ```json { ... } ```
    json_block_match = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", cleaned, re.DOTALL)
    if json_block_match:
        cleaned = json_block_match.group(1).strip()
    else:
        # Fallback to finding first '{' or '[' and last '}' or ']'
        object_match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if object_match:
            cleaned = object_match.group(1).strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        raise InvalidLLMOutputError(f"Expected JSON object but parsed type '{type(parsed).__name__}'")
    except json.JSONDecodeError as exc:
        raise InvalidLLMOutputError(f"Failed to parse LLM text as JSON: {cleaned[:200]}...") from exc


class BaseLLMClient(abc.ABC):
    """Abstract Base Class for LLM providers."""

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """Generate raw text response from the LLM provider."""
        pass

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> T:
        """Generate structured response parsed into a Pydantic model."""
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        instruction = (
            f"You MUST respond ONLY with a single valid JSON object strictly matching this JSON Schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Do not include any conversational preamble, markdown outside codeblock, or extra text."
        )

        full_system_prompt = f"{system_prompt}\n\n{instruction}" if system_prompt else instruction
        raw_output = await self.generate(prompt=prompt, system_prompt=full_system_prompt, timeout=timeout)

        json_data = extract_json_from_text(raw_output)
        try:
            return response_model.model_validate(json_data)
        except ValidationError as val_err:
            raise InvalidLLMOutputError(
                f"LLM JSON output failed schema validation for {response_model.__name__}: {val_err.errors()}",
                details={"raw_output": raw_output, "validation_errors": val_err.errors()},
            ) from val_err
