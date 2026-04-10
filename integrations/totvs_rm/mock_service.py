"""Domain logic for the local TOTVS RM mock integration."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from integrations.totvs_rm.mock_loader import (
    has_required_fixtures,
    load_coligadas,
    load_filiais,
    load_funcionarios,
    load_movimentos,
)
from integrations.totvs_rm.schemas import (
    ACTION_BUSCAR_COLIGADA_POR_CODIGO,
    ACTION_BUSCAR_FILIAL_POR_ID,
    ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA,
    ACTION_BUSCAR_MOVIMENTO_POR_ID,
    ACTION_LISTAR_COLIGADAS,
    ACTION_LISTAR_FILIAIS,
    ACTION_LISTAR_FUNCIONARIOS,
    ACTION_LISTAR_MOVIMENTOS,
    MockServiceResult,
)

FilterSpec = Tuple[str, str, Tuple[str, ...], str]

_EMPTY_RESULT_WARNING = "Nenhum registro encontrado para os filtros informados"
_SIMULATED_ERROR_MESSAGES = {
    "data_unavailable": "Dados indisponiveis para a acao",
    "inconsistent_record": "Registro inconsistente simulado",
}


class TotvsRmMockError(Exception):
    """Base error for the mock service."""


class TotvsRmMockValidationError(TotvsRmMockError):
    """Raised when the request payload is invalid."""


class TotvsRmMockNotFoundError(TotvsRmMockError):
    """Raised when a requested record does not exist."""


class TotvsRmMockFunctionalError(TotvsRmMockError):
    """Raised for predictable functional failures."""


def _normalize_action(action: Any) -> str:
    return str(action or "").strip().lower()


def _normalize_payload(payload: Any) -> Dict[str, Any]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise TotvsRmMockValidationError("Payload deve ser um objeto JSON")
    return payload


def _bool_from_value(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "sim", "s"}:
            return True
        if normalized in {"false", "0", "no", "nao", "n"}:
            return False
    return None


def _payload_value(payload: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            value = payload.get(key)
            if value not in (None, ""):
                return value
    return None


def _normalize_identifier(value: Any) -> str:
    return str(value).strip()


def _normalize_code(value: Any) -> str:
    return str(value).strip().upper()


def _normalize_text(value: Any) -> str:
    return str(value).strip().lower()


def _normalize_filter_value(canonical: str, value: Any, kind: str) -> Any:
    if kind == "bool":
        normalized = _bool_from_value(value)
        if normalized is None:
            raise TotvsRmMockValidationError(f"Filtro {canonical} invalido")
        return normalized
    text = str(value).strip()
    if kind == "code":
        return text.upper()
    if kind == "text":
        return text.lower()
    return text


def _row_matches_filter(record_value: Any, expected: Any, kind: str) -> bool:
    if record_value is None:
        return False
    if kind == "bool":
        return bool(record_value) is expected
    if kind == "code":
        return _normalize_code(record_value) == expected
    if kind == "text":
        return _normalize_text(record_value) == expected
    return _normalize_identifier(record_value) == expected


def _apply_filters(rows: List[Dict[str, Any]], payload: Dict[str, Any], specs: List[FilterSpec]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    filters_applied: Dict[str, Any] = {}
    filtered_rows = rows

    for canonical, row_field, aliases, kind in specs:
        raw_value = _payload_value(payload, canonical, *aliases)
        if raw_value is None:
            continue

        normalized = _normalize_filter_value(canonical, raw_value, kind)
        filters_applied[canonical] = normalized
        filtered_rows = [
            row for row in filtered_rows
            if _row_matches_filter(row.get(row_field), normalized, kind)
        ]

    return filtered_rows, filters_applied


def _copy_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [dict(row) for row in rows]


def _collection_data(
    rows: List[Dict[str, Any]],
    filters_applied: Dict[str, Any],
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "items": _copy_rows(rows),
        "count": len(rows),
        "filters_applied": dict(filters_applied),
        "warnings": list(warnings or []),
    }


def _item_data(
    record: Dict[str, Any],
    filters_applied: Dict[str, Any],
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "item": dict(record),
        "count": 1,
        "filters_applied": dict(filters_applied),
        "warnings": list(warnings or []),
    }


def _read_fail_on_empty(payload: Dict[str, Any]) -> bool:
    if "fail_on_empty" not in payload:
        return False
    value = _bool_from_value(payload.get("fail_on_empty"))
    if value is None:
        raise TotvsRmMockValidationError("fail_on_empty invalido")
    return value


def _maybe_simulate_error(payload: Dict[str, Any]) -> None:
    raw_value = _payload_value(payload, "simulate_error")
    if raw_value is None:
        return
    normalized = _normalize_text(raw_value)
    message = _SIMULATED_ERROR_MESSAGES.get(normalized)
    if message is None:
        raise TotvsRmMockValidationError("simulate_error invalido")
    raise TotvsRmMockFunctionalError(message)


def _list_coligadas(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows = load_coligadas()
    rows, filters_applied = _apply_filters(
        rows,
        payload,
        [
            ("codigo", "codigo", (), "code"),
            ("ativa", "ativa", (), "bool"),
        ],
    )

    if not rows:
        if _read_fail_on_empty(payload):
            raise TotvsRmMockFunctionalError(_EMPTY_RESULT_WARNING)
        return _collection_data(rows, filters_applied, [_EMPTY_RESULT_WARNING])

    return _collection_data(rows, filters_applied)


def _list_filiais(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows = load_filiais()
    rows, filters_applied = _apply_filters(
        rows,
        payload,
        [
            ("coligada_id", "coligada_id", (), "identifier"),
            ("coligada_codigo", "coligada_codigo", (), "code"),
            ("filial_codigo", "codigo", (), "code"),
            ("ativa", "ativa", (), "bool"),
        ],
    )

    if not rows:
        if _read_fail_on_empty(payload):
            raise TotvsRmMockFunctionalError(_EMPTY_RESULT_WARNING)
        return _collection_data(rows, filters_applied, [_EMPTY_RESULT_WARNING])

    return _collection_data(rows, filters_applied)


def _list_funcionarios(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows = load_funcionarios()
    rows, filters_applied = _apply_filters(
        rows,
        payload,
        [
            ("coligada_id", "coligada_id", (), "identifier"),
            ("coligada_codigo", "coligada_codigo", (), "code"),
            ("filial_id", "filial_id", (), "identifier"),
            ("filial_codigo", "filial_codigo", (), "code"),
            ("status", "status", (), "text"),
            ("ativa", "ativa", (), "bool"),
        ],
    )

    if not rows:
        if _read_fail_on_empty(payload):
            raise TotvsRmMockFunctionalError(_EMPTY_RESULT_WARNING)
        return _collection_data(rows, filters_applied, [_EMPTY_RESULT_WARNING])

    return _collection_data(rows, filters_applied)


def _list_movimentos(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows = load_movimentos()
    rows, filters_applied = _apply_filters(
        rows,
        payload,
        [
            ("coligada_id", "coligada_id", (), "identifier"),
            ("coligada_codigo", "coligada_codigo", (), "code"),
            ("filial_id", "filial_id", (), "identifier"),
            ("filial_codigo", "filial_codigo", (), "code"),
            ("chapa", "chapa", (), "identifier"),
            ("status", "status", (), "text"),
            ("tipo", "tipo", (), "text"),
        ],
    )

    if not rows:
        if _read_fail_on_empty(payload):
            raise TotvsRmMockFunctionalError(_EMPTY_RESULT_WARNING)
        return _collection_data(rows, filters_applied, [_EMPTY_RESULT_WARNING])

    return _collection_data(rows, filters_applied)


def _find_coligada_por_codigo(payload: Dict[str, Any]) -> Dict[str, Any]:
    codigo = _payload_value(payload, "codigo", "coligada_codigo")
    if codigo is None:
        raise TotvsRmMockValidationError("codigo e obrigatorio")

    rows, filters_applied = _apply_filters(
        load_coligadas(),
        payload,
        [
            ("codigo", "codigo", ("coligada_codigo",), "code"),
            ("ativa", "ativa", (), "bool"),
        ],
    )

    if len(rows) == 0:
        raise TotvsRmMockNotFoundError("Coligada nao encontrada")
    if len(rows) > 1:
        raise TotvsRmMockFunctionalError("Consulta retornou mais de um registro")

    return _item_data(rows[0], filters_applied)


def _find_filial_por_id(payload: Dict[str, Any]) -> Dict[str, Any]:
    filial_id = _payload_value(payload, "filial_id", "id")
    if filial_id is None:
        raise TotvsRmMockValidationError("filial_id e obrigatorio")

    rows, filters_applied = _apply_filters(
        load_filiais(),
        payload,
        [
            ("filial_id", "id", ("id",), "identifier"),
            ("coligada_id", "coligada_id", (), "identifier"),
            ("coligada_codigo", "coligada_codigo", (), "code"),
            ("ativa", "ativa", (), "bool"),
        ],
    )

    if len(rows) == 0:
        raise TotvsRmMockNotFoundError("Filial nao encontrada")
    if len(rows) > 1:
        raise TotvsRmMockFunctionalError("Consulta retornou mais de um registro")

    return _item_data(rows[0], filters_applied)


def _find_funcionario_por_chapa(payload: Dict[str, Any]) -> Dict[str, Any]:
    chapa = _payload_value(payload, "chapa")
    if chapa is None:
        raise TotvsRmMockValidationError("Chapa e obrigatoria")

    rows, filters_applied = _apply_filters(
        load_funcionarios(),
        payload,
        [
            ("chapa", "chapa", (), "identifier"),
            ("coligada_id", "coligada_id", (), "identifier"),
            ("coligada_codigo", "coligada_codigo", (), "code"),
            ("filial_id", "filial_id", (), "identifier"),
            ("filial_codigo", "filial_codigo", (), "code"),
            ("status", "status", (), "text"),
            ("ativa", "ativa", (), "bool"),
        ],
    )

    if len(rows) == 0:
        raise TotvsRmMockNotFoundError("Funcionario nao encontrado")
    if len(rows) > 1:
        raise TotvsRmMockFunctionalError("Consulta retornou mais de um registro")

    return _item_data(rows[0], filters_applied)


def _find_movimento_por_id(payload: Dict[str, Any]) -> Dict[str, Any]:
    movimento_id = _payload_value(payload, "movimento_id", "id")
    if movimento_id is None:
        raise TotvsRmMockValidationError("movimento_id e obrigatorio")

    rows, filters_applied = _apply_filters(
        load_movimentos(),
        payload,
        [
            ("movimento_id", "id", ("id",), "identifier"),
            ("coligada_id", "coligada_id", (), "identifier"),
            ("coligada_codigo", "coligada_codigo", (), "code"),
            ("filial_id", "filial_id", (), "identifier"),
            ("chapa", "chapa", (), "identifier"),
            ("status", "status", (), "text"),
            ("tipo", "tipo", (), "text"),
        ],
    )

    if len(rows) == 0:
        raise TotvsRmMockNotFoundError("Movimento nao encontrado")
    if len(rows) > 1:
        raise TotvsRmMockFunctionalError("Consulta retornou mais de um registro")

    return _item_data(rows[0], filters_applied)


_ACTION_HANDLERS = {
    ACTION_LISTAR_COLIGADAS: _list_coligadas,
    ACTION_LISTAR_FILIAIS: _list_filiais,
    ACTION_LISTAR_FUNCIONARIOS: _list_funcionarios,
    ACTION_LISTAR_MOVIMENTOS: _list_movimentos,
    ACTION_BUSCAR_COLIGADA_POR_CODIGO: _find_coligada_por_codigo,
    ACTION_BUSCAR_FILIAL_POR_ID: _find_filial_por_id,
    ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA: _find_funcionario_por_chapa,
    ACTION_BUSCAR_MOVIMENTO_POR_ID: _find_movimento_por_id,
}


def _success(action: str, data: Any) -> MockServiceResult:
    return {"ok": True, "action": action, "data": data, "errors": []}


def _error(action: str, message: str) -> MockServiceResult:
    return {"ok": False, "action": action, "data": None, "errors": [str(message)]}


def handle_action(action: Any, payload: Any = None) -> MockServiceResult:
    """Execute a single mock action and return the raw service result."""
    normalized_action = _normalize_action(action)
    if not normalized_action:
        return _error("", "Action e obrigatoria")

    handler = _ACTION_HANDLERS.get(normalized_action)
    if handler is None:
        return _error(normalized_action, f"Acao nao suportada: {normalized_action}")

    try:
        normalized_payload = _normalize_payload(payload)
    except TotvsRmMockValidationError as exc:
        return _error(normalized_action, str(exc))

    if not has_required_fixtures():
        return _error(normalized_action, "Fixtures TOTVS RM nao disponiveis")

    try:
        _maybe_simulate_error(normalized_payload)
        data = handler(normalized_payload)
        return _success(normalized_action, data)
    except TotvsRmMockError as exc:
        return _error(normalized_action, str(exc))
    except Exception:
        return _error(normalized_action, "Erro inesperado na integracao mock TOTVS RM")


def handle_request(request: Any) -> MockServiceResult:
    """Validate a request envelope and dispatch the requested action."""
    if not isinstance(request, dict):
        return _error("", "Request deve ser um objeto JSON")

    return handle_action(request.get("action"), request.get("payload"))
