"""Tests for the controlled real TOTVS RM client foundation."""

import pytest

from integrations.totvs_rm.real_client import TotvsRmRealClient
from integrations.totvs_rm.real_errors import (
    TotvsRmRealConfigurationError,
    TotvsRmRealContractError,
    TotvsRmRealTimeoutError,
    TotvsRmRealTransportError,
)


class TestTotvsRmRealClient:
    def test_client_requires_transport_or_base_url(self):
        with pytest.raises(TotvsRmRealConfigurationError, match="base_url"):
            TotvsRmRealClient()

    def test_from_env_builds_request_context_and_uses_auth(self, monkeypatch):
        monkeypatch.setenv("TOTVS_RM_REAL_BASE_URL", "https://rm.example/api")
        monkeypatch.setenv("TOTVS_RM_REAL_TOKEN", "token-123")
        monkeypatch.setenv("TOTVS_RM_REAL_TIMEOUT_SECONDS", "9.5")

        seen: dict[str, object] = {}

        def transport(request):
            seen["request"] = request
            return {"item": {"chapa": "000123", "nome": "Ana Souza"}}

        client = TotvsRmRealClient.from_env(
            transport=transport,
            action_routes={"buscar_funcionario_por_chapa": "/rh/funcionarios/busca"},
        )

        response = client.request("buscar_funcionario_por_chapa", {"chapa": "000123"})
        request = seen["request"]

        assert request.url == "https://rm.example/api/rh/funcionarios/busca"
        assert request.headers["Authorization"] == "Bearer token-123"
        assert request.method == "POST"
        assert request.timeout_seconds == 9.5
        assert request.payload == {"chapa": "000123"}
        assert response["item"]["nome"] == "Ana Souza"

    def test_client_supports_transport_only_stub(self):
        seen: dict[str, object] = {}

        def transport(request):
            seen["url"] = request.url
            seen["method"] = request.method
            seen["payload"] = request.payload
            return {"item": {"id": 101, "nome": "Matriz Sao Paulo"}}

        client = TotvsRmRealClient(transport=transport)
        response = client.buscar_filial_por_id("101")

        assert seen["url"] == "mock://totvs-rm/cadastros/filiais/busca"
        assert seen["method"] == "GET"
        assert seen["payload"] == {"filial_id": "101"}
        assert response["item"]["id"] == 101

    def test_client_uses_action_specific_headers_for_custom_overrides(self):
        seen: dict[str, object] = {}

        def transport(request):
            seen["request"] = request
            return {"item": {"codigo": "COL001", "nome": "Hermes Servicos"}}

        client = TotvsRmRealClient(
            base_url="https://rm.example/api",
            transport=transport,
            action_headers={
                "buscar_coligada_por_codigo": {
                    "X-RM-Query-Semantics": "codigo",
                }
            },
        )

        response = client.buscar_coligada_por_codigo("COL001")
        request = seen["request"]

        assert request.url == "https://rm.example/api/cadastros/coligadas/busca"
        assert request.method == "GET"
        assert request.headers["X-RM-Query-Semantics"] == "codigo"
        assert request.payload == {"codigo": "COL001"}
        assert response["item"]["codigo"] == "COL001"

    def test_client_converts_transport_failure_to_transport_error(self):
        def transport(_request):
            raise ConnectionError("down")

        client = TotvsRmRealClient(base_url="https://rm.example/api", transport=transport)

        with pytest.raises(TotvsRmRealTransportError, match="Falha de transporte"):
            client.request("buscar_movimento_por_id", {"movimento_id": "MOV-1002"})

    def test_client_converts_timeout_to_timeout_error(self):
        def transport(_request):
            raise TimeoutError("slow")

        client = TotvsRmRealClient(base_url="https://rm.example/api", transport=transport)

        with pytest.raises(TotvsRmRealTimeoutError, match="Timeout na integracao RM"):
            client.request("buscar_funcionario_por_chapa", {"chapa": "000123"})

    def test_client_rejects_non_mapping_response(self):
        def transport(_request):
            return ["not", "a", "mapping"]

        client = TotvsRmRealClient(base_url="https://rm.example/api", transport=transport)

        with pytest.raises(TotvsRmRealContractError, match="objeto JSON"):
            client.request("buscar_funcionario_por_chapa", {"chapa": "000123"})
