import dataclasses
import glob
import logging
import os
import signal
import subprocess
from pathlib import Path
from typing import Literal

import jinja2
import psycopg2

import charms.operator_libs_linux.v2.snap as snap

import relations

TEMPLATES_DIR = (Path(__file__).parent / "templates").absolute()
BACULA_SERVER_SNAP_COMMON = Path("/var/snap/charmed-bacula-server/common")


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class BaculaConfig:
    def __init__(
        self,
        dir_address: str,
        sd_address: str,
        dir_password: str,
        sd_password: str,
        fd_password: str,
        file_retention: str,
        job_retention: str,
        volume_retention: str,
    ):
        self.dir_address = dir_address
        self.sd_address = sd_address
        self.dir_password = dir_password
        self.sd_password = sd_password
        self.fd_password = fd_password
        self.file_retention = file_retention
        self.job_retention = job_retention
        self.volume_retention = volume_retention


@dataclasses.dataclass
class DbConfig:
    def __init__(self, host: str, port: int, name: str, username: str, password: str):
        self.host = host
        self.port = port
        self.name = name
        self.username = username
        self.password = password


@dataclasses.dataclass
class S3Config:
    def __init__(
        self,
        address: str,
        bucket: str,
        access_key: str,
        secret_key: str,
        protocol: Literal["HTTP", "HTTPS"],
        uri_style: Literal["Path", "VirtualHost"],
    ):
        self.address = address
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.protocol = protocol
        self.uri_style = uri_style


class BaculumApiConfig:
    def __init__(self, username: str, password: str, endpoint: str = "http://localhost:9096"):
        self.username = username
        self.password = password
        self.endpoint = endpoint


class BaculaServiceException(Exception):
    pass


class BaculaService:
    name: str
    config_files: list[str]
    config_templates: dict[str, str]

    def _test_config(self) -> bool:
        file = self._config_tmp_path(self.config_files[0])
        try:
            subprocess.check_output(
                [
                    f"charmed-bacula-server.{self.name}-test",
                    str(file),
                ],
                stderr=subprocess.STDOUT,
                encoding="utf-8",
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error("errors detected in %s configuration: %s", self.name, e.output)
        return False

    def _config_path(self, config: str) -> Path:
        return BACULA_SERVER_SNAP_COMMON / config.removeprefix("/")

    def _config_tmp_path(self, config: str) -> Path:
        return BACULA_SERVER_SNAP_COMMON / (config.removeprefix("/") + ".tmp")

    def _reload(self):
        bacula_snap = snap.SnapCache()["charmed-bacula-server"]
        bacula_service = bacula_snap.services[self.name]
        if bacula_service["active"]:
            logger.warning("restarting %s service", self.name)
            bacula_snap.restart([self.name])
        else:
            logger.warning("starting %s service", self.name)
            bacula_snap.start([self.name], enable=True)

    def _current_config(self) -> dict[str, str]:
        content = {}
        for file in self.config_files:
            content[file] = (
                self._config_path(file).read_text(encoding="utf-8")
                if self._config_path(file).exists()
                else ""
            )
        return content

    def _new_config(self, template_environment: jinja2.Environment) -> dict[str, str]:
        content = {}
        for file in self.config_files:
            template = template_environment.get_template(self.config_templates[file])
            content[file] = template.render()
        return content

    def apply(
        self,
        **template_globals: dict,
    ):
        templates = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
            undefined=jinja2.StrictUndefined,
        )
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
            raise BaculaServiceException(f"error in {self.name} configuration")
        for file, new_content in new_config.items():
            self._config_path(file).write_text(new_content, encoding="utf-8")
        self._reload()


class BaculaFdService(BaculaService):
    name: str = "bacula-fd"
    config_files: list[str] = ["/opt/bacula/etc/bacula-fd.conf"]
    config_templates: dict[str, str] = {"/opt/bacula/etc/bacula-fd.conf": "bacula-fd.conf.j2"}


class BaculaSdService(BaculaService):
    name: str = "bacula-sd"
    config_files: list[str] = ["/opt/bacula/etc/bacula-sd.conf"]
    config_templates: dict[str, str] = {"/opt/bacula/etc/bacula-sd.conf": "bacula-sd.conf.j2"}


class BaculaDirService(BaculaService):
    name: str = "bacula-dir"
    config_files: list[str] = ["/opt/bacula/etc/bacula-dir.conf", "/opt/bacula/etc/bconsole.conf"]
    config_templates: dict[str, str] = {
        "/opt/bacula/etc/bacula-dir.conf": "bacula-dir.conf.j2",
        "/opt/bacula/etc/bconsole.conf": "bconsole.conf.j2",
    }

    def _reload_bacula_dir(self):
        for exe_link in glob.glob("/proc/[0-9]*/exe"):
            try:
                exe = Path(os.readlink(exe_link)).resolve()
                if exe.name == "bacula-dir":
                    pid = int(exe_link.removeprefix("/proc/").removesuffix("/exe"))
                    os.kill(pid, signal.SIGHUP)
            except FileNotFoundError:
                continue

    def _reload(self):
        bacula_snap = snap.SnapCache()["charmed-bacula-server"]
        bacula_service = bacula_snap.services[self.name]
        if bacula_service["active"]:
            logger.info("reloading bacula-dir service")
            self._reload_bacula_dir()
        else:
            logger.info("starting bacula-dir service")
            bacula_snap.start([self.name], enable=True)


class BaculumService(BaculaService):
    name: str = "baculum"
    config_files = [
        "/usr/share/baculum/htdocs/protected/API/Config/api.conf",
        "/usr/share/baculum/htdocs/protected/Web/Config/hosts.conf",
        "/usr/share/baculum/htdocs/protected/Web/Config/settings.conf",
    ]
    config_templates = {
        "/usr/share/baculum/htdocs/protected/API/Config/api.conf": "baculum-api.conf.j2",
        "/usr/share/baculum/htdocs/protected/Web/Config/hosts.conf": "baculum-web-hosts.conf.j2",
        "/usr/share/baculum/htdocs/protected/Web/Config/settings.conf": "baculum-web-settings.conf.j2",
    }

    def _test_config(self) -> bool:
        return True

    def _reload(self):
        bacula_snap = snap.SnapCache()["charmed-bacula-server"]
        bacula_service = bacula_snap.services[self.name]
        if not bacula_service["active"]:
            logger.info("starting baculum service")
            bacula_snap.start([self.name], enable=True)


class Bacula:
    def __init__(self):
        self._bacula_dir = BaculaDirService()
        self._bacula_sd = BaculaSdService()
        self._bacula_fd = BaculaFdService()
        self._baculum = BaculumService()

    @staticmethod
    def is_installed() -> bool:
        return Path("/snap/charmed-bacula-server").exists()

    @staticmethod
    def install() -> None:
        logger.info("installing charmed-bacula-server snap")
        snap_file = (Path(__file__).parent / "charmed-bacula-server_15.0.3_amd64.snap").absolute()
        snap.install_local(filename=str(snap_file), dangerous=True)

    def is_initialized(self, db: DbConfig) -> bool:
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
        )

    def apply(
        self,
        name: str,
        bacula_config: BaculaConfig,
        db_config: DbConfig,
        s3_config: S3Config,
        baculum_api_config: BaculumApiConfig,
        relation_fd_list: list[relations.BaculaFdInfo],
    ):
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
    ):
        cmd = ["charmed-bacula-server.htpasswd", "-i"]
        if not (BACULA_SERVER_SNAP_COMMON / user_file.removeprefix("/")).exists():
            cmd.append("-c")
        cmd.append(user_file)
        cmd.append(username)
        subprocess.check_output(cmd, input=password, encoding="utf-8", stderr=subprocess.STDOUT)

    def update_baculum_api_user(
        self,
        username: str,
        password: str,
    ) -> None:
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
        self._update_baculum_user(
            "/usr/share/baculum/htdocs/protected/Web/Config/baculum.users",
            username=username,
            password=password,
        )
