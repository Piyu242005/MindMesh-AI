const API_URL = "http://localhost:8000";
let currentSessionId = localStorage.getItem("session_id");

// On Load
document.addEventListener("DOMContentLoaded", () => {
    // Generate new session ID if not exists
    if (!currentSessionId) {
        currentSessionId = crypto.randomUUID();
        localStorage.setItem("session_id", currentSessionId);
    }

    // Load sessions list
    loadSessions();

    // Load available models
    loadModels();

    // Load current session history
    loadHistory(currentSessionId);

    // Auto-focus input
    document.getElementById("chat-input").focus();
    setupEventListeners();
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
        await fetch(`${API_URL}/sessions/${sessionId}`, { method: "DELETE" });

        if (currentSessionId === sessionId) {
            startNewChat();
        } else {
            loadSessions();
        }
    } catch (e) {
        console.error("Failed to delete session", e);
    }
}

function startNewChat() {
    currentSessionId = crypto.randomUUID();
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

    input.value = "";
    input.style.height = "auto";

    // UI Updates
    document.getElementById("send-btn").style.display = "none";
    const stopBtn = document.getElementById("stop-btn");
    stopBtn.style.display = "flex";

    // Remove welcome screen
    const welcome = document.getElementById("welcome-screen");
    if (welcome) welcome.remove();

    // Add User Message
    try {
        addMessage("user", text);
    } catch (e) {
        console.error("Error adding user message", e);
        return;
    }

    // Create Assistant Message Placeholder
    let assistantContentDiv;
    let cursor;
    let typingDiv;
    const messagesContainer = document.getElementById("messages-container");

    try {
        const assistantMsgId = addMessage("assistant", "");
        const msgEl = document.getElementById(assistantMsgId);
        if (msgEl) {
            assistantContentDiv = msgEl.querySelector(".text");
            const sourcesDiv = msgEl.querySelector(".sources-container");
            const sourcesList = msgEl.querySelector(".sources-list");

            // Add Cursor
            cursor = document.createElement("span");
            cursor.className = "cursor";
            assistantContentDiv.appendChild(cursor);
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
        controller = new AbortController();

        const response = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: text,
                session_id: currentSessionId,
                model: selectedModel
            }),
            signal: controller.signal
        });

        if (!response.ok) throw new Error(`Server Error: ${response.statusText}`);

        // Helper to remove typing safely
        if (typingDiv) {
            typingDiv.remove();
            typingDiv = null;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split("\n\n");

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const dataStr = line.substring(6);
                    if (dataStr === "[DONE]") break;

                    try {
                        const data = JSON.parse(dataStr);

                        if (data.type === "content") {
                            fullResponse += data.content;
                            if (assistantContentDiv) {
                                assistantContentDiv.innerHTML = marked.parse(fullResponse);
                                if (cursor) assistantContentDiv.appendChild(cursor);
                            }
                            scrollToBottom();
                        } else if (data.type === "sources") {
                            // Re-query elements just in case
                            const msgEl = document.getElementById(assistantMsgId);
                            if (msgEl) {
                                const sDiv = msgEl.querySelector(".sources-container");
                                const sList = msgEl.querySelector(".sources-list");
                                renderSources(data.sources, sDiv, sList);
                            }
                        }
                    } catch (e) {
                        console.error("Error parsing chunk", e, line);
                    }
                }
            }
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
            // If we failed before creating the bubble, show alert
            alert("Error sending message: " + error.message);
        }
    } finally {
        if (typingDiv) typingDiv.remove();
        if (cursor && cursor.parentNode) cursor.parentNode.removeChild(cursor);
        scrollToBottom();
        resetInputState();
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
    document.getElementById("send-btn").style.display = "flex";
    document.getElementById("send-btn").disabled = true;
    document.getElementById("stop-btn").style.display = "none";
    document.getElementById("chat-input").focus();
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

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    // Show loading state (simple toast or log)
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
        alert(`Successfully uploaded and indexed ${data.filename} (${data.chunks_added} chunks)`);

    } catch (e) {
        console.error(e);
        alert("Upload failed: " + e.message);
    } finally {
        btn.innerHTML = originalContent;
        btn.disabled = false;
        event.target.value = ""; // Request reset
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
        alert("Speech recognition not supported in this browser.");
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
