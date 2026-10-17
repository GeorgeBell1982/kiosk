"""Launcher and autostart regressions using temporary files and stubbed OS tools."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallationScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bash = shutil.which("bash")
        if os.name == "nt":
            cls.bash = str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe")
        if not cls.bash or not Path(cls.bash).is_file():
            raise unittest.SkipTest("Bash is required")

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="kiosk-install-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.project = self.root / "project with spaces % and $sign"
        self.project.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        self.config = self.home / "custom config"
        self.config.mkdir()
        for name in ("scripts/start_kiosk.sh", "install/setup_autostart.sh", "install/manage_autostart.sh"):
            target = self.project / name
            target.parent.mkdir(exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
        (self.project / "kiosk_browser.py").write_text("", encoding="utf-8")
        self.env = os.environ.copy()
        self.env.update(HOME=self.home.as_posix(), XDG_CONFIG_HOME=self.config.as_posix(),
                        REAL_PYTHON=sys.executable, DISPLAY=":test", WAYLAND_DISPLAY="",
                        XDG_SESSION_TYPE="x11", QT_QPA_PLATFORM="", TEST_UID="1000",
                        PYTHONIOENCODING="utf-8")

    COMMON = r'''
id() { if [ "$1" = -u ]; then echo "$TEST_UID"; else command id "$@"; fi; }
sudo() { echo UNEXPECTED_SYSTEM_CHANGE >&2; exit 99; }
systemctl() { return 1; }
crontab() { return 1; }
pgrep() { return 1; }
export -f id sudo systemctl crontab pgrep
'''

    def invoke(self, relative, *args, prelude=""):
        return subprocess.run(
            [self.bash, "-c", self.COMMON + prelude + '\nbash "$@"', "test",
             (self.project / relative).as_posix(), *args],
            cwd=self.root, env=self.env, input="", capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=15,
        )

    def fake_python(self, relative=".venv/bin/python"):
        target = self.project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('''#!/bin/bash
if [ "$1" = -c ]; then exit "${FAKE_IMPORT_STATUS:-0}"; fi
printf 'ARG=<%s>\\n' "$@"
exit "${FAKE_APP_STATUS:-0}"
''', encoding="utf-8")
        target.chmod(0o755)
        return target

    def test_linux_launcher_preserves_arguments_and_failure_status(self):
        self.fake_python()
        self.env["FAKE_APP_STATUS"] = "23"
        result = self.invoke("scripts/start_kiosk.sh", "--fullscreen", "two words", "*.txt")
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertIn("ARG=<two words>", result.stdout)
        self.assertIn("ARG=<*.txt>", result.stdout)
        self.assertNotIn("UNEXPECTED_SYSTEM_CHANGE", result.stderr)

    def test_linux_launcher_does_not_install_when_qt_is_missing(self):
        self.fake_python()
        self.env["FAKE_IMPORT_STATUS"] = "1"
        result = self.invoke("scripts/start_kiosk.sh")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Qt6 WebEngine is unavailable", result.stderr)
        self.assertNotIn("ARG=<", result.stdout)
        self.assertNotIn("UNEXPECTED_SYSTEM_CHANGE", result.stderr)

    def test_incomplete_environment_stops_instead_of_falling_back(self):
        (self.project / ".venv").mkdir()
        result = self.invoke("scripts/start_kiosk.sh")
        self.assertEqual(result.returncode, 1)
        self.assertIn("interpreter is missing", result.stderr)

    def test_no_display_is_reported_before_starting(self):
        self.fake_python()
        self.env["DISPLAY"] = ""
        result = self.invoke("scripts/start_kiosk.sh")
        self.assertEqual(result.returncode, 1)
        self.assertIn("No graphical session", result.stderr)

    def test_root_launch_is_rejected(self):
        self.fake_python()
        self.env["TEST_UID"] = "0"
        result = self.invoke("scripts/start_kiosk.sh")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not root", result.stderr)

    def test_raspberry_pi_adds_fullscreen_exactly_once(self):
        self.fake_python()
        for arguments in ((), ("--fullscreen",)):
            with self.subTest(arguments=arguments):
                result = self.invoke("scripts/start_kiosk.sh", *arguments, prelude='''
grep() { return 0; }
export -f grep
''')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout.count("ARG=<--fullscreen>"), 1)

    def test_system_python_is_used_when_no_project_environment_exists(self):
        self.fake_python("bin/python3")
        self.env["TEST_BIN"] = (self.project / "bin").as_posix()
        result = self.invoke("scripts/start_kiosk.sh", prelude='''
TEST_BIN="$(cd "$TEST_BIN" && pwd)"
export PATH="$TEST_BIN:$PATH"
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("kiosk_browser.py>", result.stdout)
        self.assertFalse((self.project / ".venv").exists())

    def test_desktop_entry_uses_launcher_and_quotes_special_paths(self):
        self.fake_python()
        result = self.invoke("install/setup_autostart.sh", prelude=r'''
python3() { "$REAL_PYTHON" "$@"; }
export -f python3
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        desktop = self.config / "autostart/office-kiosk-browser.desktop"
        content = desktop.read_text(encoding="utf-8")
        self.assertIn("Exec=/bin/bash ", content)
        self.assertIn("%%", content)
        self.assertNotIn("Exec=python3", content)
        self.assertFalse((self.config / "systemd").exists())
        self.assertFalse((self.home / ".bashrc").exists())
        # Apply the desktop string-unescape pass, then execute the quoted command.
        command = next(line[5:] for line in content.splitlines() if line.startswith("Exec="))
        command = command.replace("\\\\", "\\").replace("%%", "%")
        executed = subprocess.run([self.bash, "-c", self.COMMON + "\nexec " + command],
                                  env=self.env, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=10)
        self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
        self.assertIn("ARG=<--fullscreen>", executed.stdout)

    def test_status_does_not_exit_when_first_enabled_entry_is_counted(self):
        directory = self.config / "autostart"
        directory.mkdir()
        (directory / "office-kiosk-browser.desktop").write_text("Name=Office Kiosk Browser\n")
        result = self.invoke("install/manage_autostart.sh", "status")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Only 1 autostart method enabled", result.stdout)

    def test_disable_preserves_unrelated_entries_and_shell_logic(self):
        directory = self.config / "autostart"
        directory.mkdir()
        owned = directory / "office-kiosk-browser.desktop"
        owned.write_text("Name=Office Kiosk Browser\n")
        other = directory / "office-spreadsheet.desktop"
        other.write_text("Name=Office Spreadsheet\n")
        profile = self.home / ".bashrc"
        original = 'if true; then\n  echo kiosk_browser reference\nfi\n'
        profile.write_text(original)
        result = self.invoke("install/manage_autostart.sh", "disable")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(owned.exists())
        self.assertTrue(other.exists())
        self.assertEqual(profile.read_text(), original)
        self.assertIn("file preserved", result.stdout)

    def test_setup_does_not_overwrite_a_different_application(self):
        directory = self.config / "autostart"
        directory.mkdir()
        desktop = directory / "office-kiosk-browser.desktop"
        desktop.write_text("Name=Another App\n")
        result = self.invoke("install/setup_autostart.sh")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(desktop.read_text(), "Name=Another App\n")

    def test_stop_targets_current_user_and_owned_keyboard_children(self):
        result = self.invoke("install/manage_autostart.sh", "stop", prelude=r'''
pgrep() {
    [ "$1" = -u ] && [ "$2" = 1000 ] || exit 91
    if [ "$3" = -f ]; then echo 42; fi
    if [ "$3" = -P ]; then
        [ "$4" = 42 ] && [ "$5" = -x ] && [ "$6" = wvkbd-mobintl ] || exit 92
        echo 43
    fi
}
kill() { if [ "$1" = -0 ]; then return 1; fi; printf 'STOP %s %s\n' "$1" "$2"; }
sleep() { :; }
export -f pgrep kill sleep
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("STOP -TERM 42", result.stdout)
        self.assertIn("STOP -TERM 43", result.stdout)
        self.assertEqual(result.stdout.count("STOP -TERM"), 2)

    def installer_harness(self, functions, *args):
        source = (ROOT / "install/quick_install_pyqt6.sh").read_text().rsplit('main "$@"', 1)[0]
        commands = (self.COMMON + source + '\nPROJECT_DIR="$1"\n'
                    'VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"\nshift\n' + functions + '\nmain "$@"')
        return subprocess.run([self.bash, "-c", commands,
                               (ROOT / "install/quick_install_pyqt6.sh").as_posix(),
                               self.project.as_posix(), *args],
                              env=self.env, input="", capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=15)

    def test_existing_qt_unattended_install_does_not_prompt_or_install(self):
        result = self.installer_harness('''
grep() { return 0; }
test_pyqt6() { return 0; }
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Autostart unchanged", result.stdout)
        self.assertNotIn("UNEXPECTED_SYSTEM_CHANGE", result.stderr)

    def test_explicit_autostart_works_when_qt_is_already_installed(self):
        result = self.installer_harness(r'''
grep() { return 0; }
test_pyqt6() { return 0; }
bash() { printf 'AUTOSTART=<%s>\n' "$@"; }
''', "--autostart")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        expected = ROOT / "install/setup_autostart.sh"
        self.assertIn(expected.name, result.stdout)
        self.assertIn("AUTOSTART=<", result.stdout)

    def test_failed_methods_do_not_implicitly_start_a_source_build(self):
        result = self.installer_harness('''
grep() { return 0; }
test_pyqt6() { return 1; }
try_system_packages() { return 1; }
try_pip_piwheels() { return 1; }
try_regular_pip() { return 1; }
try_build_from_source() { echo UNEXPECTED_BUILD; return 0; }
''', "--no-autostart")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("UNEXPECTED_BUILD", result.stdout)

    def test_pip_fallback_installs_into_project_environment(self):
        self.fake_python()
        result = self.installer_harness('''
grep() { return 0; }
probe_count=0
test_pyqt6() { probe_count=$((probe_count + 1)); [ "$probe_count" -gt 1 ]; }
try_system_packages() { return 1; }
try_pip_piwheels() { return 1; }
python3() { echo PREPARED_VENV; printf 'VENV_ARG=<%s>\n' "$@"; return 0; }
''', "--no-autostart")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PREPARED_VENV", result.stdout)
        self.assertIn("VENV_ARG=<--system-site-packages>", result.stdout)
        self.assertIn("ARG=<pip>", result.stdout)
        self.assertIn("ARG=<install>", result.stdout)
        self.assertIn("requirements.txt>", result.stdout)

    def test_explicit_autostart_failure_is_not_hidden(self):
        result = self.installer_harness('''
grep() { return 0; }
test_pyqt6() { return 0; }
bash() { return 7; }
''', "--autostart")
        self.assertEqual(result.returncode, 1)


@unittest.skipUnless(os.name == "nt", "Windows launcher integration")
class WindowsLauncherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="kiosk-windows-")
        self.addCleanup(self.directory.cleanup)
        self.project = Path(self.directory.name) / "project with spaces"
        scripts = self.project / "scripts"
        scripts.mkdir(parents=True)
        for name in ("start_kiosk.ps1", "start_kiosk.bat"):
            shutil.copyfile(ROOT / "scripts" / name, scripts / name)
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(self.project / ".venv")],
                       check=True, capture_output=True, timeout=20)
        modules = self.project / "PyQt6"
        modules.mkdir()
        (modules / "__init__.py").write_text("")
        (modules / "QtWidgets.py").write_text("class QApplication: pass\n")
        (modules / "QtWebEngineWidgets.py").write_text("class QWebEngineView: pass\n")
        (self.project / "kiosk_browser.py").write_text("import sys; print(repr(sys.argv)); sys.exit(23)\n")

    def test_batch_preserves_arguments_and_exit_status(self):
        result = subprocess.run(["cmd.exe", "/d", "/c", "call", str(self.project / "scripts/start_kiosk.bat"),
                                 "--fullscreen", "two words"],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertIn("'two words'", result.stdout)

    def test_powershell_exits_without_waiting_for_a_key(self):
        shell = shutil.which("pwsh") or shutil.which("powershell")
        result = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-File",
                                 str(self.project / "scripts/start_kiosk.ps1"), "-Fullscreen"],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertIn("'--fullscreen'", result.stdout)


if __name__ == "__main__":
    unittest.main()
