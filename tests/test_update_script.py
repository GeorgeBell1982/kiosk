"""Updater policy tests and local Git integration tests; no network is used."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class UpdateScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bash = shutil.which("bash")
        if os.name == "nt":
            cls.bash = str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) /
                           "Git/bin/bash.exe")
        if not cls.bash or not Path(cls.bash).is_file():
            raise unittest.SkipTest("Bash is required")
        if not shutil.which("git"):
            raise unittest.SkipTest("Git is required")
        cls.script = Path(__file__).resolve().parents[1] / "scripts/update_check.sh"
        cls.source = cls.script.read_text().rsplit('main "$@"', 1)[0]

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="kiosk-updater-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def run_shell(self, commands, *args):
        return subprocess.run(
            [self.bash, "-c", self.source + "\n" + commands,
             self.script.as_posix(), *map(str, args)],
            input="", capture_output=True, text=True, timeout=15,
        )

    def test_disabled_auto_apply_is_respected_without_a_terminal(self):
        result = self.run_shell('''
AUTO_UPDATE_APPLY=false
grep() { return 0; }
log_message() { :; }
check_for_updates() { return 0; }
apply_updates() { echo UNEXPECTED_APPLY; exit 91; }
main
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("automatic application is disabled", result.stdout)
        self.assertNotIn("UNEXPECTED_APPLY", result.stdout)

    def test_enabled_auto_apply_emits_success_marker(self):
        result = self.run_shell('''
AUTO_UPDATE_APPLY=true
grep() { return 0; }
log_message() { :; }
check_for_updates() { return 0; }
apply_updates() { echo APPLIED; }
touch() { :; }
main
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("APPLIED", result.stdout)
        self.assertIn("UPDATES_APPLIED_AUTOMATICALLY", result.stdout)

    def test_fetch_errors_are_not_reported_as_success(self):
        result = self.run_shell('''
grep() { return 0; }
log_message() { :; }
check_for_updates() { return 2; }
main
''')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_timeout_cannot_be_disabled_by_invalid_configuration(self):
        for value in ("0", "-1", "bad", ""):
            with self.subTest(value=value):
                result = self.run_shell('''
UPDATE_TIMEOUT="$1"
grep() { return 0; }
log_message() { echo "$1"; }
check_for_updates() { echo UNEXPECTED_CHECK; return 0; }
main
''', value)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertNotIn("UNEXPECTED_CHECK", result.stdout)

    def test_logging_does_not_require_sudo(self):
        result = self.run_shell('''
UPDATE_LOG="$1/update.log"
sudo() { echo UNEXPECTED_SUDO; exit 91; }
log_message 'test update log'
''', self.root.as_posix())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("UNEXPECTED_SUDO", result.stdout)
        self.assertIn("test update log", (self.root / "update.log").read_text())

    def test_fetch_is_bounded_by_the_configured_timeout(self):
        (self.root / ".git").mkdir()
        commands = self.root / "bin"
        commands.mkdir()
        git = commands / "git"
        git.write_text("#!/bin/sh\nsleep 10\n", encoding="utf-8")
        git.chmod(0o755)
        result = self.run_shell('''
PROJECT_DIR="$1"
PATH="$PROJECT_DIR/bin:$PATH"
UPDATE_TIMEOUT=1
log_message() { echo "$1"; }
check_for_updates
''', self.root.as_posix())
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Failed to fetch", result.stdout)

    def git(self, repo, *args):
        result = subprocess.run(["git", "-C", str(repo), *args],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def repositories(self):
        publisher = self.root / "publisher"
        publisher.mkdir()
        self.git(publisher, "init", "-b", "main")
        self.git(publisher, "config", "user.name", "Kiosk Test")
        self.git(publisher, "config", "user.email", "test@example.invalid")
        (publisher / "version.txt").write_text("first", encoding="utf-8")
        self.git(publisher, "add", "version.txt")
        self.git(publisher, "commit", "-m", "Initial")
        checkout = self.root / "checkout"
        self.git(self.root, "clone", str(publisher), str(checkout))
        return publisher, checkout

    def commit(self, repo, filename, contents):
        (repo / filename).write_text(contents, encoding="utf-8")
        self.git(repo, "add", filename)
        self.git(repo, "-c", "user.name=Kiosk Test", "-c", "user.email=test@example.invalid",
                 "commit", "-m", "Update fixture")
        return self.git(repo, "rev-parse", "HEAD")

    def test_updates_fast_forward_to_the_fetched_commit(self):
        publisher, checkout = self.repositories()
        target = self.commit(publisher, "version.txt", "second")
        result = self.run_shell('''
PROJECT_DIR="$1"
log_message() { echo "$1"; }
# Avoid copying the fixture to a production-style backup path or chmodding it.
cp() { :; }
mkdir() { :; }
chmod() { :; }
check_for_updates || exit 91
apply_updates || exit 92
''', checkout.as_posix())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git(checkout, "rev-parse", "HEAD"), target)

    def test_ahead_and_diverged_branches_are_not_treated_as_updates(self):
        publisher, checkout = self.repositories()
        local = self.commit(checkout, "local.txt", "local change")
        commands = '''
PROJECT_DIR="$1"
log_message() { echo "$1"; }
check_for_updates
'''
        ahead = self.run_shell(commands, checkout.as_posix())
        self.assertEqual(ahead.returncode, 1, ahead.stdout + ahead.stderr)
        self.commit(publisher, "remote.txt", "remote change")
        diverged = self.run_shell(commands, checkout.as_posix())
        self.assertEqual(diverged.returncode, 1, diverged.stdout + diverged.stderr)
        self.assertEqual(self.git(checkout, "rev-parse", "HEAD"), local)

    def test_failed_backup_prevents_applying_updates(self):
        publisher, checkout = self.repositories()
        previous = self.git(checkout, "rev-parse", "HEAD")
        self.commit(publisher, "version.txt", "second")
        result = self.run_shell('''
PROJECT_DIR="$1"
log_message() { echo "$1"; }
mkdir() { :; }
cp() { return 1; }
check_for_updates || exit 91
apply_updates
''', checkout.as_posix())
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(self.git(checkout, "rev-parse", "HEAD"), previous)
        self.assertIn("Backup failed", result.stdout)

    def test_dependency_changes_across_multiple_commits_are_installed(self):
        publisher, checkout = self.repositories()
        self.commit(publisher, "requirements-rpi.txt", "# target platform dependencies")
        self.commit(publisher, "version.txt", "third")
        scripts = checkout / ".venv/bin"
        scripts.mkdir(parents=True)
        python = scripts / "python"
        python.write_text('#!/bin/sh\nprintf "DEPENDENCIES %s\\n" "$*"\nexit 7\n', encoding="utf-8")
        python.chmod(0o755)
        result = self.run_shell('''
PROJECT_DIR="$1"
log_message() { echo "$1"; }
cp() { :; }
mkdir() { :; }
chmod() { :; }
check_for_updates || exit 91
apply_updates
''', checkout.as_posix())
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("DEPENDENCIES -m pip install -r requirements-rpi.txt", result.stdout)
        self.assertIn("Dependency installation failed", result.stdout)
        self.assertNotIn("Dependencies updated", result.stdout)


if __name__ == "__main__":
    unittest.main()
