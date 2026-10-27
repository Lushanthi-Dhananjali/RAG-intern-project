"""
Unified LLM Client supporting both Local Ollama (llama3) and Cloud API Keys (OpenAI, Gemini).
Enables seamless switching between local and API-driven execution with automatic fallback.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

import requests
from config import settings

logger = logging.getLogger("UnifiedLlmClient")

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


from contextvars import ContextVar

client_api_key_ctx: ContextVar[Optional[str]] = ContextVar("client_api_key_ctx", default=None)
client_provider_ctx: ContextVar[Optional[str]] = ContextVar("client_provider_ctx", default=None)


def get_active_provider_info() -> Dict[str, Any]:
    """Returns metadata about the active LLM provider and available keys."""
    config = resolve_llm_config()
    return {
        "active_provider": config["provider"],
        "active_model": config["model"],
        "has_openai_key": bool(getattr(settings, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")),
        "has_gemini_key": bool(getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")),
        "ollama_url": getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollama_model": getattr(settings, "OLLAMA_MODEL", "llama3"),
    }


def resolve_llm_config(
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Resolves the effective provider, API key, model name, and endpoint.
    Priority:
    1. Explicit call arguments (api_key, provider, model)
    2. Request ContextVar (from UI header X-LLM-API-Key / X-LLM-Provider)
    3. settings / environment variables
    4. Auto-detection based on API key prefix or presence
    """
    ctx_key = client_api_key_ctx.get()
    ctx_provider = client_provider_ctx.get()

    effective_key = (
        api_key
        or ctx_key
        or getattr(settings, "OPENAI_API_KEY", "")
        or getattr(settings, "GEMINI_API_KEY", "")
        or os.getenv("OPENAI_API_KEY", "")
        or os.getenv("GEMINI_API_KEY", "")
    ).strip()

    requested_provider = (
        provider
        or ctx_provider
        or getattr(settings, "LLM_PROVIDER", "auto")
        or os.getenv("LLM_PROVIDER", "auto")
    ).strip().lower()

    # Determine provider
    resolved_provider = requested_provider
    if resolved_provider in ("auto", "", None):
        if effective_key:
            if effective_key.startswith("AIza") or "gemini" in (model or "").lower():
                resolved_provider = "gemini"
            else:
                resolved_provider = "openai"
        else:
            resolved_provider = "ollama"

    # Determine model and base URL
    base_url = None
    if resolved_provider == "gemini":
        resolved_model = model or getattr(settings, "GEMINI_MODEL_NAME", "gemini-1.5-flash")
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        gemini_key = effective_key or getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
        effective_key = gemini_key.strip()
    elif resolved_provider == "openai":
        resolved_model = model or getattr(settings, "OPENAI_MODEL_NAME", "gpt-4o-mini")
        base_url = getattr(settings, "OPENAI_BASE_URL", None) or os.getenv("OPENAI_BASE_URL", None)
    else:  # ollama
        resolved_provider = "ollama"
        resolved_model = model or getattr(settings, "OLLAMA_MODEL", "llama3")
        base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")

    return {
        "provider": resolved_provider,
        "api_key": effective_key,
        "model": resolved_model,
        "base_url": base_url,
    }


def call_openai_compatible_api(
    prompt: str,
    api_key: str,
    model: str,
    base_url: Optional[str] = None,
    system_prompt: Optional[str] = None,
    timeout: int = 90,
) -> Dict[str, Any]:
    """Invokes OpenAI or OpenAI-compatible (Gemini, Groq, OpenRouter) endpoint for JSON output."""
    if not api_key:
        raise ValueError("Cannot call cloud API: API key is empty.")

    client_kwargs: Dict[str, Any] = {"api_key": api_key, "timeout": timeout}
    if base_url:
        client_kwargs["base_url"] = base_url

    if OpenAI is not None:
        client = OpenAI(**client_kwargs)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)

    # Fallback to direct HTTP request using requests
    url = f"{base_url.rstrip('/') if base_url else 'https://api.openai.com/v1'}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt or "You are an expert curriculum assistant. Output strictly valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }
    res = requests.post(url, json=payload, headers=headers, timeout=timeout)
    res.raise_for_status()
    raw = res.json()["choices"][0]["message"]["content"]
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(clean)


def call_local_ollama_api(
    prompt: str,
    model: str = "llama3",
    ollama_url: str = "http://localhost:11434",
    json_schema: Optional[Dict[str, Any]] = None,
    timeout: int = 180,
) -> Dict[str, Any]:
    """Invokes local Ollama endpoint with JSON mode or strict schema."""
    url = f"{ollama_url.rstrip('/')}/api/generate"
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": json_schema if json_schema else "json",
        "options": {
            "temperature": 0.2,
            "num_predict": 2500,
            "num_thread": 6,
        },
    }
    res = requests.post(url, json=payload, timeout=timeout)
    res.raise_for_status()
    raw = res.json().get("response", "{}")
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(clean)


def execute_llm_json(
    prompt: str,
    json_schema: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    ollama_url: Optional[str] = None,
    timeout: int = 180,
) -> Dict[str, Any]:
    """
    Universal JSON execution entry point.
    Dispatches to Cloud API (OpenAI/Gemini) or Local Ollama with graceful fallback.
    """
    config = resolve_llm_config(api_key=api_key, provider=provider, model=model)
    active_provider = config["provider"]
    active_key = config["api_key"]
    active_model = config["model"]
    active_base_url = config["base_url"]

    ollama_endpoint = ollama_url or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")

    # Path 1: Cloud API (OpenAI or Gemini)
    if active_provider in ("openai", "gemini") and active_key:
        try:
            logger.info("Executing LLM call via %s API (model: %s)...", active_provider.upper(), active_model)
            return call_openai_compatible_api(
                prompt=prompt,
                api_key=active_key,
                model=active_model,
                base_url=active_base_url,
                system_prompt=system_prompt,
                timeout=timeout,
            )
        except Exception as api_err:
            logger.warning("Cloud %s API call failed: %s. Attempting fallback to local Ollama...", active_provider, api_err)
            try:
                return call_local_ollama_api(
                    prompt=prompt,
                    model=getattr(settings, "OLLAMA_MODEL", "llama3"),
                    ollama_url=ollama_endpoint,
                    json_schema=json_schema,
                    timeout=timeout,
                )
            except Exception:
                raise api_err

    # Path 2: Local Ollama
    try:
        logger.info("Executing LLM call via local Ollama (model: %s)...", active_model)
        return call_local_ollama_api(
            prompt=prompt,
            model=active_model,
            ollama_url=ollama_endpoint,
            json_schema=json_schema,
            timeout=timeout,
        )
    except Exception as ollama_err:
        # If Ollama fails, check if an API key is available as fallback
        fallback_key = getattr(settings, "OPENAI_API_KEY", "") or getattr(settings, "GEMINI_API_KEY", "")
        if fallback_key and fallback_key.strip():
            logger.warning("Local Ollama call failed (%s). Falling back to Cloud API key...", ollama_err)
            fb_provider = "gemini" if fallback_key.startswith("AIza") else "openai"
            fb_model = getattr(settings, "OPENAI_MODEL_NAME", "gpt-4o-mini") if fb_provider == "openai" else getattr(settings, "GEMINI_MODEL_NAME", "gemini-1.5-flash")
            fb_base = "https://generativelanguage.googleapis.com/v1beta/openai/" if fb_provider == "gemini" else None
            return call_openai_compatible_api(
                prompt=prompt,
                api_key=fallback_key.strip(),
                model=fb_model,
                base_url=fb_base,
                system_prompt=system_prompt,
                timeout=timeout,
            )
        raise ollama_err
