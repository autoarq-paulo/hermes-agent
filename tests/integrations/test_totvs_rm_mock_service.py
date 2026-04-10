"""Tests for the local TOTVS RM mock service layer."""

from integrations.totvs_rm import mock_loader, mock_service


class TestMockLoader:
    def test_required_fixtures_exist(self):
        assert mock_loader.has_required_fixtures() is True


class TestHandleRequest:
    def test_listar_coligadas_returns_expected_rows(self):
        result = mock_service.handle_request({
            "action": "listar_coligadas",
            "payload": {},
        })
        assert result["ok"] is True
        assert result["action"] == "listar_coligadas"
        assert result["errors"] == []
        assert result["data"]["count"] == 2
        assert result["data"]["filters_applied"] == {}
        assert result["data"]["warnings"] == []
        codes = {item["codigo"] for item in result["data"]["items"]}
        assert codes == {"COL001", "COL002"}

    def test_listar_coligadas_filters_by_codigo(self):
        result = mock_service.handle_request({
            "action": "listar_coligadas",
            "payload": {"codigo": "col001"},
        })
        assert result["ok"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {"codigo": "COL001"}
        assert {item["codigo"] for item in result["data"]["items"]} == {"COL001"}

    def test_listar_filiais_filters_by_coligada_id(self):
        first = mock_service.handle_request({
            "action": "listar_filiais",
            "payload": {"coligada_id": 1},
        })
        second = mock_service.handle_request({
            "action": "listar_filiais",
            "payload": {"coligada_id": 1},
        })
        assert first == second
        assert first["ok"] is True
        assert first["data"]["count"] == 2
        assert first["data"]["filters_applied"] == {"coligada_id": "1"}
        assert {item["coligada_id"] for item in first["data"]["items"]} == {1}

    def test_listar_filiais_filters_by_filial_codigo(self):
        result = mock_service.handle_request({
            "action": "listar_filiais",
            "payload": {"filial_codigo": "rj01"},
        })
        assert result["ok"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {"filial_codigo": "RJ01"}
        assert result["data"]["items"][0]["codigo"] == "RJ01"

    def test_listar_funcionarios_filters_by_status_and_filial(self):
        result = mock_service.handle_request({
            "action": "listar_funcionarios",
            "payload": {"status": "ativo", "filial_id": 101},
        })
        assert result["ok"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {
            "filial_id": "101",
            "status": "ativo",
        }
        assert result["data"]["warnings"] == []
        assert result["data"]["items"][0]["nome"] == "Ana Souza"
        assert result["data"]["items"][0]["ativa"] is True

    def test_listar_movimentos_filters_by_tipo_and_filial(self):
        result = mock_service.handle_request({
            "action": "listar_movimentos",
            "payload": {"tipo": "ferias", "filial_id": 102},
        })
        assert result["ok"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {
            "filial_id": "102",
            "tipo": "ferias",
        }
        assert result["data"]["warnings"] == []
        assert result["data"]["items"][0]["id"] == "MOV-1002"
        assert result["data"]["items"][0]["status"] == "agendado"

    def test_listar_movimentos_filters_by_filial_codigo(self):
        result = mock_service.handle_request({
            "action": "listar_movimentos",
            "payload": {"filial_codigo": "rj01"},
        })
        assert result["ok"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {"filial_codigo": "RJ01"}
        assert result["data"]["items"][0]["id"] == "MOV-1002"

    def test_buscar_coligada_por_codigo_returns_record(self):
        result = mock_service.handle_request({
            "action": "buscar_coligada_por_codigo",
            "payload": {"codigo": "col001"},
        })
        assert result["ok"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {"codigo": "COL001"}
        assert result["data"]["warnings"] == []
        assert result["data"]["item"]["codigo"] == "COL001"
        assert result["data"]["item"]["nome_fantasia"] == "Hermes Servicos"

    def test_buscar_filial_por_id_returns_record(self):
        result = mock_service.handle_request({
            "action": "buscar_filial_por_id",
            "payload": {"id": 102},
        })
        assert result["ok"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {"filial_id": "102"}
        assert result["data"]["warnings"] == []
        assert result["data"]["item"]["codigo"] == "RJ01"
        assert result["data"]["item"]["coligada_id"] == 1

    def test_buscar_funcionario_por_chapa_returns_record(self):
        result = mock_service.handle_request({
            "action": "buscar_funcionario_por_chapa",
            "payload": {"chapa": "000123"},
        })
        assert result["ok"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {"chapa": "000123"}
        assert result["data"]["warnings"] == []
        assert result["data"]["item"]["nome"] == "Ana Souza"
        assert result["data"]["item"]["cargo"] == "Analista de RH"

    def test_buscar_movimento_por_id_returns_record(self):
        result = mock_service.handle_request({
            "action": "buscar_movimento_por_id",
            "payload": {"id": "MOV-1002"},
        })
        assert result["ok"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["filters_applied"] == {"movimento_id": "MOV-1002"}
        assert result["data"]["warnings"] == []
        assert result["data"]["item"]["chapa"] == "000456"
        assert result["data"]["item"]["tipo"] == "ferias"

    def test_missing_lookup_filter_returns_functional_error(self):
        result = mock_service.handle_request({
            "action": "buscar_filial_por_id",
            "payload": {},
        })
        assert result["ok"] is False
        assert result["data"] is None
        assert result["errors"] == ["filial_id e obrigatorio"]

    def test_unknown_action_returns_functional_error(self):
        result = mock_service.handle_request({
            "action": "acao_inexistente",
            "payload": {},
        })
        assert result["ok"] is False
        assert result["data"] is None
        assert result["errors"] == ["Acao nao suportada: acao_inexistente"]

    def test_missing_employee_returns_functional_error(self):
        result = mock_service.handle_request({
            "action": "buscar_funcionario_por_chapa",
            "payload": {"chapa": "999999"},
        })
        assert result["ok"] is False
        assert result["data"] is None
        assert result["errors"] == ["Funcionario nao encontrado"]

    def test_no_result_without_fail_on_empty_returns_warning(self):
        first = mock_service.handle_request({
            "action": "listar_movimentos",
            "payload": {"coligada_id": 1, "status": "confirmado"},
        })
        second = mock_service.handle_request({
            "action": "listar_movimentos",
            "payload": {"coligada_id": 1, "status": "confirmado"},
        })
        assert first == second
        assert first["ok"] is True
        assert first["data"]["count"] == 0
        assert first["data"]["items"] == []
        assert first["data"]["warnings"] == [
            "Nenhum registro encontrado para os filtros informados",
        ]

    def test_no_result_with_fail_on_empty_returns_functional_error(self):
        result = mock_service.handle_request({
            "action": "listar_funcionarios",
            "payload": {
                "coligada_id": 1,
                "status": "afastado",
                "fail_on_empty": True,
            },
        })
        assert result["ok"] is False
        assert result["data"] is None
        assert result["errors"] == [
            "Nenhum registro encontrado para os filtros informados",
        ]

    def test_simulated_data_unavailable_returns_functional_error(self):
        result = mock_service.handle_request({
            "action": "listar_funcionarios",
            "payload": {"simulate_error": "data_unavailable"},
        })
        assert result["ok"] is False
        assert result["data"] is None
        assert result["errors"] == ["Dados indisponiveis para a acao"]

    def test_simulated_inconsistent_record_returns_functional_error(self):
        result = mock_service.handle_request({
            "action": "buscar_movimento_por_id",
            "payload": {
                "id": "MOV-1001",
                "simulate_error": "inconsistent_record",
            },
        })
        assert result["ok"] is False
        assert result["data"] is None
        assert result["errors"] == ["Registro inconsistente simulado"]

    def test_invalid_request_shape_is_deterministic(self):
        first = mock_service.handle_request("not-a-dict")
        second = mock_service.handle_request("not-a-dict")
        assert first == second
        assert first["ok"] is False
        assert first["errors"] == ["Request deve ser um objeto JSON"]

    def test_invalid_payload_shape_returns_functional_error(self):
        result = mock_service.handle_request({
            "action": "listar_filiais",
            "payload": "not-an-object",
        })
        assert result["ok"] is False
        assert result["action"] == "listar_filiais"
        assert result["data"] is None
        assert result["errors"] == ["Payload deve ser um objeto JSON"]

    def test_invalid_boolean_filter_returns_validation_error(self):
        result = mock_service.handle_request({
            "action": "listar_coligadas",
            "payload": {"ativa": "maybe"},
        })
        assert result["ok"] is False
        assert result["data"] is None
        assert result["errors"] == ["Filtro ativa invalido"]
