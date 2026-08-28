---
myst:
  html_meta:
    "description lang=en": "Architecture of the backup charms and the Bacula components they are built on."
---

(reference_architecture)=

# Backup charm architecture

The backup charms use [Bacula](https://www.bacula.org/), an enterprise open
source backup solution, as the main component for the backup system.

The Bacula system uses a server-client architecture composed of three major
components:

* The Bacula file daemon, which is the client running on machines that need to
  be backed up and collects and uploads the files that need to be backed up.
* The Bacula storage daemon, which handles the storage of the backup files in
  actual backup media, like tape, disk, or cloud.
* The Bacula director, which supervises and orchestrates the backup service
  runs.

Bacula also optionally includes a web interface called Baculum for operators to
check backup status or initiate a backup remotely.

In the backup charm suite, the Bacula file daemon corresponds to the bacula-fd
charm, while the Bacula storage daemon, Bacula director, and Baculum are
combined into the bacula-server charm.

## Backup charm storage options

Bacula supports multiple backup storage targets and metadata storage targets
(called catalog in Bacula). For example, for backup files, Bacula supports
backup to local disk, tape, or S3-compatible storage. For the catalog database,
Bacula supports MySQL, PostgreSQL, and SQLite.

To provide the best experience with the Juju ecosystem, the backup charms are
opinionated to only support backup to S3-compatible storage and use PostgreSQL
as the catalog database.

## Per-charm architecture

Components and dependencies within each charm, along with the architecture
decisions made during charm creation.

* [Backup integrator charm architecture](reference_backup_integrator_charm_architecture)
* [Bacula server charm architecture](reference_bacula_server_charm_architecture)
* [Bacula file daemon charm architecture](reference_bacula_fd_charm_architecture)

```{toctree}
:maxdepth: 1
:hidden:
backup-integrator-charm-architecture.md
bacula-server-charm-architecture.md
bacula-fd-charm-architecture.md
```
