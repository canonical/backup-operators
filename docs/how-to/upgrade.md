(how_to_upgrade)=

# How to upgrade

## Upgrade `backup-integrator` and `bacula-fd`

The `backup-integrator` and `bacula-fd` are both stateless charms, meaning 
they don't store persistent data that could be lost during an upgrade. This makes the upgrade process for both the charms straightforward.

Upgrade the charms with the `refresh` command:

```bash
juju refresh backup-integrator
juju refresh bacula-fd
```

## Upgrade `bacula-server`

The `bacula-server` is a stateful charm as it maintains persistent data in its 
PostgreSQL database. Before upgrading the `bacula-server` charm, you must back up the PostgreSQL database.

Follow the [PostgreSQL documentation](https://canonical-charmed-postgresql.readthedocs-hosted.com/14/how-to/back-up-and-restore/create-a-backup/) 
for instructions on how to create a backup of the `postgresql` charm.

After confirming the PostgreSQL backup is complete, upgrade the `bacula-server` charm:

```bash
juju refresh bacula-server
```

# Verify the upgrade

After upgrading, verify that the charms are functioning correctly with the `juju status` command. 
The upgraded charms must be in active and idle state.

