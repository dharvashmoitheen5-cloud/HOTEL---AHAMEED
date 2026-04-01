function toggleChat() {
    const chat = document.getElementById("chatContainer");
    chat.style.display = chat.style.display === "flex" ? "none" : "flex";
}

async function sendMessage() {
    const input = document.getElementById("chatInput");
    const chatBody = document.getElementById("chatBody");
    const language = document.getElementById("languageSelect").value;
    const message = input.value.trim();

    if (message === "") return;

    // User message
    const userMsg = document.createElement("div");
    userMsg.className = "user-message";
    userMsg.textContent = message;
    chatBody.appendChild(userMsg);

    input.value = "";

    // Typing
    const typing = document.createElement("div");
    typing.className = "bot-message";
    typing.textContent = "Typing...";
    chatBody.appendChild(typing);

    chatBody.scrollTop = chatBody.scrollHeight;

    const response = await fetch("/chatbot", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: message,
            language: language
        })
    });

    const data = await response.json();

    typing.remove();

    const botMsg = document.createElement("div");
    botMsg.className = "bot-message";
    botMsg.textContent = data.reply;
    chatBody.appendChild(botMsg);

    // Speak response
    if (typeof speakText === "function") {
        speakText(data.reply, language);
    }

    chatBody.scrollTop = chatBody.scrollHeight;
}

// Enter key support
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("chatInput");
    if (input) {
        input.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                sendMessage();
            }
        });
    }
});