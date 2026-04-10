"""Shared schemas for the local TOTVS RM mock integration."""

from __future__ import annotations

from typing import Any, Dict, List, TypedDict

SOURCE_NAME = "totvs_rm_mock"

ACTION_LISTAR_COLIGADAS = "listar_coligadas"
ACTION_LISTAR_FILIAIS = "listar_filiais"
ACTION_LISTAR_FUNCIONARIOS = "listar_funcionarios"
ACTION_LISTAR_MOVIMENTOS = "listar_movimentos"
ACTION_BUSCAR_COLIGADA_POR_CODIGO = "buscar_coligada_por_codigo"
ACTION_BUSCAR_FILIAL_POR_ID = "buscar_filial_por_id"
ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA = "buscar_funcionario_por_chapa"
ACTION_BUSCAR_MOVIMENTO_POR_ID = "buscar_movimento_por_id"

SUPPORTED_ACTIONS = (
    ACTION_LISTAR_COLIGADAS,
    ACTION_LISTAR_FILIAIS,
    ACTION_LISTAR_FUNCIONARIOS,
    ACTION_LISTAR_MOVIMENTOS,
    ACTION_BUSCAR_COLIGADA_POR_CODIGO,
    ACTION_BUSCAR_FILIAL_POR_ID,
    ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA,
    ACTION_BUSCAR_MOVIMENTO_POR_ID,
)


class MockRequest(TypedDict, total=False):
    action: str
    payload: Dict[str, Any]


class MockResultData(TypedDict, total=False):
    items: List[Dict[str, Any]]
    item: Dict[str, Any]
    count: int
    filters_applied: Dict[str, Any]
    warnings: List[str]


class MockServiceResult(TypedDict):
    ok: bool
    action: str
    data: MockResultData | None
    errors: List[str]


class MockToolResponse(MockServiceResult):
    source: str


TOOL_SCHEMA = {
    "name": SOURCE_NAME,
    "description": (
        "Consultar dados mockados de TOTVS RM em arquivos JSON locais. "
        "Use action para escolher a consulta: listar_coligadas, "
        "listar_filiais, listar_funcionarios, listar_movimentos, "
        "buscar_coligada_por_codigo, buscar_filial_por_id, "
        "buscar_funcionario_por_chapa ou buscar_movimento_por_id. "
        "Sempre retorna um envelope JSON padronizado com ok, source, "
        "action, data e errors."
    ),
    "parameters": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {
                "type": "string",
                "enum": list(SUPPORTED_ACTIONS),
                "description": "Acao mockada a executar.",
            },
            "payload": {
                "type": "object",
                "description": (
                    "Parametros da acao. Ex.: {\"chapa\": \"000123\"} "
                    "ou {\"coligada_id\": 1}. O retorno bem-sucedido pode "
                    "incluir items, item, count, filters_applied e warnings."
                ),
                "properties": {
                    "chapa": {
                        "type": "string",
                        "description": "Chapa do funcionario.",
                    },
                    "codigo": {
                        "type": "string",
                        "description": "Codigo da coligada.",
                    },
                    "filial_id": {
                        "type": ["integer", "string"],
                        "description": "Identificador da filial.",
                    },
                    "filial_codigo": {
                        "type": "string",
                        "description": "Codigo da filial.",
                    },
                    "movimento_id": {
                        "type": "string",
                        "description": "Identificador do movimento.",
                    },
                    "id": {
                        "type": ["integer", "string"],
                        "description": (
                            "Alias opcional para o id da filial ou do "
                            "movimento, conforme a action."
                        ),
                    },
                    "coligada_id": {
                        "type": ["integer", "string"],
                        "description": "Filtra por coligada.",
                    },
                    "coligada_codigo": {
                        "type": "string",
                        "description": "Filtra por codigo da coligada.",
                    },
                    "ativa": {
                        "type": "boolean",
                        "description": "Filtra por status ativo/inativo.",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filtra por status do registro.",
                    },
                    "tipo": {
                        "type": "string",
                        "description": "Filtra por tipo de movimento.",
                    },
                    "fail_on_empty": {
                        "type": "boolean",
                        "description": (
                            "Quando true, combinações sem resultado viram "
                            "erro funcional."
                        ),
                    },
                    "simulate_error": {
                        "type": "string",
                        "enum": ["data_unavailable", "inconsistent_record"],
                        "description": (
                            "Simula um erro funcional previsivel para testes."
                        ),
                    },
                },
                "additionalProperties": True,
            },
        },
        "required": ["action"],
    },
}
