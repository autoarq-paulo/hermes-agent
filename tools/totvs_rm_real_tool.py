"""Thin Hermes tool wrapper for the controlled TOTVS RM real integration."""

from __future__ import annotations

from typing import Any

from adapters.totvs_rm import real_response_adapter
from integrations.totvs_rm import real_service
from integrations.totvs_rm.real_errors import TotvsRmRealError
from integrations.totvs_rm.real_schemas import SOURCE_NAME, TOOL_SCHEMA
from tools.registry import registry


def _normalize_request(args: Any) -> dict[str, Any]:
    if isinstance(args, dict):
        return args
    return {}


def _build_error_result(action: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "action": action,
        "data": None,
        "errors": [str(message)],
    }


def totvs_rm_real_tool(args: Any, **_kwargs) -> str:
    # Controlled real connector: no fallback to the mock and no implicit endpoint guessing.
    request = _normalize_request(args)
    try:
        result = real_service.handle_request(request)
    except TotvsRmRealError as exc:
        action = str(request.get("action") or "").strip()
        result = _build_error_result(action, str(exc))
    except Exception:
        action = str(request.get("action") or "").strip()
        result = _build_error_result(
            action,
            "Erro inesperado na integracao real TOTVS RM",
        )
    return real_response_adapter.serialize_response(result)


registry.register(
    name=SOURCE_NAME,
    toolset=SOURCE_NAME,
    schema=TOOL_SCHEMA,
    handler=totvs_rm_real_tool,
    emoji="",
)
