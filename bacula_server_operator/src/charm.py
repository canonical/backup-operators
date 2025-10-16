#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more at: https://documentation.ubuntu.com/juju/3.6/howto/manage-charms/#build-a-charm

"""Bacula-server charm the service."""

import json
import logging
import secrets
import typing
import urllib.parse

import ops

import charms.data_platform_libs.v0.data_interfaces as data_interfaces
import charms.data_platform_libs.v0.s3 as s3
from . import bacula
from . import relations

PEER_RELATION_NAME = "bacula-peer"
BACULUM_CHARM_USERNAME = "charm-admin"

logger = logging.getLogger(__name__)


class NotReadyError(Exception):
    pass


class UnrecoverableError(Exception):
    pass


class BaculaServerCharm(ops.CharmBase):
    """Charm the service."""

    def __init__(self, *args: typing.Any):
        """Construct.

        Args:
            args: Arguments passed to the CharmBase parent constructor.
        """
        super().__init__(*args)
        self._database = data_interfaces.DatabaseRequires(
            charm=self,
            relation_name="postgresql",
            database_name=self.app.name,
        )
        self._s3 = s3.S3Requirer(
            charm=self,
            relation_name="s3",
            bucket_name=self.app.name,
        )
        self._bacula = bacula.Bacula()
        self._bacula_dir_relation = relations.BaculaProvider(charm=self)

        self.framework.observe(self.on.postgresql_relation_changed, self._reconcile_event)
        self.framework.observe(self.on.postgresql_relation_broken, self._reconcile_event)
        self.framework.observe(self.on.s3_relation_changed, self._reconcile_event)
        self.framework.observe(self.on.s3_relation_broken, self._reconcile_event)
        self.framework.observe(self.on.config_changed, self._reconcile_event)
        self.framework.observe(self.on.upgrade_charm, self._reconcile_event)
        self.framework.observe(self.on.secret_changed, self._reconcile_event)

        self.framework.observe(self.on.bacula_peer_relation_created, self._reconcile_event)
        self.framework.observe(self.on.bacula_peer_relation_changed, self._reconcile_event)
        self.framework.observe(self.on.bacula_peer_relation_departed, self._reconcile_event)

        self.framework.observe(self.on.bacula_dir_relation_changed, self._reconcile_event)
        self.framework.observe(self.on.bacula_dir_relation_joined, self._reconcile_event)
        self.framework.observe(self.on.bacula_dir_relation_departed, self._reconcile_event)
        self.framework.observe(self.on.bacula_dir_relation_broken, self._reconcile_event)

        self.framework.observe(self.on.update_status, self._reconcile_event)

        self.framework.observe(self.on.create_api_user_action, self._on_create_api_user)
        self.framework.observe(self.on.create_web_user_action, self._on_create_web_user)

    def _dump_relation(self, name: str) -> str:
        """Create a debug string representation of the give integration.

        Args:
            name: The name of the integration.

        Returns:
            a string representation of the integration.
        """
        integration = self.model.get_relation(name)
        if not integration:
            return json.dumps(None)
        dump: dict = {}
        app = integration.app
        if not app:
            dump["application-data"] = None
        else:
            dump["application-data"] = dict(integration.data[app])
        units = integration.units
        if not units:
            dump["unit-data"] = {}
        else:
            dump["unit-data"] = {unit.name: dict(integration.data[unit]) for unit in units}
        return json.dumps(dump)

    def _get_db_config(self) -> bacula.DbConfig:
        """Get database configuration from the database relation.

        Returns:
            a database configuration object.
        """
        relation = typing.cast(ops.Relation, self.model.get_relation(self._database.relation_name))
        if relation is None:
            raise NotReadyError("waiting for postgresql relation")
        relation_id = relation.id
        try:
            db_data = self._database.fetch_relation_data(
                relation_ids=[relation_id],
                fields=["endpoints", "username", "password", "database"],
            )[relation_id]
        except ops.ModelError as exc:
            # secret in integration not accessible before the integration events?
            logger.error(
                "invalid postgresql integration: %s",
                self._dump_relation("postgresql"),
            )
            raise UnrecoverableError("invalid postgresql relation") from exc
        if "database" not in db_data:
            raise NotReadyError("waiting for postgresql relation data")
        host, port = db_data["endpoints"].split(",")[0].split(":")
        return bacula.DbConfig(
            host=host,
            port=int(port),
            name=db_data["database"],
            username=db_data["username"],
            password=db_data["password"],
        )

    def _get_s3_config(self) -> bacula.S3Config:
        """Get s3 configuration from the s3 relation.

        Returns:
            a s3 configuration object.
        """
        relation = typing.cast(ops.Relation, self.model.get_relation(self._s3.relation_name))
        if relation is None:
            raise NotReadyError("waiting for s3 relation")
        s3_data = self._s3.get_s3_connection_info()
        if not s3_data or "access-key" not in s3_data:
            raise NotReadyError("waiting for s3 integration")
        url = urllib.parse.urlparse(s3_data["endpoint"])
        return bacula.S3Config(
            address=url.netloc,
            bucket=s3_data["bucket"],
            access_key=s3_data["access-key"],
            secret_key=s3_data["secret-key"],
            protocol="HTTP" if url.scheme == "http" else "HTTPS",
            uri_style="Path" if s3_data.get("s3-uri-style") == "path" else "VirtualHost",
        )

    def _get_unit_address(self) -> str:
        """Get the unit address of the unit.

        Returns:
            IP address of the unit.
        """
        peer_relation = self.model.get_relation(PEER_RELATION_NAME)
        if not peer_relation:
            raise NotReadyError("waiting for peer relation")
        return peer_relation.data[self.unit]["ingress-address"]

    def _get_peer_data(self) -> dict:
        """Get the peer data from the peer relation and initialize it if not exist.

        Returns:
            a dict containing the peer data.
        """
        peer_relation = self.model.get_relation(PEER_RELATION_NAME)
        if not peer_relation:
            raise NotReadyError("waiting for peer relation")
        data = peer_relation.data[self.app]
        password_secret_id = data.get("passwords")
        if not self.unit.is_leader():
            if not password_secret_id:
                raise NotReadyError("waiting for peer relation data")
        if not password_secret_id:
            passwords = {
                "dir-password": secrets.token_urlsafe(32),
                "fd-password": secrets.token_urlsafe(32),
                "sd-password": secrets.token_urlsafe(32),
                "api-password": secrets.token_urlsafe(32),
            }
            secret = self.app.add_secret(content=passwords)
            data["passwords"] = secret.id
            return passwords
        else:
            secret = self.model.get_secret(id=password_secret_id)
            return secret.get_content(refresh=True)

    def _get_bacula_config(self) -> bacula.BaculaConfig:
        """Get bacula configuration.

        Returns:
            a bacula configuration object.
        """
        passwords = self._get_peer_data()
        return bacula.BaculaConfig(
            dir_address=self._get_unit_address(),
            sd_address=self._get_unit_address(),
            dir_password=passwords["dir-password"],
            fd_password=passwords["fd-password"],
            sd_password=passwords["sd-password"],
            file_retention=self.config.get("file-retention"),
            job_retention=self.config.get("job-retention"),
            volume_retention=self.config.get("volume-retention"),
        )

    def _get_baculum_api_config(self) -> bacula.BaculumApiConfig:
        """Get baculum api configuration.

        Returns:
            a baculum api configuration object.
        """
        return bacula.BaculumApiConfig(
            username=BACULUM_CHARM_USERNAME,
            password=self._get_peer_data()["api-password"],
        )

    def _is_singleton(self) -> bool:
        """Check if there are more than one unit in the bacula-server charm.

        Returns:
            True if there are only one unit in the bacula-server charm.
        """
        relation = self.model.get_relation(PEER_RELATION_NAME)
        if not relation:
            return False
        unit_names = [unit.name for unit in relation.units]
        if not unit_names:  # only one unit
            return True
        unit_names.sort(key=lambda name: int(name.split("/")[-1]))
        return self.unit.name == unit_names[0]

    def _list_relation_fd(self) -> list[relations.BaculaFdInfo]:
        """List all established bacula-dir relations.

        Returns:
            a list of bacula-dir relations.
        """
        self._bacula_dir_relation.send_to_bacula_fd()
        return self._bacula_dir_relation.receive_from_bacula_fd()

    def _reconcile(self) -> None:
        """Reconcile the bacula-server."""
        bacula_config = self._get_bacula_config()
        baculum_api_config = self._get_baculum_api_config()
        db_config = self._get_db_config()
        s3_config = self._get_s3_config()
        if not self._is_singleton():
            raise UnrecoverableError("bacula-server charm does not support multiple units")
        if not self._bacula.is_installed():
            self.unit.status = ops.MaintenanceStatus("installing charmed-bacula-server")
            self._bacula.install()
        if not self._bacula.is_initialized(db=db_config):
            self.unit.status = ops.MaintenanceStatus("initializing bacula database")
            self._bacula.initialize(db=db_config)
        self.unit.status = ops.MaintenanceStatus("sync bacula config")
        relation_fd_list = self._list_relation_fd()
        try:
            self._bacula.apply(
                name=self.app.name,
                bacula_config=bacula_config,
                db_config=db_config,
                s3_config=s3_config,
                baculum_api_config=baculum_api_config,
                relation_fd_list=relation_fd_list,
            )
        except bacula.InvalidConfigError as exc:
            raise UnrecoverableError("failed to apply bacula configuration") from exc
        self.unit.set_ports(9101, 9103, 9095, 9096)
        self._bacula.update_baculum_api_user(
            baculum_api_config.username,
            baculum_api_config.password,
        )
        self._bacula.update_baculum_web_user(
            baculum_api_config.username,
            baculum_api_config.password,
        )

    def _reconcile_event(self, _: ops.EventBase) -> None:
        """Reconcile the bacula-server charm."""
        try:
            self._reconcile()
            self.unit.status = ops.ActiveStatus()
        except UnrecoverableError as exc:
            self.unit.status = ops.BlockedStatus(str(exc))
            return
        except NotReadyError as exc:
            self.unit.status = ops.WaitingStatus(str(exc))
            return

    def _on_create_api_user(self, event: ops.ActionEvent) -> None:
        """Event handler for the create-api-user action.

        Args:
            event: create-api-user action event.
        """
        username = event.params["username"]
        password = secrets.token_urlsafe(16)
        self._bacula.update_baculum_api_user(username, password)
        event.set_results({"username": username, "password": password})

    def _on_create_web_user(self, event: ops.ActionEvent) -> None:
        """Event handler for the create-web-user action.

        Args:
            event: create-web-user action event.
        """
        username = event.params["username"]
        password = secrets.token_urlsafe(16)
        self._bacula.update_baculum_web_user(username, password)
        event.set_results({"username": username, "password": password})


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(BaculaServerCharm)
