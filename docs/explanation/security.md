(explanation_security)=

# Security overview

## Bacula charms

Please refer to the Bacula security document on Bacula security
issues: [https://www.bacula.org/15.0.x-manuals/en/main/Bacula_Security_Issues.html](https://www.bacula.org/15.0.x-manuals/en/main/Bacula_Security_Issues.html)

In the current version of the Bacula charms (bacula-server, bacula-fd),
the following non-default protections are omitted:

* bacula-dir and bacula-sd run as root.
* The internal firewall and TCP wrappers are not enabled.
* TLS is not enabled, meaning transmission between bacula-fd and bacula-server
  is unencrypted.
* Volume encryption is disabled; backups stored in S3 are unencrypted.

# Backup integrator charm

The backup integrator charm is a workload-less subordinate
charm. There are no security vulnerabilities beyond [Juju's intrinsic ones](https://documentation.ubuntu.com/juju/3.6/explanation/juju-security/).
