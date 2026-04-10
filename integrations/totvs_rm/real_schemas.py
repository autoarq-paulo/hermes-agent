"""Shared schemas for the real TOTVS RM integration foundation."""

from __future__ import annotations

from typing import Any, Dict, List, TypedDict

SOURCE_NAME = "totvs_rm_real"
REAL_ENV_PREFIX = "TOTVS_RM_REAL_"
DEFAULT_TIMEOUT_SECONDS = 15.0

ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA = "buscar_funcionario_por_chapa"
ACTION_BUSCAR_MOVIMENTO_POR_ID = "buscar_movimento_por_id"
ACTION_BUSCAR_FILIAL_POR_ID = "buscar_filial_por_id"
ACTION_BUSCAR_COLIGADA_POR_CODIGO = "buscar_coligada_por_codigo"

SUPPORTED_ACTIONS = (
    ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA,
    ACTION_BUSCAR_MOVIMENTO_POR_ID,
    ACTION_BUSCAR_FILIAL_POR_ID,
    ACTION_BUSCAR_COLIGADA_POR_CODIGO,
)


class RealRequest(TypedDict, total=False):
    action: str
    payload: Dict[str, Any]


class RealResultData(TypedDict, total=False):
    items: List[Dict[str, Any]]
    item: Dict[str, Any]
    count: int
    filters_applied: Dict[str, Any]
    warnings: List[str]


class RealServiceResult(TypedDict):
    ok: bool
    action: str
    data: RealResultData | None
    errors: List[str]


class RealToolResponse(RealServiceResult):
    source: str


TOOL_SCHEMA = {
    "name": SOURCE_NAME,
    "description": (
        "Consultar dados reais controlados de TOTVS RM. "
        "Use apenas quando a integracao real for intencional; nao e o mock "
        "e nao faz fallback para ele. Sempre retorna o envelope JSON "
        "padronizado com ok, source, action, data e errors."
    ),
    "parameters": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {
                "type": "string",
                "enum": list(SUPPORTED_ACTIONS),
                "description": "Acao real controlada a executar.",
            },
            "payload": {
                "type": "object",
                "description": (
                    "Parametros da acao. Ex.: {\"chapa\": \"000123\"}, "
                    "{\"codigo\": \"COL001\"} ou {\"filial_id\": 101}."
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
                    "movimento_id": {
                        "type": "string",
                        "description": "Identificador do movimento.",
                    },
                    "id": {
                        "type": ["integer", "string"],
                        "description": (
                            "Alias opcional para filial ou movimento, "
                            "conforme a action."
                        ),
                    },
                    "coligada_codigo": {
                        "type": "string",
                        "description": "Alias opcional para o codigo da coligada.",
                    },
                },
                "additionalProperties": True,
            },
        },
        "required": ["action"],
    },
}
