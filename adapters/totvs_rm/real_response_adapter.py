"""Serialize real TOTVS RM service results into the fork contract."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from integrations.totvs_rm.real_schemas import RealServiceResult, RealToolResponse, SOURCE_NAME


def _normalize_errors(errors: Any) -> List[str]:
    if errors is None:
        return []
    if isinstance(errors, list):
        return [str(error) for error in errors if str(error)]
    return [str(errors)]


def build_response(result: Dict[str, Any], source: str = SOURCE_NAME) -> RealToolResponse:
    ok = bool(result.get("ok"))
    response: RealToolResponse = {
        "ok": ok,
        "source": source,
        "action": str(result.get("action") or "").strip(),
        "data": result.get("data") if ok else None,
        "errors": _normalize_errors(result.get("errors")),
    }
    if not ok:
        response["data"] = None
    return response


def serialize_response(result: RealServiceResult, source: str = SOURCE_NAME) -> str:
    return json.dumps(build_response(result, source=source), ensure_ascii=False)
