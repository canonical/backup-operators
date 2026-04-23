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

* [Use the Baculum web interface]
* [Integrate with the backup integrator]
* [Upgrade]

## Guide for developers

Learn the guidelines and best practices before contributing to the
backup charm project.

* [Contribute]

```{toctree}
:maxdepth: 1
Contribute <contribution.md>
Integrate with the backup integrator <integrate-with-backup-integrator-charm.md>
Use the Baculum web interface <use-baculum.md>
Upgrade <upgrade.md>
```
