"""Thin Hermes tool wrapper for the local TOTVS RM mock integration.

The actual registration happens in the project plugin under
``.hermes/plugins/totvs_rm`` so this module stays importable without
side effects and the fork-specific discovery path stays out of the core.
"""

from __future__ import annotations

from typing import Any

from adapters.totvs_rm.response_adapter import serialize_response
from integrations.totvs_rm.mock_service import handle_request
from integrations.totvs_rm.schemas import TOOL_SCHEMA


def totvs_rm_mock_tool(args: Any, **_kwargs) -> str:
    # Keep malformed tool-call arguments deterministic: treat anything that is
    # not a dict as an empty request and let the service return the contract.
    request = args if isinstance(args, dict) else {}
    return serialize_response(handle_request(request))
