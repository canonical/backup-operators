---
myst:
  html_meta:
    "description lang=en": "Technical information related to backup charms."
---

(reference)=

# Reference

Technical specifications and architectural details for backup charms
serve as authoritative look-up material when configuring,  extending,
or integrating the charm.

## Charm configuration and operations

Operators control charm behavior through configuration options and Juju
actions. Here are the configuration and day-to-day operation related to
the Bacula charms.

* [Actions](reference_actions)
* [Configurations](reference_configurations)
* [Integrations](reference_integrations)

## Charm architecture and designs

Components and dependencies within the Bacula charms, along with the
architecture decisions made during charm creation.

* [Backup integrator charm architecture](explanation_backup_integrator_charm_architecture)
* [Bacula server charm architecture](explanation_backup_server_charm_architecture)
* [Bacula file daemon charm architecture](explanation_bacula_fd_charm_architecture)


```{toctree}
:maxdepth: 1
:hidden:
actions.md
backup-integrator-charm-architecture.md
bacula-server-charm-architecture.md
bacula-fd-charm-architecture.md
configurations.md
integrations.md
```
