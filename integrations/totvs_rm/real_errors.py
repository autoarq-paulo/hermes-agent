"""Error hierarchy for the real TOTVS RM integration foundation."""

from __future__ import annotations


class TotvsRmRealError(Exception):
    """Base error for the real integration."""


class TotvsRmRealConfigurationError(TotvsRmRealError):
    """Raised when connection or authentication configuration is invalid."""


class TotvsRmRealAuthenticationError(TotvsRmRealError):
    """Raised when RM rejects the configured credentials."""


class TotvsRmRealTransportError(TotvsRmRealError):
    """Raised when transport or connectivity fails."""


class TotvsRmRealTimeoutError(TotvsRmRealTransportError):
    """Raised when the transport times out."""


class TotvsRmRealContractError(TotvsRmRealError):
    """Raised when RM returns an invalid or unexpected payload."""


class TotvsRmRealNotFoundError(TotvsRmRealError):
    """Raised when the requested record is not found."""


class TotvsRmRealUnsupportedActionError(TotvsRmRealError):
    """Raised when the requested action is not supported yet."""


class TotvsRmRealValidationError(TotvsRmRealError):
    """Raised when the request payload is invalid."""
