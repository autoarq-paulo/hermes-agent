"""Tests for the controlled TOTVS RM real tool wrapper."""

import json

import tools.totvs_rm_real_tool as real_tool_module

from integrations.totvs_rm.real_errors import TotvsRmRealConfigurationError
from integrations.totvs_rm.real_schemas import SOURCE_NAME, TOOL_SCHEMA


class TestRealToolSchema:
    def test_tool_schema_lists_supported_actions(self):
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

    def test_source_name_matches_schema(self):
        assert SOURCE_NAME == "totvs_rm_real"


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
