const startButton = document.querySelector("#start");
const stopButton = document.querySelector("#stop");
const durationInput = document.querySelector("#duration-minutes");
const typeSelect = document.querySelector("#interview-type");
const statusText = document.querySelector("#status");
const timerText = document.querySelector("#timer");
const questionText = document.querySelector("#question");
const listeningText = document.querySelector("#listening");
const transcriptList = document.querySelector("#transcript");

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

let socket = null;
let recognition = null;
let timerHandle = null;
let remainingSeconds = 0;
let answerStartedAt = null;
let microphoneStream = null;
let audioContext = null;
let analyser = null;
let audioMonitorHandle = null;
let silenceStartedAt = null;
let pauseCount = 0;
let longPauseCount = 0;
let sawSpeech = false;
let recognitionConfidence = null;
let recorder = null;
let pendingTranscript = null;
let recordingContentType = "audio/webm";
let recognitionLang = "en-US";

async function startMicrophoneMonitor() {
  if (!navigator.mediaDevices?.getUserMedia) return;
  microphoneStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextConstructor) return;
  audioContext = new AudioContextConstructor();
  const source = audioContext.createMediaStreamSource(microphoneStream);
  analyser = audioContext.createAnalyser();
  analyser.fftSize = 512;
  source.connect(analyser);
}

function resetAudioMetrics() {
  silenceStartedAt = null;
  pauseCount = 0;
  longPauseCount = 0;
  sawSpeech = false;
  recognitionConfidence = null;
}

function monitorMicrophone() {
  if (!analyser) return;
  const samples = new Uint8Array(analyser.fftSize);
  analyser.getByteTimeDomainData(samples);
  const rms = Math.sqrt(
    samples.reduce((sum, value) => {
      const normalized = (value - 128) / 128;
      return sum + normalized * normalized;
    }, 0) / samples.length
  );
  const now = performance.now();

  if (listeningText && !listeningText.hidden) {
    const bars = document.querySelectorAll(".audio-wave .bar");
    if (bars.length > 0) {
      const intensity = Math.min(1, Math.max(0.12, rms * 16));
      bars.forEach((bar, index) => {
        const waveFactor = 0.45 + 0.55 * Math.sin((now / 110) + index * 0.75);
        const scaleY = Math.max(0.2, Math.min(1.85, intensity * waveFactor * 2.6));
        bar.style.transform = `scaleY(${scaleY.toFixed(2)})`;
      });
    }
  }

  if (rms < 0.018) {
    if (silenceStartedAt === null && sawSpeech) silenceStartedAt = now;
  } else {
    if (silenceStartedAt !== null) {
      const silenceMs = now - silenceStartedAt;
      if (silenceMs >= 250) pauseCount += 1;
      if (silenceMs >= 1000) longPauseCount += 1;
      silenceStartedAt = null;
    }
    sawSpeech = true;
  }
  audioMonitorHandle = window.requestAnimationFrame(monitorMicrophone);
}

function stopMicrophoneMonitor() {
  if (audioMonitorHandle !== null) {
    window.cancelAnimationFrame(audioMonitorHandle);
    audioMonitorHandle = null;
  }
  document.querySelectorAll(".audio-wave .bar").forEach((bar) => {
    bar.style.transform = "scaleY(0.25)";
  });
  microphoneStream?.getTracks().forEach((track) => track.stop());
  microphoneStream = null;
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  analyser = null;
}

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.style.color = isError ? "var(--red)" : "var(--mint-light)";
  const indicator = document.querySelector(".status-indicator");
  if (indicator) {
    indicator.style.background = isError ? "var(--red)" : "var(--mint)";
    indicator.style.boxShadow = isError ? "0 0 8px var(--red)" : "0 0 8px var(--mint)";
  }
}

function renderTimer() {
  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;
  timerText.textContent =
    `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function stopTimer() {
  if (timerHandle !== null) {
    window.clearInterval(timerHandle);
    timerHandle = null;
  }
}

function startTimer(seconds) {
  remainingSeconds = Math.max(0, Number(seconds) || 0);
  renderTimer();
  stopTimer();
  timerHandle = window.setInterval(() => {
    remainingSeconds = Math.max(0, remainingSeconds - 1);
    renderTimer();
  }, 1000);
}

function addTranscript(text) {
  const emptyItem = transcriptList.querySelector(".transcript-empty, .muted");
  if (emptyItem) {
    transcriptList.replaceChildren();
  }
  const item = document.createElement("li");
  item.textContent = text;
  transcriptList.appendChild(item);
}

function stopRecognition() {
  stopAnswerRecorder(false);
  if (recognition !== null) {
    recognition.onresult = null;
    recognition.onerror = null;
    recognition.onend = null;
    recognition.stop();
    recognition = null;
  }
  listeningText.hidden = true;
}

function stopAnswerRecorder(sendTranscript) {
  if (!recorder) {
    if (sendTranscript) sendPendingTranscript();
    return;
  }
  recorder.onstop = () => {
    recorder = null;
    if (sendTranscript) sendPendingTranscript();
  };
  recorder.stop();
}

function sendPendingTranscript() {
  const text = pendingTranscript;
  pendingTranscript = null;
  if (!text || socket?.readyState !== WebSocket.OPEN) return;
  socket.send(JSON.stringify({
    type: "answer_transcript",
    text,
    duration_ms: answerStartedAt === null
      ? 0
      : Math.round(performance.now() - answerStartedAt),
    language: recognitionLang,
    pause_count: pauseCount,
    long_pause_count: longPauseCount,
    recognition_confidence: recognitionConfidence,
    audio_content_type: recordingContentType,
  }));
}

function listenForAnswer() {
  if (!SpeechRecognition) {
    setStatus("Use Chrome or Edge for browser speech recognition.", true);
    return;
  }

  stopRecognition();
  resetAudioMetrics();
  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognitionLang = recognition.lang;
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.onstart = () => {
    answerStartedAt = performance.now();
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "answer_start" }));
    }
    if (microphoneStream && window.MediaRecorder) {
      const options = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? { mimeType: "audio/webm;codecs=opus" }
        : {};
      recorder = new MediaRecorder(microphoneStream, options);
      recordingContentType = recorder.mimeType || "audio/webm";
      recorder.ondataavailable = (event) => {
        if (event.data.size && socket?.readyState === WebSocket.OPEN) {
          socket.send(event.data);
        }
      };
      recorder.start(250);
    }
    listeningText.hidden = false;
    setStatus("Listening…");
  };
  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript.trim();
    recognitionConfidence = event.results[0][0].confidence || null;
    pendingTranscript = text;
  };
  recognition.onerror = (event) => {
    if (event.error !== "aborted") {
      setStatus(`Microphone error: ${event.error}`, true);
    }
  };
  recognition.onend = () => {
    stopAnswerRecorder(true);
    recognition = null;
    listeningText.hidden = true;
  };
  recognition.start();
}

function speakQuestion(text) {
  stopRecognition();
  questionText.textContent = text;
  if (!("speechSynthesis" in window)) {
    setStatus("Speech output is not supported by this browser.", true);
    return;
  }
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.onend = listenForAnswer;
  speechSynthesis.cancel();
  speechSynthesis.speak(utterance);
}

function finishClient() {
  stopRecognition();
  stopMicrophoneMonitor();
  speechSynthesis?.cancel();
  stopTimer();
  socket = null;
  startButton.disabled = false;
  stopButton.disabled = true;
}

async function createAndStartInterview() {
  const durationMinutes = Number(durationInput.value);
  if (!Number.isInteger(durationMinutes) || durationMinutes < 1 || durationMinutes > 60) {
    throw new Error("Choose an interview duration from 1 to 60 whole minutes.");
  }
  const payload = {
    duration_seconds: durationMinutes * 60,
    interview_type: typeSelect.value,
  };
  const createdResponse = await fetch("/interviews", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!createdResponse.ok) {
    let detail = "Could not create interview";
    try {
      const errorData = await createdResponse.json();
      detail = errorData?.detail || detail;
    } catch (_) { /* non-JSON response body */ }
    throw new Error(detail);
  }
  const session = await createdResponse.json();
  const startResponse = await fetch(`/interviews/${session.id}/start`, {
    method: "POST",
  });
  if (!startResponse.ok) {
    let detail = "Could not start interview";
    try {
      const errorData = await startResponse.json();
      detail = errorData?.detail || detail;
    } catch (_) { /* non-JSON response body */ }
    throw new Error(detail);
  }
  return session.id;
}

startButton.addEventListener("click", async () => {
  if (!SpeechRecognition) {
    setStatus("Use Chrome or Edge for browser speech recognition.", true);
    return;
  }
  startButton.disabled = true;
  setStatus("Preparing interview…");
  try {
    await startMicrophoneMonitor();
    monitorMicrophone();
    const sessionId = await createAndStartInterview();
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    socket = new WebSocket(
      `${protocol}://${window.location.host}/interviews/${sessionId}/voice`
    );
    socket.onopen = () => {
      stopButton.disabled = false;
      setStatus("Interview connected.");
    };
    socket.onmessage = ({ data }) => {
      if (typeof data !== "string") return;
      const message = JSON.parse(data);
      if (message.type === "ready") {
        startTimer(message.remaining_seconds);
      } else if (message.type === "question") {
        startTimer(message.remaining_seconds);
        speakQuestion(message.text);
      } else if (message.type === "transcript") {
        addTranscript(message.text);
      } else if (message.type === "evaluation") {
        if (message.adaptive && message.score !== null) {
          setStatus(`Answer evaluated: ${message.score}/100 — ${message.feedback}`);
        } else {
          setStatus("Answer saved. Continuing with the next question.");
        }
      } else if (message.type === "voice_analysis") {
        if (message.fluency_score !== null) {
          const pronunciation = message.pronunciation_status === "queued"
            ? "Pronunciation analysis pending"
            : message.pronunciation_status === "processing"
              ? "Pronunciation analysis processing"
              : "";
          setStatus(`Voice: fluency ${message.fluency_score}/100, clarity ${message.clarity_score}/100${pronunciation ? ` — ${pronunciation}` : ""}`);
        }
      } else if (message.type === "ended") {
        setStatus("Interview ended.");
        finishClient();
      } else if (message.type === "error") {
        setStatus(message.message, true);
      }
    };
    socket.onerror = () => setStatus("Interview connection failed.", true);
    socket.onclose = () => {
      if (socket !== null) finishClient();
    };
  } catch (error) {
    stopMicrophoneMonitor();
    setStatus(error.message, true);
    startButton.disabled = false;
  }
});

stopButton.addEventListener("click", () => {
  stopRecognition();
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "end" }));
  }
});
