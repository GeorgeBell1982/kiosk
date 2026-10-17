"use strict";

// Each attempt owns a new Audio element. Events and promises from a previous
// attempt must never restart or change the state of the current station.
let selected = 0;
let wanted = false;
let audio = null;
let retryTimer = null;
let watchdog = null;
let failures = 0;
let lastProgress = 0;
let lastPosition = 0;
let playingSince = 0;
let volume = 0.7;
const status = document.getElementById("status");
const playButton = document.getElementById("play");
const stopButton = document.getElementById("stop");
const stationButtons = stations.map((station, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = station.name;
    button.setAttribute("aria-pressed", "false");
    button.onclick = () => selectStation(index);
    document.getElementById("stations").appendChild(button);
    return button;
});

function updateControls() {
    playButton.disabled = wanted;
    stopButton.disabled = !wanted;
    stationButtons.forEach((button, index) =>
        button.setAttribute("aria-pressed", String(index === selected)));
}

function releaseAudio() {
    clearInterval(watchdog);
    watchdog = null;
    const previous = audio;
    audio = null;
    if (previous) {
        previous.pause();
        previous.removeAttribute("src");
        previous.load();
    }
}

function stopRadio() {
    wanted = false;
    clearTimeout(retryTimer);
    retryTimer = null;
    releaseAudio();
    failures = 0;
    status.textContent = "Stopped — " + stations[selected].name;
    updateControls();
}

function retry(message) {
    if (!wanted || retryTimer !== null) return;
    releaseAudio();
    const delay = Math.min(30000, 1000 * 2 ** Math.min(failures++, 5));
    status.textContent = stations[selected].name + " — " + message +
        ". Reconnecting in " + delay / 1000 + "s…";
    retryTimer = setTimeout(() => {
        retryTimer = null;
        if (wanted) connect();
    }, delay);
}

function connect() {
    releaseAudio();
    if (!wanted) return;
    const current = new Audio();
    audio = current;
    if (!current.canPlayType("audio/mpeg")) {
        stopRadio();
        status.textContent = "MP3 audio is unavailable in this WebEngine build.";
        return;
    }
    current.preload = "none";
    current.volume = volume;
    lastProgress = Date.now();
    lastPosition = 0;
    playingSince = 0;
    status.textContent = "Connecting to " + stations[selected].name + "…";
    const isCurrent = () => wanted && audio === current;
    current.addEventListener("playing", () => {
        if (!isCurrent()) return;
        playingSince = Date.now();
        status.textContent = "Playing — " + stations[selected].name;
    });
    current.addEventListener("timeupdate", () => {
        if (!isCurrent() || current.currentTime === lastPosition) return;
        lastPosition = current.currentTime;
        lastProgress = Date.now();
        // A short connection followed by another failure keeps its backoff.
        if (playingSince && Date.now() - playingSince >= 15000) failures = 0;
    });
    current.addEventListener("waiting", () => {
        if (isCurrent()) status.textContent = "Buffering — " + stations[selected].name;
    });
    current.addEventListener("error", () => {
        if (!isCurrent()) return;
        retry(current.error && current.error.code === 4
            ? "Stream unavailable or audio format unsupported" : "Connection lost");
    });
    current.addEventListener("ended", () => { if (isCurrent()) retry("Stream ended"); });
    watchdog = setInterval(() => {
        if (isCurrent() && Date.now() - lastProgress >= 20000) retry("Stream stalled");
    }, 1000);
    current.src = stations[selected].url;
    const result = current.play();
    if (result) result.catch(error => {
        if (!isCurrent()) return;
        if (error.name === "NotAllowedError") {
            stopRadio();
            status.textContent = "Playback blocked. Tap Play to try again.";
        } else retry("Unable to connect");
    });
}

function selectStation(index) {
    stopRadio();
    selected = index;
    wanted = true;
    updateControls();
    connect();
}

playButton.onclick = () => selectStation(selected);
stopButton.onclick = stopRadio;
document.getElementById("volume").oninput = event => {
    volume = Number(event.target.value) / 100;
    if (audio) audio.volume = volume;
};
window.addEventListener("online", () => {
    if (wanted && retryTimer !== null) {
        clearTimeout(retryTimer);
        retryTimer = null;
        connect();
    }
});
window.addEventListener("pagehide", stopRadio);
updateControls();
