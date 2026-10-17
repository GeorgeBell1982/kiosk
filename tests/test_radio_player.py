"""Radio state-machine tests in the actual embedded JavaScript engine, offline."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import QEventLoop, QTimer, QUrl
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView

from kiosk_browser import KioskBrowser
from radio_player import STATIONS, radio_html


HARNESS = """
let clock = 100000;
Date.now = () => clock;
let serial = 0;
const timers = new Map();
window.setTimeout = (fn, ms) => { timers.set(++serial, {fn, due: clock + ms}); return serial; };
window.setInterval = (fn, ms) => { timers.set(++serial, {fn, due: clock + ms, interval: ms}); return serial; };
window.clearTimeout = window.clearInterval = id => timers.delete(id);
window.tick = ms => {
    clock += ms;
    for (const [id, timer] of [...timers]) {
        if (timers.has(id) && timer.due <= clock) {
            if (timer.interval) timer.due = clock + timer.interval;
            else timers.delete(id);
            timer.fn();
        }
    }
};
window.instances = [];
window.mp3Supported = true;
window.Audio = class extends EventTarget {
    constructor() { super(); this.currentTime = 0; instances.push(this); }
    canPlayType() { return mp3Supported ? 'probably' : ''; }
    play() { return new Promise((resolve, reject) => { this.reject = reject; }); }
    pause() { this.paused = true; }
    removeAttribute() { this.src = ''; }
    load() { this.released = true; }
    emit(name) { this.dispatchEvent(new Event(name)); }
};
"""


class RadioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["radio-tests"])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.view = QWebEngineView()
        self.view.setHtml(radio_html().replace('"use strict";', HARNESS + '\n"use strict";'),
                          QUrl("https://radio.office-kiosk.invalid/"))
        self.wait_until(lambda: self.js("typeof selectStation === 'function'"))

    def tearDown(self):
        self.view.close()
        self.view.deleteLater()
        loop = QEventLoop()
        QTimer.singleShot(50, loop.quit)
        loop.exec()

    def js(self, source, view=None):
        results = []
        loop = QEventLoop()
        (view or self.view).page().runJavaScript(source, lambda value: (results.append(value), loop.quit()))
        QTimer.singleShot(3000, loop.quit)
        loop.exec()
        self.assertTrue(results, "JavaScript callback timed out")
        return results[0]

    def wait_until(self, condition):
        for _ in range(100):
            if condition():
                return
            loop = QEventLoop()
            QTimer.singleShot(20, loop.quit)
            loop.exec()
        self.fail("Radio page did not load")

    def test_no_autoplay_and_station_buttons(self):
        self.assertEqual(self.js("instances.length"), 0)
        self.assertEqual(self.js("stationButtons.length"), len(STATIONS))
        self.js("stationButtons[1].click()")
        self.assertEqual(self.js("audio.src"), STATIONS[1]["url"])
        self.assertTrue(self.js("playButton.disabled && !stopButton.disabled"))
        self.assertEqual(self.js("stationButtons[1].getAttribute('aria-pressed')"), "true")

    def test_stop_cancels_reconnect_and_releases_stream(self):
        self.js("selectStation(0); instances[0].emit('error'); stopButton.click(); tick(60000)")
        self.assertEqual(self.js("instances.length"), 1)
        self.assertTrue(self.js("!wanted && audio === null && retryTimer === null && watchdog === null"))
        self.assertTrue(self.js("instances[0].paused && instances[0].released && instances[0].src === ''"))

    def test_switch_ignores_stale_events_and_promises(self):
        self.js("selectStation(0); selectStation(1); instances[0].emit('error'); "
                "instances[0].emit('ended'); instances[0].emit('playing'); "
                "instances[0].reject({name:'NotAllowedError'})")
        self.assertTrue(self.js("wanted && audio === instances[1] && retryTimer === null"))
        self.assertIn("947", self.js("status.textContent"))
        self.assertTrue(self.js("instances[0].released"))

    def test_retry_backoff_is_capped_and_no_duplicate_timers(self):
        self.js("selectStation(0)")
        for delay in [1000, 2000, 4000, 8000, 16000, 30000, 30000]:
            self.js("audio.emit('error'); instances.at(-1).emit('ended')")
            self.assertEqual(self.js("timers.get(retryTimer).due - clock"), delay)
            self.js(f"tick({delay})")
        self.assertEqual(self.js("instances.length"), 8)

    def test_stalled_or_never_connected_stream_retries(self):
        self.js("selectStation(0); tick(20000)")
        self.assertIn("stalled", self.js("status.textContent"))
        self.assertTrue(self.js("audio === null && retryTimer !== null"))
        self.js("tick(1000); audio.emit('ended'); tick(2000)")
        self.assertEqual(self.js("instances.length"), 3)

    def test_only_sustained_playback_resets_backoff(self):
        self.js("selectStation(0); audio.emit('error'); tick(1000); audio.emit('playing')")
        self.assertEqual(self.js("failures"), 1)
        self.js("tick(16000); audio.currentTime = 16; audio.emit('timeupdate')")
        self.assertEqual(self.js("failures"), 0)
        self.js("audio.emit('error')")
        self.assertEqual(self.js("timers.get(retryTimer).due - clock"), 1000)

    def test_network_returns_or_stop_before_network_returns(self):
        self.js("selectStation(0); audio.emit('error'); window.dispatchEvent(new Event('online'))")
        self.assertEqual(self.js("instances.length"), 2)
        self.js("audio.emit('error'); stopRadio(); window.dispatchEvent(new Event('online')); tick(60000)")
        self.assertEqual(self.js("instances.length"), 2)

    def test_policy_denial_requires_manual_play(self):
        self.js("selectStation(0); audio.reject({name:'NotAllowedError'})")
        self.assertFalse(self.js("wanted"))
        self.assertIn("Tap Play", self.js("status.textContent"))
        self.js("tick(60000)")
        self.assertEqual(self.js("instances.length"), 1)

    def test_unavailable_stream_retries_but_missing_codec_is_reported(self):
        self.js("selectStation(0); audio.error = {code:4}; audio.emit('error')")
        self.assertTrue(self.js("wanted && retryTimer !== null"))
        self.js("stopRadio(); mp3Supported = false; selectStation(1)")
        self.assertFalse(self.js("wanted"))
        self.assertIn("MP3 audio", self.js("status.textContent"))

    def test_volume_survives_reconnect_and_station_switch(self):
        self.js("selectStation(0); const slider = document.getElementById('volume'); "
                "slider.value = 23; slider.dispatchEvent(new Event('input'))")
        self.assertAlmostEqual(self.js("audio.volume"), .23)
        self.js("audio.emit('error'); tick(1000); selectStation(2)")
        self.assertAlmostEqual(self.js("audio.volume"), .23)

    def test_pagehide_stops_everything(self):
        self.js("selectStation(0); window.dispatchEvent(new Event('pagehide')); tick(60000)")
        self.assertFalse(self.js("wanted"))
        self.assertEqual(self.js("instances.length"), 1)

    def test_station_buttons_fit_narrow_touchscreen(self):
        self.view.resize(340, 460)
        self.view.show()
        self.app.processEvents()
        self.assertTrue(self.js("stationButtons.every(b => { const r = b.getBoundingClientRect(); "
                                "return r.height >= 44 && r.left >= 0 && r.right <= innerWidth; })"))
        self.assertTrue(self.js("document.documentElement.scrollWidth <= innerWidth"))

    def test_home_station_buttons_fit_without_scrolling(self):
        from radio_player import HOME_URL, radio_home_html
        self.view.setHtml(radio_home_html(), QUrl(HOME_URL))
        self.wait_until(lambda: self.js("document.querySelectorAll('nav a').length === 7"))
        self.wait_until(lambda: self.js("[...document.querySelectorAll('nav img')].length === 7 && "
                                       "[...document.querySelectorAll('nav img')].every(img => "
                                       "img.complete && img.naturalWidth > 0)"))
        for width, height in ((1000, 350), (776, 350), (340, 400)):
            with self.subTest(size=(width, height)):
                self.view.resize(width, height)
                self.view.show()
                self.app.processEvents()
                self.assertTrue(self.js("[...document.querySelectorAll('nav a')].every(b => {"
                                        "const r = b.getBoundingClientRect();"
                                        "return r.height >= 44 && r.left >= 0 && r.top >= 0 && "
                                        "r.right <= innerWidth && r.bottom <= innerHeight; })"))
                self.assertTrue(self.js("document.documentElement.scrollWidth <= innerWidth && "
                                        "document.documentElement.scrollHeight <= innerHeight"))
                self.assertTrue(self.js("(() => { const tiles = [...document.querySelectorAll('.primary a')];"
                                        "const first = tiles[0].getBoundingClientRect();"
                                        "return tiles.every(tile => {const r = tile.getBoundingClientRect();"
                                        "return Math.abs(r.width-first.width)<1 && Math.abs(r.height-first.height)<1;}); })()"))
                self.assertTrue(self.js("document.querySelector('.secondary').getBoundingClientRect().top >= "
                                        "document.querySelector('.primary').getBoundingClientRect().bottom"))

    def test_home_station_click_starts_player_and_keeps_home_visible(self):
        from radio_player import HOME_URL
        with tempfile.TemporaryDirectory() as storage:
            with patch("kiosk_browser.os.path.expanduser", return_value=storage), \
                    patch.object(KioskBrowser, "check_for_updates"):
                browser = KioskBrowser()
            try:
                self.wait_until(lambda: self.js("document.querySelectorAll('nav a').length === 7",
                                                browser.web_view))
                with patch("radio_player.radio_html", return_value=radio_html().replace(
                        '"use strict";', HARNESS + '\n"use strict";')):
                    self.js("document.querySelectorAll('nav a')[4].click()", browser.web_view)
                    self.wait_until(lambda: browser.radio_dialog is not None)
                dialog = browser.radio_dialog
                self.wait_until(lambda: self.js("typeof wanted !== 'undefined' && wanted", dialog.view))
                self.assertEqual(self.js("audio.src", dialog.view), STATIONS[4]["url"])
                self.assertEqual(browser.web_view.url(), QUrl(HOME_URL))
                dialog.hide()
                self.js("document.querySelectorAll('nav a')[1].click()", browser.web_view)
                self.wait_until(lambda: self.js("selected === 1 && wanted", dialog.view))
                self.assertIs(browser.radio_dialog, dialog)
                self.assertFalse(self.js("!!document.querySelector('.is-playing')", browser.web_view))
                self.js("audio.emit('playing')", dialog.view)
                self.wait_until(lambda: self.js("document.querySelector('[data-station=\"1\"]').classList.contains('is-playing')",
                                                browser.web_view))
                self.assertIn("Playing", self.js("document.querySelector('.is-playing').getAttribute('aria-label')",
                                                browser.web_view))
                self.js("audio.emit('waiting')", dialog.view)
                self.wait_until(lambda: not self.js("!!document.querySelector('.is-playing')", browser.web_view))
                self.js("audio.emit('playing')", dialog.view)
                self.wait_until(lambda: self.js("!!document.querySelector('.is-playing')", browser.web_view))
                browser.web_view.setHtml("<p>Another browser page</p>")
                self.wait_until(lambda: self.js("document.body.textContent.includes('Another browser page')", browser.web_view))
                browser.load_home_page()
                self.wait_until(lambda: self.js("!!document.querySelector('.is-playing')", browser.web_view))
                self.js("stopRadio()", dialog.view)
                self.wait_until(lambda: not self.js("!!document.querySelector('.is-playing')", browser.web_view))
            finally:
                browser.close()
                browser.deleteLater()
                loop = QEventLoop()
                QTimer.singleShot(100, loop.quit)
                loop.exec()

    def test_dialog_reused_navigation_unaffected_and_shutdown_muted(self):
        with tempfile.TemporaryDirectory() as storage:
            with patch("kiosk_browser.os.path.expanduser", return_value=storage), \
                    patch.object(KioskBrowser, "check_for_updates"), \
                    patch.object(KioskBrowser, "load_home_page"):
                browser = KioskBrowser()
            try:
                with patch("radio_player.radio_html", return_value=radio_html().replace(
                        '"use strict";', HARNESS + '\n"use strict";')):
                    browser.shortcut_buttons[2].click()
                dialog = browser.radio_dialog
                self.assertIsNotNone(dialog)
                self.wait_until(lambda: self.js("typeof selectStation === 'function'", dialog.view))
                self.js("selectStation(0)", dialog.view)
                dialog.hide()
                browser.web_view.setHtml("<p>Another browser page</p>")
                browser.show_radio()
                self.assertIs(browser.radio_dialog, dialog)
                self.assertTrue(dialog.isVisible())
                self.assertTrue(self.js("wanted && audio === instances[0]", dialog.view))
                browser.close()
                self.assertTrue(dialog.view.page().isAudioMuted())
                self.assertFalse(dialog._state_timer.isActive())
            finally:
                browser.close()
                browser.deleteLater()
                loop = QEventLoop()
                QTimer.singleShot(200, loop.quit)
                loop.exec()


if __name__ == "__main__":
    unittest.main()
