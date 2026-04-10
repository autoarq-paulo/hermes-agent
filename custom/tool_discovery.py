"""Explicit discovery boundary for fork-specific tool modules.

Keep this list small and intentional. The Hermes baseline stays in
``model_tools.CORE_TOOL_MODULES``; fork-specific tools are added here so the
core discovery list does not need to change for every new extension.
"""

from __future__ import annotations

FORK_TOOL_MODULES = (
    "tools.totvs_rm_mock_tool",
    "tools.totvs_rm_real_tool",
)
