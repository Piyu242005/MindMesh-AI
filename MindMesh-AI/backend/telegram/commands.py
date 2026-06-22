import os
import psutil
from backend.telegram.bot import send_message
from backend.telegram.analytics import AnalyticsStore
import time
from backend.llm_manager import generate_response
from backend.embeddings import get_embedding_model, embed_single, get_qdrant_client
from backend.retrieval import retrieve_from_qdrant, retrieve_from_joblib, build_rag_prompt

# Store the application start time for /uptime
APP_START_TIME = time.time()

def format_uptime(seconds):
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, sec = divmod(rem, 60)
    return f"{int(days)} days {int(hours)} hours {int(mins)} mins"

async def process_telegram_message(message: dict):
    """Dispatcher for incoming messages."""
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return

    if text.startswith("/"):
        await handle_command(text, chat_id)
    else:
        await handle_ai_query(text, chat_id)

async def handle_command(text: str, chat_id: str):
    cmd = text.split()[0].lower()
    
    if cmd == "/status":
        uptime = format_uptime(time.time() - APP_START_TIME)
        msg = f"🟢 <b>MindMesh AI Online</b>\n\nUptime: {uptime}\nVersion: 1.0.0\nEnvironment: Production"
        send_message(msg, chat_id)
        
    elif cmd == "/uptime":
        uptime = format_uptime(time.time() - APP_START_TIME)
        msg = f"🟢 <b>MindMesh AI</b>\n\nUptime: {uptime}\nVersion: 1.0.0"
        send_message(msg, chat_id)

    elif cmd == "/stats":
        msg = f"Users: {AnalyticsStore.users_today}\nQueries: {AnalyticsStore.queries_today}\nVideos: {AnalyticsStore.videos_uploaded}\nChunks: {AnalyticsStore.qdrant_searches}"
        send_message(msg, chat_id)

    elif cmd == "/health":
        send_message("✅ Website is reachable and APIs are online.", chat_id)

    elif cmd in ["/qdrant", "/gemini", "/groq"]:
        from backend.llm_manager import check_providers
        status = check_providers()
        prov = cmd.replace("/", "")
        state, reason = status.get(prov, (False, "Unknown"))
        icon = "✅" if state else "❌"
        send_message(f"{icon} {prov.title()} Status: {reason}", chat_id)

    elif cmd == "/help":
        send_message("Commands:\n/status\n/uptime\n/stats\n/health\n/qdrant\n/gemini\n/groq\nJust type a question to ask the AI!", chat_id)

async def handle_ai_query(text: str, chat_id: str):
    """Processes RAG query via LLM Manager."""
    from backend.retrieval import retrieve, rewrite_query
    try:
        start_time = time.time()
        optimized_query = rewrite_query(text)
        
        q_client, _ = get_qdrant_client()
        embed_model = get_embedding_model()
        
        hits, source_label, confidence = retrieve(
            embed_model=embed_model,
            query=optimized_query,
            qdrant_client=q_client,
            top_k=5,
            score_threshold=0.0
        )

        if not hits:
            send_message("⚠️ No source context found.", chat_id)
            return

        prompt = build_rag_prompt(optimized_query, hits)
        
        # Use existing LLM manager with built-in Gemini -> Groq failover
        provider = os.getenv("LLM_PROVIDER", "gemini")
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") if provider == "gemini" else os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        answer = generate_response(prompt, provider=provider, model_name=model, stream=False)
        
        # Format response
        conf_icon = "🟢" if confidence == "High" else "🟡" if confidence == "Medium" else "🔴"
        source_ref = f"\n\n{conf_icon} <b>Confidence:</b> {confidence}"
        
        # Log to analytics
        duration = time.time() - start_time
        AnalyticsStore.add_query(provider, duration)
        
        send_message(answer + source_ref, chat_id)

    except Exception as e:
        send_message(f"❌ <b>AI Error:</b> {e}", chat_id)
