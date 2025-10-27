# How to use the Baculum web interface

Baculum is the web interface for Bacula. The Bacula server charm manages
and installs Baculum along with other Bacula server components, which
you can access using the URL `http://<bacula-server-ip>:9095/web/`.

## Obtain a Baculum credential

Run the `create-web-user` Juju action on the `bacula-server` charm to
create a new login credential for Baculum. You can choose any username;
in this example, `admin` is used.

```
juju run bacula-server/leader create-web-user username=admin                                          
```

## Navigate the list of connected `bacula-fd` charms

`http://<bacula-server-ip>:9095/web/client/` displays a list of all
Bacula clients that are connected to the Bacula server.

The client named `charm-bacula-fd` is the Bacula file daemon installed
on the Bacula server; it usually serves as a placeholder in
configuration files and has no other use. All clients that start with
`relation-` are `bacula-fd` charms connected to the Bacula server. Each
of their names has the format
`relation-<juju_model_name>-<juju_unit_name>-<partial_juju_model_uuid>-fd`,
which you can use to identify the location of the `bacula-fd` charm.

Clicking the "Details" button in the client list navigates to the client
detail page, where you can click the "Status client" button to verify
the client connection.

## Perform a manual backup

`http://<bacula-server-ip>:9095/web/job/` displays a list of backup and
restore jobs the charm has created for all backup clients.

The naming format is similar to the client name, except that backup jobs
have the `-backup` suffix and restore jobs have the `-restore` suffix.

The Bacula server charm performs backups automatically based on the
schedule configured in each `bacula-fd` charm. To perform an
ad-hoc backup, click the "Details" button for the backup job in the job
list. Then click the "Run job" button on the job details page, and click
the "Run job" button in the popup window. It is advised not to modify
any default settings in the popup window unless you are certain of the
required changes.

## Perform a restore

`http://<bacula-server-ip>:9095/web/restore/` provides the restore
wizard, which is an interactive way of setting up a restoration.

### Step 1 - Select source backup client

Select the backup client that owns the backup you want to
restore from.

### Step 2 - Select backup to restore

Select the version of the backup you want to restore.

### Step 3 - Select files to restore

Select the files you want to restore. It is advised to
select all files in the backup.

### Step 4 - Select destination for restore

Select the destination for the restore. It's important to
change the "Restore to directory:" setting to "/", which restores files
to their original locations. This is required for the backup charm to
function correctly.

### Step 5 - Options for restore

Select the destination client that the files need to be
restored to by choosing the corresponding restore job.

### Step 6 - Finish

Click "Run restore" to start the restoration.
