import asyncio
from typing import Optional
import httpx
from app.core.exceptions import LLMProviderError, TimeoutExecutionError
from app.llm.base import BaseLLMClient


class GroqClient(BaseLLMClient):
    """LLM client for Groq API."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile", base_url: str = "https://api.groq.com/openai/v1"):
        if not api_key:
            raise LLMProviderError("Groq API key is required when using 'groq' provider")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout: Optional[float] = 30.0,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        req_timeout = timeout or 30.0
        try:
            async with httpx.AsyncClient(timeout=req_timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    raise LLMProviderError(
                        f"Groq API returned HTTP status {response.status_code}: {response.text}",
                        details={"status_code": response.status_code},
                    )
                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise LLMProviderError("Groq API returned no choices in response")
                return choices[0].get("message", {}).get("content", "")
        except httpx.TimeoutException as err:
            raise TimeoutExecutionError(f"Groq API request timed out after {req_timeout}s") from err
        except httpx.RequestError as req_err:
            raise LLMProviderError(f"Network error communicating with Groq API: {req_err}") from req_err
