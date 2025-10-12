from pathlib import Path

import jinja2

import charms.operator_libs_linux.v0.apt as apt
import charms.operator_libs_linux.v0.systemd as systemd

BACULA_FD_CONFIG_TEMPLATE_FILE = Path(__file__).parent / "templates/bacula-fd.conf.j2"
BACULA_FD_CONFIG_FILE = Path("/etc/bacula/bacula-fd.conf")


def is_installed():
    return Path("/usr/sbin/bacula-fd").exists()


def install():
    apt.add_package(["bacula-fd"], update_cache=True)


def config_reload(
    *,
    name: str,
    host: str,
    port: int,
    director_name: str,
    director_password: str,
):
    env = jinja2.Environment()
    template = env.from_string(BACULA_FD_CONFIG_TEMPLATE_FILE.read_text())
    config = template.render(
        host=host,
        director_name=director_name,
        director_password=director_password,
        name=name,
        port=port,
    )
    current_config = BACULA_FD_CONFIG_FILE.read_text(encoding="utf-8")
    if current_config == config:
        return
    BACULA_FD_CONFIG_FILE.write_text(config)
    systemd.service_restart("bacula-fd")
