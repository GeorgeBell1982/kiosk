"""Self-contained radio panel using the already installed WebEngine audio support."""

import json
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QDialog, QPushButton, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings


# Public broadcaster streams. Use the provider redirect service rather than
# pinning a particular CDN server, which can change without notice.
STATIONS = [
    {"name": "Jacaranda FM", "url": "https://live.jacarandafm.com/jacarandahigh.mp3"},
    {"name": "947", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/FM947.mp3"},
    {"name": "Kfm 94.5", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/KFM.mp3"},
    {"name": "702", "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/FM702.mp3"},
    {"name": "HOT 102.7 FM", "url": "https://edge.iono.fm/xice/57_high.mp3"},
]


def radio_html():
    assets = Path(__file__).resolve().parent
    return (assets.joinpath("radio_player.html").read_text(encoding="utf-8")
            .replace("/* STATIONS */", "const stations = " + json.dumps(STATIONS) + ";")
            .replace("/* PLAYER */", assets.joinpath("radio_player.js").read_text(encoding="utf-8")))


class RadioDialog(QDialog):
    """Hiding the panel preserves playback; shutting down releases its page."""

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
        # A synthetic HTTPS origin lets this isolated page play HTTPS media
        # without granting the browser's local documents remote access.
        self.view.setHtml(radio_html(), QUrl("https://radio.office-kiosk.invalid/"))
        layout.addWidget(self.view)
        hide = QPushButton("Hide radio — keep listening", self)
        hide.setMinimumHeight(44)
        hide.clicked.connect(self.hide)
        layout.addWidget(hide)

    def shutdown(self):
        # Muting is synchronous even if the renderer is busy or unavailable.
        self.view.page().setAudioMuted(True)
        self.view.setHtml("")
        self.close()
