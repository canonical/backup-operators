# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for charm tests."""

import unittest.mock

import pytest

import bacula_server_operator.src.bacula


@pytest.fixture(autouse=True)
def mock_bacula_services(monkeypatch):
    """Patch bacula services."""
    monkeypatch.setattr(
        bacula_server_operator.src.bacula.BaculaFdService,
        "_reload",
        unittest.mock.MagicMock(),
    )
    monkeypatch.setattr(
        bacula_server_operator.src.bacula.BaculaFdService,
        "_test_config",
        unittest.mock.MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        bacula_server_operator.src.bacula.BaculaSdService,
        "_reload",
        unittest.mock.MagicMock(),
    )
    monkeypatch.setattr(
        bacula_server_operator.src.bacula.BaculaSdService,
        "_test_config",
        unittest.mock.MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        bacula_server_operator.src.bacula.BaculaDirService,
        "_reload",
        unittest.mock.MagicMock(),
    )
    monkeypatch.setattr(
        bacula_server_operator.src.bacula.BaculaDirService,
        "_test_config",
        unittest.mock.MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        bacula_server_operator.src.bacula.BaculumService,
        "_reload",
        unittest.mock.MagicMock(),
    )


@pytest.fixture(autouse=True)
def mock_bacula(monkeypatch):
    """Patch bacula install/initialization related functions."""
    monkeypatch.setattr(
        bacula_server_operator.src.bacula.Bacula,
        "is_installed",
        unittest.mock.MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        bacula_server_operator.src.bacula.Bacula,
        "install",
        unittest.mock.MagicMock(),
    )
    monkeypatch.setattr(
        bacula_server_operator.src.bacula.Bacula,
        "is_initialized",
        unittest.mock.MagicMock(return_value=True),
    )
    monkeypatch.setattr(
        bacula_server_operator.src.bacula.Bacula,
        "initialize",
        unittest.mock.MagicMock(),
    )


@pytest.fixture(autouse=True)
def baculum_api_htpasswd(monkeypatch):
    """Patch Bacula.update_baculum_api_user."""
    htpasswd = {}

    def update_user(self, username: str, password: str):
        htpasswd[username] = password

    monkeypatch.setattr(
        bacula_server_operator.src.bacula.Bacula,
        "update_baculum_api_user",
        update_user,
    )

    return htpasswd


@pytest.fixture(autouse=True)
def baculum_web_htpasswd(monkeypatch):
    """Patch Bacula.update_baculum_web_user."""
    htpasswd = {}

    def update_user(self, username: str, password: str):
        htpasswd[username] = password

    monkeypatch.setattr(
        bacula_server_operator.src.bacula.Bacula,
        "update_baculum_web_user",
        update_user,
    )

    return htpasswd


@pytest.fixture(autouse=True)
def patch_bacula_snap_path(monkeypatch, tmp_path):
    """Patch charmed-bacula-server snap directory path."""
    monkeypatch.setattr(
        bacula_server_operator.src.bacula,
        "BACULA_SERVER_SNAP_COMMON",
        tmp_path,
    )

    for path in [
        "opt/bacula/etc",
        "usr/share/baculum/htdocs/protected/API/Config",
        "usr/share/baculum/htdocs/protected/Web/Config",
    ]:
        (tmp_path / path).mkdir(parents=True, exist_ok=True)
