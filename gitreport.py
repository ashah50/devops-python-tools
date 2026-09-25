from importlib.resources import path
import subprocess
from dataclasses import dataclass
from pathlib import Path

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