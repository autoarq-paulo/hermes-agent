"""Load local JSON fixtures for the TOTVS RM mock integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, TypeAlias

_FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "totvs_rm"
JSON_ROWS: TypeAlias = list[dict[str, Any]]
_FIXTURE_FILES = {
    "coligadas": "coligadas.json",
    "filiais": "filiais.json",
    "funcionarios": "funcionarios.json",
    "movimentos": "movimentos.json",
}


def fixture_dir() -> Path:
    """Return the directory that stores the mock fixtures."""
    return _FIXTURE_ROOT


def _fixture_path(filename: str) -> Path:
    return _FIXTURE_ROOT / filename


def _read_json(filename: str) -> JSON_ROWS:
    path = _fixture_path(filename)
    if not path.is_file():
        raise FileNotFoundError(f"Fixture nao encontrado: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise TypeError(f"Fixture {filename} deve conter uma lista JSON")
    return data


def has_required_fixtures() -> bool:
    """Return True when all expected mock fixture files are present."""
    try:
        return all(_fixture_path(filename).is_file() for filename in _FIXTURE_FILES.values())
    except OSError:
        return False


def load_coligadas() -> List[Dict[str, Any]]:
    return _read_json(_FIXTURE_FILES["coligadas"])


def load_filiais() -> List[Dict[str, Any]]:
    return _read_json(_FIXTURE_FILES["filiais"])


def load_funcionarios() -> List[Dict[str, Any]]:
    return _read_json(_FIXTURE_FILES["funcionarios"])


def load_movimentos() -> List[Dict[str, Any]]:
    return _read_json(_FIXTURE_FILES["movimentos"])


def load_catalog() -> Dict[str, JSON_ROWS]:
    """Load the full mock catalog in a single call."""
    return {
        "coligadas": load_coligadas(),
        "filiais": load_filiais(),
        "funcionarios": load_funcionarios(),
        "movimentos": load_movimentos(),
    }
