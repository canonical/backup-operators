# Integrations

## Bacula server charm

Following are integrations for the Bacula server charm.

### `bacula-dir`

*Interface*: `bacula_dir`    
*Supported charms*: [`bacula-fd`](https://charmhub.io/bacula-fd)

The `bacula-dir` relation connects the `bacula-server` charm and the
`bacula-fd` charm to exchange `backup-dir` and `bacula-fd` information.

Example `bacula-dir` integration command:

```
juju integrate bacula-server bacula-fd:bacula-dir
```

### `postgresql`

*Interface*: `postgresql_client`    
*Supported
charms*: [`postgresql`](https://charmhub.io/postgresql), [`pgbouncer`](https://charmhub.io/pgbouncer)

The `postgresql` relation provides a PostgreSQL database for the Bacula
server to store backup metadata.

Example `postgresql` integration command:

```
juju integrate bacula-server postgresql
```

### `s3`

*Interface*: `s3`    
*Supported charms*: [`s3-integrator`](https://charmhub.io/s3-integrator)

The `s3` relation provides S3-compatible storage for the Bacula server
to store backup files.

Example `s3` integration command:

```
juju integrate bacula-server s3-integrator
```

## Bacula-fd charm

Following are integrations for the Bacula-fd charm.

### `bacula-dir`

*Interface*: `bacula_dir`    
*Supported charms*: [`bacula-server`](https://charmhub.io/bacula-server)

The `bacula-dir` relation connects the `bacula-server` charm and the
`bacula-fd` charm to exchange `backup-dir` and `bacula-fd` information.

Example `bacula-dir` integration command:

```
juju integrate bacula-fd bacula-server:bacula-dir
```

### `backup`

*Interface*: `backup`    
*Supported
charms*: [`backup-integrator`](https://charmhub.io/backup-integrator)

The Bacula-fd charm implements the provider side of the `backup`
relation and uses it to provide backup services.

Example `backup` integration command:

```
juju integrate bacula-fd backup-integrator:backup
```

### `juju-info`

*Interface*: `juju-info`    
*Supported charms*: Any machine charm

The Bacula-fd charm uses the `juju-info` relation to attach itself to a
principal charm.

Example `juju-info` integration command:

```
juju integrate bacula-fd ubuntu:juju-info
```

## Backup integrator charm

Following are integrations for the backup integrator charm.

### `backup`

*Interface*: `backup`    
*Supported charms*: [`bacula-fd`](https://charmhub.io/bacula-fd)

The Backup integrator charm implements the requirer side of the `backup`
relation and uses it to request backup services from providers.

Example `backup` integration command:

```
juju integrate backup-integrator bacula-fd:backup
```

### `juju-info`

*Interface*: `juju-info`    
*Supported charms*: Any machine charm

The Backup integrator charm uses the `juju-info` relation to attach
itself to a principal charm.

Example `juju-info` integration command:

```
juju integrate backup-integrator ubuntu:juju-info
```
