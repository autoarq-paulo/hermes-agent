"""Domain logic for the controlled real TOTVS RM integration foundation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List

from integrations.totvs_rm.real_client import (
    TotvsRmRealClient,
    TotvsRmRealClientProtocol,
)
from integrations.totvs_rm.real_errors import (
    TotvsRmRealAuthenticationError,
    TotvsRmRealConfigurationError,
    TotvsRmRealContractError,
    TotvsRmRealError,
    TotvsRmRealNotFoundError,
    TotvsRmRealTimeoutError,
    TotvsRmRealTransportError,
    TotvsRmRealValidationError,
)
from integrations.totvs_rm.real_schemas import (
    ACTION_BUSCAR_COLIGADA_POR_CODIGO,
    ACTION_BUSCAR_FILIAL_POR_ID,
    ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA,
    ACTION_BUSCAR_MOVIMENTO_POR_ID,
    RealServiceResult,
    SUPPORTED_ACTIONS,
)

_ACTION_SET = set(SUPPORTED_ACTIONS)


def _normalize_action(action: Any) -> str:
    return str(action or "").strip().lower()


def _normalize_payload(payload: Any) -> Dict[str, Any]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise TotvsRmRealValidationError("Payload deve ser um objeto JSON")
    return payload


def _payload_value(payload: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        if key in payload:
            value = payload.get(key)
            if value not in (None, ""):
                return str(value).strip()
    return ""


def _dedupe_strings(values: List[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _extract_warnings(source: Mapping[str, Any] | None) -> List[str]:
    if not source:
        return []
    warnings = source.get("warnings")
    if not isinstance(warnings, list):
        return []
    return [str(item) for item in warnings if str(item).strip()]


def _unwrap_record_payload(response: Any, expected_field: str) -> tuple[Dict[str, Any], List[str]]:
    if not isinstance(response, Mapping):
        raise TotvsRmRealContractError("Resposta do RM precisa ser um objeto JSON")

    warnings: List[str] = []
    warnings.extend(_extract_warnings(response))

    candidate: Any = response
    data = response.get("data")
    if isinstance(data, Mapping):
        warnings.extend(_extract_warnings(data))
        candidate = data

    if isinstance(candidate, Mapping) and isinstance(candidate.get("item"), Mapping):
        warnings.extend(_extract_warnings(candidate.get("item")))
        candidate = candidate["item"]

    if not isinstance(candidate, Mapping):
        raise TotvsRmRealContractError("Resposta invalida do RM")

    item = dict(candidate)
    if expected_field not in item or str(item.get(expected_field)).strip() == "":
        raise TotvsRmRealContractError(
            f"Resposta do RM precisa conter o campo {expected_field}"
        )

    return item, _dedupe_strings(warnings)


def _item_result(
    item: Dict[str, Any],
    filters_applied: Dict[str, Any],
    warnings: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "item": dict(item),
        "count": 1,
        "filters_applied": dict(filters_applied),
        "warnings": _dedupe_strings(list(warnings or [])),
    }


def _lookup_single_record(
    client: TotvsRmRealClientProtocol,
    action: str,
    payload: Dict[str, Any],
    *,
    payload_keys: tuple[str, ...],
    request_key: str,
    expected_field: str,
    validation_message: str,
) -> Dict[str, Any]:
    value = _payload_value(payload, *payload_keys)
    if not value:
        raise TotvsRmRealValidationError(validation_message)

    response = client.request(action, {request_key: value})
    item, warnings = _unwrap_record_payload(response, expected_field)
    return _item_result(item, {request_key: value}, warnings)


def _success(action: str, data: Any) -> RealServiceResult:
    return {"ok": True, "action": action, "data": data, "errors": []}


def _error(action: str, message: str) -> RealServiceResult:
    return {"ok": False, "action": action, "data": None, "errors": [str(message)]}


def _handle_client_error(action: str, exc: Exception) -> RealServiceResult:
    if isinstance(exc, TotvsRmRealConfigurationError):
        return _error(action, str(exc))
    if isinstance(exc, TotvsRmRealValidationError):
        return _error(action, str(exc))
    if isinstance(exc, TotvsRmRealNotFoundError):
        return _error(action, str(exc))
    if isinstance(exc, TotvsRmRealAuthenticationError):
        return _error(action, "Falha de autenticacao no RM")
    if isinstance(exc, TotvsRmRealTimeoutError):
        return _error(action, "Timeout na integracao RM")
    if isinstance(exc, TotvsRmRealTransportError):
        return _error(action, "Falha de transporte na integracao RM")
    if isinstance(exc, TotvsRmRealContractError):
        return _error(action, "Resposta invalida do RM")
    if isinstance(exc, TotvsRmRealError):
        return _error(action, str(exc))
    return _error(action, "Erro inesperado na integracao real TOTVS RM")


class TotvsRmRealService:
    """Normalize RM client results into the fork contract."""

    def __init__(self, client: TotvsRmRealClientProtocol):
        self.client = client

    def handle_request(self, request: Any) -> RealServiceResult:
        if not isinstance(request, dict):
            return _error("", "Request deve ser um objeto JSON")
        return self.handle_action(request.get("action"), request.get("payload"))

    def handle_action(self, action: Any, payload: Any = None) -> RealServiceResult:
        normalized_action = _normalize_action(action)
        if not normalized_action:
            return _error("", "Action e obrigatoria")
        if normalized_action not in _ACTION_SET:
            return _error(normalized_action, f"Acao nao suportada: {normalized_action}")

        try:
            normalized_payload = _normalize_payload(payload)
            if normalized_action == ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA:
                return _success(normalized_action, self._buscar_funcionario_por_chapa(normalized_payload))
            if normalized_action == ACTION_BUSCAR_MOVIMENTO_POR_ID:
                return _success(normalized_action, self._buscar_movimento_por_id(normalized_payload))
            if normalized_action == ACTION_BUSCAR_FILIAL_POR_ID:
                return _success(normalized_action, self._buscar_filial_por_id(normalized_payload))
            if normalized_action == ACTION_BUSCAR_COLIGADA_POR_CODIGO:
                return _success(normalized_action, self._buscar_coligada_por_codigo(normalized_payload))
            return _error(normalized_action, f"Acao nao suportada: {normalized_action}")
        except Exception as exc:
            return _handle_client_error(normalized_action, exc)

    def _buscar_funcionario_por_chapa(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return _lookup_single_record(
            self.client,
            ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA,
            payload,
            payload_keys=("chapa",),
            request_key="chapa",
            expected_field="chapa",
            validation_message="Chapa e obrigatoria",
        )

    def _buscar_movimento_por_id(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return _lookup_single_record(
            self.client,
            ACTION_BUSCAR_MOVIMENTO_POR_ID,
            payload,
            payload_keys=("movimento_id", "id"),
            request_key="movimento_id",
            expected_field="id",
            validation_message="movimento_id e obrigatorio",
        )

    def _buscar_filial_por_id(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return _lookup_single_record(
            self.client,
            ACTION_BUSCAR_FILIAL_POR_ID,
            payload,
            payload_keys=("filial_id", "id"),
            request_key="filial_id",
            expected_field="id",
            validation_message="filial_id e obrigatorio",
        )

    def _buscar_coligada_por_codigo(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return _lookup_single_record(
            self.client,
            ACTION_BUSCAR_COLIGADA_POR_CODIGO,
            payload,
            payload_keys=("codigo", "coligada_codigo"),
            request_key="codigo",
            expected_field="codigo",
            validation_message="codigo e obrigatorio",
        )


def _resolve_client(client: TotvsRmRealClientProtocol | None) -> TotvsRmRealClientProtocol:
    if client is not None:
        return client
    return TotvsRmRealClient.from_env()


def handle_action(
    action: Any,
    payload: Any = None,
    client: TotvsRmRealClientProtocol | None = None,
) -> RealServiceResult:
    normalized_action = _normalize_action(action)
    if not normalized_action:
        return _error("", "Action e obrigatoria")
    if normalized_action not in _ACTION_SET:
        return _error(normalized_action, f"Acao nao suportada: {normalized_action}")
    try:
        normalized_payload = _normalize_payload(payload)
    except TotvsRmRealValidationError as exc:
        return _error(normalized_action, str(exc))

    service = TotvsRmRealService(_resolve_client(client))
    return service.handle_action(normalized_action, normalized_payload)


def handle_request(
    request: Any,
    client: TotvsRmRealClientProtocol | None = None,
) -> RealServiceResult:
    if not isinstance(request, dict):
        return _error("", "Request deve ser um objeto JSON")

    normalized_action = _normalize_action(request.get("action"))
    if not normalized_action:
        return _error("", "Action e obrigatoria")
    if normalized_action not in _ACTION_SET:
        return _error(normalized_action, f"Acao nao suportada: {normalized_action}")

    return handle_action(
        normalized_action,
        request.get("payload"),
        client=client,
    )
