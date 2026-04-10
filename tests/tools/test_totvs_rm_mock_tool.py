"""Tests for the TOTVS RM mock tool wrapper."""

import json

from custom.tool_discovery import FORK_TOOL_MODULES
from model_tools import CORE_TOOL_MODULES
from tools.registry import registry
from tools.totvs_rm_mock_tool import TOOL_SCHEMA, totvs_rm_mock_tool


class TestToolRegistration:
    def test_tool_is_registered_under_its_own_toolset(self):
        assert registry.get_toolset_for_tool("totvs_rm_mock") == "totvs_rm_mock"
        assert registry.get_schema("totvs_rm_mock") == TOOL_SCHEMA

    def test_schema_lists_supported_actions(self):
        enum_values = TOOL_SCHEMA["parameters"]["properties"]["action"]["enum"]
        assert enum_values == [
            "listar_coligadas",
            "listar_filiais",
            "listar_funcionarios",
            "listar_movimentos",
            "buscar_coligada_por_codigo",
            "buscar_filial_por_id",
            "buscar_funcionario_por_chapa",
            "buscar_movimento_por_id",
        ]

    def test_schema_lists_enriched_payload_fields(self):
        payload_props = TOOL_SCHEMA["parameters"]["properties"]["payload"]["properties"]
        for field in (
            "codigo",
            "filial_id",
            "filial_codigo",
            "status",
            "tipo",
            "fail_on_empty",
            "simulate_error",
        ):
            assert field in payload_props

    def test_schema_is_closed_at_top_level(self):
        assert TOOL_SCHEMA["parameters"]["additionalProperties"] is False

    def test_fork_tool_is_registered_in_custom_discovery_boundary(self):
        assert "tools.totvs_rm_mock_tool" in FORK_TOOL_MODULES
        assert "tools.totvs_rm_mock_tool" not in CORE_TOOL_MODULES


class TestToolOutputContract:
    def test_valid_action_returns_json_string(self):
        result = totvs_rm_mock_tool({
            "action": "buscar_funcionario_por_chapa",
            "payload": {"chapa": "000123"},
        })
        assert isinstance(result, str)
        data = json.loads(result)
        assert set(data) == {"ok", "source", "action", "data", "errors"}
        assert data["ok"] is True
        assert data["source"] == "totvs_rm_mock"
        assert data["action"] == "buscar_funcionario_por_chapa"
        assert data["errors"] == []
        assert data["data"]["count"] == 1
        assert data["data"]["filters_applied"] == {"chapa": "000123"}
        assert data["data"]["warnings"] == []
        assert data["data"]["item"]["nome"] == "Ana Souza"

    def test_new_action_returns_json_string(self):
        result = json.loads(totvs_rm_mock_tool({
            "action": "buscar_coligada_por_codigo",
            "payload": {"codigo": "COL002"},
        }))
        assert result["ok"] is True
        assert result["source"] == "totvs_rm_mock"
        assert result["action"] == "buscar_coligada_por_codigo"
        assert result["errors"] == []
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {"codigo": "COL002"}
        assert result["data"]["warnings"] == []
        assert result["data"]["item"]["codigo"] == "COL002"

    def test_unknown_action_returns_standard_error_envelope(self):
        result = json.loads(totvs_rm_mock_tool({
            "action": "acao_inexistente",
            "payload": {},
        }))
        assert result == {
            "ok": False,
            "source": "totvs_rm_mock",
            "action": "acao_inexistente",
            "data": None,
            "errors": ["Acao nao suportada: acao_inexistente"],
        }

    def test_missing_record_returns_standard_error_envelope(self):
        result = json.loads(totvs_rm_mock_tool({
            "action": "buscar_movimento_por_id",
            "payload": {"movimento_id": "MOV-9999"},
        }))
        assert result["ok"] is False
        assert result["source"] == "totvs_rm_mock"
        assert result["action"] == "buscar_movimento_por_id"
        assert result["data"] is None
        assert result["errors"] == ["Movimento nao encontrado"]

    def test_non_dict_args_fall_back_to_empty_request(self):
        result = json.loads(totvs_rm_mock_tool("not-a-dict"))
        assert result == {
            "ok": False,
            "source": "totvs_rm_mock",
            "action": "",
            "data": None,
            "errors": ["Action e obrigatoria"],
        }
