#!/usr/bin/env python3
"""Check Hermes container image supply-chain guardrails.

The policy is intentionally narrow: it protects terminal/runtime image
configuration surfaces and Dockerfile bases without trying to lint arbitrary
documentation examples or benchmark fixtures.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BANNED_IMAGE = "nikolaik/" + "python-nodejs"
BANNED_EXCEPTIONS = {
    Path("docs/governanca/adr/ADR-006-runtime-container-supply-chain.md"),
    Path("docs/governanca/adr/ADR-007-publicacao-runtime-ghcr.md"),
    Path("docs/governanca/runtime_container_policy.md"),
    Path("docs/governanca/runtime_container_rollback.md"),
}

APPROVED_TERMINAL_IMAGE_PATTERNS = (
    re.compile(r"^hermes-agent-local:runtime-python3\.11-node20$"),
    re.compile(r"^docker://hermes-agent-local:runtime-python3\.11-node20$"),
    re.compile(
        r"^(docker://)?ghcr\.io/autoarq-paulo/hermes-agent-runtime:"
        r"(python3\.11-node20|stable|sha-[0-9a-f]{7,40}|v?[0-9][A-Za-z0-9._-]*-runtime)"
        r"(@sha256:[0-9a-f]{64})?$"
    ),
)

APPROVED_DOCKERFILE_BASES = {
    "python:3.11-slim-bookworm",
    "node:20-bookworm-slim",
    "node:22-trixie-slim",
    "debian:13.4",
    "ghcr.io/astral-sh/uv:0.11.6-python3.13-trixie@sha256:b3c543b6c4f23a5f2df22866bd7857e5d304b67a564f4feab6ac22044dde719b",
    "tianon/gosu:1.19-trixie@sha256:3b176695959c71e123eb390d427efc665eeb561b1540e82679c15e992006b8b9",
}

POLICY_PATHS = [
    Path(".env.example"),
    Path("docker-compose.yml"),
    Path(".github/workflows/runtime-image.yml"),
    Path("cli-config.yaml.example"),
    Path("hermes_constants.py"),
    Path("cli.py"),
    Path("hermes_cli/config.py"),
    Path("hermes_cli/setup.py"),
    Path("hermes_cli/status.py"),
    Path("tools/terminal_tool.py"),
    Path("website/docs/user-guide/configuration.md"),
    Path("website/docs/user-guide/security.md"),
    Path("website/docs/guides/team-telegram-assistant.md"),
    Path("website/docs/reference/environment-variables.md"),
]

TERMINAL_IMAGE_RE = re.compile(
    r"(?P<key>TERMINAL_(?:DOCKER|SINGULARITY|MODAL|DAYTONA)_IMAGE|"
    r"HERMES_(?:LOCAL_DOCKER|TERMINAL_RUNTIME|REMOTE_TERMINAL)_IMAGE|"
    r"(?:docker|singularity|modal|daytona)_image)"
    r"['\"]?\s*[:=]\s*['\"]?(?P<image>[A-Za-z0-9./:_@-]+)"
)
FROM_RE = re.compile(r"^FROM\s+(?P<image>\S+)", re.MULTILINE)


def iter_text_files() -> list[Path]:
    ignored_parts = {".git", "venv", ".venv", "__pycache__", "docker/data"}
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        rel_text = str(rel)
        if any(part in rel.parts for part in ignored_parts) or rel_text.startswith("docker/data/"):
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        files.append(rel)
    return files


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def _is_approved_terminal_image(image: str) -> bool:
    return any(pattern.match(image) for pattern in APPROVED_TERMINAL_IMAGE_PATTERNS)


def check_banned_image(failures: list[str]) -> None:
    for rel in iter_text_files():
        if rel in BANNED_EXCEPTIONS:
            continue
        text = (ROOT / rel).read_text(encoding="utf-8")
        if BANNED_IMAGE in text:
            fail(
                f"{rel}: banned image '{BANNED_IMAGE}' found. Use the project-owned runtime image or document an explicit exception.",
                failures,
            )


def check_terminal_policy_paths(failures: list[str]) -> None:
    for rel in POLICY_PATHS:
        path = ROOT / rel
        if not path.exists():
            fail(f"{rel}: policy path is missing", failures)
            continue
        text = path.read_text(encoding="utf-8")
        for match in TERMINAL_IMAGE_RE.finditer(text):
            image = match.group("image").rstrip("`,")
            if image.startswith((
                "DEFAULT_TERMINAL_",
                "TERMINAL_",
                "HERMES_TERMINAL_",
                "os.getenv",
                "get_default_terminal_",
                "f",
                "published",
            )) or image == "str":
                continue
            if not _is_approved_terminal_image(image):
                fail(
                    f"{rel}: unapproved terminal image '{image}' for {match.group('key')}. "
                    "Allowed runtime images are hermes-agent-local:runtime-python3.11-node20 "
                    "or ghcr.io/autoarq-paulo/hermes-agent-runtime with an approved tag/digest. "
                    "Update docs/governanca/runtime_container_policy.md and this script if governance approves a new image.",
                    failures,
                )


def check_dockerfile_bases(failures: list[str]) -> None:
    for path in (ROOT / "docker").glob("Dockerfile*"):
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        for match in FROM_RE.finditer(text):
            image = match.group("image")
            if image not in APPROVED_DOCKERFILE_BASES:
                fail(
                    f"{rel}: unapproved Dockerfile base '{image}'. "
                    "Use an approved official/pinned base or update governance first.",
                    failures,
                )


def main() -> int:
    failures: list[str] = []
    check_banned_image(failures)
    check_terminal_policy_paths(failures)
    check_dockerfile_bases(failures)
    if failures:
        print("Container image policy check failed:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Container image policy check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
