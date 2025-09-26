#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""
import json
import shutil
import subprocess
import textwrap

import jubilant


def deploy_minio(juju: jubilant.Juju):
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
        constraints={"virt-type": "virtual-machine"},
    )


def test_deploy(juju: jubilant.Juju):
    subprocess.check_call(["snapcraft", "pack"], cwd="./charmed-bacula-server/")
    try:
        shutil.copy(
            "./bacula-server-operator/bacula-server_ubuntu@24.04-amd64.charm",
            "./bacula-server-operator/src",
        )
    except shutil.SameFileError:
        pass

    subprocess.check_call(["charmcraft", "pack"], cwd="./bacula-server-operator/")
    subprocess.check_call(["charmcraft", "pack"], cwd="./bacula-fd-operator/")
    subprocess.check_call(["charmcraft", "pack"], cwd="./backup-integrator-operator/")

    deploy_minio(juju)
    juju.deploy("ubuntu", base="ubuntu@24.04")
    juju.deploy(
        "./backup-integrator-operator/backup-integrator_ubuntu@24.04-amd64.charm",
        config={"fileset": "/srv"},
    )
    juju.deploy(
        "./bacula-fd-operator/bacula-fd_ubuntu@24.04-amd64.charm",
    )
    juju.integrate("ubuntu:juju-info", "backup-integrator")
    juju.integrate("backup-integrator:backup", "bacula-fd")
    juju.deploy("postgresql", constraints={"virt-type": "virtual-machine"})
    juju.deploy("s3-integrator", constraints={"virt-type": "virtual-machine"})
    juju.deploy("./bacula-server-operator/bacula-server_ubuntu@24.04-amd64.charm")
    juju.wait(
        lambda status: jubilant.all_agents_idle(status, "s3-integrator"),
        timeout=600,
    )

    minio_address = juju.status().apps["minio"].address
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
    juju.integrate("bacula-server", "postgresql")
    juju.integrate("bacula-server", "s3-integrator")
    juju.integrate("bacula-server:backup", "bacula-fd")

    juju.wait(lambda status: jubilant.all_active(status), timeout=600)
