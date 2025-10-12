# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""A helper library for managing bacula-fd"""

from pathlib import Path

import jinja2

import charms.operator_libs_linux.v0.apt as apt
import charms.operator_libs_linux.v0.systemd as systemd

BACULA_FD_CONFIG_TEMPLATE_FILE = Path(__file__).parent / "templates/bacula-fd.conf.j2"
BACULA_FD_CONFIG_FILE = Path("/etc/bacula/bacula-fd.conf")


def is_installed() -> bool:
    """Check if bacula-fd is installed.

    Returns:
        True if bacula-fd is installed.
    """
    return Path("/usr/sbin/bacula-fd").exists()


def install() -> None:
    """Install bacula-fd."""
    apt.add_package(["bacula-fd"], update_cache=True)


def restart() -> None:
    """Restart bacula-fd service."""
    systemd.service_restart("bacula-fd")


def read_config() -> str:
    """Read the current bacula-fd configuration file.

    Returns:
        The content of the bacula-fd configuration file, empty string if not exists.
    """
    if not BACULA_FD_CONFIG_FILE.exists():
        return ""
    return BACULA_FD_CONFIG_FILE.read_text(encoding="utf-8")


def config_reload(
    *,
    name: str,
    host: str,
    port: int,
    director_name: str,
    director_password: str,
) -> None:
    """Update and reload bacula-fd configuration.

    Args:
        name: bacula-fd name.
        host: bacula-fd address.
        port: bacula-fd port.
        director_name: bacula-dir name.
        director_password: bacula-dir password.
    """
    env = jinja2.Environment()
    template = env.from_string(BACULA_FD_CONFIG_TEMPLATE_FILE.read_text())
    config = template.render(
        host=host,
        director_name=director_name,
        director_password=director_password,
        name=name,
        port=port,
    )
    if config == read_config():
        return
    BACULA_FD_CONFIG_FILE.write_text(config)
    import uuid
()
