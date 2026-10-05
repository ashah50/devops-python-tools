import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DiskUsage:
    filesystem: str
    size: str
    used: str
    avail: str
    use_pct: str
    mounted_on: str

def disk_usage(path):
    proc = subprocess.run(
        ["df", "-hP", path],
        capture_output=True,
        text=True,
        check=False,
    )

    if proc.returncode != 0:
        logger.warning("df command failed for %s (rc=%d): %s", path, proc.returncode, proc.stderr.strip())
        return None

    lines = proc.stdout.strip().splitlines()
    if len(lines) < 2:
        logger.warning("df command output is unexpected for %s: %r", path, proc.stdout.strip())
        return None

    parts = lines[1].split(maxsplit=5)
    if len(parts) < 6:
        logger.warning("Could not parse output line for %s: %r", path, lines[1])
        return None


    return DiskUsage(
        filesystem=parts[0],
        size=parts[1],
        used=parts[2],
        avail=parts[3],
        use_pct=parts[4],
        mounted_on=parts[5]
    )