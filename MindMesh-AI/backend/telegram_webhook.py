import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from dotenv import load_dotenv



from backend.telegram_helper import send_notification
from process_incoming import (
    create_embedding, 
    retrieve_from_qdrant, 
    retrieve_from_joblib, 
    build_rag_prompt, 
    inference,
    qdrant_client
)

load_dotenv()

app = FastAPI(title="MindMesh AI Telegram Webhook")

@app.post("/telegram_webhook")
async def telegram_webhook(request: Request):
    """Receive incoming Telegram messages via Webhook."""
    try:
        data = await request.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # Extract message details
    if "message" not in data:
        return {"status": "ignored"}
        
    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if not text:
        return {"status": "ignored"}

    # Handle /start command
    if text.startswith("/start"):
        send_notification("👋 Welcome to MindMesh AI!\nAsk me any question about your processed video courses.", chat_id)
        return {"status": "ok"}

    try:
        # 1. Generate embedding
        query_vector = create_embedding(text)

        # 2. Retrieve context
        if qdrant_client is not None:
            hits = retrieve_from_qdrant(qdrant_client, query_vector)
        else:
            hits = retrieve_from_joblib(query_vector)

        if not hits:
            send_notification("⚠️ No course content found. Have you uploaded and processed your videos yet?", chat_id)
            return {"status": "ok"}

        # 3. Build prompt and generate answer
        prompt = build_rag_prompt(text, hits)
        response_dict = inference(prompt)
        answer = response_dict.get("response", "Sorry, I couldn't generate an answer.")

        # 4. Format source reference
        top_hit = hits[0]
        mins, secs = divmod(int(top_hit["start"]), 60)
        source_ref = f"\n\n📚 <b>Source:</b> Video {top_hit['number']} - {top_hit['title']}\n⏱️ <b>Timestamp:</b> {mins}:{secs:02d}"

        # 5. Send back to Telegram
        final_message = answer + source_ref
        send_notification(final_message, chat_id)

    except Exception as e:
        send_notification(f"❌ <b>Error processing query:</b> {str(e)}", chat_id)

    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # Local testing setup
    # Run via: uvicorn backend.telegram_webhook:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
