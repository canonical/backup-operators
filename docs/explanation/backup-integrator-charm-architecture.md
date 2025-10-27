# Charm architecture: backup integrator

Backup Integrator charm is a subordinate charm that requires a backup
provider charm on behalf of other charms. Usually this is necessary
because the charm needs backup functionality but either has not
implemented the backup relation itself or cannot implement it.

The design and functionality of the backup integrator are very simple.
Basically, it passes the backup integrator charm’s configuration values 
to the backup relation. For the `fileset` configuration, the backup 
integrator validates it before passing it to the relation. For the 
`run-*` configurations, the backup integrator writes the configuration
content to a local file and passes the filename to the backup relation.

## Juju events

For this charm, the following Juju events are observed:

1. [`backup-relation-changed`](https://documentation.ubuntu.com/juju/latest/reference/hook/index.html#endpoint-relation-changed), 
   [`backup-relation-created`](https://documentation.ubuntu.com/juju/latest/reference/hook/index.html#endpoint-relation-created):
   Monitors changes and creation of the `backup` relation to update
   relation data when needed.
2. [`config-changed`](https://documentation.ubuntu.com/juju/latest/reference/hook/index.html#config-changed):
   Monitors changes to the backup integrator configuration to update the
   relation data with the latest configuration values.
3. [`leader-elected`](https://documentation.ubuntu.com/juju/latest/reference/hook/index.html#leader-elected), 
   [`leader-settings-changed`](https://documentation.ubuntu.com/juju/latest/reference/hook/index.html#leader-settings-changed):
   Monitors changes in the charm’s leadership. Since only the leader
   unit can modify application relation data, triggering a relation data
   update when leadership changes ensures the relation is updated
   regardless of leader status during relation establishment.
4. [`upgrade-charm`](https://documentation.ubuntu.com/juju/latest/reference/hook/index.html#upgrade-charm):
   Triggered when the charm has been upgraded. This ensures that the new
   version of the backup integrator charm can update the relation data
   if needed.

> See more in the Juju docs: [Hook](https://documentation.ubuntu.com/juju/latest/user/reference/hook/)

## Charm code overview

The `src/__main__.py` file is the default entry point for the backup
integrator charm; it creates an instance of the `BackupIntegratorCharm`
class (imported from the `charm` module), which inherits from
`ops.CharmBase`. `ops.CharmBase` is the base class from which all charms
are derived, provided
by [Ops](https://ops.readthedocs.io/en/latest/index.html) (the Python
framework for developing charms).

> See more in the Juju docs: [Charm](https://documentation.ubuntu.com/juju/latest/user/reference/charm/)

The `__init__` method of `BackupIntegratorCharm` ensures that the charm
observes and handles all events relevant to its operation.

For example, when a configuration is changed via the CLI:

1. The user runs the configuration command:

```bash
juju config backup-integrator fileset=/var/backups
```

2. A `config-changed` event is emitted.
3. In the `__init__` method, the handler for this event is defined as
   follows:

```python
self.framework.observe(self.on.config_changed, self._reconcile)
```

4. The `_reconcile` method, in turn, takes the necessary actions, such
   as waiting for the backup relation(s) and updating the backup
   relation data.
