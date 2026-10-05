import subprocess
import pytest
from dfreport import DiskUsage, disk_usage


# Sample stdout from `df -hP /`
DF_SUCCESS_STDOUT = (
    "Filesystem      Size  Used Avail Use% Mounted on\n"
    "/dev/nvme0n1p2  468G  177G  268G  40% /\n"
)

# Sample stdout where mount point contains spaces
DF_SPACES_STDOUT = (
    "Filesystem      Size  Used Avail Use% Mounted on\n"
    "/dev/sda1       1.8T  500G  1.3T  28% /media/External Drive\n"
)


def test_builds_correct_command(monkeypatch):
    """Verifies that disk_usage invokes subprocess.run with exact command arguments."""
    called_cmd = None

    def fake_run(cmd, **kwargs):
        nonlocal called_cmd
        called_cmd = cmd
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout=DF_SUCCESS_STDOUT, stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    disk_usage("/")

    # The exact command vector must match: catches typos like ['df', '-hp', '/']
    assert called_cmd == ["df", "-hP", "/"]


def test_parses_df_output(monkeypatch):
    """Verifies successful parsing into a DiskUsage dataclass instance."""
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout=DF_SUCCESS_STDOUT, stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = disk_usage("/")

    expected = DiskUsage(
        filesystem="/dev/nvme0n1p2",
        size="468G",
        used="177G",
        avail="268G",
        use_pct="40%",
        mounted_on="/",
    )

    assert result == expected


def test_returns_none_on_df_failure(monkeypatch):
    """Verifies that a non-zero exit code returns None safely."""
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=1,
            stdout="",
            stderr="df: '/invalid/path': No such file or directory",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert disk_usage("/invalid/path") is None


def test_parses_mount_point_with_spaces(monkeypatch):
    """Bonus: Verifies maxsplit=5 preserves spaces in the mount point."""
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout=DF_SPACES_STDOUT, stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = disk_usage("/media/External Drive")

    assert result is not None
    assert result.mounted_on == "/media/External Drive"