"""Self-contained radio panel using the already installed WebEngine audio support."""

import base64
import json
from html import escape
from pathlib import Path

from PyQt6.QtCore import QUrl, QTimer, pyqtSignal
from PyQt6.QtWidgets import QDialog, QPushButton, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings


# Public broadcaster streams. Use the provider redirect service rather than
# pinning a particular CDN server, which can change without notice.
STATIONS = [
    {"name": "Jacaranda FM", "icon": "radio-jacaranda.png", "url": "https://live.jacarandafm.com/jacarandahigh.mp3"},
    {"name": "947", "icon": "radio-947.png", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/FM947.mp3"},
    {"name": "Kfm 94.5", "icon": "radio-kfm.png", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/KFM.mp3"},
    {"name": "702", "icon": "radio-702.png", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/FM702.mp3"},
    {"name": "HOT 102.7 FM", "icon": "radio-hot.png", "url": "https://edge.iono.fm/xice/57_high.mp3"},
]


HOME_URL = "https://home.office-kiosk.invalid/"


def radio_home_html():
    def icon(filename):
        path = Path(__file__).with_name("icons") / filename
        mime = "image/svg+xml" if path.suffix == ".svg" else "image/png"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'<img class="station-icon" src="data:{mime};base64,{data}" alt="">'

    buttons = "\n".join(
        f'<a href="#station/{index}" data-station="{index}">{icon(station["icon"])}'
        f'<span class="station-name">{escape(station["name"])}</span>'
        '<svg class="playing-icon" viewBox="0 0 24 24" aria-hidden="true">'
        '<path d="M3 9h4l5-4v14l-5-4H3z" fill="currentColor"/>'
        '<path d="M16 8q4 4 0 8m3-11q7 7 0 14" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></a>'
        for index, station in enumerate(STATIONS))
    return (Path(__file__).with_name("radio_home.html").read_text(encoding="utf-8")
            .replace("<!-- STATIONS -->", buttons)
            .replace("<!-- SKY_ICON -->", icon("radio-sky.svg"))
            .replace("<!-- QMUSIC_ICON -->", icon("radio-qmusic.svg")))


def radio_html():
    assets = Path(__file__).resolve().parent
    return (assets.joinpath("radio_player.html").read_text(encoding="utf-8")
            .replace("/* STATIONS */", "const stations = " + json.dumps(STATIONS) + ";")
            .replace("/* PLAYER */", assets.joinpath("radio_player.js").read_text(encoding="utf-8")))


class RadioDialog(QDialog):
    """Hiding the panel preserves playback; shutting down releases its page."""

    playbackChanged = pyqtSignal(int, bool)

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("South African Radio")
        layout = QVBoxLayout(self)
        self.view = QWebEngineView(self)
        settings = self.view.settings()
        for name in ("PluginsEnabled", "LocalContentCanAccessRemoteUrls",
                     "LocalContentCanAccessFileUrls", "AllowRunningInsecureContent",
                     "JavascriptCanOpenWindows", "JavascriptCanAccessClipboard"):
            settings.setAttribute(getattr(QWebEngineSettings.WebAttribute, name), False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        self.view.page().setBackgroundColor(parent.palette().window().color())
        self._ready = False
        self._pending_station = None
        self._shutting_down = False
        self._last_playback = (-1, False)
        self._state_timer = QTimer(self)
        self._state_timer.setInterval(500)
        self._state_timer.timeout.connect(self._poll_playback)
        self.view.loadFinished.connect(self._on_loaded)
        # A synthetic HTTPS origin lets this isolated page play HTTPS media
        # without granting the browser's local documents remote access.
        self.view.setHtml(radio_html(), QUrl("https://radio.office-kiosk.invalid/"))
        layout.addWidget(self.view)
        hide = QPushButton("Hide radio — keep listening", self)
        hide.setMinimumHeight(44)
        hide.clicked.connect(self.hide)
        layout.addWidget(hide)

    def play_station(self, index):
        if not 0 <= index < len(STATIONS):
            raise ValueError("Unknown radio station")
        self._pending_station = index
        if self._ready:
            self._on_loaded(True)

    def _on_loaded(self, ok):
        if self._shutting_down:
            return
        self._ready = ok
        if ok:
            self._state_timer.start()
        if ok and self._pending_station is not None:
            index = self._pending_station
            self._pending_station = None
            self.view.page().runJavaScript(f"selectStation({index})")

    def _poll_playback(self):
        if self._ready and not self._shutting_down:
            self.view.page().runJavaScript(
                "({station: selected, playing: isPlaying})", self._receive_playback)

    def _receive_playback(self, state):
        if self._shutting_down or not isinstance(state, dict):
            return
        current = (int(state["station"]), bool(state["playing"]))
        if current != self._last_playback:
            self._last_playback = current
            self.playbackChanged.emit(*current)

    def shutdown(self):
        self._shutting_down = True
        self._state_timer.stop()
        self.playbackChanged.emit(-1, False)
        self._pending_station = None
        # Muting is synchronous even if the renderer is busy or unavailable.
        self.view.page().setAudioMuted(True)
        self.view.setHtml("")
        self.close()
