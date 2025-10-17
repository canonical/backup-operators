#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Bacula file daemon charm the service."""

import logging
import typing
from pathlib import Path

import ops
from charms.backup_integrator.v0 import backup

from . import bacula, bacula_relation

BACKUP_RELATION_NAME = "backup"
BACULA_DIR_RELATION_NAME = "bacula-dir"
PEER_RELATION_NAME = "bacula-peer"
NOOP_SCRIPT = str((Path(__file__).parent.parent / "scripts/noop").absolute())


class NotReadyError(Exception):
    """Charm is not ready."""


class UnrecoverableCharmError(Exception):
    """Unrecoverable Charm failure."""


logger = logging.getLogger(__name__)


class BaculaFdCharm(ops.CharmBase):
    """Bacula file daemon charm the service."""

    def __init__(self, *args: typing.Any):
        """Construct.

        Args:
            args: Arguments passed to the CharmBase parent constructor.
        """
        super().__init__(*args)
        self._backup_provider = backup.BackupProvider(charm=self)
        self._bacula_dir = bacula_relation.BaculaRequirer(charm=self)

        self.framework.observe(self.on.config_changed, self._reconcile_event)
        self.framework.observe(self.on.upgrade_charm, self._reconcile_event)
        self.framework.observe(self.on.secret_changed, self._reconcile_event)
        self.framework.observe(self.on.leader_elected, self._reconcile_event)
        self.framework.observe(self.on.leader_settings_changed, self._reconcile_event)

        self.framework.observe(self.on.bacula_peer_relation_created, self._reconcile_event)
        self.framework.observe(self.on.bacula_peer_relation_changed, self._reconcile_event)
        self.framework.observe(self.on.bacula_peer_relation_departed, self._reconcile_event)

        self.framework.observe(self.on.backup_relation_created, self._reconcile_event)
        self.framework.observe(self.on.backup_relation_changed, self._reconcile_event)
        self.framework.observe(self.on.backup_relation_departed, self._reconcile_event)
        self.framework.observe(self.on.backup_relation_broken, self._reconcile_event)

        self.framework.observe(self.on.bacula_dir_relation_changed, self._reconcile_event)
        self.framework.observe(self.on.bacula_dir_relation_broken, self._reconcile_event)

    def _get_peer_data(self) -> dict[str, str] | None:
        """Get data stored in the peer relation and initialize it if not exist.

        Returns:
            peer data stored in the peer relation, None if peer relation doesn't exist yet.
        """
        peer_relation = self.model.get_relation(PEER_RELATION_NAME)
        if not peer_relation:
            return None
        data = peer_relation.data[self.app]
        peer_relation_factory = {
            "name": lambda charm: "-".join(
                [
                    "relation",
                    charm.model.name,
                    charm.unit.name.replace("/", "-"),
                    charm.model.uuid.split("-")[-1],
                    "fd",
                ]
            ),
        }
        if set(data.keys()) != set(peer_relation_factory.keys()):
            if self.unit.is_leader():
                for key, factory in peer_relation_factory.items():
                    if key not in data:
                        data[key] = factory(self)
                return dict(data)
            return {}
        return dict(data)

    def _load_schedule(self) -> list[str]:
        """Load the backup schedule configuration.

        Returns:
            Backup schedule configuration.
        """
        schedule_config = typing.cast(str, self.config.get("schedule", "")).split(",")
        return [schedule.strip() for schedule in schedule_config if schedule.strip()]

    def _get_unit_address(self) -> str:
        """Get the address of the unit.

        Returns:
            The IP address of the unit.
        """
        peer_relation = self.model.get_relation(PEER_RELATION_NAME)
        if not peer_relation:
            raise NotReadyError("waiting for peer relation")
        return peer_relation.data[self.unit]["ingress-address"]

    def _reconcile(self) -> None:
        """Reconcile the charm."""
        if not bacula.is_installed():
            self.unit.status = ops.WaitingStatus("installing bacula-fd")
            bacula.install()
            self.unit.status = ops.ActiveStatus()
        peer_data = self._get_peer_data()
        if not peer_data:
            raise NotReadyError("waiting for peer data to be initialized")
        name = peer_data["name"]
        backup_relation = self.model.get_relation(BACKUP_RELATION_NAME)
        if not backup_relation:
            raise NotReadyError("waiting for backup relation")
        try:
            backup_spec = self._backup_provider.get_backup_spec(backup_relation)
        except ValueError as exc:
            logger.exception("invalid backup relation data")
            raise UnrecoverableCharmError("invalid backup relation data") from exc
        if not backup_spec:
            raise NotReadyError("waiting for backup relation data")
        bacula_dir = self.model.get_relation(BACULA_DIR_RELATION_NAME)
        if not bacula_dir:
            raise NotReadyError("waiting for bacula-dir relation")
        port = typing.cast(int, self.config.get("port", 9102))
        self.unit.set_ports(port)
        self._bacula_dir.send_to_bacula_dir(
            name=name,
            port=port,
            fileset=",".join(map(str, backup_spec.fileset)),
            schedule=",".join(self._load_schedule()),
            client_run_before_backup=backup_spec.run_before_backup or NOOP_SCRIPT,
            client_run_after_backup=backup_spec.run_after_backup or NOOP_SCRIPT,
            client_run_before_restore=backup_spec.run_before_restore or NOOP_SCRIPT,
            client_run_after_restore=backup_spec.run_after_restore or NOOP_SCRIPT,
        )
        dir_data = self._bacula_dir.receive_from_bacula_dir()
        if not dir_data:
            raise NotReadyError("waiting for bacula-dir relation data")
        bacula.config_reload(
            name=name,
            host=self._get_unit_address(),
            port=port,
            director_name=dir_data.name,
            director_password=dir_data.password,
        )

    def _reconcile_event(self, _: ops.EventBase) -> None:
        """Reconcile the charm."""
        try:
            self._reconcile()
            self.unit.status = ops.ActiveStatus()
        except NotReadyError as exc:
            self.unit.status = ops.WaitingStatus(str(exc))
        except UnrecoverableCharmError as exc:
            self.unit.status = ops.BlockedStatus(str(exc))


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(BaculaFdCharm)
