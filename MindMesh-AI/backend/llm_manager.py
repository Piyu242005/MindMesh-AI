"""Unified LLM gateway with Gemini, Groq and Ollama fallback."""
import os, time, json
from typing import Generator, Dict, Tuple
import requests
from google import genai
from groq import Groq

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
_cli_metrics = {"total_requests": 0, "total_tokens": 0, "avg_response_time": 0.0, "response_times": []}

def _update_metrics(provider: str, model: str, duration: float, tokens: int = 0):
    _cli_metrics["total_requests"] += 1
    _cli_metrics["total_tokens"] += tokens
    _cli_metrics["response_times"].append(duration)
    _cli_metrics["avg_response_time"] = sum(_cli_metrics["response_times"]) / len(_cli_metrics["response_times"])
    from backend.telegram.analytics import AnalyticsStore
    AnalyticsStore.add_query(provider, duration)

def check_providers() -> Dict[str, Tuple[bool, str]]:
    status = {"gemini": (bool(GEMINI_API_KEY), "Ready" if GEMINI_API_KEY else "Missing API Key"), "groq": (bool(GROQ_API_KEY), "Ready" if GROQ_API_KEY else "Missing API Key")}
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        status["ollama"] = (r.status_code == 200, "Ready" if r.status_code == 200 else f"HTTP {r.status_code}")
    except requests.RequestException:
        status["ollama"] = (False, "Offline")
    return status

def _generate_with_gemini(prompt, model_name, stream=True):
    if not gemini_client: raise ValueError("GEMINI_API_KEY is not set.")
    if stream:
        response = gemini_client.models.generate_content_stream(model=model_name, contents=prompt)
        return (chunk.text for chunk in response if chunk.text)
    return gemini_client.models.generate_content(model=model_name, contents=prompt).text

def _generate_with_groq(prompt, model_name, stream=True):
    if not groq_client: raise ValueError("GROQ_API_KEY is not set.")
    response = groq_client.chat.completions.create(model=model_name, messages=[{"role":"user","content":prompt}], stream=stream, temperature=0.3, max_tokens=2048)
    if stream:
        def stream_gen():
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content: yield content
        return stream_gen()
    return response.choices[0].message.content

def _generate_with_ollama(prompt, model_name, stream=True):
    if stream:
        def stream_gen():
            try:
                with requests.post(f"{OLLAMA_URL}/api/generate", json={"model":model_name,"prompt":prompt,"stream":True}, stream=True, timeout=180) as r:
                    r.raise_for_status()
                    for line in r.iter_lines():
                        if line:
                            data=json.loads(line); token=data.get("response","")
                            if token: yield token
                            if data.get("done"): break
            except requests.RequestException as e:
                yield f"\n\n⚠️ Ollama error: {e}"
        return stream_gen()
    r=requests.post(f"{OLLAMA_URL}/api/generate",json={"model":model_name,"prompt":prompt,"stream":False},timeout=180)
    r.raise_for_status(); return r.json().get("response","")

def generate_response(prompt: str, provider: str = "gemini", model_name: str = "gemini-2.5-flash", stream: bool = True, fallback_allowed: bool = True) -> Generator[str, None, None] | str:
    start=time.time(); calls={"gemini":_generate_with_gemini,"groq":_generate_with_groq,"ollama":_generate_with_ollama}
    fallbacks={"gemini":("groq",os.getenv("GROQ_MODEL","llama-3.3-70b-versatile")),"groq":("gemini",os.getenv("GEMINI_MODEL","gemini-2.5-flash")),"ollama":("gemini",os.getenv("GEMINI_MODEL","gemini-2.5-flash"))}
    if provider not in calls: raise ValueError(f"Unknown LLM provider: {provider}")
    try:
        result=calls[provider](prompt,model_name,stream)
        if stream:
            def tracked():
                try:
                    for chunk in result: yield chunk
                finally:
                    _update_metrics(provider,model_name,time.time()-start,0)
            return tracked()
        _update_metrics(provider,model_name,time.time()-start,0); return result
    except Exception as e:
        if fallback_allowed and provider in fallbacks:
            fb,model=fallbacks[provider]
            return generate_response(prompt,fb,model,stream,False)
        msg=f"⚠️ LLM Error ({provider}): {e}"
        return (iter([msg]) if stream else msg)
