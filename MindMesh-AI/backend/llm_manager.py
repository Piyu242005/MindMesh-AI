"""
backend/llm_manager.py — MindMesh AI
Unified Cloud LLM manager with automatic failover and token/cost tracking.
Supports Gemini (Primary), Groq (Fallback), and Ollama (Local Dev).
"""

import os
import sys
import time
import json
from typing import Generator, Dict, Any, Tuple
from pathlib import Path

from google import genai
from groq import Groq
import requests

# ── Environment configuration ──────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "").strip()
OLLAMA_URL     = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Configure SDKs
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    gemini_client = None

if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    groq_client = None

# ── Tracking Defaults ────────────────────────────────────────────────────────
# Metrics tracking: populated in global state for Dashboard display
# or kept in memory for CLI usage.
_cli_metrics = {
    "total_requests": 0,
    "total_tokens": 0,
    "avg_response_time": 0.0,
    "response_times": []
}

def _update_metrics(provider: str, model: str, duration: float, tokens: int = 0):
    """Update global metrics for Dashboard display."""
    _cli_metrics["total_requests"] += 1
    _cli_metrics["total_tokens"] += tokens
    _cli_metrics["response_times"].append(duration)
    
    # Telegram Analytics
    from backend.telegram.analytics import AnalyticsStore
    AnalyticsStore.add_query(provider, duration)


# ── Health Checks ────────────────────────────────────────────────────────────

def check_providers() -> Dict[str, Tuple[bool, str]]:
    """Return health status for all providers."""
    status = {}
    
    # Gemini
    if not GEMINI_API_KEY:
        status["gemini"] = (False, "Missing API Key")
    else:
        status["gemini"] = (True, "Ready")
        
    # Groq
    if not GROQ_API_KEY:
        status["groq"] = (False, "Missing API Key")
    else:
        status["groq"] = (True, "Ready")
        
    # Ollama
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if r.status_code == 200:
            status["ollama"] = (True, "Ready")
        else:
            status["ollama"] = (False, f"HTTP {r.status_code}")
    except Exception:
        status["ollama"] = (False, "Offline")
        
    return status


# ── Generation Implementations ───────────────────────────────────────────────

def _generate_with_gemini(prompt: str, model_name: str, stream: bool = True):
    """Generate response using Google Gemini."""
    if not gemini_client:
        raise ValueError("GEMINI_API_KEY is not set.")
        
    if stream:
        response = gemini_client.models.generate_content_stream(
            model=model_name,
            contents=prompt,
        )
        def stream_gen():
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        return stream_gen()
    else:
        response = gemini_client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text


def _generate_with_groq(prompt: str, model_name: str, stream: bool = True):
    """Generate response using Groq."""
    if not groq_client:
        raise ValueError("GROQ_API_KEY is not set.")
        
    response = groq_client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        stream=stream,
        temperature=0.3,
        max_tokens=2048,
    )
    
    if stream:
        def stream_gen():
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        return stream_gen()
    else:
        return response.choices[0].message.content


def _generate_with_ollama(prompt: str, model_name: str, stream: bool = True):
    """Generate response using local Ollama."""
    import requests
    
    if stream:
        def stream_gen():
            try:
                with requests.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={"model": model_name, "prompt": prompt, "stream": True},
                    stream=True,
                    timeout=180,
                ) as r:
                    for line in r.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                token = data.get("response", "")
                                if token:
                                    yield token
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
            except requests.exceptions.ConnectionError:
                yield "\n\n⚠️ **Ollama is not running.** Start it with: `ollama serve`"
            except Exception as e:
                yield f"\n\n⚠️ **Error:** {e}"
        return stream_gen()
    else:
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": model_name, "prompt": prompt, "stream": False},
                timeout=180,
            )
            r.raise_for_status()
            return r.json().get("response", "")
        except requests.exceptions.ConnectionError:
            return "⚠️ **Ollama is not running.** Start it with: `ollama serve`"
        except Exception as e:
            return f"⚠️ **LLM error:** {e}"


# ── Unified Interface & Auto-Failover ─────────────────────────────────────────

def generate_response(
    prompt: str,
    provider: str = "gemini",
    model_name: str = "gemini-2.5-flash",
    stream: bool = True,
    fallback_allowed: bool = True
) -> Generator[str, None, None] | str:
    """
    Unified entry point for LLM generation.
    Routes to the requested provider and handles automatic failover.
    
    Yields chunks if stream=True, else returns full string.
    """
    start_time = time.time()
    
    # Provider mapping
    _call_map = {
        "gemini": _generate_with_gemini,
        "groq":   _generate_with_groq,
        "ollama": _generate_with_ollama
    }
    
    # Fallback paths mapping (provider -> next fallback)
    _fallback_map = {
        "gemini": ("groq", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")),
        "groq":   ("gemini", os.getenv("GEMINI_MODEL", "gemini-2.5-flash")),
        "ollama": ("gemini", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    }
    
    generate_fn = _call_map.get(provider)
    if not generate_fn:
        raise ValueError(f"Unknown LLM provider: {provider}")

    try:
        # Attempt primary provider
        result = generate_fn(prompt, model_name, stream)
        
        # We can't strictly track generated token counts accurately across 
        # arbitrary streaming providers without their specific tokenisers, 
        # so we track a rough estimate for the dashboard.
        est_tokens = len(prompt.split()) + 500  
        
        # Wrapping the stream to capture duration properly
        if stream:
            def tracking_generator():
                chunks = []
                try:
                    for chunk in result:
                        chunks.append(chunk)
                        yield chunk
                finally:
                    duration = time.time() - start_time
                    _update_metrics(provider, model_name, duration, est_tokens)
            return tracking_generator()
        else:
            duration = time.time() - start_time
            _update_metrics(provider, model_name, duration, est_tokens)
            return result
            
    except Exception as e:
        # Fallback mechanism
        if fallback_allowed and provider in _fallback_map:
            fb_provider, fb_model = _fallback_map[provider]
            print(f"⚠️ [LLM Manager] {provider.title()} failed ({e}). Falling back to {fb_provider.title()}...")
            
            # Record failed attempt as a zero-duration error (or handle separately)
            # Proceeding to secondary provider
            try:
                # Disable double-fallback to prevent infinite loops
                return generate_response(
                    prompt, 
                    provider=fb_provider, 
                    model_name=fb_model, 
                    stream=stream, 
                    fallback_allowed=False
                )
            except Exception as fb_err:
                error_msg = f"⚠️ Both primary ({provider}) and fallback ({fb_provider}) failed.\nPrimary err: {e}\nFallback err: {fb_err}"
                if stream:
                    def err_gen(): yield error_msg
                    return err_gen()
                return error_msg
        else:
            error_msg = f"⚠️ LLM Error ({provider}): {e}"
            if stream:
                def err_gen(): yield error_msg
                return err_gen()
            return error_msg
