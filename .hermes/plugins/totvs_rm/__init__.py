"""Project plugin for the TOTVS RM mock and controlled real tools.

This plugin keeps fork-specific discovery out of ``model_tools.py`` so the
core Hermes import path stays unchanged. Enable project plugins with
``HERMES_ENABLE_PROJECT_PLUGINS=true`` when you want this extension loaded.
"""

from __future__ import annotations

from integrations.totvs_rm.mock_loader import has_required_fixtures
from integrations.totvs_rm.real_schemas import SOURCE_NAME as REAL_SOURCE_NAME
from integrations.totvs_rm.real_schemas import TOOL_SCHEMA as REAL_TOOL_SCHEMA
from integrations.totvs_rm.schemas import SOURCE_NAME as MOCK_SOURCE_NAME
from integrations.totvs_rm.schemas import TOOL_SCHEMA as MOCK_TOOL_SCHEMA
from tools.totvs_rm_mock_tool import totvs_rm_mock_tool
from tools.totvs_rm_real_tool import totvs_rm_real_tool


def _check_totvs_rm_mock_available() -> bool:
    return has_required_fixtures()


def register(ctx) -> None:
    ctx.register_tool(
        name=MOCK_SOURCE_NAME,
        toolset=MOCK_SOURCE_NAME,
        schema=MOCK_TOOL_SCHEMA,
        handler=totvs_rm_mock_tool,
        check_fn=_check_totvs_rm_mock_available,
        emoji="",
    )
    ctx.register_tool(
        name=REAL_SOURCE_NAME,
        toolset=REAL_SOURCE_NAME,
        schema=REAL_TOOL_SCHEMA,
        handler=totvs_rm_real_tool,
        emoji="",
    )
