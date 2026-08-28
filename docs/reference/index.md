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

* [Backup charm architecture](reference_architecture)
* [Backup integrator charm architecture](reference_backup_integrator_charm_architecture)
* [Bacula server charm architecture](reference_bacula_server_charm_architecture)
* [Bacula file daemon charm architecture](reference_bacula_fd_charm_architecture)


```{toctree}
:maxdepth: 1
:hidden:
actions.md
architecture/index.md
configurations.md
integrations.md
```
