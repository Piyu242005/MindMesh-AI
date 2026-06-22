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
    """Processes RAG query via LLM Manager with memory."""
    from backend.retrieval import retrieve, build_rag_prompt, rewrite_query
    from backend.memory import (
        get_conversation, create_conversation, get_chat_history,
        add_message, generate_conversation_title, update_conversation_title,
        generate_conversation_summary, update_conversation_summary
    )
    
    chat_id_str = str(chat_id)
    try:
        start_time = time.time()
        
        # Check if conversation exists, create if not
        conv = get_conversation(chat_id_str)
        is_new = False
        summary = ""
        chat_history = []
        
        if not conv:
            create_conversation(chat_id_str, title="Telegram Chat")
            is_new = True
        else:
            chat_history = get_chat_history(chat_id_str, limit=8)
            summary = conv.get("summary", "")
            
        # Add User Message to DB
        add_message(chat_id_str, role="user", content=text)

        optimized_query = rewrite_query(text)
        
        q_client, _ = get_qdrant_client()
        embed_model = get_embedding_model()
        
        # Fix retrieval unpacking
        retrieval_result = retrieve(
            embed_model=embed_model,
            query=optimized_query,
            qdrant_client=q_client,
            top_k=5,
            score_threshold=0.0
        )
        
        confidence = retrieval_result.get("confidence", "Medium")

        prompt = build_rag_prompt(optimized_query, retrieval_result, chat_history=chat_history, summary=summary)
        
        provider = os.getenv("LLM_PROVIDER", "gemini")
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") if provider == "gemini" else os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        answer = generate_response(prompt, provider=provider, model_name=model, stream=False)
        
        # Add Assistant Message to DB
        add_message(chat_id_str, role="assistant", content=answer, confidence=confidence)
        
        if is_new:
            title = generate_conversation_title(text)
            update_conversation_title(chat_id_str, title)
            
        if len(chat_history) >= 18 and len(chat_history) % 10 == 0:
            from backend.memory import get_full_chat_history
            full_history = get_full_chat_history(chat_id_str)
            new_summary = generate_conversation_summary(full_history)
            update_conversation_summary(chat_id_str, new_summary)
            
        # Format response
        conf_icon = "🟢" if confidence == "High" else "🟡" if confidence == "Medium" else "🔴"
        source_ref = f"\n\n{conf_icon} <b>Confidence:</b> {confidence}"
        
        # Log to analytics
        duration = time.time() - start_time
        AnalyticsStore.add_query(provider, duration)
        
        send_message(answer + source_ref, chat_id)

    except Exception as e:
        send_message(f"❌ <b>AI Error:</b> {e}", chat_id)
