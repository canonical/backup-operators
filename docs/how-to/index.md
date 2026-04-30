---
myst:
  html_meta:
    "description lang=en": "How-to guides covering backup charm operations lifecycle."
---

(how_to)=

# How-to guides

Guides for managing the full operations lifecycle of the Bacula charms,
from user operation and maintenance to developer contribution. Each 
guide assumes that you've already deployed the charm with Juju.

## Guide for charm users

Manage the Bacula deployment using the Baculum web interface, including
using the web interface to start a backup or restoration. Or learn how
to integrate Bacula charms with a legacy charm deployment using the
backup-integrator charm.

* [Use the Baculum web interface](how_to_use_baculum)
* [Integrate with the backup integrator](how_to_integrate_with_backup_integrator_charm)

## Maintenance and development

Learn the guidelines and best practices for maintaining and contributing to the
Bacula charms project.

* [Upgrade](how_to_upgrade)
* [Contribute](how_to_contribute)

```{toctree}
:maxdepth: 1
:hidden:
Contribute <contribution.md>
Integrate with the backup integrator <integrate-with-backup-integrator-charm.md>
Use the Baculum web interface <use-baculum.md>
Upgrade <upgrade.md>
```
