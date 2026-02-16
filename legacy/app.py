"""Streamlit web UI for the RAG Course Assistant."""

import streamlit as st
import logging
import json
import time
from datetime import datetime
from config import Config
from utils import check_ollama_availability, inference, seconds_to_timestamp
from search import HybridSearchEngine
from prompts import build_query_prompt, build_summary_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG.app")

# ──────────────────────────── Page Config ────────────────────────────
st.set_page_config(
    page_title="RAG Course Assistant | Piyush Ramteke",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────── Custom Theme CSS ────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* ═══════════════════ CHATGPT DARK THEME ═══════════════════ */
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    :root {
        --bg-primary: #212121;
        --bg-secondary: #2f2f2f;
        --bg-tertiary: #1a1a1a;
        --border-color: #3e3e3e;
        --text-primary: #ececec;
        --text-secondary: #b4b4b4;
        --text-muted: #8e8e8e;
        --accent-color: #19c37d;
        --hover-bg: #2a2a2a;
    }
    
    /* Main Background - Solid Dark */
    [data-testid="stAppViewContainer"] {
        background: var(--bg-primary) !important;
    }
    
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    
    [data-testid="stMainBlockContainer"] {
        padding-top: 2rem !important;
        padding-bottom: 140px !important;
        max-width: 900px !important;
        margin: 0 auto !important;
    }
    
    .stApp {
        background: var(--bg-primary);
        color: var(--text-primary) !important;
    }
    
    /* ═══════════════════ SIDEBAR - DARK ═══════════════════ */
    [data-testid="stSidebar"] {
        background: var(--bg-tertiary) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: var(--text-primary) !important;
    }
    
    /* ═══════════════════ ANIMATIONS ═══════════════════ */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    [data-testid="stChatMessage"] {
        animation: fadeIn 0.3s ease-out;
    }
    
    .stButton > button {
        animation: slideIn 0.2s ease-out;
    }
    
    /* ═══════════════════ HERO SECTION - CHATGPT STYLE ═══════════════════ */
    .hero-container {
        text-align: center;
        padding: 80px 40px 40px;
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 40vh;
    }
    
    .hero-title {
        font-size: 48px;
        font-weight: 600;
        line-height: 1.3;
        margin-bottom: 60px;
        color: var(--text-primary);
        letter-spacing: -0.5px;
    }
    
    .hero-subtitle {
        font-size: 16px;
        font-weight: 400;
        color: var(--text-secondary);
        line-height: 1.5;
        max-width: 600px;
        margin: 0 auto 60px;
    }
    
    /* Suggestion button container spacing */
    div[data-testid="column"] {
        padding: 4px 6px !important;
    }
    
    /* ═══════════════════ BUTTONS - CLEAN ═══════════════════ */
    .stButton > button {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 12px 20px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    
    /* Secondary buttons styled as suggestion chips */
    button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 20px !important;
        padding: 10px 18px !important;
        color: var(--text-secondary) !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        white-space: normal !important;
        text-align: center !important;
        line-height: 1.4 !important;
        min-height: 42px !important;
    }
    
    button[kind="secondary"]:hover {
        background: var(--hover-bg) !important;
        border-color: var(--text-muted) !important;
        color: var(--text-primary) !important;
    }
    
    .stButton > button:hover {
        background: var(--hover-bg) !important;
        border-color: var(--text-muted) !important;
    }
    
    .stButton > button:active {
        transform: scale(0.98) !important;
    }
    
    /* ═══════════════════ CHAT INPUT - CENTERED LIKE CHATGPT ═══════════════════ */
    [data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 1000 !important;
        background: var(--bg-primary) !important;
        padding: 20px 0 !important;
        border-top: 1px solid var(--border-color) !important;
        box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.4) !important;
    }
    
    [data-testid="stChatInput"] > div {
        max-width: 800px !important;
        margin: 0 auto !important;
        padding: 0 20px !important;
    }
    
    .stChatInput > div > textarea,
    .stTextInput > div > div > input {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 24px !important;
        color: var(--text-primary) !important;
        padding: 14px 20px !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
        resize: none !important;
        min-height: 52px !important;
        max-height: 200px !important;
    }
    
    .stChatInput > div > textarea:focus,
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-color) !important;
        outline: none !important;
        box-shadow: 0 2px 12px rgba(25, 195, 125, 0.2) !important;
    }
    
    .stChatInput > div > textarea::placeholder {
        color: var(--text-muted) !important;
        font-size: 15px !important;
    }
    
    /* Send button styling */
    [data-testid="stChatInput"] button {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        padding: 8px 12px !important;
        transition: all 0.2s ease !important;
        margin-left: 8px !important;
    }
    
    [data-testid="stChatInput"] button:hover {
        background: var(--accent-color) !important;
        border-color: var(--accent-color) !important;
        color: #000 !important;
    }
    
    [data-testid="stChatInput"] button:disabled {
        opacity: 0.4 !important;
        cursor: not-allowed !important;
    }
    
    /* ═══════════════════ CHAT MESSAGES - FLAT ═══════════════════ */
    [data-testid="stChatMessageContent"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        color: var(--text-primary) !important;
        box-shadow: none !important;
    }
    
    [data-testid="stChatMessage"] {
        margin-bottom: 12px;
    }
    
    /* User Message */
    [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"] {
        background: var(--bg-tertiary) !important;
    }
    
    /* ═══════════════════ EXPANDER - MINIMAL ═══════════════════ */
    .streamlit-expanderHeader {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-secondary) !important;
        padding: 10px 14px !important;
        font-weight: 500 !important;
        transition: background 0.2s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--hover-bg) !important;
    }
    
    /* ═══════════════════ SLIDERS & INPUTS ═══════════════════ */
    .stSlider > div > div > div {
        background: var(--border-color) !important;
    }
    
    .stSlider > div > div > div > div {
        background: var(--accent-color) !important;
    }
    
    .stSelectbox > div > div,
    .stCheckbox > label {
        color: var(--text-primary) !important;
    }
    
    .stSelectbox > div > div > div {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
    }
    
    /* ═══════════════════ TYPOGRAPHY ═════════════════════ */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px !important;
    }
    
    h1 {
        font-size: 40px !important;
    }
    
    h2 {
        font-size: 32px !important;
    }
    
    h3 {
        font-size: 24px !important;
    }
    
    p, label, .stMarkdown, .stText {
        color: var(--text-primary) !important;
        line-height: 1.6;
    }
    
    .stCaption {
        color: var(--text-muted) !important;
        font-size: 14px;
        font-weight: 400;
    }
    
    /* ═══════════════════ STATUS MESSAGES ═══════════════════ */
    .stSuccess {
        background: rgba(25, 195, 125, 0.1) !important;
        border: 1px solid rgba(25, 195, 125, 0.3) !important;
        color: var(--accent-color) !important;
        border-radius: 8px;
        padding: 12px 16px;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        color: #ef4444 !important;
        border-radius: 8px;
        padding: 12px 16px;
    }
    
    /* ═══════════════════ DIVIDER ═══════════════════ */
    hr {
        border-color: var(--border-color) !important;
        margin: 20px 0;
    }
    
    /* ═══════════════════ FOOTER ═══════════════════ */
    .footer {
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        background: var(--bg-tertiary);
        border-top: 1px solid var(--border-color);
        text-align: center;
        padding: 14px 20px;
        z-index: 100;
    }
    
    .footer a {
        color: var(--accent-color);
        text-decoration: none;
        font-weight: 500;
        transition: opacity 0.2s ease;
    }
    
    .footer a:hover {
        opacity: 0.8;
    }
    
    /* ═══════════════════ SCROLLBAR ═══════════════════ */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
    
    /* ═══════════════════ REMOVE STREAMLIT BRANDING ═══════════════════ */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ═══════════════════ MOBILE RESPONSIVE ═══════════════════ */
    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1rem 1rem 140px 1rem !important;
        }
        
        [data-testid="stChatInput"] > div {
            max-width: 100% !important;
            padding: 0 16px !important;
        }
        
        .hero-container {
            padding: 60px 20px 30px !important;
            min-height: 35vh !important;
        }
        
        .hero-title {
            font-size: 32px !important;
            margin-bottom: 40px !important;
        }
        
        .hero-subtitle {
            font-size: 16px !important;
        }
        
        button[kind="secondary"] {
            font-size: 13px !important;
            padding: 8px 14px !important;
            min-height: 38px !important;
        }
        
        .stButton > button {
            font-size: 13px !important;
            padding: 10px 16px !important;
        }
    }
    
    @media (max-width: 480px) {
        [data-testid="stMainBlockContainer"] {
            padding: 0.5rem 0.5rem 140px 0.5rem !important;
        }
        
        .hero-container {
            padding: 40px 15px 25px !important;
            min-height: 30vh !important;
        }
        
        .hero-title {
            font-size: 26px !important;
            margin-bottom: 35px !important;
        }
        
        .hero-subtitle {
            font-size: 14px !important;
        }
        
        button[kind="secondary"] {
            font-size: 12px !important;
            padding: 7px 12px !important;
            min-height: 36px !important;
        }
    }
    
    /* ═══════════════════ COPY BUTTON STYLES ═══════════════════ */
    .copy-button {
        position: absolute;
        top: 8px;
        right: 8px;
        background: var(--hover-bg);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 4px 8px;
        cursor: pointer;
        font-size: 12px;
        color: var(--text-muted);
        transition: all 0.2s ease;
    }
    
    .copy-button:hover {
        background: var(--bg-secondary);
        color: var(--text-primary);
    }
    
    .copy-button.copied {
        color: var(--accent-color);
    }
    
    .message-container {
        position: relative;
    }
    
    /* ═══════════════════ ACCESSIBILITY ═══════════════════ */
    .stButton > button:focus,
    .stChatInput > div > textarea:focus {
        outline: 2px solid var(--accent-color) !important;
        outline-offset: 2px !important;
    }
    
    *:focus-visible {
        outline: 2px solid var(--accent-color);
        outline-offset: 2px;
    }
</style>

<script>
// Copy to clipboard functionality
function copyToClipboard(text, buttonId) {
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.getElementById(buttonId);
        if (btn) {
            btn.textContent = '✓ Copied';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.textContent = '📋 Copy';
                btn.classList.remove('copied');
            }, 2000);
        }
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const input = document.querySelector('[data-testid="stChatInput"] textarea');
        if (input) input.focus();
    }
    
    // Ctrl/Cmd + Shift + C to clear chat
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
        e.preventDefault();
        const clearBtn = Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('Clear Chat'));
        if (clearBtn) clearBtn.click();
    }
});

// Scroll to bottom on new messages
const observer = new MutationObserver(() => {
    const messages = document.querySelectorAll('[data-testid="stChatMessage"]');
    if (messages.length > 0) {
        messages[messages.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
});

setTimeout(() => {
    const chatContainer = document.querySelector('[data-testid="stMainBlockContainer"]');
    if (chatContainer) {
        observer.observe(chatContainer, { childList: true, subtree: true });
    }
}, 1000);

// Enhanced copy functionality for assistant messages
document.addEventListener('click', function(e) {
    if (e.target.textContent === '📋' || e.target.closest('button[kind="secondary"]')?.textContent.includes('📋')) {
        const messageContent = e.target.closest('[data-testid="stChatMessage"]')?.querySelector('[data-testid="stMarkdownContainer"]');
        if (messageContent) {
            navigator.clipboard.writeText(messageContent.innerText).then(() => {
                console.log('Copied to clipboard!');
            });
        }
    }
});

// Add scroll to top button
window.addEventListener('scroll', function() {
    let scrollBtn = document.getElementById('scroll-to-top');
    if (!scrollBtn) {
        scrollBtn = document.createElement('button');
        scrollBtn.id = 'scroll-to-top';
        scrollBtn.innerHTML = '↑';
        scrollBtn.style.cssText = `
            position: fixed;
            bottom: 80px;
            right: 20px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 50%;
            width: 45px;
            height: 45px;
            font-size: 20px;
            color: var(--text-primary);
            cursor: pointer;
            display: none;
            z-index: 1000;
            transition: all 0.3s ease;
        `;
        scrollBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        document.body.appendChild(scrollBtn);
    }
    
    if (window.pageYOffset > 300) {
        scrollBtn.style.display = 'block';
    } else {
        scrollBtn.style.display = 'none';
    }
});
</script>
""", unsafe_allow_html=True)

# ──────────────────────────── Session State ────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "engine" not in st.session_state:
    st.session_state.engine = None
if "regenerate_prompt" not in st.session_state:
    st.session_state.regenerate_prompt = None
if "last_query_time" not in st.session_state:
    st.session_state.last_query_time = 0
if "message_timestamps" not in st.session_state:
    st.session_state.message_timestamps = []


# ──────────────────────────── Sidebar ────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")

    model = st.selectbox(
        "LLM Model",
        ["llama3.2", "llama3.1", "deepseek-r1", "mistral", "gemma2"],
        index=0,
    )
    
    # Collapsible Advanced Settings
    with st.expander("🔧 Advanced Settings", expanded=False):
        top_k = st.slider("Number of results", 1, 15, Config.TOP_K_RESULTS)
        use_reranker = st.checkbox("Enable Reranking", value=True)
        temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)

    st.divider()
    st.markdown("### 📊 System Status")

    # Check Ollama
    ollama_ok = check_ollama_availability()
    if ollama_ok:
        st.success("✅ Ollama is running")
    else:
        st.error("❌ Ollama is not running")

    # Chat management buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("📥 Export", use_container_width=True):
            if st.session_state.messages:
                chat_data = {
                    "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "model": model,
                    "conversation": st.session_state.messages
                }
                json_str = json.dumps(chat_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="💾 Download JSON",
                    data=json_str,
                    file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            else:
                st.info("No messages to export")

    st.divider()
    st.markdown(
        """
        <div style='padding: 20px; 
        background: #2f2f2f; 
        border-radius: 8px; 
        border: 1px solid #3e3e3e; 
        text-align: center;'>
        <h4 style='color: #ececec; margin: 0 0 12px 0; font-size: 18px; font-weight: 600;'>🎓 Course Assistant</h4>
        <p style='color: #b4b4b4; font-size: 14px; margin: 12px 0; line-height: 1.5;'>
        AI-powered search for<br/>Sigma Web Development Course
        </p>
        <hr style='border-color: #3e3e3e; margin: 16px 0;'/>
        <p style='color: #ececec; font-size: 13px; margin: 8px 0; font-weight: 500;'>
        Built by Piyush Ramteke
        </p>
        <p style='color: #8e8e8e; font-size: 12px; margin: 4px 0;'>
        Hybrid RAG • Ollama • Streamlit
        </p>
        <p style='color: #8e8e8e; font-size: 11px; margin-top: 8px;'>
        Shortcuts: <b>Ctrl+K</b> (Focus) • <b>Ctrl+Shift+C</b> (Clear)
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ──────────────────────────── Initialize Engine ────────────────────────────
@st.cache_resource
def load_engine(use_reranker: bool):
    """Load the search engine (cached across reruns)."""
    try:
        return HybridSearchEngine(use_reranker=use_reranker)
    except Exception as e:
        st.error(f"Failed to load search engine: {e}")
        return None


engine = load_engine(use_reranker)

# ──────────────────────────── Main UI ────────────────────────────
# Hero Section (shown when no messages)
if not st.session_state.messages:
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">What's on your mind today?</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Centered suggestion buttons
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        suggestions = [
            "Where is HTML concluded?",
            "How to create forms?",
            "CSS Box Model explained",
            "What are semantic tags?",
            "Adding images in HTML",
        ]
        
        # Create buttons in a grid
        button_cols = st.columns(3)
        for i, suggestion in enumerate(suggestions):
            with button_cols[i % 3]:
                if st.button(suggestion, key=f"suggest_{i}", type="secondary", use_container_width=True):
                    st.session_state.messages.append(
                        {"role": "user", "content": suggestion}
                    )
                    st.rerun()
else:
    st.markdown("<h1 style='font-size: 32px; margin-bottom: 8px; text-align: center;'>🎓 RAG Course Assistant</h1>", unsafe_allow_html=True)
    st.caption("💬 Ask anything about the Sigma Web Development Course — get answers with video timestamps!")

# Display chat history
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        # Show timestamp if available
        if idx < len(st.session_state.message_timestamps):
            timestamp = st.session_state.message_timestamps[idx]
            st.caption(f"🕐 {timestamp}")
        
        st.markdown(msg["content"])
        
        # Add copy button for assistant messages
        if msg["role"] == "assistant":
            col1, col2, col3 = st.columns([6, 1, 1])
            with col2:
                if st.button("📋", key=f"copy_{idx}", help="Copy response"):
                    st.toast("✅ Copied to clipboard!")
                    # Copy functionality handled by JavaScript
            with col3:
                # Show regenerate only for the last assistant message
                if idx == len(st.session_state.messages) - 1:
                    if st.button("🔄", key=f"regen_{idx}", help="Regenerate response"):
                        # Remove last assistant message and trigger regeneration
                        st.session_state.messages.pop()
                        if st.session_state.message_timestamps:
                            st.session_state.message_timestamps.pop()
                        if st.session_state.messages:  # Get the last user message
                            last_user_msg = st.session_state.messages[-1]["content"]
                            st.session_state.regenerate_prompt = last_user_msg
                        st.rerun()
        
        if msg["role"] == "assistant" and "sources" in msg:
            with st.expander("📎 Source Chunks", expanded=False):
                for src in msg["sources"]:
                    start_ts = seconds_to_timestamp(src["start"])
                    end_ts = seconds_to_timestamp(src["end"])
                    start_seconds = int(src["start"])
                    
                    # Create clickable timestamp (assumes YouTube URLs)
                    video_title = src.get('title', 'Unknown')
                    video_num = src.get('number', '')
                    
                    st.markdown(
                        f"**🎥 Video {video_num}: {video_title}**"
                    )
                    st.markdown(
                        f"⏱️ [{start_ts} - {end_ts}](javascript:void(0)) "
                        f"<small style='color: #8e8e8e;'>({start_seconds}s)</small>",
                        unsafe_allow_html=True
                    )
                    
                    # Expandable text preview
                    text_preview = src["text"][:150] + "..." if len(src["text"]) > 150 else src["text"]
                    with st.expander("📄 View full text", expanded=False):
                        st.text(src["text"])
                    st.caption(text_preview)
                    st.divider()

# Handle regeneration
if st.session_state.regenerate_prompt:
    prompt = st.session_state.regenerate_prompt
    st.session_state.regenerate_prompt = None  # Reset
    process_query = True
else:
    prompt = st.chat_input("Ask anything...")
    process_query = bool(prompt)

# Chat input with rate limiting
if process_query and prompt:
    # Rate limiting check (3 second cooldown)
    current_time = time.time()
    time_since_last = current_time - st.session_state.last_query_time
    cooldown_time = 3  # seconds
    
    if time_since_last < cooldown_time and st.session_state.last_query_time != 0:
        remaining = int(cooldown_time - time_since_last)
        st.warning(f"⏳ Please wait {remaining} second(s) before sending another message.")
    elif not engine:
        st.error("❌ Search engine not loaded. Check that embeddings exist.")
        st.info("💡 Try running the preprocessing script to generate embeddings.")
    elif not ollama_ok:
        st.error("❌ Ollama is not running. Please start it first.")
        st.info("💡 Run: `ollama serve` in your terminal")
    else:
        # Update last query time
        st.session_state.last_query_time = current_time
        
        # Get current timestamp
        message_time = datetime.now().strftime("%I:%M %p")
        
        # Add user message (only if not regenerating)
        if not st.session_state.regenerate_prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.message_timestamps.append(message_time)
            with st.chat_message("user"):
                st.caption(f"🕐 {message_time}")
                st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching and generating response..."):
                # Build enhanced query with conversation context
                if len(st.session_state.messages) > 2:
                    last_exchange = st.session_state.messages[-3:-1]
                    context_str = " ".join(
                        m["content"][:100] for m in last_exchange
                    )
                    enhanced_query = f"Context: {context_str}. Question: {prompt}"
                else:
                    enhanced_query = prompt

                # Search
                results = engine.search(enhanced_query, top_k=top_k)

                if not results:
                    response = (
                        "I couldn't find relevant content for your question. "
                        "Try asking about HTML, CSS, or other web development topics covered in the course."
                    )
                    sources = []
                else:
                    # Build prompt and get response
                    llm_prompt = build_query_prompt(prompt, results)
                    response = inference(llm_prompt, model=model, temperature=temperature)
                    sources = results

                st.markdown(response)

                if sources:
                    with st.expander("📎 Source Chunks", expanded=False):
                        for src in sources:
                            start_ts = seconds_to_timestamp(src["start"])
                            end_ts = seconds_to_timestamp(src["end"])
                            start_seconds = int(src["start"])
                            
                            st.markdown(f"**🎥 Video {src['number']}: {src['title']}**")
                            st.markdown(
                                f"⏱️ [{start_ts} - {end_ts}](javascript:void(0)) "
                                f"<small style='color: #8e8e8e;'>({start_seconds}s)</small>",
                                unsafe_allow_html=True
                            )
                            
                            text_preview = src["text"][:150] + "..." if len(src["text"]) > 150 else src["text"]
                            with st.expander("📄 View full text", expanded=False):
                                st.text(src["text"])
                            st.caption(text_preview)
                            st.divider()

        # Save assistant message
        assistant_time = datetime.now().strftime("%I:%M %p")
        st.session_state.messages.append(
            {"role": "assistant", "content": response, "sources": sources if sources else []}
        )
        st.session_state.message_timestamps.append(assistant_time)

# ──────────────────────────── Footer ────────────────────────────
st.markdown("""
<style>
.footer {
    position: relative;
    margin-top: 60px;
    padding: 24px 0;
    text-align: center;
    border-top: 1px solid var(--border-color);
}

.footer a {
    color: var(--accent-color);
    text-decoration: none;
    transition: all 0.2s ease;
    font-weight: 500;
}

.footer a:hover {
    color: var(--text-primary);
    text-decoration: underline;
}
</style>

<div class="footer">
    <p style="margin:0; color: var(--text-secondary); font-size: 14px; line-height: 1.8;">
        Made with ❤️ by 
        <a href="https://www.linkedin.com/in/piyu24" target="_blank" rel="noopener">Piyush Ramteke</a>
        <br>
        <a href="mailto:piyu.143247@gmail.com">piyu.143247@gmail.com</a>
        <br>
        <span style="color: var(--text-muted); font-size: 12px;">
            Powered by Hybrid RAG • Ollama • Streamlit
        </span>
    </p>
</div>
""", unsafe_allow_html=True)
