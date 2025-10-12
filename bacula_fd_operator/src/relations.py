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

    def __init__(self, charm: ops.CharmBase, relation_name=BACULA_DIR_RELATION_NAME):
        """Initialize the requirer.

        Args:
            charm: the charm instance.
            relation_name: the bacula-dir relation name.
        """
        self._charm = charm
        self._relation_name = relation_name

    def send_to_bacula_dir(
        self,
        *,
        name: str,
        fileset: str,
        port: int = 9102,
        client_run_before_backup: str,
        client_run_after_backup: str,
        client_run_before_restore: str,
        client_run_after_restore: str,
        schedule: str | None = None,
    ) -> None:
        relation = self._charm.model.get_relation(self._relation_name)
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
