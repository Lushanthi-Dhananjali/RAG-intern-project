"""
Unified LLM Client supporting both Local Ollama (llama3) and Cloud API Keys (OpenAI, Gemini).
Enables seamless switching between local and API-driven execution with automatic fallback.
"""

import os
import json
import time
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

    openai_env_key = (getattr(settings, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")).strip()
    gemini_env_key = (getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")).strip()

    # Determine effective key
    effective_key = (
        api_key
        or ctx_key
        or openai_env_key
        or gemini_env_key
    ).strip()

    # Determine requested provider
    env_provider = (getattr(settings, "LLM_PROVIDER", "auto") or os.getenv("LLM_PROVIDER", "auto")).strip().lower()
    raw_provider = provider or ctx_provider or env_provider or "auto"
    if raw_provider == "auto" and env_provider not in ("auto", "", None):
        raw_provider = env_provider

    requested_provider = raw_provider.strip().lower()

    # Determine provider
    resolved_provider = requested_provider
    if resolved_provider in ("auto", "", None):
        if effective_key:
            # Check for Gemini key signatures:
            # - 'AQ.' prefix (new Google AI Studio authorization keys)
            # - 'AIza' prefix (legacy Google API keys)
            # - Or key came from GEMINI_API_KEY while OPENAI_API_KEY is empty
            # - Or 'gemini' is explicitly in requested model
            if (
                effective_key.startswith("AQ.")
                or effective_key.startswith("AIza")
                or (gemini_env_key and effective_key == gemini_env_key and not openai_env_key)
                or "gemini" in (model or "").lower()
            ):
                resolved_provider = "gemini"
            elif effective_key.startswith("sk-") or (openai_env_key and effective_key == openai_env_key):
                resolved_provider = "openai"
            elif gemini_env_key and not openai_env_key:
                resolved_provider = "gemini"
            else:
                resolved_provider = "openai"
        elif gemini_env_key and not openai_env_key:
            resolved_provider = "gemini"
            effective_key = gemini_env_key
        elif openai_env_key:
            resolved_provider = "openai"
            effective_key = openai_env_key
        else:
            resolved_provider = "ollama"

    # Fallback to Ollama if cloud provider was requested but no API key is available
    if resolved_provider in ("gemini", "openai") and not effective_key:
        logger.info(
            "Cloud provider '%s' requested but no API key was found in UI, .env, or code. Automatically falling back to local Ollama.",
            resolved_provider
        )
        resolved_provider = "ollama"

    # Determine model and base URL
    base_url = None
    if resolved_provider == "gemini":
        legacy_models = ("gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.0-flash")
        if not model or "llama" in (model or "").lower() or (model or "").lower() in legacy_models:
            resolved_model = getattr(settings, "GEMINI_MODEL_NAME", "gemini-3.8-flash")
            if resolved_model in legacy_models:
                resolved_model = "gemini-3.8-flash"
        else:
            resolved_model = model
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        gemini_key = effective_key or gemini_env_key
        effective_key = gemini_key.strip()
    elif resolved_provider == "openai":
        if not model or "llama" in (model or "").lower():
            resolved_model = getattr(settings, "OPENAI_MODEL_NAME", "gpt-4o-mini")
        else:
            resolved_model = model
        base_url = getattr(settings, "OPENAI_BASE_URL", None) or os.getenv("OPENAI_BASE_URL", None)
        openai_key = effective_key or openai_env_key
        effective_key = openai_key.strip()
    else:  # ollama
        resolved_provider = "ollama"
        resolved_model = model if (model and "gemini" not in model.lower() and "gpt" not in model.lower()) else getattr(settings, "OLLAMA_MODEL", "llama3")
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
    temperature: float = 0.65,
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

        candidate_models = [model]
        if base_url and "googleapis" in base_url:
            for alt in ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]:
                if alt not in candidate_models:
                    candidate_models.append(alt)

        last_err = None
        for cand_model in candidate_models:
            max_retries = 3 if ("googleapis" in (base_url or "") or "gemini" in cand_model.lower()) else 1
            for attempt in range(max_retries):
                try:
                    response = client.chat.completions.create(
                        model=cand_model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=temperature,
                    )
                    content = response.choices[0].message.content or "{}"
                    clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                    return json.loads(clean)
                except Exception as call_err:
                    last_err = call_err
                    err_text = str(call_err).lower()

                    # 1. 404 Model Not Found / Deprecated: skip to next model immediately without retrying
                    if "not found" in err_text:
                        logger.warning("Model '%s' returned 404. Switching to next candidate model...", cand_model)
                        break

                    # 2. 503 Service Unavailable, 429 Rate Limit, 500 Server Error: wait and retry
                    is_transient = any(t in err_text for t in ["503", "unavailable", "429", "resource_exhausted", "500", "overloaded", "capacity"])
                    if is_transient:
                        if attempt < max_retries - 1:
                            wait_s = 1.5 * (attempt + 1)
                            logger.warning(
                                "Transient error on '%s' (%s). Retrying in %.1fs (attempt %d/%d)...",
                                cand_model, call_err, wait_s, attempt + 1, max_retries
                            )
                            time.sleep(wait_s)
                            continue
                        else:
                            logger.warning("Model '%s' still unavailable after %d attempts. Trying next alternative candidate...", cand_model, max_retries)
                            break

                    # Non-transient errors (e.g. 401 invalid key) raise immediately
                    raise call_err
        if last_err:
            raise last_err

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
        "temperature": temperature,
    }
    res = requests.post(url, json=payload, headers=headers, timeout=timeout)
    res.raise_for_status()
    raw = res.json()["choices"][0]["message"]["content"]
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(clean)


def call_gemini_native_rest_api(
    prompt: str,
    api_key: str,
    model: str = "gemini-3.8-flash",
    system_prompt: Optional[str] = None,
    json_schema: Optional[Dict[str, Any]] = None,
    temperature: float = 0.65,
    timeout: int = 90,
) -> Dict[str, Any]:
    """
    Directly invokes Google Gemini's native generateContent REST endpoint.
    Bypasses the OpenAI bridge to eliminate connection hangs, ReadTimeout, and gateway latency.
    """
    if not api_key:
        raise ValueError("Cannot call Gemini API: API key is empty.")

    candidate_models = [model]
    for m in ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash-lite"]:
        if m not in candidate_models:
            candidate_models.append(m)

    schema_hint = ""
    if json_schema and isinstance(json_schema, dict):
        properties = json_schema.get("properties", {})
        if properties:
            keys_list = list(properties.keys())
            schema_hint = f"\n\nCRITICAL INSTRUCTION: Your output MUST be valid JSON containing these exact top-level keys:\n{keys_list}"

    combined_text = f"System Instruction:\n{system_prompt}\n\nTask:\n{prompt}{schema_hint}" if system_prompt else f"{prompt}{schema_hint}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": combined_text}
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key.strip(),
    }

    last_err = None
    for cand_model in candidate_models:
        clean_model = cand_model.removeprefix("models/")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent"

        for attempt in range(3):
            try:
                logger.info("Calling native Gemini REST API with model: %s (attempt %d/3)...", clean_model, attempt + 1)
                res = requests.post(url, json=payload, headers=headers, timeout=timeout)

                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_part = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                        clean = text_part.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                        return json.loads(clean)
                    raise ValueError(f"Gemini returned empty candidate response: {data}")

                # If 404 Not Found, switch to next candidate model
                if res.status_code == 404:
                    logger.warning("Gemini model '%s' returned 404 Not Found. Trying alternative...", clean_model)
                    last_err = RuntimeError(f"Model {clean_model} not found: {res.text}")
                    break

                # If 503 Unavailable or 429 Rate Limit, wait and retry
                if res.status_code in (429, 500, 502, 503, 504):
                    wait_s = 2.0 * (attempt + 1)
                    logger.warning("Gemini returned %d (%s). Retrying in %.1fs...", res.status_code, res.text[:200], wait_s)
                    time.sleep(wait_s)
                    continue

                res.raise_for_status()
            except requests.exceptions.Timeout as timeout_err:
                logger.warning("Timeout on Gemini model '%s' (attempt %d/3). Trying next model...", clean_model, attempt + 1)
                last_err = timeout_err
                break
            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                if any(x in err_str for x in ["503", "unavailable", "429", "timeout"]):
                    time.sleep(2.0)
                    continue
                break

    if last_err:
        raise last_err
    raise RuntimeError("Failed to obtain response from Gemini native API.")


def call_local_ollama_api(
    prompt: str,
    model: str = "llama3",
    ollama_url: str = "http://localhost:11434",
    json_schema: Optional[Dict[str, Any]] = None,
    temperature: float = 0.65,
    timeout: int = 180,
) -> Dict[str, Any]:
    """Invokes local Ollama endpoint with JSON mode or strict schema."""
    target_model = model
    default_ollama_model = getattr(settings, "OLLAMA_MODEL", "llama3")
    if not target_model or any(x in target_model.lower() for x in ["gemini", "gpt", "claude"]):
        target_model = default_ollama_model

    url_base = ollama_url.rstrip("/")
    try:
        tags_res = requests.get(f"{url_base}/api/tags", timeout=3)
        if tags_res.ok:
            available = [m.get("name", "") for m in tags_res.json().get("models", [])]
            if available:
                if target_model not in available:
                    match = next((m for m in available if m.split(":")[0] == target_model.split(":")[0]), None)
                    if match:
                        target_model = match
                    elif not any(m == target_model for m in available):
                        target_model = available[0]
    except Exception:
        pass

    url = f"{url_base}/api/generate"
    payload: Dict[str, Any] = {
        "model": target_model,
        "prompt": prompt,
        "stream": False,
        "format": json_schema if json_schema else "json",
        "options": {
            "temperature": max(temperature, 0.75),
            "top_p": 0.9,
            "repeat_penalty": 1.25,
            "frequency_penalty": 0.35,
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
    temperature: float = 0.65,
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
            if active_provider == "gemini":
                return call_gemini_native_rest_api(
                    prompt=prompt,
                    api_key=active_key,
                    model=active_model,
                    system_prompt=system_prompt,
                    json_schema=json_schema,
                    temperature=temperature,
                    timeout=min(timeout, 90),
                )
            else:
                return call_openai_compatible_api(
                    prompt=prompt,
                    api_key=active_key,
                    model=active_model,
                    base_url=active_base_url,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    timeout=min(timeout, 90),
                )
        except Exception as api_err:
            logger.warning("Cloud %s API call failed: %s. Attempting fallback to local Ollama...", active_provider, api_err)
            try:
                return call_local_ollama_api(
                    prompt=prompt,
                    model=getattr(settings, "OLLAMA_MODEL", "llama3"),
                    ollama_url=ollama_endpoint,
                    json_schema=json_schema,
                    temperature=temperature,
                    timeout=timeout,
                )
            except Exception:
                raise api_err

    # Path 2: Local Ollama
    try:
        local_model = active_model
        if not local_model or any(x in local_model.lower() for x in ["gemini", "gpt", "claude"]):
            local_model = getattr(settings, "OLLAMA_MODEL", "llama3")
        logger.info("Executing LLM call via local Ollama (model: %s)...", local_model)
        return call_local_ollama_api(
            prompt=prompt,
            model=local_model,
            ollama_url=ollama_endpoint,
            json_schema=json_schema,
            temperature=temperature,
            timeout=timeout,
        )
        logger.info("Executing LLM call via local Ollama (model: %s)...", local_model)
        return call_local_ollama_api(
            prompt=prompt,
            model=local_model,
            ollama_url=ollama_endpoint,
            json_schema=json_schema,
            timeout=timeout,
        )
    except Exception as ollama_err:
        # If Ollama fails, check if an API key is available as fallback (from request context, env, or code)
        ctx_key = client_api_key_ctx.get()
        fallback_key = (
            active_key
            or ctx_key
            or getattr(settings, "OPENAI_API_KEY", "")
            or getattr(settings, "GEMINI_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
            or os.getenv("GEMINI_API_KEY", "")
        )
        if fallback_key and fallback_key.strip():
            fallback_key = fallback_key.strip()
            logger.warning("Local Ollama call failed (%s). Falling back to Cloud API key...", ollama_err)
            fb_provider = "gemini" if (fallback_key.startswith("AQ.") or fallback_key.startswith("AIza") or (getattr(settings, "GEMINI_API_KEY", "") and not getattr(settings, "OPENAI_API_KEY", ""))) else "openai"
            fb_model = getattr(settings, "OPENAI_MODEL_NAME", "gpt-4o-mini") if fb_provider == "openai" else getattr(settings, "GEMINI_MODEL_NAME", "gemini-3.8-flash")
            if fb_model in ("gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"): fb_model = "gemini-3.8-flash"
            fb_base = "https://generativelanguage.googleapis.com/v1beta/openai/" if fb_provider == "gemini" else None
            if fb_provider == "gemini":
                return call_gemini_native_rest_api(
                    prompt=prompt,
                    api_key=fallback_key,
                    model=fb_model,
                    system_prompt=system_prompt,
                    json_schema=json_schema,
                    timeout=min(timeout, 90),
                )
            else:
                return call_openai_compatible_api(
                    prompt=prompt,
                    api_key=fallback_key,
                    model=fb_model,
                    base_url=fb_base,
                    system_prompt=system_prompt,
                    timeout=min(timeout, 90),
                )
        raise RuntimeError(
            "No LLM API key detected and local Ollama is not running on http://localhost:11434. "
            "Please provide an API key (Google Gemini or OpenAI) in the UI ('AI Model & Key' button) or "
            "in 'backend pycharm/.env' (GEMINI_API_KEY=... / OPENAI_API_KEY=...), or start Ollama locally."
        ) from ollama_err
