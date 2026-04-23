---
myst:
  html_meta:
    "description lang=en": "Technical information related to backup charms."
---

(reference)=

# Reference

Technical specifications and architectural details for Baculum charms
serve as authoritative look-up material when configuring,  extending,
or integrating the charm.

## Charm Configuration and operations

Operators control charm behavior through configuration options and Juju
actions. Understanding the overall charm architecture provides the 
structural context needed to see how those settings and actions interact
at runtime.

* [Actions](actions.md)
* [Configurations](configurations.md)
* [Integrations](integrations.md)

## Charm architecture and designs

Components and dependencies within the Bacula charms, along with the
architecture decisions made during charm creation.

* [Backup integrator charm architecture](backup-integrator-charm-architecture.md)
* [Bacula server charm architecture](bacula-server-charm-architecture.md)
* [Bacula fd charm architecture](bacula-fd-charm-architecture.md)


```{toctree}
:maxdepth: 1
actions.md
backup-integrator-charm-architecture.md
bacula-server-charm-architecture.md
bacula-fd-charm-architecture.md
configurations.md
integrations.md
```
