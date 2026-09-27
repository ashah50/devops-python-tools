import subprocess
from dataclasses import dataclass
from pathlib import Path
import argparse

@dataclass
class GitResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    error: str | None = None  # e.g., "INVALID_DIRECTORY", "GIT_NOT_INSTALLED", "NOT_A_REPO"

@dataclass
class RepoState:
    path: str
    is_repo: bool
    branch: str | None = None
    is_dirty: bool | None = None
    ahead: int | None = None  
    behind: int | None = None  
    commit_hash: str | None = None
    error_message: str | None = None

def run_git(args, cwd, timeout: float = 5.0):
    target_dir = Path(cwd)

    # 1. Validate cwd up front to disambiguate missing dir vs. missing git binary
    if not target_dir.exists() or not target_dir.is_dir():
        return GitResult(
            ok=False,
            error="INVALID_DIRECTORY",
            stderr=f"Path is not a valid directory: {cwd}",
        )
    # 2. Run git command safely inside target_dir
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=target_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError:
        # Raised if 'git' executable itself is missing on PATH
        return GitResult(
            ok=False,
            error="GIT_NOT_INSTALLED",
            stderr="git executable not found on system PATH",
        )
    except subprocess.TimeoutExpired:
        return GitResult(
            ok=False,
            error="TIMEOUT",
            stderr=f"Git command timed out after {timeout} seconds",
        )
    except Exception as e:
        return GitResult(
            ok=False,
            error="UNKNOWN_ERROR",
            stderr=str(e),
        )
    # 3. Handle returncode mapping (rc=0 is success, non-zero is failure)
    if proc.returncode != 0:
        stderr_msg = proc.stderr.strip()
        error_type = "NOT_A_REPO" if "not a git repository" in stderr_msg.lower() else "GIT_ERROR"
        return GitResult(
            ok=False,
            stdout=proc.stdout.strip(),
            stderr=stderr_msg,
            error=error_type,
            returncode=proc.returncode,
        )

    return GitResult(
        ok=True,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
        returncode=proc.returncode,
    )

def collect(paths):
    reports = []

    for path in paths:
        probe = run_git(["rev-parse", "--abbrev-ref", "HEAD"], path)

        if not probe.ok:
            reports.append(RepoState(
                path=str(path),
                is_repo=False,
                error_message=probe.stderr,
            ))
            continue

        head = run_git(["rev-parse", "--short", "HEAD"], path)
        status = run_git(["status", "--porcelain"], path)

        counts = run_git(["rev-list", "--count", "--left-right", "@{upstream}...HEAD"], path)

        ahead = behind = None
        if counts.ok:
            behind_str, ahead_str = counts.stdout.split("\t")
            behind = int(behind_str)
            ahead = int(ahead_str)

        reports.append(RepoState(
            path=str(path),
            is_repo=True,
            branch=probe.stdout,
            commit_hash=head.stdout if head.ok else None,
            is_dirty=bool(status.stdout) if status.ok else None,
            ahead=ahead,
            behind=behind,
        ))

    return reports

def _fmt(value):
    if value is None:
        return "-"
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return str(value)

def render(reports):
    if not reports:
        return "No repos"

    width = max(len(r.path) for r in reports)

    header = (
        f"{'REPO':<{width}}  {'BRANCH':<8} {'HEAD':<9}  "
        f"{'DIRTY':<5} {'AHEAD':>5} {'BEHIND':<6}  ERROR"
    )
    lines = [header]

    for r in reports:
        lines.append(
            f"{r.path:<{width}}  {_fmt(r.branch):<8} {_fmt(r.commit_hash):<9}  "
            f"{_fmt(r.is_dirty):<5} {_fmt(r.ahead):>5} {_fmt(r.behind):<6}  "
            f"{_fmt(r.error_message or '')}"
        )

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Report on the state of git repos")
    parser.add_argument("paths", nargs="+", help="repo paths to report on")
    args = parser.parse_args()

    print(render(collect(args.paths)))


if __name__ == "__main__":
    main()
