const API_URL = "http://localhost:8000";
let currentSessionId = localStorage.getItem("session_id") || generateUUID();
let chatHistory = [];

document.addEventListener("DOMContentLoaded", () => {
    localStorage.setItem("session_id", currentSessionId);
    loadHistory();
    setupEventListeners();
});

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function setupEventListeners() {
    const input = document.getElementById("chat-input");
    input.addEventListener("input", () => {
        const btn = document.getElementById("send-btn");
        btn.disabled = input.value.trim() === "";
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
}

function setInput(text) {
    const input = document.getElementById("chat-input");
    input.value = text;
    input.dispatchEvent(new Event('input'));
    input.focus();
}

function startNewChat() {
    currentSessionId = generateUUID();
    localStorage.setItem("session_id", currentSessionId);
    document.getElementById("messages-container").innerHTML = `
        <div class="welcome-screen" id="welcome-screen">
             <div class="logo">🎓</div>
             <h1>How can I help you today?</h1>
             <!-- suggestions reused -->
        </div>
    `;
    chatHistory = [];
}

async function loadHistory() {
    // Optional: Fetch history from backend if implemented
    // const res = await fetch(`${API_URL}/history?session_id=${currentSessionId}`);
    // const data = await res.json();
    // Replay messages...
}

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

    // Hide welcome screen
    const welcome = document.getElementById("welcome-screen");
    if (welcome) welcome.style.display = "none";

    // Add User Message
    addMessage("user", text);

    // Create Assistant Message Placeholder
    const assistantMsgId = addMessage("assistant", "");
    const assistantContentDiv = document.getElementById(assistantMsgId).querySelector(".text");
    const sourcesDiv = document.getElementById(assistantMsgId).querySelector(".sources-container");
    const sourcesList = sourcesDiv.querySelector(".sources-list");

    // Add Cursor
    const cursor = document.createElement("span");
    cursor.className = "cursor";
    assistantContentDiv.appendChild(cursor);

    let fullResponse = "";
    controller = new AbortController();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query: text,
                session_id: currentSessionId,
                model: "llama3.2"
            }),
            signal: controller.signal
        });

        if (!response.ok) throw new Error("Network response was not ok");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

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
                            assistantContentDiv.innerHTML = marked.parse(fullResponse);
                            assistantContentDiv.appendChild(cursor);
                            scrollToBottom();
                        } else if (data.type === "sources") {
                            renderSources(data.sources, sourcesDiv, sourcesList);
                        }
                    } catch (e) {
                        console.error("Error parsing chunk", e, line);
                    }
                }
            }
        }

    } catch (error) {
        if (error.name === 'AbortError') {
            assistantContentDiv.innerHTML += " [Stopped]";
        } else {
            assistantContentDiv.innerHTML += `\n\n**Error:** ${error.message}`;
        }
    } finally {
        if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
        scrollToBottom();
        resetInputState();
        controller = null;
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

function addMessage(role, text) {
    const container = document.getElementById("messages-container");
    const template = document.getElementById("message-template");
    const clone = template.content.cloneNode(true);

    const msgDiv = clone.querySelector(".message");
    msgDiv.setAttribute("data-role", role);
    msgDiv.id = `msg-${Date.now()}`;

    const textDiv = clone.querySelector(".text");
    textDiv.innerHTML = role === "user" ? text : ""; // Assistant fills in later

    container.appendChild(msgDiv);
    scrollToBottom();
    return msgDiv.id;
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

function scrollToBottom() {
    const container = document.getElementById("messages-container");
    container.scrollTop = container.scrollHeight;
}
