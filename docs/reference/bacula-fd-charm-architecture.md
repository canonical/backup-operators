(explanation_bacula_fd_charm_architecture)=

<!-- vale Canonical.007-Headings-sentence-case = NO -->

# Charm architecture: bacula-fd

<!-- vale Canonical.007-Headings-sentence-case = YES -->

The bacula-fd charm is a subordinate charm that installs and
manages the Bacula file daemon on target machines. Bacula-fd (Bacula
File Daemon) is the backup agent that needs to be installed on machines
requiring backups. The bacula-fd handles many important duties, such as
uploading backup files and downloading restored backup files.

## High-level overview of backup charms deployment

Here's a typical backup charm suite deployment in the machine charm
environment. This deployment shows the bacula-server charm as the backup server,
the bacula-fd charm as the backup agent, and the backup-integrator charm
as the backup relation provider.

The backup-integrator charm requests backups from the bacula-fd charm on
behalf of the backup source charm `source`. The bacula-fd charm then
integrates with the bacula-server charm to submit the backup files. The
bacula-server charm is integrated with the PostgreSQL charm for storing
backup metadata and with the s3-integrator charm to use S3 storage as
the destination for backup files.

```{mermaid}
C4Context
    title Container diagram for backup charms

    System_Boundary(backup server, "Backup Server Model") {
        Container(s3-integrator, "S3 Integrator", "", "Provide backup destination")
        Container(bacula-server, "Bacula Server", "", "Backup server")
        Container(postgresql, "PostgreSQL", "", "Store backup metadata")
        Rel(s3-integrator, bacula-server, "")
        Rel(postgresql, bacula-server, "")
    }

    System_Boundary(backup source, "Backup Source Model") {
        Container_Boundary(backup-source, "Backup Source") {
            Component(source, "", "Backup source principal charm")
            Component(backup-integrator, "", "Backup relation integrator")
            Component(bacula-fd, "", "Bacula file daemon")
        }
        Rel(source, backup-integrator, "")
        Rel(backup-integrator, bacula-fd, "")
    }
    Rel(bacula-fd, bacula-server, "")
```

## Juju events

1. {ref}`config-changed <juju:hook-config-changed>`:
   Monitors changes to the backup integrator configuration to update the
   relation data with the latest configuration values.
2. `leader-elected`, `leader-settings-changed`:
   Monitors changes in the charm’s leadership. Since only the leader
   unit can modify application relation data, triggering a relation data
   update when leadership changes ensures the relation is updated
   regardless of leader status during relation establishment.
3. {ref}`upgrade-charm <juju:hook-upgrade-charm>`:
   Triggered when the charm has been upgraded. This ensures that the new
   version of the backup integrator charm can update the relation data
   if needed.
4. {ref}`bacula-peer-relation-changed <juju:hook-relation-changed>`,  
   {ref}`bacula-peer-relation-created <juju:hook-relation-created>`, 
   {ref}`bacula-peer-relation-departed <juju:hook-relation-departed>`:
   Monitors changes, creation, and removal of the `bacula-peer` relation
   to update relation data when needed.
5. {ref}`bacula-dir-relation-changed <juju:hook-relation-changed>`,  
   {ref}`bacula-dir-relation-broken <juju:hook-relation-broken>`:
   Monitors changes, creation, and removal of the `bacula-dir` relation
   to update relation data when needed.
6. {ref}`backup-relation-changed <juju:hook-relation-changed>`,
   {ref}`backup-relation-broken <juju:hook-relation-broken>`,
   {ref}`backup-relation-departed <juju:hook-relation-departed>`:
   Monitors changes, creation, and removal of the `backup` relation to
   update relation data when needed.
7. {ref}`secret-changed <juju:hook-secret-changed>`:
   Monitors changes in secrets inside relations to update configuration
   when needed.

```{note}
See more in the Juju docs: {ref}`juju:hook`
```

## Charm code overview

The `src/__main__.py` file is the default entry point for the backup
integrator charm; it creates an instance of the `BaculaFdCharm`
class (imported from the `charm` module), which inherits from
`ops.CharmBase`. `ops.CharmBase` is the base class from which all charms
are derived, provided
by [Ops](https://ops.readthedocs.io/en/latest/index.html) (the Python
framework for developing charms).

```{note}
See more in the Juju docs: {ref}`juju:charm`
```

The `__init__` method of `BaculaFdCharm` ensures that the charm observes
and handles all events relevant to its operation.

For example, when a configuration is changed via the CLI:

1. The user runs the configuration command:

```bash
juju config bacula-fd port=8888
```

2. A `config-changed` event is emitted.
3. In the `__init__` method, the handler for this event is defined as
   follows:

```python
self.framework.observe(self.on.config_changed, self._reconcile_event)
```

4. The `__reconcile_event` method, in turn, takes the necessary actions,
   such as waiting for the backup relation(s) and updating the backup
   relation data.
