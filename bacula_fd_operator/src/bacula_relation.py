# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Library to handle the requirer part of the bacula-dir relation."""

import ops
from pydantic import BaseModel, Field

BACULA_DIR_RELATION_NAME = "bacula-dir"


class BaculaDirInfo(BaseModel):
    """Bacula-dir relation model.

    Attributes:
        name: bacula-dir name.
        password: bacula-dir password.
    """

    name: str = Field(min_length=1)
    password: str = Field(min_length=1)


class BaculaRequirer:
    """Requirer for the bacula-dir relation."""

    def __init__(
        self, charm: ops.CharmBase, relation_name: str = BACULA_DIR_RELATION_NAME
    ) -> None:
        """Initialize the requirer.

        Args:
            charm: the charm instance.
            relation_name: the bacula-dir relation name.
        """
        self._charm = charm
        self._relation_name = relation_name

    def send_to_bacula_dir(  # pylint: disable=too-many-arguments
        self,
        *,
        name: str,
        fileset: str,
        client_run_before_backup: str,
        client_run_after_backup: str,
        client_run_before_restore: str,
        client_run_after_restore: str,
        port: int = 9102,
        schedule: str | None = None,
    ) -> None:
        """Send bacula-fd information to the bacula-dir.

        Args:
            name: bacula-fd name.
            fileset: backup fileset.
            client_run_before_backup: backup run-before-backup script.
            client_run_after_backup: backup run-after-backup script.
            client_run_before_restore: backup run-before-restore script.
            client_run_after_restore: backup run-after-restore script.
            port: bacula-fd port.
            schedule: backup schedule.
        """
        relation = self._charm.model.get_relation(self._relation_name)
        if not relation:
            return
        data = relation.data[self._charm.unit]
        data["name"] = name
        data["fileset"] = fileset
        data["port"] = str(port)
        data["client-run-before-backup"] = str(client_run_before_backup)
        data["client-run-after-backup"] = str(client_run_after_backup)
        data["client-run-before-restore"] = str(client_run_before_restore)
        data["client-run-after-restore"] = str(client_run_after_restore)
        if schedule:
            data["schedule"] = schedule
        else:
            del data["schedule"]

    def receive_from_bacula_dir(self) -> BaculaDirInfo | None:
        """Receive the bacula-dir information from the bacula-dir.

        Returns:
            bacula-dir information or None if the relation or relation data doesn't exist.
        """
        relation = self._charm.model.get_relation(self._relation_name)
        if not relation or not relation.app:
            return None
        data = relation.data[relation.app]
        name = data.get("name")
        password_secret_id = data.get("password")
        if name and password_secret_id:
            password = self._charm.model.get_secret(id=password_secret_id).get_content(
                refresh=True
            )["password"]
            return BaculaDirInfo(name=name, password=password)
        return None
