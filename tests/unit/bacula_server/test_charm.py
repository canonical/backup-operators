# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# for checking configuration files and mocking
# pylint: disable=line-too-long,no-member

"""bacula-server charm unit tests."""

import re
import textwrap

import ops.testing

from bacula_server_operator.src import bacula
from bacula_server_operator.src.charm import BaculaServerCharm


def make_s3_relation() -> ops.testing.Relation:
    """Create an example S3 relation.

    Returns:
        An example S3 relation object.
    """
    return ops.testing.Relation(
        remote_app_name="s3-integrator",
        endpoint="s3",
        remote_app_data={
            "access-key": "minioadmin",
            "bucket": "bacula",
            "endpoint": "http://minio.test:9000",
            "secret-key": "minioadmin",
            "s3-uri-style": "path",
        },
    )


def make_postgresql_relation() -> ops.testing.Relation:
    """Create an example postgresql relation.

    Returns:
        An example postgresql relation object.
    """
    return ops.testing.Relation(
        remote_app_name="postgresql",
        endpoint="postgresql",
        remote_app_data={
            "endpoints": "postgresql.test:5432",
            "database": "bacula_db",
            "username": "bacula_db_username",
            "password": "bacula_db_password",  # nosec: hardcoded_password_string
        },
    )


def test_no_database():
    """
    arrange: deploy a bacula-server charm without database relation.
    act: run config-changed event hook.
    assert: the charm should be in waiting state
    """
    ctx = ops.testing.Context(BaculaServerCharm)
    state_in = ops.testing.State(
        leader=True,
        relations=[ops.testing.PeerRelation(endpoint="bacula-peer")],
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.message == "waiting for postgresql relation"
    assert state_out.unit_status.name == "waiting"


def test_no_s3():
    """
    arrange: deploy a bacula-server charm without s3 relation.
    act: run config-changed event hook.
    assert: the charm should be in waiting state
    """
    ctx = ops.testing.Context(BaculaServerCharm)
    state_in = ops.testing.State(
        leader=True,
        relations=[
            ops.testing.PeerRelation(endpoint="bacula-peer"),
            make_postgresql_relation(),
        ],
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "waiting"
    assert state_out.unit_status.message == "waiting for s3 relation"


def test_install_and_initialize():
    """
    arrange: integrate bacula-server charm with a postgresql relation.
    act: run config-changed event hook.
    assert: the charm should install the charmed-bacula-server snap and initialize the database.
    """
    bacula.Bacula.is_installed.return_value = False
    bacula.Bacula.is_initialized.return_value = False

    ctx = ops.testing.Context(BaculaServerCharm)
    state_in = ops.testing.State(
        leader=True,
        relations=[
            ops.testing.PeerRelation(endpoint="bacula-peer"),
            make_postgresql_relation(),
            make_s3_relation(),
        ],
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status.name == "active"
    bacula.Bacula.install.assert_called_once()
    bacula.Bacula.initialize.assert_called_once()


def test_initial_charm_baculum_user(baculum_api_htpasswd, baculum_web_htpasswd):
    """
    arrange: integrate bacula-server charm with a postgresql and s3 relation.
    act: run config-changed event hook.
    assert: the charm should create a default baculum API and a default baculum web user
    """
    ctx = ops.testing.Context(BaculaServerCharm)
    state_in = ops.testing.State(
        leader=True,
        relations=[
            ops.testing.PeerRelation(endpoint="bacula-peer"),
            make_postgresql_relation(),
            make_s3_relation(),
        ],
    )
    ctx.run(ctx.on.config_changed(), state_in)

    assert "charm-admin" in baculum_api_htpasswd
    assert "charm-admin" in baculum_web_htpasswd


def test_bacula_fd_config():
    """
    arrange: integrate bacula-server charm with a postgresql and s3 relation.
    act: run config-changed event hook.
    assert: the charm should create a correct bacula-fd.conf
    """
    ctx = ops.testing.Context(BaculaServerCharm)
    state_in = ops.testing.State(
        leader=True,
        relations=[
            ops.testing.PeerRelation(endpoint="bacula-peer", id=1),
            make_postgresql_relation(),
            make_s3_relation(),
        ],
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    peer_data = state_out.get_relation(1).local_app_data
    peer_secret_data = state_out.get_secret(id=peer_data["passwords"]).tracked_content
    file = bacula.BACULA_SERVER_SNAP_COMMON / "opt/bacula/etc/bacula-fd.conf"
    assert file.read_text().strip() == textwrap.dedent(f"""\
            Director {{
              Name = charm-bacula-dir
              Password = {peer_secret_data["fd-password"]}
            }}

            FileDaemon {{
              Name = charm-bacula-fd
              FDport = 9102
              WorkingDirectory = /opt/bacula/working
              Pid Directory = /opt/bacula/run
              Maximum Concurrent Jobs = 20
              Plugin Directory = /opt/bacula/plugins
              FDAddress = 127.0.0.1
            }}

            Messages {{
              Name = Standard
              director = client1-dir = all, !skipped, !restored, !saved
            }}
            """).strip()


def test_bacula_sd_config():
    """
    arrange: integrate bacula-server charm with a postgresql and s3 relation.
    act: run config-changed event hook.
    assert: the charm should create a correct bacula-sd.conf
    """
    ctx = ops.testing.Context(BaculaServerCharm)
    state_in = ops.testing.State(
        leader=True,
        relations=[
            ops.testing.PeerRelation(endpoint="bacula-peer", id=1),
            make_postgresql_relation(),
            make_s3_relation(),
        ],
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    peer_data = state_out.get_relation(1).local_app_data
    peer_secret_data = state_out.get_secret(id=peer_data["passwords"]).tracked_content
    file = bacula.BACULA_SERVER_SNAP_COMMON / "opt/bacula/etc/bacula-sd.conf"
    assert file.read_text().strip() == textwrap.dedent(f"""\
            Storage {{
              Name = charm-bacula-sd
              SDPort = 9103
              WorkingDirectory = "/opt/bacula/working"
              Pid Directory = "/opt/bacula/working"
              Plugin Directory = "/opt/bacula/plugins"
              Maximum Concurrent Jobs = 20
              SDAddress = 192.0.2.0
            }}

            Cloud {{
              Name           = charm-s3-cloud
              Driver         = S3
              HostName       = "minio.test:9000"
              BucketName     = "bacula"
              AccessKey      = "minioadmin"
              SecretKey      = "minioadmin"
              Protocol       = HTTP
              UriStyle       = Path
              Truncate Cache = AfterUpload
              Upload         = EachPart
            }}

            Device {{
              Name              = charm-s3-storage
              Media Type        = CloudType
              Device Type       = Cloud
              Cloud             = charm-s3-cloud
              Archive Device    = /opt/bacula/archive
              Maximum Part Size = 10MB
              LabelMedia        = yes
              Random Access     = yes
              AutomaticMount    = yes
              RemovableMedia    = no
              AlwaysOpen        = no
            }}

            Director {{
              Name = charm-bacula-dir
              Password = "{peer_secret_data['sd-password']}"
            }}

            Messages {{
              Name = Standard
              director = charm-bacula-dir = all
            }}
            """).strip()


def test_bacula_dir_config():
    """
    arrange: integrate bacula-server charm with a postgresql and s3 relation.
    act: run config-changed event hook.
    assert: the charm should create a correct bacula-dir.conf
    """
    ctx = ops.testing.Context(BaculaServerCharm)
    state_in = ops.testing.State(
        leader=True,
        relations=[
            ops.testing.PeerRelation(endpoint="bacula-peer", id=1),
            make_postgresql_relation(),
            make_s3_relation(),
        ],
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)
    peer_data = state_out.get_relation(1).local_app_data
    peer_secret_data = state_out.get_secret(id=peer_data["passwords"]).tracked_content
    file = bacula.BACULA_SERVER_SNAP_COMMON / "opt/bacula/etc/bacula-dir.conf"
    assert file.read_text().strip() == textwrap.dedent(f"""\
            Director {{
              Name = charm-bacula-dir
              DIRport = 9101
              QueryFile = "/opt/bacula/scripts/query.sql"
              WorkingDirectory = "/opt/bacula/working"
              PidDirectory = "/opt/bacula/working"
              Maximum Concurrent Jobs = 20
              Password = {peer_secret_data["dir-password"]}
              Messages = charm-daemon-messages
              DirAddress = 127.0.0.1
            }}

            Storage {{
              Name        = charm-s3-storage
              Address     = 192.0.2.0
              SDPort      = 9103
              Password    = {peer_secret_data["sd-password"]}
              Device      = charm-s3-storage
              Media Type  = CloudType
            }}

            Pool {{
              Name = charm-cloud-pool
              Pool Type = Backup
              Recycle = yes
              AutoPrune = yes
              Maximum Volume Jobs = 1
              Volume Retention = 1 year
              Label Format = "bacula-server-vol-${{Year}}${{Month:p/2/0/r}}${{Day:p/2/0/r}}-${{Job}}-${{NumVols}}"
            }}

            Schedule {{
              Name = charm-cloud-upload-schedule
              Run = daily at 01:00
            }}

            Job {{
                Name = charm-cloud-upload
                Type = Admin
                Client = charm-bacula-fd
                Schedule = charm-cloud-upload-schedule
                RunScript {{
                    RunsOnClient = No
                    RunsWhen = Always
                    Console = "cloud upload storage=charm-s3-storage allpools"
                    Console = "cloud truncate storage=charm-s3-storage allpools"
                }}
                Storage = charm-s3-storage
                Messages = charm-daemon-messages
                Pool = charm-cloud-pool
                Fileset = charm-empty-fileset
            }}

            FileSet {{
              Name = charm-empty-fileset
              Include {{ File = /dev/null }}
            }}

            Client {{
              Name = charm-bacula-fd
              Address = 127.0.0.1
              FDPort = 9102
              Catalog = charm-catalog
              Password = "{peer_secret_data['fd-password']}"
              File Retention = 1 year
              Job Retention = 1 year
            }}

            Catalog {{
              Name = charm-catalog
              dbname = "bacula_db"
              DB Address = "postgresql.test"
              DB Port = 5432
              dbuser = "bacula_db_username"
              dbpassword = "bacula_db_password"
            }}

            Messages {{
              Name = charm-daemon-messages
              # mailcommand = "/sbin/bsmtp -h localhost -f \\"\\(Bacula\\) \\<%r\\>\\" -s \\"Bacula daemon message\\" %r"
              # mail = root = all, !skipped
              console = all, !skipped, !saved
              append = "/opt/bacula/log/bacula.log" = all, !skipped
            }}
            """).strip()


def test_bacula_fd_relation():
    """
    arrange: integrate bacula-server charm with a postgresql and s3 relation.
    act: integrate the bacula-server with two bacula-fd charm.
    assert: the charm should create a bacula-dir.conf with corresponding bacula-fd entries.
    """
    ctx = ops.testing.Context(BaculaServerCharm)
    state_in = ops.testing.State(
        leader=True,
        relations=[
            ops.testing.PeerRelation(endpoint="bacula-peer"),
            make_postgresql_relation(),
            make_s3_relation(),
            ops.testing.Relation(
                endpoint="bacula-dir",
                remote_app_name="bacula-fd-one",
                remote_units_data={
                    0: {
                        "name": "relation-test-bacula-bacula-fd-one-0-2e79074dc082-fd",
                        "fileset": "/var/backups/one",
                        "port": "9102",
                        "client-run-before-backup": "/opt/backup-integrator-charm/backup-integrator-0/scripts/run-before-backup",
                        "client-run-after-backup": "/opt/backup-integrator-charm/backup-integrator-0/scripts/run-after-backup",
                        "client-run-before-restore": "/var/lib/juju/agents/unit-bacula-fd-one-0/charm/scripts/noop",
                        "client-run-after-restore": "/opt/backup-integrator-charm/backup-integrator-0/scripts/run-after-restore",
                        "ingress-address": "10.0.1.1",
                    }
                },
            ),
            ops.testing.Relation(
                endpoint="bacula-dir",
                remote_app_name="bacula-fd-two",
                remote_units_data={
                    0: {
                        "name": "relation-test-bacula-bacula-fd-two-0-2e79074dc082-fd",
                        "fileset": "/var/backups/two",
                        "port": "9102",
                        "client-run-before-backup": "/var/lib/juju/agents/unit-bacula-fd-one-0/charm/scripts/noop",
                        "client-run-after-backup": "/var/lib/juju/agents/unit-bacula-fd-one-0/charm/scripts/noop",
                        "client-run-before-restore": "/var/lib/juju/agents/unit-bacula-fd-one-0/charm/scripts/noop",
                        "client-run-after-restore": "/var/lib/juju/agents/unit-bacula-fd-one-0/charm/scripts/noop",
                        "schedule": "Level=Full sun at 01:00,Level=Incremental mon-sat at 01:00",
                        "ingress-address": "10.0.2.1",
                    }
                },
            ),
        ],
    )
    ctx.run(ctx.on.config_changed(), state_in)
    file = bacula.BACULA_SERVER_SNAP_COMMON / "opt/bacula/etc/bacula-dir.conf"
    file_content = file.read_text(encoding="utf-8")
    file_content = re.sub(r"(?m)^\s*(?:\r?\n|$)", "", file_content)
    assert textwrap.dedent("""\
            Job {
              Name = "relation-test-bacula-bacula-fd-one-0-2e79074dc082-backup"
              Type = Backup
              Client  = "relation-test-bacula-bacula-fd-one-0-2e79074dc082-fd"
              FileSet = "relation-test-bacula-bacula-fd-one-0-2e79074dc082-fileset"
              Storage = charm-s3-storage
              Messages = charm-daemon-messages
              Pool = charm-cloud-pool
              RunScript {
                Command = "/opt/backup-integrator-charm/backup-integrator-0/scripts/run-before-backup"
                RunsOnClient = yes
                RunsWhen = Before
                FailJobOnError = yes
              }
              RunScript {
                Command = "/opt/backup-integrator-charm/backup-integrator-0/scripts/run-after-backup"
                RunsOnClient = yes
                RunsWhen = After
                FailJobOnError = no
              }
            }
            Job {
              Name = "relation-test-bacula-bacula-fd-one-0-2e79074dc082-restore"
              Type = Restore
              Client  = "relation-test-bacula-bacula-fd-one-0-2e79074dc082-fd"
              FileSet = "relation-test-bacula-bacula-fd-one-0-2e79074dc082-fileset"
              Storage = charm-s3-storage
              Messages = charm-daemon-messages
              Pool = charm-cloud-pool
              Where = /
              Replace = IfNewer
              RunScript {
                Command = "/var/lib/juju/agents/unit-bacula-fd-one-0/charm/scripts/noop"
                RunsOnClient = yes
                RunsWhen = Before
                FailJobOnError = yes
              }
              RunScript {
                Command = "/opt/backup-integrator-charm/backup-integrator-0/scripts/run-after-restore"
                RunsOnClient = yes
                RunsWhen = After
                FailJobOnError = no
              }
            }
            """) in file_content
    assert textwrap.dedent("""\
            Schedule {
              Name = "relation-test-bacula-bacula-fd-two-0-2e79074dc082-schedule"
              Run = Level=Full sun at 01:00
              Run = Level=Incremental mon-sat at 01:00
            }
            Job {
              Name = "relation-test-bacula-bacula-fd-two-0-2e79074dc082-backup"
              Type = Backup
              Client  = "relation-test-bacula-bacula-fd-two-0-2e79074dc082-fd"
              FileSet = "relation-test-bacula-bacula-fd-two-0-2e79074dc082-fileset"
              Storage = charm-s3-storage
              Messages = charm-daemon-messages
              Pool = charm-cloud-pool
              Schedule = charm-cloud-upload-schedule
              RunScript {
                Command = "/var/lib/juju/agents/unit-bacula-fd-one-0/charm/scripts/noop"
                RunsOnClient = yes
                RunsWhen = Before
                FailJobOnError = yes
              }
              RunScript {
                Command = "/var/lib/juju/agents/unit-bacula-fd-one-0/charm/scripts/noop"
                RunsOnClient = yes
                RunsWhen = After
                FailJobOnError = no
              }
            }
            Job {
              Name = "relation-test-bacula-bacula-fd-two-0-2e79074dc082-restore"
              Type = Restore
              Client  = "relation-test-bacula-bacula-fd-two-0-2e79074dc082-fd"
              FileSet = "relation-test-bacula-bacula-fd-two-0-2e79074dc082-fileset"
              Storage = charm-s3-storage
              Messages = charm-daemon-messages
              Pool = charm-cloud-pool
              Where = /
              Replace = IfNewer
              RunScript {
                Command = "/var/lib/juju/agents/unit-bacula-fd-one-0/charm/scripts/noop"
                RunsOnClient = yes
                RunsWhen = Before
                FailJobOnError = yes
              }
              RunScript {
                Command = "/var/lib/juju/agents/unit-bacula-fd-one-0/charm/scripts/noop"
                RunsOnClient = yes
                RunsWhen = After
                FailJobOnError = no
              }
            }
            """) in file_content
