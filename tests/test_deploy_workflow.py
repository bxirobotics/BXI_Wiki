"""Exercise rsync and archive deployment with an isolated SSH transport."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/deploy.yml"
RSYNC = shutil.which("rsync")


@unittest.skipUnless(RSYNC, "rsync is required for deployment integration tests")
class DeploymentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source"
        self.destination = self.root / "destination"
        self.bin = self.root / "bin"
        self.ssh_temp = self.root / "ssh-temp"
        self.log = self.root / "ssh.jsonl"
        for directory in (self.source, self.destination, self.bin, self.ssh_temp):
            directory.mkdir()
        for name, data in {
            "docs/page.md": b"alpha",
            "docs/assets/demo.mp4": bytes(range(256)) * 4096,
            "overrides/main.html": b"template",
            "hooks/example.py": b"hook",
            ".git/HEAD": b"ref: refs/heads/master\n",
            ".git/refs/heads/master": b"commit\n",
            "mkdocs.yml": b"site_name: Test\n",
            "requirements.txt": b"mkdocs==1.6.1\n",
        }.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        # Run rsync's receiver locally, exercising the same remote-shell protocol
        # without a network connection or access to the production server.
        self.executable("ssh", r'''
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

args = sys.argv[1:]
key = Path(args[args.index("-i") + 1])
assert stat.S_IMODE(key.stat().st_mode) == 0o600
assert key.read_text() == "test-private-key\n"
with open(os.environ["TEST_SSH_LOG"], "a") as log:
    log.write(json.dumps(args) + "\n")
if "--server" in args:
    if os.environ.get("TEST_TRANSFER_FAIL"):
        sys.exit(23)
    receiver = args[args.index("--server"):]
    receiver[-1] = os.environ["TEST_DESTINATION"] + "/"
    os.execv(os.environ["TEST_RSYNC"], ["rsync", *receiver])
elif "command -v rsync" in args[-1]:
    if os.environ.get("TEST_PREFLIGHT_FAIL"):
        sys.exit(1)
    print("archive" if os.environ.get("TEST_NO_REMOTE_RSYNC") else "rsync")
elif "tar -xzf" in args[-1]:
    if os.environ.get("TEST_TRANSFER_FAIL"):
        sys.exit(23)
    script = args[-1].replace(
        "/opt/1panel/apps/mkdocs-material/mkdocs-material/data",
        os.environ["TEST_DESTINATION"],
    )
    if os.environ.get("TEST_TRUNCATED_ARCHIVE"):
        archive = sys.stdin.buffer.read()
        result = subprocess.run(["sh", "-c", script], input=archive[:len(archive) // 2])
        sys.exit(result.returncode)
    os.execv("/bin/sh", ["sh", "-c", script])
elif "docker compose restart" not in args[-1]:
    raise AssertionError("Unexpected SSH command")
''')
        self.executable("ssh-keyscan", 'print("example.invalid ssh-ed25519 test-host-key")\n')
        self.env = {
            **os.environ,
            "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
            "TMPDIR": str(self.ssh_temp),
            "LC_ALL": "C",
            "SERVER_HOST": "example.invalid",
            "SERVER_USER": "deploy",
            "SERVER_SSH_KEY": "test-private-key",
            "SERVER_PORT": "2222",
            "TEST_SSH_LOG": str(self.log),
            "TEST_DESTINATION": str(self.destination),
            "TEST_RSYNC": RSYNC,
        }
        workflow = yaml.safe_load(WORKFLOW.read_text())
        self.script = next(step["run"] for step in workflow["jobs"]["deploy"]["steps"] if "run" in step)

    def executable(self, name, body):
        path = self.bin / name
        path.write_text(f"#!{sys.executable}\n" + body)
        path.chmod(0o700)

    def deploy(self, **extra_env):
        self.log.write_text("")
        result = subprocess.run(
            ["bash", "-euo", "pipefail", "-c", self.script],
            cwd=self.source, env={**self.env, **extra_env},
            text=True, capture_output=True, timeout=20,
        )
        self.assertEqual(list(self.ssh_temp.iterdir()), [], "temporary SSH credentials were not removed")
        self.assertEqual(list(self.destination.glob(".deploy-*")), [], "remote staging directory was not removed")
        self.assertNotIn("test-private-key", result.stdout + result.stderr)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        return result, calls

    def transferred(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        match = re.search(r"Number of regular files transferred: ([\d,]+)", result.stdout)
        self.assertIsNotNone(match, result.stdout)
        return int(match.group(1).replace(",", ""))

    def test_incremental_sync_and_scoped_deletion(self):
        (self.destination / "docs").mkdir()
        stale = self.destination / "docs/removed.md"
        stale.write_text("removed from repository")
        unrelated = self.destination / "runtime-state.txt"
        unrelated.write_text("preserve server state")
        result, calls = self.deploy()
        self.assertEqual(self.transferred(result), 8)
        self.assertFalse(stale.exists())
        self.assertEqual(unrelated.read_text(), "preserve server state")
        self.assertTrue((self.destination / ".git/HEAD").is_file())
        self.assertIn("docker compose restart", calls[-1][-1])

        # A fresh checkout changes mtimes, but identical file contents must not upload.
        for path in self.source.rglob("*"):
            if path.is_file():
                stat = path.stat()
                os.utime(path, (stat.st_atime, stat.st_mtime + 60))
        result, _ = self.deploy()
        self.assertEqual(self.transferred(result), 0)

        # The checksum must also detect a change with the same size and timestamp.
        page = self.source / "docs/page.md"
        timestamp = page.stat().st_mtime
        page.write_text("bravo")
        os.utime(page, (timestamp, timestamp))
        result, _ = self.deploy()
        self.assertEqual(self.transferred(result), 1)
        self.assertEqual((self.destination / "docs/page.md").read_text(), "bravo")
        self.assertEqual(
            (self.destination / "docs/assets/demo.mp4").read_bytes(),
            (self.source / "docs/assets/demo.mp4").read_bytes(),
        )

    def test_preflight_failure_stops_before_transfer_and_restart(self):
        result, calls = self.deploy(TEST_PREFLIGHT_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_transfer_failure_does_not_restart_container(self):
        result, calls = self.deploy(TEST_TRANSFER_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("--server" in call for call in calls))
        self.assertFalse(any("docker compose restart" in call[-1] for call in calls))

    def test_archive_fallback_without_remote_rsync(self):
        (self.destination / "docs").mkdir()
        stale = self.destination / "docs/removed.md"
        stale.write_text("removed from repository")
        unrelated = self.destination / "runtime-state.txt"
        unrelated.write_text("preserve server state")
        result, calls = self.deploy(TEST_NO_REMOTE_RSYNC="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("using a full archive over SSH", result.stdout)
        self.assertFalse(any("--server" in call for call in calls))
        self.assertFalse(stale.exists())
        self.assertEqual(unrelated.read_text(), "preserve server state")
        for source in self.source.rglob("*"):
            if source.is_file():
                self.assertEqual(
                    (self.destination / source.relative_to(self.source)).read_bytes(),
                    source.read_bytes(),
                )
        self.assertIn("docker compose restart", calls[-1][-1])

    def test_incomplete_archive_keeps_existing_site(self):
        (self.destination / "docs").mkdir()
        existing = self.destination / "docs/page.md"
        existing.write_text("existing published page")
        result, calls = self.deploy(TEST_NO_REMOTE_RSYNC="1", TEST_TRUNCATED_ARCHIVE="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(existing.read_text(), "existing published page")
        self.assertFalse((self.destination / ".git").exists())
        self.assertFalse(any("docker compose restart" in call[-1] for call in calls))

    def test_archive_upload_failure_does_not_restart_container(self):
        result, calls = self.deploy(TEST_NO_REMOTE_RSYNC="1", TEST_TRANSFER_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.destination.iterdir()), [])
        self.assertFalse(any("docker compose restart" in call[-1] for call in calls))


if __name__ == "__main__":
    unittest.main()
