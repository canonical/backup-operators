# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Library to handle the provider part of the bacula-dir relation."""

import logging
import secrets
import typing
from pathlib import Path

import ops
from pydantic import BaseModel, ConfigDict, Field, field_validator

BACULA_DIR_RELATION_NAME = "bacula-dir"
BACULA_DIR_NAME = "charm-bacula-dir"

logger = logging.getLogger(__name__)


class BaculaFdInfo(BaseModel):
    """Bacula file daemon information model.

    Attributes:
        model_config: Pydantic model configuration.
        name: Bacula file daemon name.
        password: Bacula file daemon password.
        fileset: backup fileset.
        host: Bacula file daemon host.
        port: Bacula file daemon port.
        schedule: backup schedule.
        client_run_before_backup: run script on Bacula file daemon before backup.
        client_run_after_backup: run script on Bacula file daemon after backup
        client_run_before_restore: run script on Bacula file daemon before restore.
        client_run_after_restore: run script on Bacula file daemon after restore.
    """

    model_config = ConfigDict(
        alias_generator=lambda name: name.replace("_", "-"), serialize_by_alias=True
    )
    name: str
    password: str
    fileset: list[Path]
    host: str = Field(..., alias="ingress-address")
    port: int = 9102
    schedule: list[str] = Field(default_factory=list)
    client_run_before_backup: str
    client_run_after_backup: str
    client_run_before_restore: str
    client_run_after_restore: str

    @field_validator("name", mode="before")
    @classmethod
    def _coerce_name(cls, value: str) -> str:
        """Normalize Bacula file daemon name.

        Args:
            value: Bacula file daemon name.

        Returns:
            Normalized Bacula file daemon name.
        """
        return value.removesuffix("-fd")

    @field_validator("schedule", mode="before")
    @classmethod
    def _coerce_schedule(cls, value: str | None) -> list[str]:
        """Normalize backup schedule.

        Args:
            value: backup schedule input.

        Returns: normalized schedule.
        """
        if not value:
            return []
        return [p.strip() for p in value.split(",") if p.strip()]

    @field_validator("fileset", mode="before")
    @classmethod
    def _coerce_fileset(cls, value: str) -> list[Path]:
        """Normalize backup fileset.

        Args:
            value: backup fileset input.

        Returns: normalized backup fileset.
        """
        if isinstance(value, str):
            parts = [p.strip() for p in value.split(",") if p.strip()]
            return [Path(p) for p in parts]
        return [Path(p) for p in value]

    @field_validator("fileset", mode="after")
    @classmethod
    def _validate_fileset(cls, value: list[Path]) -> list[Path]:
        """Validate backup fileset input.

        Args:
            value: backup fileset input.

        Returns: validated backup fileset.
        """
        if not value:
            raise ValueError("fileset cannot be empty")
        for path in value:
            str_path = str(path)
            if str_path != str_path.strip():
                raise ValueError("path cannot start or end with whitespaces")
            if "," in str_path:
                raise ValueError("path cannot contain commas")
            if not path.is_absolute():
                raise ValueError("all path in fileset must be absolute.")
        return value


class BaculaProvider:
    """bacula-dir relation provider."""

    def __init__(
        self, charm: ops.CharmBase, relation_name: str = BACULA_DIR_RELATION_NAME
    ) -> None:
        """Initialize bacula-dir relation provider.

        Args:
            charm: charm instance.
            relation_name: bacula-dir relation name.
        """
        self._charm = charm
        self._relation_name = relation_name

    def send_to_bacula_fd(self) -> None:
        """Send Bacula directory information to the Bacula file daemon."""
        relations = self._charm.model.relations[self._relation_name]
        for relation in relations:
            data = relation.data[self._charm.app]
            password_secret_id = data.get("password")
            if password_secret_id is None:
                password_secret = self._charm.app.add_secret(
                    content={"password": secrets.token_urlsafe(32)},
                    label=f"relation-{relation.id}",
                )
                password_secret.grant(relation)
                password_secret_id = password_secret.id
            data["name"] = BACULA_DIR_NAME
            data["password"] = typing.cast(str, password_secret_id)

    def receive_from_bacula_fd(self) -> list[BaculaFdInfo]:
        """Receive Bacula file daemon information from relations.

        Returns:
            list of BaculaFdInfo retrieved from relations.
        """
        relations = self._charm.model.relations[self._relation_name]
        info = []
        for relation in relations:
            if relation.app is None:
                continue
            password = self._charm.model.get_secret(
                id=relation.data[self._charm.app]["password"]
            ).get_content(refresh=True)["password"]
            for unit in relation.units:
                data = dict(relation.data[unit])
                if "name" not in data:
                    continue
                try:
                    info.append(
                        BaculaFdInfo.model_validate(
                            {
                                **relation.data[unit],
                                "password": password,
                            }
                        )
                    )
                except ValueError as exc:
                    logger.error(
                        "skipping invalid bacula-dir relation (id: %s) from %s: %s",
                        relation.id,
                        relation.app.name,
                        exc,
                    )
                    continue
        return info
