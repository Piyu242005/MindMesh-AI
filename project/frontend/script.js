const API_URL = "http://localhost:8000";
let currentSessionId = localStorage.getItem("session_id");
let isGenerating = false;

// ------------------- Mode Selector -------------------

function setMode(mode) {
    // Update active button
    document.querySelectorAll(".mode-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.mode === mode);
    });
    // Persist selection
    localStorage.setItem("selected_mode", mode);

    // Update input placeholder based on mode
    const input = document.getElementById("chat-input");
    if (!input) return;
    if (mode === "qa") {
        input.placeholder = "Ask a question...";
    } else if (mode === "coding") {
        input.placeholder = "Describe what code you need...";
    } else {
        input.placeholder = "Message RAG Assistant...";
    }
}

function getActiveMode() {
    const active = document.querySelector(".mode-btn.active");
    return active ? active.dataset.mode : (localStorage.getItem("selected_mode") || "chat");
}

// ------------------- Helpers -------------------
function generateSessionId() {
    // crypto.randomUUID() can fail in some browsers / contexts (e.g. file://)
    try {
        if (window.crypto && typeof window.crypto.randomUUID === "function") {
            return window.crypto.randomUUID();
        }
    } catch (_) { /* ignore */ }
    return `sess-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function scrollToBottom() {
    const container = document.getElementById("messages-container");
    if (!container) return;
    requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight;
    });
}

function setGenerating(next) {
    isGenerating = next;
    const input = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const stopBtn = document.getElementById("stop-btn");
    const uploadBtn = document.getElementById("upload-btn");
    const micBtn = document.getElementById("mic-btn");

    if (input) input.disabled = next;
    if (uploadBtn) uploadBtn.disabled = next;
    if (micBtn) micBtn.disabled = next;

    if (sendBtn && stopBtn) {
        if (next) {
            sendBtn.style.display = "none";
            stopBtn.style.display = "flex";
        } else {
            stopBtn.style.display = "none";
            sendBtn.style.display = "flex";
            // Enable send if text exists
            sendBtn.disabled = (document.getElementById("chat-input")?.value || "").trim() === "";
        }
    }
}

async function updateBackendStatus() {
    const el = document.getElementById("backend-status");
    if (!el) return;

    const dot = el.querySelector(".dot");
    const label = el.querySelector(".label");

    try {
        const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
        if (!res.ok) throw new Error("bad status");
        const data = await res.json();
        if (data?.status === "ok") {
            el.classList.add("online");
            el.classList.remove("offline");
            if (label) label.textContent = "Online";
            if (dot) dot.setAttribute("aria-label", "Online");
            return;
        }
        throw new Error("unhealthy");
    } catch (_) {
        el.classList.add("offline");
        el.classList.remove("online");
        if (label) label.textContent = "Offline";
        if (dot) dot.setAttribute("aria-label", "Offline");
    }
}

// On Load
document.addEventListener("DOMContentLoaded", () => {
    // Generate new session ID if not exists
    if (!currentSessionId) {
        currentSessionId = generateSessionId();
        localStorage.setItem("session_id", currentSessionId);
    }

    // Load sessions list
    loadSessions();

    // Load available models
    loadModels();

    // Restore saved mode
    const savedMode = localStorage.getItem("selected_mode") || "chat";
    setMode(savedMode);

    // Load current session history
    loadHistory(currentSessionId);

    // Auto-focus input
    document.getElementById("chat-input").focus();
    setupEventListeners();

    // Backend status pill (non-blocking)
    updateBackendStatus();
    setInterval(updateBackendStatus, 5000);
});

async function loadModels() {
    try {
        const response = await fetch(`${API_URL}/models`);
        if (!response.ok) return;

        const data = await response.json();
        const select = document.getElementById("model-select");
        select.innerHTML = ""; // Clear existing options

        if (data.models.length === 0) {
            const option = document.createElement("option");
            option.text = "No models found";
            select.add(option);
            return;
        }

        data.models.forEach(model => {
            const option = document.createElement("option");
            option.value = model;
            option.textContent = model;
            select.appendChild(option);
        });

        // Restore selection if saved
        const savedModel = localStorage.getItem("selected_model");
        if (savedModel && data.models.includes(savedModel)) {
            select.value = savedModel;
        }

        // Save selection on change
        select.onchange = () => {
            localStorage.setItem("selected_model", select.value);
        };

    } catch (e) {
        console.error("Failed to load models", e);
        const select = document.getElementById("model-select");
        select.innerHTML = ""; // Clear

        // Fallback models so UI doesn't look broken
        const fallbackModels = ["llama3.2", "mistral", "gemma:2b"];
        fallbackModels.forEach(model => {
            const option = document.createElement("option");
            option.value = model;
            option.textContent = model;
            select.appendChild(option);
        });
    }
}

function setupEventListeners() {
    const input = document.getElementById("chat-input");
    input.addEventListener("input", () => {
        const btn = document.getElementById("send-btn");
        btn.disabled = input.value.trim() === "";
        autoResize(input);
    });
}

function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
    if (textarea.value === "") textarea.style.height = 'auto';
}

function setInput(text) {
    const input = document.getElementById("chat-input");
    input.value = text;
    input.dispatchEvent(new Event('input'));
    input.focus();
}

// ------------------- Session Management -------------------

async function loadSessions() {
    try {
        const response = await fetch(`${API_URL}/sessions`);
        if (!response.ok) return;

        const sessions = await response.json();
        const listContainer = document.getElementById("history-list");
        listContainer.innerHTML = "";

        sessions.forEach(session => {
            const item = document.createElement("div");
            item.className = "history-item";
            if (session.id === currentSessionId) item.classList.add("active");

            item.innerHTML = `
                <span class="title">${session.title || "New Chat"}</span>
                <span class="delete-btn" title="Delete Chat">×</span>
            `;

            // Click to load
            item.onclick = (e) => {
                loadSession(session.id);
            };

            // Click delete
            const deleteBtn = item.querySelector(".delete-btn");
            deleteBtn.onclick = (e) => {
                e.stopPropagation(); // prevent loading
                deleteSession(session.id);
            };

            listContainer.appendChild(item);
        });
    } catch (e) {
        console.error("Failed to load sessions", e);
    }
}

async function loadSession(sessionId) {
    if (currentSessionId === sessionId) return;

    currentSessionId = sessionId;
    localStorage.setItem("session_id", sessionId);

    // Update active UI
    document.querySelectorAll(".history-item").forEach(item => item.classList.remove("active"));
    loadSessions(); // re-render to set active class

    // Clear chat area
    document.getElementById("messages-container").innerHTML = "";

    // Load history
    await loadHistory(sessionId);
}

async function loadHistory(sessionId) {
    try {
        const response = await fetch(`${API_URL}/history/${sessionId}`);
        if (!response.ok) return;

        const history = await response.json();
        const container = document.getElementById("messages-container");

        if (history.length === 0) {
            // Show welcome screen
            container.innerHTML = `
                <div class="welcome-screen" id="welcome-screen">
                     <div class="logo">🎓</div>
                     <h1>How can I help you today?</h1>
                     <div class="suggestions-grid">
                        <button class="suggestion-card" onclick="setInput('Where is HTML concluded?')">
                            <div class="suggestion-title">HTML Support</div>
                            <div class="suggestion-text">Where is HTML concluded?</div>
                        </button>
                        <button class="suggestion-card" onclick="setInput('How to create forms?')">
                            <div class="suggestion-title">Web Forms</div>
                            <div class="suggestion-text">How to create forms?</div>
                        </button>
                        <button class="suggestion-card" onclick="setInput('CSS Box Model explained')">
                            <div class="suggestion-title">CSS Layout</div>
                            <div class="suggestion-text">Explain the Box Model</div>
                        </button>
                        <button class="suggestion-card" onclick="setInput('What are semantic tags?')">
                            <div class="suggestion-title">Semantic HTML</div>
                            <div class="suggestion-text">What are semantic tags?</div>
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        // Clear welcome screen if exists
        container.innerHTML = "";

        history.forEach(msg => {
            // Don't render "system" messages if any
            if (msg.role === "user" || msg.role === "assistant") {
                addMessage(msg.role, msg.content, false);
            }
        });
        scrollToBottom();
    } catch (e) {
        console.error("Failed to load history", e);
    }
}

async function deleteSession(sessionId) {
    if (!confirm("Delete this chat?")) return;

    try {
        const response = await fetch(`${API_URL}/sessions/${sessionId}`, { method: "DELETE" });
        
        if (!response.ok) {
            throw new Error("Failed to delete session");
        }

        showToast("Chat deleted successfully", 'success');

        if (currentSessionId === sessionId) {
            startNewChat();
        } else {
            loadSessions();
        }
    } catch (e) {
        console.error("Failed to delete session", e);
        showToast("Failed to delete chat: " + e.message, 'error');
    }
}

function startNewChat() {
    currentSessionId = generateSessionId();
    localStorage.setItem("session_id", currentSessionId);

    document.getElementById("messages-container").innerHTML = "";
    loadHistory(currentSessionId); // Will show welcome screen
    loadSessions();
}

// ------------------- Chat Logic -------------------

let controller = null;

async function sendMessage() {
    const input = document.getElementById("chat-input");
    const text = input.value.trim();
    if (!text) return;
    if (isGenerating) return;

    console.log("🚀 sendMessage called with:", text);

    input.value = "";
    input.style.height = "auto";

    // UI Updates
    setGenerating(true);

    // Remove welcome screen
    const welcome = document.getElementById("welcome-screen");
    if (welcome) welcome.remove();

    // Add User Message
    try {
        addMessage("user", text);
        console.log("✅ User message added");
    } catch (e) {
        console.error("Error adding user message", e);
        return;
    }

    // Create Assistant Message Placeholder
    let assistantContentDiv;
    let assistantMsgId;
    let cursor;
    let typingDiv;
    const messagesContainer = document.getElementById("messages-container");

    try {
        assistantMsgId = addMessage("assistant", "");
        console.log("✅ Assistant message placeholder created:", assistantMsgId);
        
        const msgEl = document.getElementById(assistantMsgId);
        if (msgEl) {
            assistantContentDiv = msgEl.querySelector(".text");
            const sourcesDiv = msgEl.querySelector(".sources-container");
            const sourcesList = msgEl.querySelector(".sources-list");

            console.log("✅ Found elements:", {
                contentDiv: !!assistantContentDiv,
                sourcesDiv: !!sourcesDiv,
                sourcesList: !!sourcesList
            });

            // Add Cursor
            cursor = document.createElement("span");
            cursor.className = "cursor";
            assistantContentDiv.appendChild(cursor);
        } else {
            console.error("❌ Could not find message element with ID:", assistantMsgId);
        }

        // Show typing indicator
        typingDiv = document.createElement("div");
        typingDiv.className = "typing-indicator active";
        typingDiv.innerHTML = `
            <span>AI is typing</span>
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        const selectedModel = document.getElementById("model-select").value || "llama3.2";
        const selectedMode = getActiveMode();
        console.log("📡 Sending request to backend with model:", selectedModel, "mode:", selectedMode);
        controller = new AbortController();

        const response = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: text,
                session_id: currentSessionId,
                model: selectedModel,
                mode: selectedMode,
            }),
            signal: controller.signal
        });

        if (!response.ok) throw new Error(`Server Error: ${response.statusText}`);

        // NOTE: Do NOT remove typing indicator here — Llama may take 30-60s to generate.
        // It will be removed when the first content token arrives.
        // Show "Thinking..." placeholder in assistant bubble
        if (assistantContentDiv) {
            assistantContentDiv.innerHTML = '<em style="opacity:0.5">Thinking…</em>';
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = "";
        let buffer = "";
        let streamDone = false;

        console.log("📡 Starting stream reader...");

        while (!streamDone) {
            const { done, value } = await reader.read();
            if (done) {
                console.log("✅ Stream reading completed");
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");

            // Keep the last incomplete line in buffer
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (!line.trim()) continue;

                // Handle SSE format (data: {...})
                let jsonStr = line;
                if (line.startsWith("data: ")) {
                    jsonStr = line.substring(6);
                    if (jsonStr === "[DONE]") {
                        console.log("🏁 Received DONE signal");
                        streamDone = true;
                        break; // exits for-loop; while condition re-checked → exits
                    }
                }

                try {
                    const data = JSON.parse(jsonStr);

                    if (data.type === "content") {
                        const delta = (data.data ?? data.content ?? "");
                        if (!delta) continue;
                        fullResponse += delta;

                        // Remove typing indicator on first token
                        if (typingDiv) { typingDiv.remove(); typingDiv = null; }

                        if (assistantContentDiv) {
                            try {
                                assistantContentDiv.innerHTML = marked.parse(fullResponse);
                            } catch (_) {
                                assistantContentDiv.textContent = fullResponse;
                            }
                            if (cursor) assistantContentDiv.appendChild(cursor);
                        }
                        scrollToBottom();

                    } else if (data.type === "sources") {
                        const sources = (data.data ?? data.sources ?? []);
                        console.log("📚 Sources received:", sources?.length || 0);
                        const msgEl = document.getElementById(assistantMsgId);
                        if (msgEl) {
                            const sDiv = msgEl.querySelector(".sources-container");
                            const sList = msgEl.querySelector(".sources-list");
                            renderSources(sources, sDiv, sList);
                        }

                    } else if (data.type === "error") {
                        if (typingDiv) { typingDiv.remove(); typingDiv = null; }
                        if (assistantContentDiv) {
                            assistantContentDiv.innerHTML = `<span style="color:#ef4444">⚠️ ${data.message || "Unknown error"}</span>`;
                        }
                        streamDone = true;
                        break;
                    }
                } catch (e) {
                    console.error("❌ Error parsing chunk:", e, line.substring(0, 100));
                }
            }
        }

        // If Llama returned nothing at all, show a fallback
        if (!fullResponse && assistantContentDiv) {
            assistantContentDiv.innerHTML = '<span style="opacity:0.6">No response received. Check that Ollama is running and the model is loaded.</span>';
        }

        // Speak response
        if (fullResponse) speak(fullResponse);

    } catch (error) {
        console.error("Chat Error:", error);
        if (assistantContentDiv) {
            if (error.name === 'AbortError') {
                assistantContentDiv.innerHTML += " [Stopped]";
            } else {
                assistantContentDiv.innerHTML += `\n\n**Error:** ${error.message || "Failed to get response"}`;
            }
            if (cursor && cursor.parentNode) cursor.parentNode.removeChild(cursor);
        } else {
            // If we failed before creating the bubble, show toast
            showToast("Error sending message: " + error.message, 'error');
        }
    } finally {
        if (typingDiv) typingDiv.remove();
        if (cursor && cursor.parentNode) cursor.parentNode.removeChild(cursor);
        scrollToBottom();
        resetInputState();
        setGenerating(false);
        controller = null;
        loadSessions();
    }
}

function stopGeneration() {
    if (controller) {
        controller.abort();
    }
}

function resetInputState() {
    const input = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const stopBtn = document.getElementById("stop-btn");

    if (sendBtn) sendBtn.style.display = "flex";
    if (stopBtn) stopBtn.style.display = "none";
    if (sendBtn) sendBtn.disabled = (input?.value || "").trim() === "";
    if (input) input.focus();
}

function addMessage(role, text, isStream = true) {
    const container = document.getElementById("messages-container");
    const template = document.getElementById("message-template");
    const clone = template.content.cloneNode(true);

    const msgDiv = clone.querySelector(".message");
    const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    msgDiv.id = msgId;
    msgDiv.setAttribute("data-role", role);

    const textDiv = clone.querySelector(".text");

    if (role === "assistant" && !isStream) {
        textDiv.innerHTML = marked.parse(text);
    } else {
        textDiv.textContent = text;
    }

    container.appendChild(msgDiv);
    scrollToBottom();
    return msgId;
}

function renderSources(sources, container, list) {
    if (!sources || sources.length === 0) return;

    container.style.display = "block";
    list.innerHTML = sources.map(src => {
        const start = formatTime(src.start);
        const end = formatTime(src.end);
        return `
            <div class="source-item">
                <div class="source-time">🎥 ${src.title} (${start} - ${end})</div>
                <div class="source-text">${src.text}</div>
            </div>
        `;
    }).join("");
    scrollToBottom();
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
}

// ------------------- Theme Logic -------------------

function toggleTheme() {
    const body = document.body;
    const btn = document.querySelector(".theme-toggle-btn .icon");

    body.classList.toggle("light-theme");

    const isLight = body.classList.contains("light-theme");
    btn.textContent = isLight ? "🌙" : "☀️";

    localStorage.setItem("theme", isLight ? "light" : "dark");
}

// Initialize Theme
document.addEventListener("DOMContentLoaded", () => {
    const savedTheme = localStorage.getItem("theme");
    const btn = document.querySelector(".theme-toggle-btn .icon");

    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
        if (btn) btn.textContent = "🌙";
    }

    // Modal Events
    setupModalEvents();
});

// --- Modal Logic ---
function setupModalEvents() {
    const userProfile = document.querySelector('.user-profile');
    const settingsBtn = document.querySelector('.settings-btn');

    if (userProfile) {
        userProfile.onclick = () => openModal('user-modal');
    }

    if (settingsBtn) {
        settingsBtn.onclick = () => openModal('settings-modal');
    }

    // Close on outside click
    window.onclick = (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.classList.remove('show');
        }
    };
}

function openModal(id) {
    document.getElementById(id).classList.add('show');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('show');
}

function toggleThemeInSettings(btn) {
    toggleTheme();
    btn.classList.toggle('active');
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
        <div class="msg">${message}</div>
    `;
    
    container.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 200);
    }, 3000);
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['text/plain', 'application/pdf', 'text/markdown'];
    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.txt') && !file.name.endsWith('.pdf') && !file.name.endsWith('.md')) {
        showToast('Please upload a valid file type (TXT, PDF, or MD)', 'error');
        event.target.value = "";
        return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
        showToast('File size must be less than 10MB', 'error');
        event.target.value = "";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    // Show loading state
    const btn = document.getElementById("upload-btn");
    const originalContent = btn.innerHTML;
    btn.innerHTML = "⏳";
    btn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Upload failed");
        }

        const data = await response.json();
        showToast(`Successfully uploaded ${data.filename} (${data.chunks_added} chunks indexed)`, 'success');

    } catch (e) {
        console.error(e);
        showToast("Upload failed: " + e.message, 'error');
    } finally {
        btn.innerHTML = originalContent;
        btn.disabled = false;
        event.target.value = ""; // Reset input
    }
}

// ------------------- Voice Logic -------------------

let recognition = null;
let isListening = false;
let synth = window.speechSynthesis;

if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        const input = document.getElementById("chat-input");
        input.value += (input.value ? " " : "") + text;
        autoResize(input);
        document.getElementById("send-btn").disabled = false;
        stopListening();
        // Optional: Auto-send
        // sendMessage();
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        stopListening();
    };

    recognition.onend = () => {
        stopListening();
    };
}

function toggleVoice() {
    if (!recognition) {
        showToast("Speech recognition not supported in this browser.", 'error');
        return;
    }

    if (isListening) {
        stopListening();
    } else {
        startListening();
    }
}

function startListening() {
    try {
        recognition.start();
        isListening = true;
        document.getElementById("mic-btn").classList.add("listening");
    } catch (e) {
        console.error(e);
    }
}

function stopListening() {
    try {
        recognition.stop();
        isListening = false;
        document.getElementById("mic-btn").classList.remove("listening");
    } catch (e) {
        console.error(e);
    }
}

function speak(text) {
    if (synth.speaking) synth.cancel();

    // Check if user has muted/disabled TTS (can add a toggle for this later)
    // For now, let's just speak if it's brief or user requested? 
    // Actually, let's keep it simple: speak the response.

    const utterance = new SpeechSynthesisUtterance(text);
    // Simple regex to strip markdown for cleaner speech
    utterance.text = text.replace(/[*#`_]/g, '');
    synth.speak(utterance);
}

// Update sendMessage to speak response
// ------------------- End of Voice Logic -------------------
