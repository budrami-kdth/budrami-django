// DOM 요소 가져오기
const recordButton = document.getElementById('recordButton');
const chatContainer = document.getElementById('chatContainer');
const textInput = document.getElementById('textInput');
const sendButton = document.getElementById('sendButton');
const waveform = document.getElementById('waveform');
const interimResult = document.getElementById('interimResult');

// Web Speech API 설정
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.lang = 'ko-KR';
recognition.continuous = true;
recognition.interimResults = true;

// 음성 인식 시작/중지 토글
let isRecording = false;

recordButton.addEventListener('click', () => {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
});

function startRecording() {
    isRecording = true;
    recordButton.textContent = '말하기 중지';
    recognition.start();
    animateWaveform(true);
    interimResult.textContent = '';
    interimResult.style.display = 'block';
    document.getElementById('finalResult').style.display = 'none';
}

function stopRecording() {
    isRecording = false;
    recordButton.textContent = '말하기 시작';
    recognition.stop();
    animateWaveform(false);
    interimResult.style.display = 'none';
    if (interimResult.textContent.trim() !== '') {
        document.getElementById('finalResult').textContent = interimResult.textContent;
        document.getElementById('finalResult').style.display = 'block';
        sendMessageToServer(interimResult.textContent);
    }
}
// 음성 인식 결과 실시간 처리
recognition.onresult = (event) => {
    let interimTranscript = '';
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
            finalTranscript += transcript;
        } else {
            interimTranscript += transcript;
        }
    }

    interimResult.textContent = interimTranscript;
    document.getElementById('finalResult').style.display = 'none';

    if (finalTranscript !== '') {
        document.getElementById('finalResult').textContent = finalTranscript;
        document.getElementById('finalResult').style.display = 'block';
        sendMessageToServer(finalTranscript);
        interimResult.textContent = '';
    }
};

// 음성 인식 종료 시 처리
recognition.onend = () => {
    if (isRecording) {
        recognition.start();
    }
};

// 텍스트 입력 처리
sendButton.addEventListener('click', () => {
    const message = textInput.value.trim();
    if (message) {
        addMessageToChat(message, 'userMessage');
        sendMessageToServer(message);
        textInput.value = '';
    }
});

textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendButton.click();
    }
});

// 서버로 메시지 전송
function sendMessageToServer(message) {
    fetch('/process_speech', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: message }),
    })
    .then(response => response.json())
    .then(data => {
        addMessageToChat(data.response, 'botMessage');
        speakResponse(data.response);
    })
    .catch(error => console.error('Error:', error));
}

// 채팅에 메시지 추가
function addMessageToChat(message, className) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chatMessage', className);
    messageDiv.textContent = message;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Clear the finalResult div after adding the message to chat
    document.getElementById('finalResult').textContent = '';
    document.getElementById('finalResult').style.display = 'none';
}
// TTS로 응답 말하기
function speakResponse(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ko-KR';
    speechSynthesis.speak(utterance);
}

// 웨이브폼 애니메이션
function animateWaveform(isAnimating) {
    waveform.innerHTML = ''; // 기존 점들 제거
    if (isAnimating) {
        for (let i = 0; i < 20; i++) {
            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("cx", i * 5 + 2.5);
            circle.setAttribute("cy", 15);
            circle.setAttribute("r", 1.5);
            circle.style.fill = "#4CAF50";
            waveform.appendChild(circle);
        }
        animateDots();
    }
}

function animateDots() {
    const dots = waveform.querySelectorAll('circle');
    dots.forEach((dot, index) => {
        const delay = index * 50;
        const duration = 500;
        dot.animate([
            { cy: 15 },
            { cy: 5 + Math.random() * 20 },
            { cy: 15 }
        ], {
            duration: duration,
            delay: delay,
            iterations: Infinity
        });
    });
}

// 별 배경 생성
function createStars() {
    const starContainer = document.getElementById('starContainer');
    for (let i = 0; i < 100; i++) {
        const star = document.createElement('div');
        star.classList.add('star');
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;
        star.style.animationDelay = `${Math.random() * 5}s`;
        starContainer.appendChild(star);
    }
}

createStars();