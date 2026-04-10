"""Tests for the controlled TOTVS RM real tool wrapper."""

import json

import tools.totvs_rm_mock_tool as mock_tool_module
import tools.totvs_rm_real_tool as real_tool_module

from custom.tool_discovery import FORK_TOOL_MODULES
from integrations.totvs_rm.real_errors import TotvsRmRealConfigurationError
from integrations.totvs_rm.real_schemas import SOURCE_NAME, TOOL_SCHEMA
from model_tools import CORE_TOOL_MODULES
from tools.registry import registry


class TestRealToolRegistration:
    def test_tool_is_registered_under_its_own_toolset(self):
        assert registry.get_toolset_for_tool(SOURCE_NAME) == SOURCE_NAME
        assert registry.get_schema(SOURCE_NAME) == TOOL_SCHEMA

    def test_schema_lists_supported_actions(self):
        enum_values = TOOL_SCHEMA["parameters"]["properties"]["action"]["enum"]
        assert enum_values == [
            "buscar_funcionario_por_chapa",
            "buscar_movimento_por_id",
            "buscar_filial_por_id",
            "buscar_coligada_por_codigo",
        ]

    def test_schema_describes_controlled_real_connector(self):
        description = TOOL_SCHEMA["description"].lower()
        assert "real" in description
        assert "nao e o mock" in description
        assert "nao faz fallback" in description

    def test_real_tool_stays_in_fork_discovery_boundary(self):
        assert "tools.totvs_rm_mock_tool" in FORK_TOOL_MODULES
        assert "tools.totvs_rm_real_tool" in FORK_TOOL_MODULES
        assert "tools.totvs_rm_mock_tool" not in CORE_TOOL_MODULES
        assert "tools.totvs_rm_real_tool" not in CORE_TOOL_MODULES

    def test_mock_and_real_remain_separate_toolsets(self):
        assert registry.get_toolset_for_tool("totvs_rm_mock") == "totvs_rm_mock"
        assert registry.get_toolset_for_tool("totvs_rm_real") == "totvs_rm_real"
        assert mock_tool_module is not None
        assert real_tool_module is not None


class TestRealToolOutputContract:
    def test_valid_action_returns_json_string(self, monkeypatch):
        seen: dict[str, object] = {}

        def fake_handle_request(request):
            seen["request"] = request
            return {
                "ok": True,
                "action": "buscar_filial_por_id",
                "data": {
                    "item": {
                        "id": 101,
                        "codigo": "SP01",
                        "nome": "Matriz Sao Paulo",
                    },
                    "count": 1,
                    "filters_applied": {"filial_id": "101"},
                    "warnings": [],
                },
                "errors": [],
            }

        monkeypatch.setattr(real_tool_module.real_service, "handle_request", fake_handle_request)

        result = real_tool_module.totvs_rm_real_tool({
            "action": "buscar_filial_por_id",
            "payload": {"filial_id": "101"},
        })

        assert isinstance(result, str)
        data = json.loads(result)
        assert set(data) == {"ok", "source", "action", "data", "errors"}
        assert data["ok"] is True
        assert data["source"] == "totvs_rm_real"
        assert data["action"] == "buscar_filial_por_id"
        assert data["errors"] == []
        assert data["data"]["count"] == 1
        assert data["data"]["filters_applied"] == {"filial_id": "101"}
        assert data["data"]["warnings"] == []
        assert data["data"]["item"]["codigo"] == "SP01"
        assert seen["request"] == {
            "action": "buscar_filial_por_id",
            "payload": {"filial_id": "101"},
        }

    def test_configuration_failure_returns_controlled_json_string(self, monkeypatch):
        def fake_handle_request(_request):
            raise TotvsRmRealConfigurationError(
                "base_url e obrigatorio quando transport nao e informado"
            )

        monkeypatch.setattr(real_tool_module.real_service, "handle_request", fake_handle_request)

        result = json.loads(real_tool_module.totvs_rm_real_tool({
            "action": "buscar_coligada_por_codigo",
            "payload": {"codigo": "COL001"},
        }))

        assert result == {
            "ok": False,
            "source": "totvs_rm_real",
            "action": "buscar_coligada_por_codigo",
            "data": None,
            "errors": ["base_url e obrigatorio quando transport nao e informado"],
        }

    def test_non_dict_args_fall_back_to_empty_request(self):
        result = json.loads(real_tool_module.totvs_rm_real_tool("not-a-dict"))
        assert result == {
            "ok": False,
            "source": "totvs_rm_real",
            "action": "",
            "data": None,
            "errors": ["Action e obrigatoria"],
        }
