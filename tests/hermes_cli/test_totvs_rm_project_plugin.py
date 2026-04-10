"""Tests for the TOTVS RM project plugin."""

from pathlib import Path

from hermes_cli.plugins import PluginManager
from tools.registry import registry


class TestTotvsRmProjectPlugin:
    def test_project_plugin_registers_totvs_rm_tools(self, monkeypatch):
        repo_root = Path(__file__).resolve().parents[2]
        monkeypatch.chdir(repo_root)
        monkeypatch.setenv("HERMES_ENABLE_PROJECT_PLUGINS", "true")

        mgr = PluginManager()
        mgr.discover_and_load()

        assert "totvs_rm" in mgr._plugins
        assert mgr._plugins["totvs_rm"].enabled is True
        assert registry.get_toolset_for_tool("totvs_rm_mock") == "totvs_rm_mock"
        assert registry.get_toolset_for_tool("totvs_rm_real") == "totvs_rm_real"
        assert {"totvs_rm_mock", "totvs_rm_real"} <= mgr._plugin_tool_names

    def test_project_plugin_exposes_two_tools(self, monkeypatch):
        repo_root = Path(__file__).resolve().parents[2]
        monkeypatch.chdir(repo_root)
        monkeypatch.setenv("HERMES_ENABLE_PROJECT_PLUGINS", "true")

        mgr = PluginManager()
        mgr.discover_and_load()

        listing = mgr.list_plugins()
        plugin_info = next(item for item in listing if item["name"] == "totvs_rm")
        assert plugin_info["enabled"] is True
        assert plugin_info["tools"] == 2
