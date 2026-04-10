"""Client foundation for a future controlled TOTVS RM integration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import os
from typing import Any, Callable, Protocol
from urllib.parse import urljoin

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
    DEFAULT_TIMEOUT_SECONDS,
    REAL_ENV_PREFIX,
)


_DEFAULT_ACTION_ROUTES = {
    ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA: "/rh/funcionarios/busca",
    ACTION_BUSCAR_MOVIMENTO_POR_ID: "/rh/movimentos/busca",
    ACTION_BUSCAR_FILIAL_POR_ID: "/cadastros/filiais/busca",
    ACTION_BUSCAR_COLIGADA_POR_CODIGO: "/cadastros/coligadas/busca",
}

_DEFAULT_ACTION_METHODS = {
    ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA: "POST",
    ACTION_BUSCAR_MOVIMENTO_POR_ID: "POST",
    ACTION_BUSCAR_FILIAL_POR_ID: "GET",
    ACTION_BUSCAR_COLIGADA_POR_CODIGO: "GET",
}


@dataclass(frozen=True)
class TotvsRmRealTransportRequest:
    """Normalized request passed to the configured transport."""

    action: str
    method: str
    payload: dict[str, Any]
    url: str
    headers: dict[str, str]
    timeout_seconds: float
    username: str | None = None
    password: str | None = None
    token: str | None = None


class TotvsRmRealClientProtocol(Protocol):
    """Protocol used by the service so fake clients remain trivial."""

    def request(self, action: str, payload: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        """Perform a normalized RM request and return a mapping payload."""


RealTransport = Callable[[TotvsRmRealTransportRequest], Mapping[str, Any]]


def _clean_env_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _parse_timeout(value: str | None) -> float:
    if value is None or not value.strip():
        return DEFAULT_TIMEOUT_SECONDS
    try:
        timeout = float(value)
    except ValueError as exc:
        raise TotvsRmRealConfigurationError("TOTVS_RM_REAL_TIMEOUT_SECONDS invalido") from exc
    if timeout <= 0:
        raise TotvsRmRealConfigurationError("timeout_seconds deve ser maior que zero")
    return timeout


def _normalize_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if payload is None:
        return {}
    if not isinstance(payload, Mapping):
        raise TotvsRmRealValidationError("Payload deve ser um objeto JSON")
    return dict(payload)


@dataclass
class TotvsRmRealClient:
    """Encapsulate transport, configuration and low-level error mapping."""

    base_url: str | None = None
    username: str | None = None
    password: str | None = None
    token: str | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    action_routes: Mapping[str, str] = field(default_factory=dict)
    action_methods: Mapping[str, str] = field(default_factory=dict)
    action_headers: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    default_headers: Mapping[str, str] = field(default_factory=dict)
    transport: RealTransport | None = None

    def __post_init__(self) -> None:
        if self.transport is None and not _clean_env_value(self.base_url):
            raise TotvsRmRealConfigurationError(
                "base_url e obrigatorio quando transport nao e informado"
            )
        if self.timeout_seconds <= 0:
            raise TotvsRmRealConfigurationError("timeout_seconds deve ser maior que zero")

    @classmethod
    def from_env(
        cls,
        *,
        transport: RealTransport | None = None,
        action_routes: Mapping[str, str] | None = None,
        action_methods: Mapping[str, str] | None = None,
        action_headers: Mapping[str, Mapping[str, str]] | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> "TotvsRmRealClient":
        """Build a client from environment variables."""
        base_url = _clean_env_value(os.getenv(f"{REAL_ENV_PREFIX}BASE_URL"))
        username = _clean_env_value(os.getenv(f"{REAL_ENV_PREFIX}USERNAME"))
        password = _clean_env_value(os.getenv(f"{REAL_ENV_PREFIX}PASSWORD"))
        token = _clean_env_value(os.getenv(f"{REAL_ENV_PREFIX}TOKEN"))
        timeout_seconds = _parse_timeout(os.getenv(f"{REAL_ENV_PREFIX}TIMEOUT_SECONDS"))
        return cls(
            base_url=base_url,
            username=username,
            password=password,
            token=token,
            timeout_seconds=timeout_seconds,
            action_routes=dict(action_routes or {}),
            action_methods=dict(action_methods or {}),
            action_headers=dict(action_headers or {}),
            default_headers=dict(default_headers or {}),
            transport=transport,
        )

    def _build_url(self, action: str) -> str:
        route = _clean_env_value(self.action_routes.get(action))
        if not route:
            route = _DEFAULT_ACTION_ROUTES.get(action, f"/{action}")
        base_url = _clean_env_value(self.base_url)
        if not base_url:
            # Fallback tecnico para foundation/controlabilidade; nao representa endpoint real do RM.
            return f"mock://totvs-rm/{route.lstrip('/')}"
        return urljoin(f"{base_url.rstrip('/')}/", route.lstrip("/"))

    def _build_method(self, action: str) -> str:
        method = _clean_env_value(self.action_methods.get(action))
        if not method:
            method = _DEFAULT_ACTION_METHODS.get(action, "POST")
        return method.upper()

    def _build_headers(self, action: str) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        headers.update(dict(self.default_headers))
        headers.update(dict(self.action_headers.get(action, {})))
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _build_transport_request(self, action: str, payload: dict[str, Any]) -> TotvsRmRealTransportRequest:
        return TotvsRmRealTransportRequest(
            action=action,
            method=self._build_method(action),
            payload=payload,
            url=self._build_url(action),
            headers=self._build_headers(action),
            timeout_seconds=self.timeout_seconds,
            username=self.username,
            password=self.password,
            token=self.token,
        )

    def _default_http_transport(self, request: TotvsRmRealTransportRequest) -> Mapping[str, Any]:
        try:
            import httpx
        except Exception as exc:  # pragma: no cover - dependency failure is environmental
            raise TotvsRmRealConfigurationError(
                "httpx nao disponivel para o transporte HTTP padrao"
            ) from exc

        auth = None
        headers = dict(request.headers)
        if request.token:
            headers["Authorization"] = f"Bearer {request.token}"
        elif request.username or request.password:
            auth = httpx.BasicAuth(request.username or "", request.password or "")

        try:
            with httpx.Client(timeout=request.timeout_seconds, headers=headers, auth=auth) as client:
                method = request.method.upper()
                request_kwargs: dict[str, Any] = {}
                if method in {"GET", "HEAD"}:
                    request_kwargs["params"] = request.payload
                else:
                    request_kwargs["json"] = request.payload
                response = client.request(method, request.url, **request_kwargs)
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            raise TotvsRmRealTimeoutError("Timeout na integracao RM") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in (401, 403):
                raise TotvsRmRealAuthenticationError("Falha de autenticacao no RM") from exc
            if status == 404:
                raise TotvsRmRealNotFoundError("Registro nao encontrado no RM") from exc
            raise TotvsRmRealTransportError(f"Falha HTTP na integracao RM: {status}") from exc
        except httpx.RequestError as exc:
            raise TotvsRmRealTransportError("Falha de transporte na integracao RM") from exc
        except ValueError as exc:
            raise TotvsRmRealContractError("Resposta do RM precisa ser um objeto JSON") from exc

        if not isinstance(payload, Mapping):
            raise TotvsRmRealContractError("Resposta do RM precisa ser um objeto JSON")
        return dict(payload)

    def _invoke_transport(self, request: TotvsRmRealTransportRequest) -> Mapping[str, Any]:
        transport = self.transport or self._default_http_transport
        try:
            response = transport(request)
        except TotvsRmRealError:
            raise
        except TimeoutError as exc:
            raise TotvsRmRealTimeoutError("Timeout na integracao RM") from exc
        except ConnectionError as exc:
            raise TotvsRmRealTransportError("Falha de transporte na integracao RM") from exc
        except Exception as exc:
            raise TotvsRmRealTransportError("Falha de transporte na integracao RM") from exc

        if not isinstance(response, Mapping):
            raise TotvsRmRealContractError("Resposta do RM precisa ser um objeto JSON")
        return dict(response)

    def request(self, action: str, payload: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        """Execute a low-level request and return the raw mapping payload."""
        normalized_action = str(action or "").strip().lower()
        if not normalized_action:
            raise TotvsRmRealValidationError("Action e obrigatoria")

        normalized_payload = _normalize_payload(payload)
        request = self._build_transport_request(normalized_action, normalized_payload)
        return self._invoke_transport(request)

    def buscar_funcionario_por_chapa(self, chapa: str) -> Mapping[str, Any]:
        return self.request(ACTION_BUSCAR_FUNCIONARIO_POR_CHAPA, {"chapa": chapa})

    def buscar_movimento_por_id(self, movimento_id: str) -> Mapping[str, Any]:
        return self.request(ACTION_BUSCAR_MOVIMENTO_POR_ID, {"movimento_id": movimento_id})

    def buscar_filial_por_id(self, filial_id: str) -> Mapping[str, Any]:
        return self.request(ACTION_BUSCAR_FILIAL_POR_ID, {"filial_id": filial_id})

    def buscar_coligada_por_codigo(self, codigo: str) -> Mapping[str, Any]:
        return self.request(ACTION_BUSCAR_COLIGADA_POR_CODIGO, {"codigo": codigo})
