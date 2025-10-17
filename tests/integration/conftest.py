# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# for using fixtures in fixtures
# pylint: disable=unused-argument

"""Fixtures for integration tests."""

import json
import subprocess  # nosec
import textwrap

import boto3
import botocore.config
import jubilant
import pytest

from tests.integration import baculum


def find_charm_file(pytestconfig, name: str) -> str | None:
    """Find charm file from --charm-file input.

    Args:
        pytestconfig: pytest config.
        name: The filename of the charm file.

    Returns:
        The path to the charm file.
    """
    charm_files = pytestconfig.getoption("--charm-file")
    if not charm_files:
        return None
    for file in charm_files:
        if file.endswith(name):
            return file
    return None


@pytest.fixture(scope="module", name="backup_integrator_charm_file")
def backup_integrator_charm_file_fixture(pytestconfig) -> str:
    """Get backup-integrator charm file."""
    file = find_charm_file(pytestconfig, "backup-integrator_ubuntu@24.04-amd64.charm")
    if file:
        return file
    subprocess.check_call(["charmcraft", "pack"], cwd="./backup_integrator_operator/")  # nosec
    return "./backup_integrator_operator/backup-integrator_ubuntu@24.04-amd64.charm"


@pytest.fixture(scope="module", name="bacula_fd_charm_file")
def bacula_fd_charm_file_fixture(pytestconfig) -> str:
    """Get bacula-fd charm file."""
    file = find_charm_file(pytestconfig, "bacula-fd_ubuntu@24.04-amd64.charm")
    if file:
        return file
    subprocess.check_call(["charmcraft", "pack"], cwd="./bacula_fd_operator/")  # nosec
    return "./bacula_fd_operator/bacula-fd_ubuntu@24.04-amd64.charm"


@pytest.fixture(scope="module", name="bacula_server_charm_file")
def bacula_server_charm_file_fixture(pytestconfig) -> str:
    """Get bacula-server charm file."""
    file = find_charm_file(pytestconfig, "bacula-server_ubuntu@24.04-amd64.charm")
    if file:
        return file
    subprocess.check_call(["charmcraft", "pack"], cwd="./bacula_server_operator/")  # nosec
    return "./bacula_server_operator/bacula-server_ubuntu@24.04-amd64.charm"


@pytest.fixture(scope="module", name="deploy_minio")
def deploy_minio_fixture(juju: jubilant.Juju):
    """Deploy the minio charm (using any-charm)."""
    any_charm = textwrap.dedent(
        '''
        import os
        import subprocess
        import textwrap
        import urllib.request

        import ops

        from any_charm_base import AnyCharmBase

        class AnyCharm(AnyCharmBase):
            def __init__(self, *args):
                super().__init__(*args)
                self.framework.observe(self.on.install, self._on_install)

            def _on_install(self, _):
                self.unit.status = ops.MaintenanceStatus("downloading minio")
                urllib.request.urlretrieve(
                    "https://dl.min.io/server/minio/release/linux-amd64/minio", "/usr/bin/minio"
                )
                os.chmod("/usr/bin/minio", 0o755)
                self.unit.status = ops.MaintenanceStatus("setting up minio")
                service = textwrap.dedent(
                    """
                    [Unit]
                    Description=minio
                    Wants=network-online.target
                    After=network-online.target

                    [Service]
                    Type=simple
                    Environment="MINIO_ROOT_USER=minioadmin"
                    Environment="MINIO_ROOT_PASSWORD=minioadmin"
                    ExecStartPre=/usr/bin/mkdir -p /srv/bacula
                    ExecStart=/usr/bin/minio server --console-address :9001 /srv
                    Restart=on-failure
                    RestartSec=5

                    [Install]
                    WantedBy=multi-user.target
                    """
                )
                with open("/etc/systemd/system/minio.service", "w") as f:
                    f.write(service)
                subprocess.check_call(["systemctl", "daemon-reload"])
                subprocess.check_call(["systemctl", "enable", "--now", "minio"])
                self.unit.set_ports(9000, 9001)
                self.unit.status = ops.ActiveStatus()
        '''
    )
    juju.deploy(
        "any-charm",
        "minio",
        channel="latest/edge",
        config={"src-overwrite": json.dumps({"any_charm.py": any_charm})},
    )


@pytest.fixture(scope="module", name="deploy_charms")
def deploy_charms_fixture(
    juju: jubilant.Juju,
    deploy_minio,
    backup_integrator_charm_file,
    bacula_fd_charm_file,
    bacula_server_charm_file,
):
    """Deploy backup charms."""
    juju.deploy("ubuntu", base="ubuntu@24.04")
    juju.deploy(backup_integrator_charm_file, config={"fileset": "/var/backups/"})
    juju.deploy(bacula_fd_charm_file)
    juju.deploy(bacula_server_charm_file)
    juju.deploy("postgresql", "bacula-database", channel="14/stable")
    juju.deploy("s3-integrator")
    juju.wait(lambda status: jubilant.all_agents_idle(status, "s3-integrator"), timeout=7200)
    minio_address = list(juju.status().apps["minio"].units.values())[0].public_address
    juju.config(
        "s3-integrator",
        {
            "endpoint": f"http://{minio_address}:9000",
            "bucket": "bacula",
            "s3-uri-style": "path",
        },
    )
    juju.run(
        unit="s3-integrator/0",
        action="sync-s3-credentials",
        params={"access-key": "minioadmin", "secret-key": "minioadmin"},
    )

    juju.integrate("ubuntu:juju-info", "backup-integrator")
    juju.integrate("ubuntu:juju-info", "bacula-fd")
    juju.integrate("backup-integrator:backup", "bacula-fd")
    juju.integrate("bacula-server", "bacula-database")
    juju.integrate("bacula-server", "s3-integrator")
    juju.integrate("bacula-server", "bacula-fd")

    juju.wait(jubilant.all_active, timeout=7200)


@pytest.fixture(scope="module", name="setup_database")
def setup_database_fixture(juju: jubilant.Juju, deploy_charms):
    """Setup backup source, a simple postgresql server."""
    juju.ssh("ubuntu/0", "sudo apt-get install -y postgresql")
    juju.ssh("ubuntu/0", "sudo mkdir -p /var/backups/postgresql")
    juju.ssh("ubuntu/0", "sudo chown postgres /var/backups/postgresql")
    sql = """
          CREATE DATABASE ubuntu;

          \\c ubuntu

          CREATE TABLE IF NOT EXISTS release (
             version   TEXT NOT NULL,
             code_name TEXT NOT NULL
          );

          INSERT INTO "release" (version, code_name) VALUES
             ('25.10', 'Questing Quokka'),
             ('25.04', 'Plucky Puffin'),
             ('24.04', 'Noble Numbat'),
             ('23.10', 'Mantic Minotaur'),
             ('23.04', 'Lunar Lobster'),
             ('22.10', 'Kinetic Kudu'),
             ('22.04', 'Jammy Jellyfish'),
             ('21.10', 'Impish Indri'),
             ('21.04', 'Hirsute Hippo'),
             ('20.10', 'Groovy Gorilla'),
             ('20.04', 'Focal Fossa'),
             ('19.10', 'Eoan Ermine'),
             ('19.04', 'Disco Dingo'),
             ('18.10', 'Cosmic Cuttlefish'),
             ('18.04', 'Bionic Beaver'),
             ('17.10', 'Artful Aardvark'),
             ('17.04', 'Zesty Zapus'),
             ('16.10', 'Yakkety Yak'),
             ('16.04', 'Xenial Xerus'),
             ('15.10', 'Wily Werewolf'),
             ('15.04', 'Vivid Vervet'),
             ('14.10', 'Utopic Unicorn'),
             ('14.04', 'Trusty Tahr'),
             ('13.10', 'Saucy Salamander'),
             ('13.04', 'Raring Ringtail'),
             ('12.10', 'Quantal Quetzal'),
             ('12.04', 'Precise Pangolin'),
             ('11.10', 'Oneiric Ocelot'),
             ('11.04', 'Natty Narwhal'),
             ('10.10', 'Maverick Meerkat'),
             ('10.04', 'Lucid Lynx'),
             ('09.10', 'Karmic Koala'),
             ('09.04', 'Jaunty Jackalope'),
             ('08.10', 'Intrepid Ibex'),
             ('08.04', 'Hardy Heron'),
             ('07.10', 'Gutsy Gibbon'),
             ('07.04', 'Feisty Fawn'),
             ('06.10', 'Edgy Eft'),
             ('06.06', 'Dapper Drake'),
             ('05.10', 'Breezy Badger'),
             ('05.04', 'Hoary Hedgehog'),
             ('04.10', 'Warty Warthog');
          """
    juju.cli("ssh", "ubuntu/0", "sudo -u postgres psql -v ON_ERROR_STOP=1 postgres", stdin=sql)
    juju.config(
        "backup-integrator",
        {
            "run-before-backup": textwrap.dedent(
                """\
                #!/bin/bash
                sudo -u postgres pg_dump -d ubuntu -c -f /var/backups/postgresql/ubuntu.dump
                """
            ),
            "run-after-backup": textwrap.dedent(
                """\
                #!/bin/bash
                sudo rm -f /var/backups/postgresql/ubuntu.dump
                """
            ),
            "run-after-restore": textwrap.dedent(
                """\
                #!/bin/bash
                sudo -u postgres psql -d ubuntu -1 -f /var/backups/postgresql/ubuntu.dump
                sudo rm -f /var/backups/postgresql/ubuntu.dump
                """
            ),
        },
    )


@pytest.fixture(scope="module", name="baculum")
def baculum_client(juju: jubilant.Juju, setup_database) -> baculum.Baculum:
    """Initialize a Baculum API client."""
    unit_name, _ = list(juju.status().apps["bacula-server"].units.items())[0]
    username = "test-admin"
    password = juju.run(
        unit_name,
        "create-api-user",
        params={"username": username},
        wait=60,
    ).results["password"]
    address = list(juju.status().apps["bacula-server"].units.values())[0].public_address
    return baculum.Baculum(f"http://{address}:9096/api/v2", username=username, password=password)


@pytest.fixture(scope="module", name="s3")
def s3_client(juju: jubilant.Juju, setup_database):
    """Initialize a S3 client."""
    minio_address = list(juju.status().apps["minio"].units.values())[0].public_address
    return boto3.client(
        "s3",
        endpoint_url=f"http://{minio_address}:9000",
        aws_access_key_id="minioadmin",  # nosec
        aws_secret_access_key="minioadmin",  # nosec
        config=botocore.config.Config(s3={"addressing_style": "path"}),
    )
