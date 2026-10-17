"""Headless Qt tests for keyboard ownership, focus, and touchscreen layout."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import QEventLoop, QPoint, QRect, QProcess, Qt, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton

from kiosk_browser import KioskBrowser


class TouchKeyboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["kiosk-keyboard-tests"])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.storage = tempfile.TemporaryDirectory()
        self.child_code = "import time; time.sleep(30)"
        self.addCleanup(self.storage.cleanup)
        self.warning = self.enterContext(patch("kiosk_browser.QMessageBox.warning"))
        self.information = self.enterContext(patch("kiosk_browser.QMessageBox.information"))
        self.enterContext(patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-test",
                                                "XDG_SESSION_TYPE": "wayland"}))
        self.enterContext(patch("kiosk_browser.shutil.which", return_value=sys.executable))
        owner = self

        class KeyboardProcess(QProcess):
            def setArguments(self, arguments):
                self.requested_arguments = arguments
                super().setArguments(["-u", "-c", owner.child_code])

        self.enterContext(patch("kiosk_browser.QProcess", KeyboardProcess))
        with patch("kiosk_browser.os.path.expanduser", return_value=self.storage.name), \
                patch.object(KioskBrowser, "detect_raspberry_pi", return_value=True), \
                patch.object(KioskBrowser, "check_for_updates"), \
                patch.object(KioskBrowser, "load_home_page"):
            self.browser = KioskBrowser()
        self.browser.show()
        self.app.processEvents()

    def tearDown(self):
        self.browser.close()
        process = self.browser.keyboard_process
        if process is not None:
            process.kill()
            process.waitForFinished(3000)
        self.browser.deleteLater()
        loop = QEventLoop()
        QTimer.singleShot(200, loop.quit)
        loop.exec()

    def wait_until(self, condition, timeout=5000):
        if condition():
            return
        loop = QEventLoop()
        poll = QTimer()
        poll.timeout.connect(lambda: loop.quit() if condition() else None)
        deadline = QTimer()
        deadline.setSingleShot(True)
        deadline.timeout.connect(loop.quit)
        poll.start(10)
        deadline.start(timeout)
        loop.exec()
        poll.stop()
        deadline.stop()
        self.assertTrue(condition(), "Timed out waiting for keyboard state")

    def start_keyboard(self):
        self.browser.toggle_virtual_keyboard()
        self.wait_until(lambda: self.browser.keyboard_visible)
        return self.browser.keyboard_process

    def read_javascript(self, source):
        values = []
        self.browser.web_view.page().runJavaScript(source, values.append)
        self.wait_until(lambda: bool(values))
        return values[0]

    def test_supported_arguments_and_owned_process_stop(self):
        with patch("kiosk_browser.subprocess.run") as external:
            process = self.start_keyboard()
            self.assertEqual(process.requested_arguments, ["-H", "180", "-L", "180"])
            self.browser.toggle_virtual_keyboard()
            self.wait_until(lambda: self.browser.keyboard_process is None)
            external.assert_not_called()
        self.assertFalse(self.browser.keyboard_visible)
        self.warning.assert_not_called()

    def test_rapid_taps_cancel_start_without_leaving_a_keyboard_running(self):
        self.browser.toggle_virtual_keyboard()
        self.browser.toggle_virtual_keyboard()
        self.browser.toggle_virtual_keyboard()
        self.wait_until(lambda: self.browser.keyboard_process is None)
        self.assertFalse(self.browser.keyboard_visible)
        self.warning.assert_not_called()

    def test_unexpected_exit_resets_button_and_reports_diagnostic(self):
        self.child_code = "import sys; sys.stderr.write('compositor unavailable'); sys.exit(3)"
        self.browser.toggle_virtual_keyboard()
        self.wait_until(lambda: self.browser.keyboard_process is None)
        self.assertFalse(self.browser.keyboard_visible)
        self.assertIn("compositor unavailable", self.warning.call_args.args[2])

    def test_failed_executable_start_resets_state(self):
        with patch("kiosk_browser.shutil.which", return_value=str(Path(self.storage.name) / "missing")):
            self.browser.toggle_virtual_keyboard()
        self.wait_until(lambda: self.browser.keyboard_process is None)
        self.assertFalse(self.browser.keyboard_visible)
        self.warning.assert_called_once()

    def test_verbose_keyboard_keeps_running_and_ui_remains_responsive(self):
        self.child_code = "import sys,time; sys.stderr.write('x'*2000000); sys.stderr.flush(); time.sleep(30)"
        self.start_keyboard()
        self.wait_until(lambda: len(self.browser.keyboard_error) == 2048)
        heartbeat = []
        QTimer.singleShot(0, lambda: heartbeat.append(True))
        self.wait_until(lambda: bool(heartbeat))
        self.assertTrue(self.browser.keyboard_visible)

    def test_closing_browser_stops_owned_keyboard(self):
        self.start_keyboard()
        self.browser.close()
        self.wait_until(lambda: self.browser.keyboard_process is None)
        self.assertFalse(self.browser.keyboard_visible)
        self.warning.assert_not_called()

    def test_x11_reports_requirement_without_spawning_keyboard(self):
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "", "XDG_SESSION_TYPE": "x11"}):
            self.browser.toggle_virtual_keyboard()
        self.assertIsNone(self.browser.keyboard_process)
        self.information.assert_called_once()
        self.assertIn("Wayland", self.information.call_args.args[1])

    def test_missing_keyboard_shows_installation_instructions(self):
        with patch("kiosk_browser.shutil.which", return_value=None):
            self.browser.toggle_virtual_keyboard()
        self.assertIsNone(self.browser.keyboard_process)
        self.assertIn("sudo apt install wvkbd", self.information.call_args.args[2])

    def test_fullscreen_is_restored_after_keyboard_closes(self):
        self.browser.showFullScreen()
        self.app.processEvents()
        self.start_keyboard()
        self.assertFalse(self.browser.isFullScreen())
        self.assertTrue(self.browser.isMaximized())
        self.browser.toggle_virtual_keyboard()
        self.wait_until(lambda: self.browser.keyboard_process is None)
        self.assertTrue(self.browser.isFullScreen())

    def test_explicit_fullscreen_change_overrides_automatic_restore(self):
        self.browser.showFullScreen()
        self.app.processEvents()
        self.start_keyboard()
        self.browser.toggle_fullscreen()  # Explicitly fullscreen, then explicitly windowed.
        self.browser.toggle_fullscreen()
        self.browser.toggle_virtual_keyboard()
        self.wait_until(lambda: self.browser.keyboard_process is None)
        self.assertFalse(self.browser.isFullScreen())

    def test_touch_targets_fit_display_after_resize(self):
        for width, height in [(1024, 600), (800, 480), (1280, 720), (800, 300), (800, 480)]:
            with self.subTest(size=(width, height)):
                self.browser.resize(width, height)
                self.app.processEvents()
                self.assertEqual(self.browser.width(), width)
                rectangles = []
                for button in self.browser.findChildren(QPushButton):
                    self.assertGreaterEqual(button.width(), 44)
                    self.assertGreaterEqual(button.height(), 44)
                    rectangle = QRect(button.mapTo(self.browser, QPoint()), button.size())
                    self.assertTrue(self.browser.rect().contains(rectangle), button.toolTip())
                    parent = button.parentWidget()
                    self.assertTrue(parent.rect().contains(button.geometry()), button.toolTip())
                    self.assertFalse(any(rectangle.intersects(other) for other in rectangles))
                    rectangles.append(rectangle)
                self.assertGreater(self.browser.web_view.height(), 100 if height == 300 else 250)

    def test_keyboard_tap_preserves_web_text_field_focus(self):
        loaded = []
        self.browser.web_view.loadFinished.connect(lambda success: loaded.append(success))
        self.browser.web_view.setHtml('<input id="entry" autofocus>')
        self.wait_until(lambda: bool(loaded))
        self.browser.activateWindow()
        self.browser.web_view.setFocus()
        self.app.processEvents()
        focused = []
        self.browser.web_view.page().runJavaScript("document.getElementById('entry').focus(); true",
                                                  lambda _: focused.append(True))
        self.wait_until(lambda: bool(focused))
        self.assertEqual(self.read_javascript("[document.activeElement.id, document.hasFocus()]"),
                         ["entry", True])
        QTest.mouseClick(self.browser.keyboard_btn, Qt.MouseButton.LeftButton)
        self.wait_until(lambda: self.browser.keyboard_visible)
        self.assertEqual(self.read_javascript("[document.activeElement.id, document.hasFocus()]"),
                         ["entry", True])
        QTest.keyClicks(self.browser.web_view.focusProxy(), "hello")
        self.assertEqual(self.read_javascript("document.getElementById('entry').value"), "hello")

    def test_fullscreen_shortcut_works_with_webview_focus(self):
        self.browser.activateWindow()
        self.browser.web_view.setFocus()
        self.app.processEvents()
        QTest.keyClick(self.browser.web_view.focusProxy(), Qt.Key.Key_F11)
        self.wait_until(self.browser.isFullScreen)


if __name__ == "__main__":
    unittest.main()
