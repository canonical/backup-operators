# How to integrate with the backup integrator charm

The backup integrator charm provides backup functionality to charms that
haven't, or cannot, implement the backup relation themselves.

To use the backup integrator charm, integrate the backup integrator
charm with the backup source using the `juju-info` relation. Then you
can use the `backup` relation endpoint to request backups from
backup-provider charms such as `bacula-fd`. Let's
demonstrate by using the Ubuntu charm as an example.

Deploy the charm and integrate with the backup integrator 
and Provider charms:

```
juju deploy ubuntu

juju integrate ubuntu:juju-info backup-integrator
juju integrate backup-integrator:backup bacula-fd
```

Attach the bacula-fd charm to the principal charm because a
subordinate charm cannot be a principal charm for another
subordinate charm.

```
juju integrate ubuntu:juju-info bacula-fd
```

Integrate bacula-fd charm with the bacula-server charm:
```
juju integrate bacula-fd bacula-server
```

## Configure the backup integrator charm

As the backup integrator charm is the requirer of backups, you need to
provide the specification of what to back up and how to back it up to
the backup integrator charm. This is controlled by the `fileset`,
`run-before-backup`, `run-after-backup`, `run-before-restore`, and
`run-after-restore` configuration options on the backup integrator
charm.

The `fileset` configuration describes what to back up; it's a
comma-separated list of absolute files or directories on the backup
source machine.

The `run-before-backup`, `run-after-backup`, `run-before-restore`, and
`run-after-restore` configurations describe how to back up and restore.
Each contains the content of a script that will run before or after a
backup or restore. These scripts can be used to prepare backup files and
to restore the service from a backup.

The following is an example configuration for the backup integrator
charm on an imaginary PostgreSQL charm (not the
real [`postgresql`](https://charmhub.io/postgresql) charm). It uses
`pg_dump` to create a backup file of the database and `psql` to restore
the database from that file during a restoration.

```yaml
fileset: /var/backups/postgresql
run-before-backup: |
  #!/bin/bash
  sudo -u postgres pg_dump -d ubuntu -c -f /var/backups/postgresql/ubuntu.dump
run-after-backup: |
  #!/bin/bash
  sudo rm -f /var/backups/postgresql/ubuntu.dump
run-before-restore: null
run-after-restore: |
  #!/bin/bash
  sudo -u postgres psql -d ubuntu -1 -f /var/backups/postgresql/ubuntu.dump
  sudo rm -f /var/backups/postgresql/ubuntu.dump
```
