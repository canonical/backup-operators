# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""backup-integrator charm unit tests."""

from pathlib import Path

import ops.testing
import pytest


@pytest.mark.parametrize("config", [{}, {"run-before-backup": "#!/bin/bash"}])
def test_no_fileset_config(backup_integrator_charm, config: dict):
    """
    arrange: none
    act: don't set the fileset charm config
    assert: the unit should be in the blocked status
    """
    ctx = ops.testing.Context(backup_integrator_charm)
    state_in = ops.testing.State(
        config=config,
        relations=[
            ops.testing.SubordinateRelation(endpoint="juju-info", id=1),
            ops.testing.Relation(endpoint="backup", id=2),
        ],
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "blocked"


def test_no_backup_relation(backup_integrator_charm) -> None:
    """
    arrange: none
    act: don't relate the backup relation
    assert: the unit should be in the waiting status
    """
    ctx = ops.testing.Context(backup_integrator_charm)
    state_in = ops.testing.State(
        config={"fileset": "/var/backups"},
        relations=[ops.testing.SubordinateRelation(endpoint="juju-info", id=1)],
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "waiting"


@pytest.mark.parametrize(
    "config",
    [
        {"fileset": "/var/backups"},
        {"fileset": "/var/backups/foo,/var/backups/bar"},
        {"fileset": "/var/backups", "run-before-backup": "run-before-backup"},
        {
            "fileset": "/var/backups",
            "run-before-backup": "run-before-backup",
            "run-after-backup": "run-after-backup",
            "run-before-restore": "run-before-restore",
            "run-after-restore": "run-after-restore",
        },
    ],
)
def test_update_backup_relation(backup_integrator_charm, config) -> None:
    """
    arrange: integrate the charm with a backup provider
    act: set appropriate backup charm configuration
    assert: backup relation should be updated with the configuration value
    """
    ctx = ops.testing.Context(backup_integrator_charm)
    relation = ops.testing.Relation(endpoint="backup", id=2)
    state_in = ops.testing.State(
        config=config,
        relations=[ops.testing.SubordinateRelation(endpoint="juju-info", id=1), relation],
        leader=True,
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    relation_data = state_out.get_relation(relation.id).local_app_data

    assert state_out.unit_status.name == "active"
    assert relation_data["fileset"] == config.get("fileset")
    scripts = ["run-before-backup", "run-after-backup", "run-before-restore", "run-after-restore"]
    for script in scripts:
        if script not in config:
            assert script not in relation_data
        else:
            assert config[script] == Path(relation_data[script]).read_text(encoding="utf-8")


@pytest.mark.parametrize("fileset", ["var/backups", "/var/backups,etc,/var/backups/foobar"])
def test_invalid_fileset(backup_integrator_charm, fileset: str) -> None:
    """
    arrange: none
    act: set the fileset charm config with an invalid value
    assert: the unit should be in the blocked status
    """
    ctx = ops.testing.Context(backup_integrator_charm)
    relation = ops.testing.Relation(endpoint="backup", id=2)
    state_in = ops.testing.State(
        config={"fileset": fileset},
        relations=[ops.testing.SubordinateRelation(endpoint="juju-info", id=1), relation],
        leader=True,
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    relation_data = state_out.get_relation(relation.id).local_app_data
    assert state_out.unit_status.name == "blocked"
    assert not relation_data
