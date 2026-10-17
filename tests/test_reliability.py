"""Headless regression tests. Run: python -m unittest discover -s tests -p test_reliability.py"""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings

import kiosk_browser
from kiosk_browser import KioskBrowser


class BrowserReliabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["kiosk-reliability-tests"])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.storage = tempfile.TemporaryDirectory()
        with patch("kiosk_browser.os.path.expanduser", return_value=self.storage.name), \
                patch.object(KioskBrowser, "detect_raspberry_pi", return_value=False), \
                patch.object(KioskBrowser, "load_home_page"):
            self.browser = KioskBrowser()

    def tearDown(self):
        self.browser.close()
        self.browser.deleteLater()
        loop = QEventLoop()
        QTimer.singleShot(50, loop.quit)
        loop.exec()
        self.storage.cleanup()

    def test_profile_supports_persistent_logins(self):
        profile = self.browser.web_view.page().profile()
        self.assertFalse(profile.isOffTheRecord())
        self.assertEqual(Path(profile.persistentStoragePath()), Path(self.storage.name))
        self.assertEqual(profile.persistentCookiesPolicy(),
                         QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.assertEqual(profile.httpCacheType(), QWebEngineProfile.HttpCacheType.DiskHttpCache)

    def test_browser_keeps_web_security_boundaries_enabled(self):
        settings = self.browser.web_view.settings()
        for name in (
            "PluginsEnabled", "LocalContentCanAccessRemoteUrls",
            "LocalContentCanAccessFileUrls", "AllowRunningInsecureContent",
            "JavascriptCanOpenWindows", "JavascriptCanAccessClipboard",
            "AllowWindowActivationFromJavaScript",
        ):
            with self.subTest(attribute=name):
                self.assertFalse(settings.testAttribute(getattr(QWebEngineSettings.WebAttribute, name)))
        self.assertTrue(settings.testAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled))
        self.assertTrue(settings.testAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled))

    def test_home_page_can_still_navigate_to_http_service(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from threading import Thread
        from PyQt6.QtCore import QUrl

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<html><body>Local service</body></html>")

            def log_message(self, *_):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        destination = f"http://127.0.0.1:{server.server_port}/"
        loop = QEventLoop()
        loaded = []

        def finished(success):
            if self.browser.web_view.url() == QUrl(destination):
                loaded.append(success)
                loop.quit()
            else:
                self.browser.web_view.page().runJavaScript("document.getElementById('service').click()")

        self.browser.web_view.loadFinished.connect(finished)
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        try:
            self.browser.web_view.setHtml(f'<a id="service" href="{destination}">Local service</a>')
            timer.start(10000)
            loop.exec()
            self.assertEqual(loaded, [True])
        finally:
            timer.stop()
            self.browser.web_view.loadFinished.disconnect(finished)
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_local_document_cannot_read_another_local_file(self):
        from PyQt6.QtCore import QUrl
        import json

        secret = Path(self.storage.name) / "secret.txt"
        secret.write_text("private-file-contents", encoding="utf-8")
        base = QUrl.fromLocalFile(str(Path(self.storage.name) / "index.html"))
        target = json.dumps(QUrl.fromLocalFile(str(secret)).toString())
        loop = QEventLoop()
        values = []

        def finished(success):
            script = f'''(() => {{
                try {{
                    const request = new XMLHttpRequest();
                    request.open('GET', {target}, false);
                    request.send();
                    return request.responseText;
                }} catch (error) {{ return 'blocked'; }}
            }})()'''
            self.browser.web_view.page().runJavaScript(
                script, lambda value: (values.append(value), loop.quit()))

        self.browser.web_view.loadFinished.connect(finished)
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        try:
            self.browser.web_view.setHtml("<html><body>Local document</body></html>", base)
            timer.start(10000)
            loop.exec()
            self.assertEqual(values, ["blocked"])
        finally:
            timer.stop()
            self.browser.web_view.loadFinished.disconnect(finished)

    def test_restart_requests_shutdown_without_spawning_a_competing_process(self):
        app = Mock()
        with patch("kiosk_browser.QApplication.instance", return_value=app), \
                patch.object(self.browser, "close") as close, \
                patch("kiosk_browser.subprocess.Popen") as popen:
            self.browser.restart_application()
        app.setProperty.assert_called_once_with("restartRequested", True)
        close.assert_called_once_with()
        app.quit.assert_called_once_with()
        popen.assert_not_called()

    def test_restart_and_dialog_close_timers_survive_method_return(self):
        with patch.object(self.browser, "restart_application") as restart:
            self.browser.show_update_notification("Test update", True)
            dialogs = self.browser.findChildren(QMessageBox)
            self.assertEqual(len(dialogs), 1)
            closed = []
            dialogs[0].finished.connect(lambda _: closed.append(True))
            loop = QEventLoop()
            QTimer.singleShot(5500, loop.quit)
            loop.exec()
            restart.assert_called_once_with()
            self.assertTrue(closed)

    def test_update_check_does_not_depend_on_working_directory(self):
        self.browser.is_raspberry_pi = True
        with tempfile.TemporaryDirectory() as unrelated, \
                patch("kiosk_browser.subprocess.Popen") as popen:
            previous = os.getcwd()
            try:
                os.chdir(unrelated)
                self.browser.check_for_updates()
            finally:
                os.chdir(previous)
            popen.assert_called_once()
            self.assertEqual(Path(popen.call_args.kwargs["cwd"]).resolve(),
                             Path(__file__).resolve().parents[1])
            self.browser.update_timer.stop()


class SingleInstanceTests(unittest.TestCase):
    CHILD = r'''
import os, sys
from unittest.mock import patch
from kiosk_browser import acquire_instance_lock
with patch("kiosk_browser.os.path.expanduser", return_value=sys.argv[1]):
    lock = acquire_instance_lock()
if lock is None:
    sys.exit(2)
print("LOCKED", flush=True)
if sys.stdin.readline().strip() == "crash":
    os._exit(0)
lock.unlock()
'''

    def setUp(self):
        self.storage = tempfile.TemporaryDirectory()
        self.addCleanup(self.storage.cleanup)

    def acquire(self):
        with patch("kiosk_browser.os.path.expanduser", return_value=self.storage.name):
            return kiosk_browser.acquire_instance_lock()

    def spawn(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
        process = subprocess.Popen(
            [sys.executable, "-u", "-c", self.CHILD, self.storage.name],
            cwd=self.storage.name, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )

        def cleanup():
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=10)

        self.addCleanup(cleanup)
        return process

    def test_second_process_is_blocked_and_clean_exit_releases_lock(self):
        first = self.acquire()
        self.assertIsNotNone(first)
        self.addCleanup(first.unlock)
        self.assertEqual(first.staleLockTime(), 0)
        second = self.spawn()
        stdout, stderr = second.communicate(input="release\n", timeout=15)
        self.assertEqual(second.returncode, 2, stdout + stderr)
        first.unlock()
        replacement = self.spawn()
        stdout, stderr = replacement.communicate(input="release\n", timeout=15)
        self.assertEqual(replacement.returncode, 0, stdout + stderr)
        self.assertIn("LOCKED", stdout)

    def test_simultaneous_launches_have_exactly_one_owner(self):
        contenders = [self.spawn(), self.spawn()]
        replies = [p.stdout.readline().strip() for p in contenders]
        self.assertEqual(replies.count("LOCKED"), 1, replies)
        for p in contenders:
            p.communicate(input="release\n", timeout=15)
        self.assertEqual(sorted(p.returncode for p in contenders), [0, 2])

    def test_crashed_owner_is_recovered_without_deleting_lock_manually(self):
        owner = self.spawn()
        stdout, stderr = owner.communicate(input="crash\n", timeout=15)
        self.assertEqual(owner.returncode, 0, stdout + stderr)
        self.assertIn("LOCKED", stdout)
        self.assertTrue((Path(self.storage.name) / "instance.lock").exists())
        replacement = self.acquire()
        self.assertIsNotNone(replacement)
        replacement.unlock()

    def test_lock_errors_stop_startup(self):
        with patch("kiosk_browser.acquire_instance_lock", side_effect=OSError("denied")), \
                patch("kiosk_browser.run_application") as run:
            self.assertEqual(kiosk_browser.main(), 1)
        run.assert_not_called()

    def test_unwritable_profile_does_not_start_without_a_lock(self):
        with patch("kiosk_browser.os.makedirs", side_effect=PermissionError("denied")), \
                patch("kiosk_browser.run_application") as run:
            self.assertEqual(kiosk_browser.main(), 1)
        run.assert_not_called()

    def test_raspberry_pi_defaults_do_not_disable_sandbox(self):
        with patch.object(KioskBrowser, "detect_raspberry_pi", return_value=True), \
                patch.dict(os.environ, {}, clear=True), \
                patch("kiosk_browser.acquire_instance_lock", return_value=None):
            kiosk_browser.main()
            flags = os.environ["QTWEBENGINE_CHROMIUM_FLAGS"].split()
        self.assertIn("--enable-accelerated-video-decode", flags)
        self.assertFalse(set(flags) & {
            "--no-sandbox", "--disable-gpu-sandbox", "--disable-setuid-sandbox",
            "--disable-web-security", "--allow-running-insecure-content",
        })

    def test_duplicate_does_not_construct_browser(self):
        with patch("kiosk_browser.acquire_instance_lock", return_value=None), \
                patch("kiosk_browser.run_application") as run:
            self.assertEqual(kiosk_browser.main(), 0)
        run.assert_not_called()

    def test_lock_is_released_when_application_fails(self):
        with patch("kiosk_browser.os.path.expanduser", return_value=self.storage.name), \
                patch("kiosk_browser.run_application", side_effect=RuntimeError("startup failed")):
            with self.assertRaisesRegex(RuntimeError, "startup failed"):
                kiosk_browser.main()
        replacement = self.acquire()
        self.assertIsNotNone(replacement)
        replacement.unlock()

    def test_restart_releases_lock_and_preserves_interpreter_and_arguments(self):
        def restart(executable, argv):
            replacement = self.acquire()
            self.assertIsNotNone(replacement)
            replacement.unlock()
            self.assertEqual(executable, sys.executable)
            self.assertEqual(argv, [sys.executable, str(Path(kiosk_browser.__file__).resolve()),
                                    "--fullscreen"])

        with patch("kiosk_browser.os.path.expanduser", return_value=self.storage.name), \
                patch("kiosk_browser.run_application", return_value=(0, True)), \
                patch("kiosk_browser.sys.argv", [kiosk_browser.__file__, "--fullscreen"]), \
                patch("kiosk_browser.os.execv", side_effect=restart) as execute:
            self.assertEqual(kiosk_browser.main(), 0)
        execute.assert_called_once()

    def test_real_qt_shutdown_precedes_restart(self):
        code = r'''
import sys
from unittest.mock import patch
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
import kiosk_browser

class RestartBrowser(kiosk_browser.KioskBrowser):
    def __init__(self):
        super().__init__()
        QTimer.singleShot(100, self.restart_application)

def replacement(*_):
    assert QApplication.instance() is None, "Qt is still using the profile"
    lock = kiosk_browser.acquire_instance_lock()
    assert lock is not None, "profile lock was not released"
    lock.unlock()
    print("RESTART_READY", flush=True)

with patch("kiosk_browser.os.path.expanduser", return_value=sys.argv[1]), \
        patch.object(RestartBrowser, "detect_raspberry_pi", return_value=False), \
        patch.object(RestartBrowser, "load_home_page"), \
        patch("kiosk_browser.KioskBrowser", RestartBrowser), \
        patch("kiosk_browser.os.execv", side_effect=replacement):
    sys.exit(kiosk_browser.main())
'''
        result = subprocess.run(
            [sys.executable, "-u", "-c", code, self.storage.name],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RESTART_READY", result.stdout)


class UpdateScriptTests(unittest.TestCase):
    def test_repository_operations_use_project_root(self):
        bash = shutil.which("bash")
        if os.name == "nt":
            bash = str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) /
                       "Git/bin/bash.exe")
        if not bash or not Path(bash).is_file():
            self.skipTest("Bash is required")
        script = Path(__file__).resolve().parents[1] / "scripts/update_check.sh"
        # Exercise the actual functions, replacing external actions with shell stubs.
        source = script.read_text().rsplit('main "$@"', 1)[0]
        harness = r'''
log_message() { :; }
git() {
    [ "$PWD" = "$PROJECT_DIR" ] || exit 91
    case "$1" in
        fetch) echo FETCH_ROOT_OK ;;
        rev-parse) echo same-commit ;;
        pull) [ "$2" = "--ff-only" ] || exit 92; echo PULL_ROOT_OK ;;
        diff) : ;;
    esac
}
mkdir() { :; }
cp() { :; }
chmod() { :; }
check_for_updates
[ "$?" = 1 ] || exit 93
apply_updates || exit 94
'''
        with tempfile.TemporaryDirectory() as unrelated:
            result = subprocess.run([bash, "-c", source + harness, script.as_posix()],
                                    cwd=unrelated, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PULL_ROOT_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
