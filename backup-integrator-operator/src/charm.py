#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import pathlib
import typing

import ops

from charms.backup_integrator.v0.backup import BackupDynamicRequirer

logger = logging.getLogger(__name__)


class BackupIntegratorCharm(ops.CharmBase):
    """Charm the service."""

    _CHARM_OPT_DIR = pathlib.Path("/opt/backup-integrator-charm")

    def __init__(self, *args: typing.Any):
        """Construct.

        Args:
            args: Arguments passed to the CharmBase parent constructor.
        """
        super().__init__(*args)
        self._requirer = BackupDynamicRequirer(charm=self)
        self.framework.observe(self.on.backup_relation_created, self._reconcile)
        self.framework.observe(self.on.backup_relation_changed, self._reconcile)
        self.framework.observe(self.on.config_changed, self._reconcile)
        self.framework.observe(self.on.upgrade_charm, self._reconcile)

    def _save_script(self, config_option: str) -> pathlib.Path | None:
        """Saves the content of a script configuration.

        Args:
            config_option: The name of the script configuration option.

        Returns:
            The path to the saved script if the configuration value is not empty, otherwise, None.
        """
        content = self.config.get(config_option)
        if not content:
            return None
        script_path = (
            self._CHARM_OPT_DIR / self.unit.name.replace("/", "-") / "scripts" / config_option
        )
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(content, encoding="utf-8")
        script_path.chmod(0o755)
        return script_path

    def _reconcile(self, _: ops.EventBase) -> None:
        """Reconciles the charm."""
        if not self.unit.is_leader():
            return
        fileset = [file.strip() for file in self.config.get("fileset").split(",") if file.strip()]
        if not fileset:
            self.unit.status = ops.WaitingStatus("waiting for fileset config")
            return
        self._requirer.request_backup(
            fileset=fileset,
            run_before_backup=self._save_script("run-before-backup"),
            run_after_backup=self._save_script("run-after-backup"),
            run_before_restore=self._save_script("run-before-restore"),
            run_after_restore=self._save_script("run-after-restore"),
        )
        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(BackupIntegratorCharm)
