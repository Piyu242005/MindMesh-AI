import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "chat_history.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Create sessions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create messages table
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_session(session_id: str, title: str = "New Chat"):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT OR IGNORE INTO sessions (id, title) VALUES (?, ?)", (session_id, title))
        conn.commit()
    finally:
        conn.close()

def update_session_title(session_id: str, title: str):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
        conn.commit()
    finally:
        conn.close()

def save_message(session_id: str, role: str, content: str):
    conn = get_db()
    c = conn.cursor()
    try:
        # Ensure session exists
        create_session(session_id)
        
        c.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", 
                  (session_id, role, content))
        conn.commit()
    finally:
        conn.close()

def get_chat_history(session_id: str) -> List[Dict]:
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
        rows = c.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]
    finally:
        conn.close()

def get_all_sessions() -> List[Dict]:
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC")
        rows = c.fetchall()
        return [{"id": row["id"], "title": row["title"], "created_at": row["created_at"]} for row in rows]
    finally:
        conn.close()

def delete_session(session_id: str):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()

# Initialize API
if __name__ == "__main__":
    init_db()
