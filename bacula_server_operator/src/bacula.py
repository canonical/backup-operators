# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""A helper library for managing bacula server components."""

# suppress pylint false positive no-member warning
# pylint: disable=no-member

import dataclasses
import glob
import logging
import os
import signal
import subprocess  # nosec
import typing
from pathlib import Path
from typing import Literal

import jinja2
import psycopg2
from charms.operator_libs_linux.v2 import snap

from . import relations

TEMPLATES_DIR = (Path(__file__).parent / "templates").absolute()
BACULA_SERVER_SNAP_COMMON = Path("/var/snap/charmed-bacula-server/common")


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class BaculaConfig:  # pylint: disable=too-many-instance-attributes
    """Bacula server configurations.

    Attributes:
        dir_address: bacula-dir address.
        sd_address: bacula-sd address.
        dir_password: bacula-dir password.
        sd_password: bacula-sd password.
        fd_password: bacula-fd password.
        file_retention: file retention.
        job_retention: job retention.
        volume_retention: volume retention.
    """

    dir_address: str
    sd_address: str
    dir_password: str
    sd_password: str
    fd_password: str
    file_retention: str
    job_retention: str
    volume_retention: str


@dataclasses.dataclass
class DbConfig:
    """Postgres database configuration.

    Attributes:
        host: postgres host.
        port: postgres port.
        name: postgres database name.
        username: postgres username.
        password: postgres password.
    """

    host: str
    port: int
    name: str
    username: str
    password: str


@dataclasses.dataclass
class S3Config:
    """S3 compatible storage configuration.

    Attributes:
        address: S3 address.
        bucket: S3 bucket.
        access_key: S3 access key.
        secret_key: S3 secret key.
        protocol: S3 protocol, HTTP or HTTPS.
        uri_style: S3 uri_style, Path or VirtualHost.
    """

    address: str
    bucket: str
    access_key: str
    secret_key: str
    protocol: Literal["HTTP", "HTTPS"]
    uri_style: Literal["Path", "VirtualHost"]


@dataclasses.dataclass
class BaculumApiConfig:
    """Baculum API configuration.

    Attributes:
        username: Baculum API username.
        password: Baculum API password.
        endpoint: Baculum API endpoint.
    """

    username: str
    password: str
    endpoint: str = "http://localhost:9096"


class InvalidConfigError(Exception):
    """Invalid bacula service configuration."""


class BaculaService:  # pylint: disable=too-few-public-methods
    """Bacula service manager.

    Attributes:
        name: name of the bacula service.
        config_files: bacula service configuration files.
        config_templates: bacula service configuration templates (filename -> template name)
    """

    name: str
    config_files: list[str]
    config_templates: dict[str, str]

    def _test_config(self) -> bool:
        """Check if bacula service configuration is valid.

        Returns:
            True if bacula service configuration is valid.
        """
        file = self._config_tmp_path(self.config_files[0])
        try:
            subprocess.check_output(
                [
                    f"charmed-bacula-server.{self.name}-test",
                    str(file),
                ],
                stderr=subprocess.STDOUT,
                encoding="utf-8",
            )  # nosec
            return True
        except subprocess.CalledProcessError as e:
            logger.error("errors detected in %s configuration: %s", self.name, e.output)
        return False

    def _config_path(self, config: str) -> Path:
        """Get the snap path to the bacula service configuration.

        Args:
            config: bacula service configuration file.

        Returns:
            Snap path to the bacula service configuration.
        """
        return BACULA_SERVER_SNAP_COMMON / config.removeprefix("/")

    def _config_tmp_path(self, config: str) -> Path:
        """Get a path to temporary file which can be used to test the configuration.

        Args:
            config: bacula service configuration file.

        Returns:
            A path to a temporary file inside the snap.
        """
        return BACULA_SERVER_SNAP_COMMON / (config.removeprefix("/") + ".tmp")

    def _reload(self) -> None:
        """Reload bacula service."""
        bacula_snap = snap.SnapCache()["charmed-bacula-server"]
        bacula_service = bacula_snap.services[self.name]
        if bacula_service["active"]:
            logger.warning("restarting %s service", self.name)
            bacula_snap.restart([self.name])
        else:
            logger.warning("starting %s service", self.name)
            bacula_snap.start([self.name], enable=True)

    def _current_config(self) -> dict[str, str]:
        """Get the current bacula service configuration.

        Returns:
            Current bacula service configuration.
        """
        content = {}
        for file in self.config_files:
            content[file] = (
                self._config_path(file).read_text(encoding="utf-8")
                if self._config_path(file).exists()
                else ""
            )
        return content

    def _new_config(self, template_environment: jinja2.Environment) -> dict[str, str]:
        """Generate new bacula service configuration files using template environment.

        Args:
            template_environment: jinja2 template environment.

        Returns:
            New bacula service configuration files.
        """
        content = {}
        for file in self.config_files:
            template = template_environment.get_template(self.config_templates[file])
            content[file] = template.render()
        return content

    def apply(
        self,
        **template_globals: typing.Any,
    ) -> None:
        """Apply bacula service configuration.

        Args:
            template_globals: template variables inputs.

        Raises:
            InvalidConfigError: if bacula service configuration is invalid.
        """
        # not used for HTML
        templates = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
            undefined=jinja2.StrictUndefined,
        )  # nosec
        templates.globals.update(template_globals)
        new_config = self._new_config(templates)
        current_config = self._current_config()
        if new_config == current_config:
            return
        logger.info("applying new configurations to %s", self.name)
        for file, new_content in new_config.items():
            self._config_tmp_path(file).write_text(new_content, encoding="utf-8")
        if not self._test_config():
            logger.error("failed to validate new %s service configuration, aborting", self.name)
            raise InvalidConfigError(f"error in {self.name} configuration")
        for file, new_content in new_config.items():
            self._config_path(file).write_text(new_content, encoding="utf-8")
        self._reload()


class BaculaFdService(BaculaService):  # pylint: disable=too-few-public-methods
    """Bacula file daemon service.

    Attributes:
        name: name of the bacula service.
        config_files: bacula service configuration files.
        config_templates: bacula service configuration templates (filename -> template name)
    """

    name: str = "bacula-fd"
    config_files: list[str] = ["/opt/bacula/etc/bacula-fd.conf"]
    config_templates: dict[str, str] = {"/opt/bacula/etc/bacula-fd.conf": "bacula-fd.conf.j2"}


class BaculaSdService(BaculaService):  # pylint: disable=too-few-public-methods
    """Bacula storage daemon service.

    Attributes:
        name: name of the bacula service.
        config_files: bacula service configuration files.
        config_templates: bacula service configuration templates (filename -> template name)
    """

    name: str = "bacula-sd"
    config_files: list[str] = ["/opt/bacula/etc/bacula-sd.conf"]
    config_templates: dict[str, str] = {"/opt/bacula/etc/bacula-sd.conf": "bacula-sd.conf.j2"}


class BaculaDirService(BaculaService):  # pylint: disable=too-few-public-methods
    """Bacula director service.

    Attributes:
        name: name of the bacula service.
        config_files: bacula service configuration files.
        config_templates: bacula service configuration templates (filename -> template name)
    """

    name: str = "bacula-dir"
    config_files: list[str] = ["/opt/bacula/etc/bacula-dir.conf", "/opt/bacula/etc/bconsole.conf"]
    config_templates: dict[str, str] = {
        "/opt/bacula/etc/bacula-dir.conf": "bacula-dir.conf.j2",
        "/opt/bacula/etc/bconsole.conf": "bconsole.conf.j2",
    }

    def _reload_bacula_dir(self) -> None:
        """Send SIGHUP to the bacula-dir service."""
        for exe_link in glob.glob("/proc/[0-9]*/exe"):
            try:
                exe = Path(os.readlink(exe_link)).resolve()
                if exe.name == "bacula-dir":
                    pid = int(exe_link.removeprefix("/proc/").removesuffix("/exe"))
                    os.kill(pid, signal.SIGHUP)
            except FileNotFoundError:
                continue

    def _reload(self) -> None:
        """Reload bacula-dir service."""
        bacula_snap = snap.SnapCache()["charmed-bacula-server"]
        bacula_service = bacula_snap.services[self.name]
        if bacula_service["active"]:
            logger.info("reloading bacula-dir service")
            self._reload_bacula_dir()
        else:
            logger.info("starting bacula-dir service")
            bacula_snap.start([self.name], enable=True)


class BaculumService(BaculaService):  # pylint: disable=too-few-public-methods
    """Baculum service.

    Attributes:
        name: name of the bacula service.
        config_files: bacula service configuration files.
        config_templates: bacula service configuration templates (filename -> template name)
    """

    name: str = "baculum"
    config_files = [
        "/usr/share/baculum/htdocs/protected/API/Config/api.conf",
        "/usr/share/baculum/htdocs/protected/Web/Config/hosts.conf",
        "/usr/share/baculum/htdocs/protected/Web/Config/settings.conf",
    ]
    config_templates = {
        "/usr/share/baculum/htdocs/protected/API/Config/api.conf": "baculum-api.conf.j2",
        "/usr/share/baculum/htdocs/protected/Web/Config/hosts.conf": "baculum-web-hosts.conf.j2",
        (
            "/usr/share/baculum/htdocs/protected/Web/Config/settings.conf"
        ): "baculum-web-settings.conf.j2",
    }

    def _test_config(self) -> bool:
        """Test if baculum configuration file is valid.

        Baculum doesn't support this.

        Returns:
            True.
        """
        return True

    def _reload(self) -> None:
        """Reload baculum service."""
        bacula_snap = snap.SnapCache()["charmed-bacula-server"]
        bacula_service = bacula_snap.services[self.name]
        if not bacula_service["active"]:
            logger.info("starting baculum service")
            bacula_snap.start([self.name], enable=True)


class Bacula:
    """Bacula service controller."""

    def __init__(self) -> None:
        """Initialize Bacula service controller."""
        self._bacula_dir = BaculaDirService()
        self._bacula_sd = BaculaSdService()
        self._bacula_fd = BaculaFdService()
        self._baculum = BaculumService()

    @staticmethod
    def is_installed() -> bool:
        """Check if bacula service is installed.

        Returns:
            True if bacula service is installed otherwise False.
        """
        return Path("/snap/charmed-bacula-server").exists()

    @staticmethod
    def install() -> None:
        """Install bacula service."""
        logger.info("installing charmed-bacula-server snap")
        cache = snap.SnapCache()
        charmed_bacula_server = cache["charmed-bacula-server"]
        if not charmed_bacula_server.present:
            charmed_bacula_server.ensure(snap.SnapState.Latest, channel="stable")

    def is_initialized(self, db: DbConfig) -> bool:
        """Check if bacula category database is initialized.

        Args:
            db: bacula category database configuration.

        Returns:
            True if bacula category database is initialized otherwise False.
        """
        conn = psycopg2.connect(
            host=db.host,
            port=db.port,
            dbname=db.name,
            user=db.username,
            password=db.password,
        )
        table = "Job"
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass(%s) IS NOT NULL", (table,))
            return cur.fetchone()[0]

    def initialize(self, db: DbConfig) -> None:
        """Initialize bacula category database.

        Args:
            db: bacula category database configuration.
        """
        logger.info(
            "initializing bacula database in postgresql://%s:%s/%s", db.name, db.port, db.name
        )
        subprocess.check_call(
            ["charmed-bacula-server.make-postgresql-tables"],
            env={
                **os.environ,
                "PGHOST": db.host,
                "PGPORT": str(db.port),
                "PGUSER": db.username,
                "PGPASSWORD": db.password,
                "db_name": db.name,
            },
        )  # nosec

    def apply(  # pylint: disable=too-many-arguments
        self,
        *,
        name: str,
        bacula_config: BaculaConfig,
        db_config: DbConfig,
        s3_config: S3Config,
        baculum_api_config: BaculumApiConfig,
        relation_fd_list: list[relations.BaculaFdInfo],
    ) -> None:
        """Apply bacula service configurations.

        Args:
            name: charm name.
            bacula_config: bacula configuration.
            db_config: bacula category database configuration.
            s3_config: s3 storage configuration.
            baculum_api_config: bacula api configuration.
            relation_fd_list: bacula-fd information from relations.
        """
        template_globals = {
            "name": name,
            "bacula": bacula_config,
            "db": db_config,
            "s3": s3_config,
            "baculum_api": baculum_api_config,
            "relation_fd_list": relation_fd_list,
        }
        self._bacula_fd.apply(**template_globals)
        self._bacula_sd.apply(**template_globals)
        self._bacula_dir.apply(**template_globals)
        self._baculum.apply(**template_globals)

    def _update_baculum_user(
        self,
        user_file: str,
        username: str,
        password: str,
    ) -> None:
        """Update or create a baculum user.

        Args:
            user_file: baculum user file.
            username: baculum username.
            password: baculum password.
        """
        cmd = ["charmed-bacula-server.htpasswd", "-i"]
        if not (BACULA_SERVER_SNAP_COMMON / user_file.removeprefix("/")).exists():
            cmd.append("-c")
        cmd.append(user_file)
        cmd.append(username)
        subprocess.check_output(
            cmd, input=password, encoding="utf-8", stderr=subprocess.STDOUT
        )  # nosec

    def update_baculum_api_user(
        self,
        username: str,
        password: str,
    ) -> None:
        """Create or update Baculum api user.

        Args:
            username: baculum API username.
            password: baculum API password.
        """
        self._update_baculum_user(
            "/usr/share/baculum/htdocs/protected/API/Config/baculum.users",
            username=username,
            password=password,
        )

    def update_baculum_web_user(
        self,
        username: str,
        password: str,
    ) -> None:
        """Create or update Baculum web user.

        Args:
            username: baculum web username.
            password: baculum web password.
        """
        self._update_baculum_user(
            "/usr/share/baculum/htdocs/protected/Web/Config/baculum.users",
            username=username,
            password=password,
        )
