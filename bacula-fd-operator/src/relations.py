# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

from pathlib import Path

import ops

BACULA_DIR_RELATION_NAME = "bacula-dir"


class BaculaRequirer:
    def __init__(self, charm: ops.CharmBase, relation_name=BACULA_DIR_RELATION_NAME):
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

    def receive_from_bacula_dir(self) -> dict[str, str] | None:
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
            return {"name": name, "password": password}
        return {}
