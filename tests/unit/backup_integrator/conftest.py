# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for charm tests."""

import pytest

import backup_integrator_operator.src.charm


@pytest.fixture(autouse=True)
def backup_integrator_charm(monkeypatch, tmp_path):
    """Patch _CHARM_OPT_DIR in BackupIntegratorCharm."""
    monkeypatch.setattr(
        backup_integrator_operator.src.charm.BackupIntegratorCharm, "_CHARM_OPT_DIR", tmp_path
    )
    return backup_integrator_operator.src.charm.BackupIntegratorCharm
