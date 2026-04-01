function startVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Voice recognition is not supported in your browser. Please use Google Chrome.");
        return;
    }

    const language = document.getElementById("languageSelect").value;

    const languageMap = {
        "English": "en-US",
        "Tamil": "ta-IN",
        "Arabic": "ar-SA",
        "Hindi": "hi-IN"
    };

    const recognition = new SpeechRecognition();
    recognition.lang = languageMap[language] || "en-US";
    recognition.start();

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById("chatInput").value = transcript;
        sendMessage();
    };

    recognition.onerror = function (event) {
        console.error("Voice recognition error:", event.error);
    };
}

function speakText(text, language = "English") {
    const speech = new SpeechSynthesisUtterance(text);

    const languageMap = {
        "English": "en-US",
        "Tamil": "ta-IN",
        "Arabic": "ar-SA",
        "Hindi": "hi-IN"
    };

    speech.lang = languageMap[language] || "en-US";
    speech.rate = 1;
    speech.pitch = 1;

    window.speechSynthesis.speak(speech);
}