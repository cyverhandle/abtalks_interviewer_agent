"""Optional LLM brain for the interviewer.

Talks to any OpenAI-compatible /chat/completions endpoint:
  * OpenAI            — https://api.openai.com/v1
  * Groq              — https://api.groq.com/openai/v1
  * Ollama (local)    — http://localhost:11434/v1   (e.g. qwen2.5-coder)

Configured via environment variables:
  AI_INTERVIEW_LLM_BASE_URL  (unset -> LLM disabled, deterministic engine used)
  AI_INTERVIEW_LLM_API_KEY   (optional; Ollama does not need one)
  AI_INTERVIEW_LLM_MODEL     (e.g. gpt-4o-mini, qwen2.5-coder:7b)

Every failure is caught and the caller falls back to the deterministic engine,
so the interview always continues.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class LLMClient:
    def __init__(self, base_url: str, api_key: str = "", model: str = "",
                 timeout: float = 12.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.model)

    def chat_json(self, messages: List[Dict[str, str]],
                  temperature: float = 0.7) -> Optional[Dict[str, Any]]:
        """Call the model, requesting JSON output. Returns a parsed dict or None."""
        if not self.enabled:
            return None
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        # Some providers reject 'response_format' — add it, and retry without it
        # on a 400 so local servers (older Ollama) still work.
        body = dict(payload)
        body["response_format"] = {"type": "json_object"}
        for attempt_body in (body, payload):
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/chat/completions",
                    data=json.dumps(attempt_body).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}),
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = json.loads(resp.read().decode("utf-8"))
                content = raw["choices"][0]["message"]["content"]
                return self._parse_json_content(content)
            except urllib.error.HTTPError as err:
                if err.code == 400 and attempt_body is body:
                    continue  # retry without response_format
                return None
            except Exception:
                return None
        return None

    @staticmethod
    def _parse_json_content(content: str) -> Optional[Dict[str, Any]]:
        if not content:
            return None
        text = content.strip()
        # strip markdown fences if present
        fence = re.match(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if fence:
            text = fence.group(1)
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            # last resort: find the first {...} block
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            try:
                parsed = json.loads(match.group(0))
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None


def llm_from_env() -> LLMClient:
    return LLMClient(
        base_url=os.environ.get("AI_INTERVIEW_LLM_BASE_URL", ""),
        api_key=os.environ.get("AI_INTERVIEW_LLM_API_KEY", ""),
        model=os.environ.get("AI_INTERVIEW_LLM_MODEL", ""),
    )
