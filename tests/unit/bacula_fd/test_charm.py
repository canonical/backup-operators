# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""bacula-fd unit tests."""

import textwrap

import ops.testing
import pytest

import bacula_fd_operator.src.bacula


def test_no_backup_relation(bacula_fd_charm) -> None:
    """
    arrange: none
    act: run config-changed event hook without backup relation
    assert: the charm should be in waiting state
    """
    ctx = ops.testing.Context(bacula_fd_charm)
    state_in = ops.testing.State(
        leader=True,
        relations=[ops.testing.PeerRelation(endpoint="bacula-peer")],
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "waiting"
    assert state_out.unit_status.message == "waiting for backup relation"


def test_no_bacula_dir_relation(bacula_fd_charm) -> None:
    """
    arrange: integrate the bacula-fd charm with a backup relation
    act: run config-changed event hook without bacula-dir relation
    assert: the charm should be in waiting state
    """
    ctx = ops.testing.Context(bacula_fd_charm)
    state_in = ops.testing.State(
        leader=True,
        relations=[
            ops.testing.PeerRelation(endpoint="bacula-peer"),
            ops.testing.Relation(endpoint="backup", remote_app_data={"fileset": "/var/backups"}),
        ],
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "waiting"
    assert state_out.unit_status.message == "waiting for bacula-dir relation"


def test_port_config(bacula_fd_charm) -> None:
    """
    arrange: integrate the bacula-fd charm with a backup relation and a bacula-dir relation.
    act: set the port configuration.
    assert: port in bacula-fd.conf and relation should be updated.
    """
    ctx = ops.testing.Context(bacula_fd_charm)
    secret = ops.testing.Secret(tracked_content={"password": "foobar"})
    state_in = ops.testing.State(
        leader=True,
        secrets=[secret],
        config={"port": 12345},
        relations=[
            ops.testing.PeerRelation(endpoint="bacula-peer"),
            ops.testing.Relation(endpoint="backup", remote_app_data={"fileset": "/var/backups"}),
            ops.testing.Relation(
                endpoint="bacula-dir",
                remote_app_data={"name": "bacula-dir", "password": secret.id},
                id=99,
            ),
        ],
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert "FDport = 12345" in bacula_fd_operator.src.bacula.read_config()
    assert state_out.get_relation(99).local_unit_data["port"] == "12345"


@pytest.mark.parametrize(
    "schedule", ["", "Level=Full sun at 01:00,Level=Incremental mon-sat at 01:00"]
)
def test_schedule_config(bacula_fd_charm, schedule) -> None:
    """
    arrange: integrate the bacula-fd charm with a backup relation and a bacula-dir relation.
    act: set the schedule configuration.
    assert: schedule in relation should be updated.
    """
    ctx = ops.testing.Context(bacula_fd_charm)
    secret = ops.testing.Secret(tracked_content={"password": "foobar"})
    state_in = ops.testing.State(
        leader=True,
        secrets=[secret],
        config={"schedule": schedule},
        relations=[
            ops.testing.PeerRelation(endpoint="bacula-peer"),
            ops.testing.Relation(endpoint="backup", remote_app_data={"fileset": "/var/backups"}),
            ops.testing.Relation(
                endpoint="bacula-dir",
                local_unit_data={"schedule": "Level=Full sun at 01:00"},
                remote_app_data={"name": "bacula-dir", "password": secret.id},
                id=99,
            ),
        ],
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    if schedule:
        assert state_out.get_relation(99).local_unit_data["schedule"] == schedule
    else:
        assert "schedule" not in state_out.get_relation(99).local_unit_data


def test_bacula_fd_config(bacula_fd_charm) -> None:
    """
    arrange: integrate the bacula-fd charm with a backup relation and a bacula-dir relation.
    act: run config-changed event hook.
    assert: the bacula-fd charm should write the correct bacula-fd configuration file.
    """
    ctx = ops.testing.Context(bacula_fd_charm)
    secret = ops.testing.Secret(tracked_content={"password": "foobar"})
    state_in = ops.testing.State(
        model=ops.testing.Model(name="test-bacula", uuid="00000000-0000-0000-0000-000000000000"),
        leader=True,
        secrets=[secret],
        relations=[
            ops.testing.PeerRelation(endpoint="bacula-peer"),
            ops.testing.Relation(endpoint="backup", remote_app_data={"fileset": "/var/backups"}),
            ops.testing.Relation(
                endpoint="bacula-dir",
                remote_app_data={"name": "bacula-dir", "password": secret.id},
            ),
        ],
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "active"
    assert (
        bacula_fd_operator.src.bacula.read_config().strip()
        == textwrap.dedent(
            """\
            Director {
              Name = bacula-dir
              Password = "foobar"
            }

            FileDaemon {
              Name = relation-test-bacula-bacula-fd-0-000000000000-fd
              FDport = 9102
              WorkingDirectory = /var/lib/bacula
              Pid Directory = /run/bacula
              Maximum Concurrent Jobs = 20
              Plugin Directory = /usr/lib/bacula
              FDAddress = 192.0.2.0
            }

            Messages {
              Name = Standard
              director = bacula-dir = all, !skipped, !restored, !verified, !saved
            }
            """
        ).strip()
    )
