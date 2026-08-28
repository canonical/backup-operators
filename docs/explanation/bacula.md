---
myst:
  html_meta:
    "description lang=en": "Explanation for the relation between bacula and backup charms."
---

(explanation_bacula)=

# Bacula backup solution

The backup charms use [Bacula](https://www.bacula.org/), an enterprise open
source backup solution, as the main component for the backup system.

The Bacula system uses a server-client architecture composed of three major
components: 

* The Bacula file daemon, which is the client running on machines that
  need to be backed up and collects and uploads the files that need to be backed
  up.
* The Bacula storage daemon, which handles the storage of the backup files in
  actual backup media, like tape, disk, or cloud.
* The Bacula director, which supervises and orchestrates the backup service runs. 

Bacula also optionally
includes a web interface called Baculum for operators to check backup status or
initiate a backup remotely.

In the backup charm suite, the Bacula file daemon corresponds to the bacula-fd
charm, while the Bacula storage daemon, Bacula director, and Baculum are
combined into the bacula-server charm.

## Backup charm storage options

Bacula supports multiple backup storage
targets and metadata storage targets (called catalog in Bacula) . For
example, for backup files, Bacula supports backup to local disk, tape, or
S3-compatible storage. For the catalog database, Bacula supports MySQL,
PostgreSQL, and SQLite.

To provide the best experience with the Juju ecosystem, the backup
charms are opinionated to only support backup to S3-compatible storage and use
PostgreSQL as the catalog database.
