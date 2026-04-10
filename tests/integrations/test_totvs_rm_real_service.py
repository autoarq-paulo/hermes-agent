"""Tests for the controlled real TOTVS RM service foundation."""

import json

from adapters.totvs_rm.real_response_adapter import serialize_response
from integrations.totvs_rm.real_errors import (
    TotvsRmRealNotFoundError,
    TotvsRmRealTransportError,
)
from integrations.totvs_rm.real_service import TotvsRmRealService


class FakeClient:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = []

    def request(self, action, payload=None):
        self.calls.append((action, dict(payload or {})))
        if self.exc is not None:
            raise self.exc
        return self.response


class TestTotvsRmRealService:
    def test_unsupported_action_returns_error_envelope(self):
        service = TotvsRmRealService(FakeClient())

        result = service.handle_request({
            "action": "listar_coligadas",
            "payload": {},
        })

        assert result == {
            "ok": False,
            "action": "listar_coligadas",
            "data": None,
            "errors": ["Acao nao suportada: listar_coligadas"],
        }

    def test_buscar_funcionario_por_chapa_normalizes_client_response(self):
        client = FakeClient(
            response={
                "item": {
                    "chapa": "000123",
                    "nome": "Ana Souza",
                    "cargo": "Analista de RH",
                }
            }
        )
        service = TotvsRmRealService(client)

        first = service.handle_request({
            "action": "buscar_funcionario_por_chapa",
            "payload": {"chapa": "000123"},
        })
        second = service.handle_request({
            "action": "buscar_funcionario_por_chapa",
            "payload": {"chapa": "000123"},
        })

        assert first == second
        assert client.calls == [
            ("buscar_funcionario_por_chapa", {"chapa": "000123"}),
            ("buscar_funcionario_por_chapa", {"chapa": "000123"}),
        ]
        assert first["ok"] is True
        assert first["action"] == "buscar_funcionario_por_chapa"
        assert first["errors"] == []
        assert first["data"]["count"] == 1
        assert first["data"]["filters_applied"] == {"chapa": "000123"}
        assert first["data"]["warnings"] == []
        assert first["data"]["item"]["nome"] == "Ana Souza"

        serialized = json.loads(serialize_response(first))
        assert serialized["ok"] is True
        assert serialized["source"] == "totvs_rm_real"
        assert serialized["action"] == "buscar_funcionario_por_chapa"
        assert serialized["errors"] == []
        assert serialized["data"]["item"]["chapa"] == "000123"

    def test_buscar_movimento_por_id_accepts_id_alias_and_normalizes_envelope(self):
        client = FakeClient(
            response={
                "data": {
                    "item": {
                        "id": "MOV-1002",
                        "chapa": "000456",
                        "tipo": "ferias",
                    },
                    "warnings": ["sincronizado"],
                }
            }
        )
        service = TotvsRmRealService(client)

        result = service.handle_request({
            "action": "buscar_movimento_por_id",
            "payload": {"id": "MOV-1002"},
        })

        assert result["ok"] is True
        assert result["action"] == "buscar_movimento_por_id"
        assert result["errors"] == []
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {"movimento_id": "MOV-1002"}
        assert result["data"]["warnings"] == ["sincronizado"]
        assert result["data"]["item"]["id"] == "MOV-1002"
        assert client.calls == [
            ("buscar_movimento_por_id", {"movimento_id": "MOV-1002"}),
        ]

    def test_buscar_filial_por_id_normalizes_client_response(self):
        client = FakeClient(
            response={
                "data": {
                    "item": {
                        "id": 101,
                        "coligada_id": 1,
                        "codigo": "SP01",
                        "nome": "Matriz Sao Paulo",
                    },
                    "warnings": ["lookup por id"],
                }
            }
        )
        service = TotvsRmRealService(client)

        result = service.handle_request({
            "action": "buscar_filial_por_id",
            "payload": {"id": "101"},
        })

        assert result["ok"] is True
        assert result["action"] == "buscar_filial_por_id"
        assert result["errors"] == []
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {"filial_id": "101"}
        assert result["data"]["warnings"] == ["lookup por id"]
        assert result["data"]["item"]["id"] == 101
        assert client.calls == [
            ("buscar_filial_por_id", {"filial_id": "101"}),
        ]

    def test_buscar_coligada_por_codigo_is_deterministic_and_serializable(self):
        client = FakeClient(
            response={
                "item": {
                    "id": 1,
                    "codigo": "COL001",
                    "razao_social": "Hermes Servicos Administrativos Ltda",
                },
                "warnings": ["cache local"],
            }
        )
        service = TotvsRmRealService(client)

        first = service.handle_request({
            "action": "buscar_coligada_por_codigo",
            "payload": {"coligada_codigo": "COL001"},
        })
        second = service.handle_request({
            "action": "buscar_coligada_por_codigo",
            "payload": {"coligada_codigo": "COL001"},
        })

        assert first == second
        assert client.calls == [
            ("buscar_coligada_por_codigo", {"codigo": "COL001"}),
            ("buscar_coligada_por_codigo", {"codigo": "COL001"}),
        ]
        assert first["ok"] is True
        assert first["action"] == "buscar_coligada_por_codigo"
        assert first["errors"] == []
        assert first["data"]["count"] == 1
        assert first["data"]["filters_applied"] == {"codigo": "COL001"}
        assert first["data"]["warnings"] == ["cache local"]
        assert first["data"]["item"]["codigo"] == "COL001"

        serialized = json.loads(serialize_response(first))
        assert serialized["ok"] is True
        assert serialized["source"] == "totvs_rm_real"
        assert serialized["action"] == "buscar_coligada_por_codigo"
        assert serialized["errors"] == []
        assert serialized["data"]["item"]["codigo"] == "COL001"

    def test_malformed_client_response_becomes_predictable_contract_error(self):
        service = TotvsRmRealService(
            FakeClient(response=["not", "a", "mapping"])
        )

        result = service.handle_request({
            "action": "buscar_filial_por_id",
            "payload": {"filial_id": "101"},
        })

        assert result == {
            "ok": False,
            "action": "buscar_filial_por_id",
            "data": None,
            "errors": ["Resposta invalida do RM"],
        }

    def test_transport_error_becomes_predictable_functional_error(self):
        service = TotvsRmRealService(
            FakeClient(exc=TotvsRmRealTransportError("socket closed"))
        )

        result = service.handle_request({
            "action": "buscar_movimento_por_id",
            "payload": {"movimento_id": "MOV-1002"},
        })

        assert result == {
            "ok": False,
            "action": "buscar_movimento_por_id",
            "data": None,
            "errors": ["Falha de transporte na integracao RM"],
        }

    def test_not_found_error_is_preserved_as_functional_error(self):
        service = TotvsRmRealService(
            FakeClient(exc=TotvsRmRealNotFoundError("Funcionario nao encontrado"))
        )

        result = service.handle_request({
            "action": "buscar_funcionario_por_chapa",
            "payload": {"chapa": "999999"},
        })

        assert result == {
            "ok": False,
            "action": "buscar_funcionario_por_chapa",
            "data": None,
            "errors": ["Funcionario nao encontrado"],
        }
