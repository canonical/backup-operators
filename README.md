# Backup operators
This repository contains a collection of operators that handle backups
in the Juju ecosystem. Its goal is to provide an easy-to-use, highly
integrated backup solution for charms in Juju.

For information about how to deploy, integrate, and manage the backup
charms, see the official [Backup charms documentation](https://canonical.com/juju/docs/backup-charms/).

## Repository layout

```
backup_integrator_operator/ # Juju charm: backup-integrator subordinate charm source
bacula_fd_operator/         # Juju charm: bacula-fd subordinate Bacula File Daemon source
bacula_server_operator/     # Juju charm: bacula-server principal Bacula server source

docs/                       # Product documentation

charmed_bacula_server/      # Snap: charmed-bacula-server workload

terraform/                  # Terraform Juju module

tests/                      # Shared unit and integration tests
```

## Components

This repository contains three Juju charms and one snapped workload:

| Component | Path | Role |
| --- | --- | --- | --- |
| `backup-integrator` | `backup_integrator_operator/` | An integrator charm that requires backup relation on behalf of other charms. |
| `bacula-server` | `bacula_server_operator/` | A machine charm that installs and manages all server components of the Bacula backup solution, including the Bacula Director, Bacula Storage Daemon, and Baculum. |
| `bacula-fd` | `bacula_fd_operator/` | A subordinate charm that installs and manages the Bacula File Daemon, which is the backup agent in the Bacula solution. |
| `charmed-bacula-server` | `charmed_bacula_server/` | A snap containing all server components of the Bacula backup solution, including the Bacula Director, Bacula Storage Daemon, and Baculum. |


### Charmhub and Snapcraft

| Name | Listing |
| --- | --- |
| `backup-integrator` | https://charmhub.io/backup-integrator |
| `bacula-server` | https://charmhub.io/bacula-server |
| `bacula-fd` | https://charmhub.io/bacula-fd |
| `charmed-bacula-server` | https://snapcraft.io/charmed-bacula-server |

## Get started

Start with the in-repository tutorial at [`docs/tutorial.md`](docs/tutorial.md).
It walks through a basic `bacula-server` deployment, including setup,
S3 storage, PostgreSQL integration, Baculum credentials, and cleanup.

## Integrations

See [`docs/reference/integrations.md`](docs/reference/integrations.md). 

## Documentation

Our documentation is stored in the `docs` directory and
can be viewed at https://canonical.com/juju/docs/backup-charms/.
It is based on the Canonical Sphinx Stack and hosted on
[Read the Docs](https://about.readthedocs.com/). In structuring, the
documentation employs the [Diátaxis](https://diataxis.fr/) approach.

You may open a pull request with your documentation changes, or you can
[file a bug](https://github.com/canonical/backup-operators/issues) to
provide constructive feedback or suggestions.

To run the documentation locally before submitting your changes:

```bash
cd docs
make run
```

GitHub runs automatic checks on the documentation to verify spelling,
validate links and style guide compliance.

You can (and should) run the same checks locally:

```bash
make spelling
make linkcheck
make vale
make lint-md
```

## Project and community

The backup operators project is a member of the Ubuntu family. It is an
open source project that welcomes community projects,
contributions, suggestions, fixes, and constructive feedback.

* [Code of conduct](https://ubuntu.com/community/code-of-conduct)
* [Get support](https://discourse.charmhub.io/)
* [Issues](https://github.com/canonical/backup-operators/issues)
* [Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
* [Contributing](https://github.com/canonical/backup-operators/blob/main/CONTRIBUTING.md)

## Licensing and trademark

See [`LICENSE`](LICENSE).
