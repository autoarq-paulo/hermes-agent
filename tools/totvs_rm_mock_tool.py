"""Thin Hermes tool wrapper for the local TOTVS RM mock integration."""

from __future__ import annotations

from typing import Any

from adapters.totvs_rm.response_adapter import serialize_response
from integrations.totvs_rm.mock_loader import has_required_fixtures
from integrations.totvs_rm.mock_service import handle_request
from integrations.totvs_rm.schemas import SOURCE_NAME, TOOL_SCHEMA
from tools.registry import registry


def _check_totvs_rm_mock_available() -> bool:
    return has_required_fixtures()


def totvs_rm_mock_tool(args: Any, **_kwargs) -> str:
    # Keep malformed tool-call arguments deterministic: treat anything that is
    # not a dict as an empty request and let the service return the contract.
    request = args if isinstance(args, dict) else {}
    return serialize_response(handle_request(request))


registry.register(
    name=SOURCE_NAME,
    toolset=SOURCE_NAME,
    schema=TOOL_SCHEMA,
    handler=totvs_rm_mock_tool,
    check_fn=_check_totvs_rm_mock_available,
    emoji="",
)
