"""Tests for hermes_constants module."""

import importlib
import os
from pathlib import Path
from unittest.mock import patch

import pytest

import hermes_constants
from hermes_constants import get_default_hermes_root, is_container


class TestTerminalRuntimeImage:
    """Tests for terminal runtime image resolution."""

    def _reload_constants(self, monkeypatch, **env):
        for key in (
            "HERMES_TERMINAL_RUNTIME_REPOSITORY",
            "HERMES_TERMINAL_RUNTIME_TAG",
            "HERMES_TERMINAL_RUNTIME_DIGEST",
            "HERMES_TERMINAL_RUNTIME_IMAGE",
            "HERMES_LOCAL_DOCKER_IMAGE",
            "HERMES_LOCAL_SINGULARITY_IMAGE",
            "HERMES_REMOTE_TERMINAL_IMAGE",
        ):
            monkeypatch.delenv(key, raising=False)
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        return importlib.reload(hermes_constants)

    def test_default_runtime_image_is_local_until_registry_opt_in(self, monkeypatch):
        module = self._reload_constants(monkeypatch)
        assert module.get_default_terminal_docker_image() == (
            "hermes-agent-local:runtime-python3.11-node20"
        )
        assert module.get_default_terminal_singularity_image() == (
            "docker://hermes-agent-local:runtime-python3.11-node20"
        )

    def test_repository_and_tag_select_published_runtime_image(self, monkeypatch):
        module = self._reload_constants(
            monkeypatch,
            HERMES_TERMINAL_RUNTIME_REPOSITORY="ghcr.io/example/hermes-runtime",
            HERMES_TERMINAL_RUNTIME_TAG="python3.11-node20-test",
        )
        assert module.get_default_terminal_docker_image() == (
            "ghcr.io/example/hermes-runtime:python3.11-node20-test"
        )

    def test_digest_pins_published_runtime_image(self, monkeypatch):
        digest = "sha256:" + ("a" * 64)
        module = self._reload_constants(
            monkeypatch,
            HERMES_TERMINAL_RUNTIME_REPOSITORY="ghcr.io/example/hermes-runtime",
            HERMES_TERMINAL_RUNTIME_DIGEST=digest,
        )
        assert module.get_default_terminal_docker_image().endswith(f"@{digest}")

    def test_full_runtime_image_override_keeps_local_dev_path(self, monkeypatch):
        module = self._reload_constants(
            monkeypatch,
            HERMES_TERMINAL_RUNTIME_IMAGE="hermes-agent-local:runtime-python3.11-node20",
        )
        assert module.get_default_terminal_docker_image() == (
            "hermes-agent-local:runtime-python3.11-node20"
        )

    def test_runtime_image_from_dotenv_loaded_after_import_is_respected(self, tmp_path, monkeypatch):
        module = self._reload_constants(monkeypatch)
        assert module.DEFAULT_TERMINAL_DOCKER_IMAGE == (
            "hermes-agent-local:runtime-python3.11-node20"
        )

        hermes_home = tmp_path / ".hermes"
        hermes_home.mkdir()
        (hermes_home / ".env").write_text(
            "HERMES_TERMINAL_RUNTIME_REPOSITORY=ghcr.io/example/from-dotenv\n"
            "HERMES_TERMINAL_RUNTIME_TAG=python3.11-node20-dotenv\n"
            "HERMES_TERMINAL_RUNTIME_DIGEST=sha256:" + ("b" * 64) + "\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        from hermes_cli.env_loader import load_hermes_dotenv

        load_hermes_dotenv(hermes_home=hermes_home)
        assert module.get_default_terminal_docker_image() == (
            "ghcr.io/example/from-dotenv:python3.11-node20-dotenv@sha256:" + ("b" * 64)
        )

    def test_persisted_terminal_image_config_still_wins_over_defaults(self, tmp_path, monkeypatch):
        hermes_home = tmp_path / ".hermes"
        hermes_home.mkdir()
        (hermes_home / "config.yaml").write_text(
            "terminal:\n"
            "  docker_image: legacy/runtime:kept\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))
        monkeypatch.setenv("HERMES_TERMINAL_RUNTIME_IMAGE", "hermes-agent-local:runtime-python3.11-node20")

        from hermes_cli.config import load_config

        assert load_config()["terminal"]["docker_image"] == "legacy/runtime:kept"


class TestGetDefaultHermesRoot:
    """Tests for get_default_hermes_root() — Docker/custom deployment awareness."""

    def test_no_hermes_home_returns_native(self, tmp_path, monkeypatch):
        """When HERMES_HOME is not set, returns ~/.hermes."""
        monkeypatch.delenv("HERMES_HOME", raising=False)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert get_default_hermes_root() == tmp_path / ".hermes"

    def test_hermes_home_is_native(self, tmp_path, monkeypatch):
        """When HERMES_HOME = ~/.hermes, returns ~/.hermes."""
        native = tmp_path / ".hermes"
        native.mkdir()
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(native))
        assert get_default_hermes_root() == native

    def test_hermes_home_is_profile(self, tmp_path, monkeypatch):
        """When HERMES_HOME is a profile under ~/.hermes, returns ~/.hermes."""
        native = tmp_path / ".hermes"
        profile = native / "profiles" / "coder"
        profile.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(profile))
        assert get_default_hermes_root() == native

    def test_hermes_home_is_docker(self, tmp_path, monkeypatch):
        """When HERMES_HOME points outside ~/.hermes (Docker), returns HERMES_HOME."""
        docker_home = tmp_path / "opt" / "data"
        docker_home.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(docker_home))
        assert get_default_hermes_root() == docker_home

    def test_hermes_home_is_custom_path(self, tmp_path, monkeypatch):
        """Any HERMES_HOME outside ~/.hermes is treated as the root."""
        custom = tmp_path / "my-hermes-data"
        custom.mkdir()
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(custom))
        assert get_default_hermes_root() == custom

    def test_docker_profile_active(self, tmp_path, monkeypatch):
        """When a Docker profile is active (HERMES_HOME=<root>/profiles/<name>),
        returns the Docker root, not the profile dir."""
        docker_root = tmp_path / "opt" / "data"
        profile = docker_root / "profiles" / "coder"
        profile.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(profile))
        assert get_default_hermes_root() == docker_root


class TestIsContainer:
    """Tests for is_container() — Docker/Podman detection."""

    def _reset_cache(self, monkeypatch):
        """Reset the cached detection result before each test."""
        monkeypatch.setattr(hermes_constants, "_container_detected", None)

    def test_detects_dockerenv(self, monkeypatch, tmp_path):
        """/.dockerenv triggers container detection."""
        self._reset_cache(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda p: p == "/.dockerenv")
        assert is_container() is True

    def test_detects_containerenv(self, monkeypatch, tmp_path):
        """/run/.containerenv triggers container detection (Podman)."""
        self._reset_cache(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda p: p == "/run/.containerenv")
        assert is_container() is True

    def test_detects_cgroup_docker(self, monkeypatch, tmp_path):
        """/proc/1/cgroup containing 'docker' triggers detection."""
        import builtins
        self._reset_cache(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda p: False)
        cgroup_file = tmp_path / "cgroup"
        cgroup_file.write_text("12:memory:/docker/abc123\n")
        _real_open = builtins.open
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(str(cgroup_file), *a, **kw) if p == "/proc/1/cgroup" else _real_open(p, *a, **kw))
        assert is_container() is True

    def test_negative_case(self, monkeypatch, tmp_path):
        """Returns False on a regular Linux host."""
        import builtins
        self._reset_cache(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda p: False)
        cgroup_file = tmp_path / "cgroup"
        cgroup_file.write_text("12:memory:/\n")
        _real_open = builtins.open
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(str(cgroup_file), *a, **kw) if p == "/proc/1/cgroup" else _real_open(p, *a, **kw))
        assert is_container() is False

    def test_caches_result(self, monkeypatch):
        """Second call uses cached value without re-probing."""
        monkeypatch.setattr(hermes_constants, "_container_detected", True)
        assert is_container() is True
        # Even if we make os.path.exists return False, cached value wins
        monkeypatch.setattr(os.path, "exists", lambda p: False)
        assert is_container() is True
