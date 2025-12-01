# Backup operators

This repository contains a collection of operators that handle backups
in the Juju ecosystem. Its goal is to provide an easy-to-use, highly
integrated backup solution for charms in Juju.

This repository contains the source code for the following
backup-related charms:

1. `backup-integrator`: An integrator charm that requires backup
   relation on behalf of other charms.
2. `bacula-server`: A machine charm that installs and manages all server
   components of the Bacula backup solution, including the Bacula
   Director, Bacula Storage Daemon, and Baculum.
3. `bacula-fd`: A subordinate charm that installs and manages the Bacula
   File Daemon, which is the backup agent in the Bacula solution.

The repository also holds the snapped workloads of the aforementioned
charms:

1. `charmed-bacula-server`: A snap containing all server components of
   the Bacula backup solution, including the Bacula Director, Bacula
   Storage Daemon, and Baculum.

## Documentation

Our documentation is stored in the `docs` directory.
It is based on the Canonical starter pack and hosted on 
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
open source project that warmly welcomes community projects,
contributions, suggestions, fixes and constructive feedback.

* [Code of conduct](https://ubuntu.com/community/code-of-conduct)
* [Get support](https://discourse.charmhub.io/)
* [Issues](https://github.com/canonical/backup-operators/issues)
* [Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
* [Contribute](https://github.com/canonical/backup-operators/blob/main/CONTRIBUTING.md)
