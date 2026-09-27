import pytest
import gitreport
from gitreport import _fmt, render, RepoState, collect, GitResult

@pytest.mark.parametrize("value, expected", [
    (None, "-"),
    (True, "Yes"),
    (False, "No"),
    (0, "0"),
    (2, "2"),
    ("master", "master"),
])
def test_fmt(value, expected):
    assert _fmt(value) == expected

def test_render_empty():
    assert render([]) == "No repos"

def test_render_no_upstream_shows_dash_not_zero():
    reports = [
        RepoState(path="/sync", is_repo=True, branch="main", commit_hash="abc1234", is_dirty=False, ahead=0, behind=0),
        RepoState(path="/noups", is_repo=True, branch="main", commit_hash="def5678", is_dirty=False, ahead=None, behind=None),
    ]
    sync_row, noups_row = render(reports).splitlines()[1:]
    assert sync_row.split()[-2:] == ["0", "0"]
    assert noups_row.split()[-2:] == ["-", "-"]

def test_render_one_line_per_repo_plus_header():
    reports = [RepoState(path=f"/r{n}", is_repo=True, branch="main") for n in range(3)]
    assert len(render(reports).splitlines()) == 4  # 3 repos + header

def test_render_broken_repo_carries_error():
    reports = [RepoState(path="/broken", is_repo=False, error_message="not a git repository")]
    assert render(reports).splitlines()[1].endswith("not a git repository")

def test_collect_non_repo(monkeypatch):
    def fake_run_git(args, cwd, timeout=5.0):
        return GitResult(ok=False, stderr="fatal: not a git repository", error="NOT_A_REPO", returncode=128)
    monkeypatch.setattr(gitreport,"run_git", fake_run_git)
    result = collect(["/nope"])
    assert len(result) == 1
    assert result[0].is_repo is False
    assert result[0].branch is None
    assert result[0].ahead is None

def test_collect_healthy_repo(monkeypatch):
    def fake_run_git(args, cwd, timeout=5.0):
        if args == ["rev-parse", "--abbrev-ref", "HEAD"]:
            return GitResult(ok=True, stdout="main", returncode=0)
        if args == ["rev-parse", "--short", "HEAD"]:
            return GitResult(ok=True, stdout="abc1234")
        if args == ["status", "--porcelain"]:
            return GitResult(ok=True, stdout="", returncode=0)
        if args[0] == "rev-list":
            return GitResult(ok=True, stdout="0\t2", returncode=0)
        raise AssertionError(f"unexpected git call: {args}")
    monkeypatch.setattr(gitreport, "run_git", fake_run_git)
    r = collect(["/repo"])[0]
    assert r.is_repo is True
    assert r.branch == "main"
    assert r.commit_hash == "abc1234"
    assert r.is_dirty is False
    assert r.behind == 0
    assert r.ahead == 2

def test_collect_no_upstream_leaves_ahead_behind_none(monkeypatch):
    def fake_run_git(args, cwd, timeout=5.0):
        if args[0] == "rev-list":
            return GitResult(ok=False, stderr="fatal: no upstream configured", error="GIT_ERROR", returncode=128)
        return GitResult(ok=True, stdout="main", returncode=0)
    monkeypatch.setattr(gitreport, "run_git", fake_run_git)
    r = collect(["/repo"])[0]
    assert r.is_repo is True
    assert r.ahead is None
    assert r.behind is None

def test_collect_one_bad_repo_does_not_stop_others(monkeypatch):
    def fake_run_git(args, cwd, timeout=5.0):
        if cwd == "/bad":
            return GitResult(ok=False, stderr="fatal: not a git repository", error="NOT_A_REPO", returncode=128)
        if args[0] == "rev-list":
            return GitResult(ok=True, stdout="0\t0", returncode=0)
        return GitResult(ok=True, stdout="main", returncode=0)
    monkeypatch.setattr(gitreport, "run_git", fake_run_git)
    results = collect(["/good1", "/bad", "/good2"])
    assert [r.is_repo for r in results] == [True, False, True]
