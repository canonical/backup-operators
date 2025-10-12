# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for charm tests."""

import pytest

import bacula_fd_operator.src.charm
import bacula_fd_operator.src.bacula


@pytest.fixture(autouse=True)
def bacula_fd_charm(monkeypatch, tmp_path):
    """Patch the BaculaFdCharm."""
    is_installed = False

    def _install():
        nonlocal is_installed
        is_installed = True

    monkeypatch.setattr(bacula_fd_operator.src.bacula, "is_installed", lambda: is_installed)
    monkeypatch.setattr(bacula_fd_operator.src.bacula, "install", _install)
    monkeypatch.setattr(bacula_fd_operator.src.bacula, "restart", lambda: None)
    monkeypatch.setattr(
        bacula_fd_operator.src.bacula,
        "BACULA_FD_CONFIG_FILE",
        tmp_path / "bacula-fd.conf",
    )

    return bacula_fd_operator.src.charm.BaculaFdCharm
