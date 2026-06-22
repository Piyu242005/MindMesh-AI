import uuid
import json
from datetime import datetime
from backend.database import get_db_connection

def create_conversation(user_id="local_user", title="New Conversation", folder=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    conversation_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO conversations (id, user_id, title, folder) VALUES (?, ?, ?, ?)",
        (conversation_id, user_id, title, folder)
    )
    conn.commit()
    conn.close()
    return conversation_id

def get_conversation(conversation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    conv = cursor.fetchone()
    conn.close()
    return dict(conv) if conv else None

def get_all_conversations(user_id="local_user"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
    convs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return convs

def add_message(conversation_id, role, content, sources=None, confidence=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    msg_id = str(uuid.uuid4())
    sources_json = json.dumps(sources) if sources else None
    
    cursor.execute(
        "INSERT INTO messages (id, conversation_id, role, content, sources, confidence) VALUES (?, ?, ?, ?, ?, ?)",
        (msg_id, conversation_id, role, content, sources_json, confidence)
    )
    cursor.execute(
        "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,)
    )
    conn.commit()
    conn.close()
    return msg_id

def get_chat_history(conversation_id, limit=8):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT ?",
        (conversation_id, limit)
    )
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages[::-1] # Return in chronological order

def get_full_chat_history(conversation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
        (conversation_id,)
    )
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages

def update_conversation_title(conversation_id, new_title):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (new_title, conversation_id))
    conn.commit()
    conn.close()

def update_conversation_summary(conversation_id, summary):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE conversations SET summary = ? WHERE id = ?", (summary, conversation_id))
    conn.commit()
    conn.close()

def toggle_pin(conversation_id, is_pinned):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE conversations SET is_pinned = ? WHERE id = ?", (int(is_pinned), conversation_id))
    conn.commit()
    conn.close()

def update_folder(conversation_id, folder):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE conversations SET folder = ? WHERE id = ?", (folder, conversation_id))
    conn.commit()
    conn.close()

def delete_conversation(conversation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()

def clear_all_conversations(user_id="local_user"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def search_conversations(query, user_id="local_user"):
    conn = get_db_connection()
    cursor = conn.cursor()
    search_query = f"%{query}%"
    
    # Search titles and messages
    cursor.execute("""
        SELECT DISTINCT c.* FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
        WHERE c.user_id = ? AND (c.title LIKE ? OR m.content LIKE ?)
        ORDER BY c.updated_at DESC
    """, (user_id, search_query, search_query))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def get_preference(user_id, key, default=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM user_preferences WHERE user_id = ? AND key = ?", (user_id, key))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else default

def set_preference(user_id, key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_preferences (user_id, key, value, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
        (user_id, key, str(value))
    )
    conn.commit()
    conn.close()

def generate_conversation_title(first_message):
    try:
        from backend.llm_manager import generate_response
        import os
        provider = os.getenv("LLM_PROVIDER", "groq")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") if provider == "gemini" else os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        prompt = f"Generate a short, concise title (max 5 words) for a conversation that starts with: '{first_message}'. Do NOT include quotes, prefixes, or any extra text. Just the title."
        
        title = generate_response(prompt, provider=provider, model_name=model_name, stream=False)
        return title.strip().strip('"').strip("'")
    except Exception:
        return "New Conversation"

def generate_conversation_summary(messages_list):
    try:
        from backend.llm_manager import generate_response
        import os
        provider = os.getenv("LLM_PROVIDER", "groq")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") if provider == "gemini" else os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        chat_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages_list])
        prompt = f"Summarize the following conversation in 3-5 concise sentences. Focus on the core topics discussed and key facts established. Do not include introductory text.\n\nConversation:\n{chat_text}"
        
        summary = generate_response(prompt, provider=provider, model_name=model_name, stream=False)
        return summary.strip()
    except Exception:
        return ""
