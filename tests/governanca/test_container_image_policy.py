import subprocess
import sys
from pathlib import Path


def test_container_image_policy_guardrail():
    repo = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "scripts/check_container_image_policy.py"],
        cwd=repo,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
