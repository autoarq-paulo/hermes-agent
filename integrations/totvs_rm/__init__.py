"""TOTVS RM mock integration package."""

from integrations.totvs_rm.mock_loader import (
    fixture_dir,
    has_required_fixtures,
    load_catalog,
    load_coligadas,
    load_filiais,
    load_funcionarios,
    load_movimentos,
)
from integrations.totvs_rm.mock_service import handle_action, handle_request

