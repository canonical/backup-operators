# Deploy the Bacula server charm for the first time

The `bacula-server` charm is the core of the Bacula backup charms. It
comprises all the server components of the Bacula charms. This tutorial
walks you through the steps to deploy a basic Bacula server.

## What you'll need

* A workstation (for example, a laptop) with AMD64 architecture.
* Juju 3 installed. For more information about installing Juju,
  see [Get started with Juju](https://canonical-juju.readthedocs-hosted.com/en/3.6/user/tutorial/).
* A Juju controller bootstrapped to LXD, for example:
  `juju bootstrap localhost tutorial-controller`

[note]
You can get a working setup by using a Multipass VM as outlined in
the [Set up your test environment](https://canonical-juju.readthedocs-hosted.com/en/latest/user/howto/manage-your-deployment/manage-your-deployment-environment/#set-things-up)
guide.
[/note]

## What you'll do

1. Deploy the [Bacula server charm](https://charmhub.io/bacula-server).
2. Deploy and integrate S3 storage.
3. Deploy and integrate a PostgreSQL database.
4. Get admin credentials.
5. Access the Baculum web interface.
6. Clean up the environment.

## Set up the environment

To work inside the Multipass VM, log in with the following command:

```bash
multipass shell my-juju-vm
```

[note]
If you're working locally, you don't need to do this step.
[/note]

To manage resources and separate this tutorial's workload from your
usual work, create a new model on the LXD controller with the following
command:

```
juju add-model bacula-tutorial
```

## Deploy the Bacula server charm

Start by deploying the Bacula server charm. For this tutorial, deploy
the `bacula-server` charm from the edge channel:

```
juju deploy bacula-server --channel edge
```

## Deploy and integrate S3 storage <a name="deploy-and-integrate-s3"></a>

The Bacula server charm requires S3-compatible storage as the backup
destination. For testing, we'll deploy MinIO and use the [
`s3-integrator`](https://charmhub.io/s3-integrator) charm to provide S3
storage.

### Deploy MinIO

We will use Docker to run MinIO. Run the following commands **inside the
Multipass VM** to install Docker and start MinIO.

```
# install docker
sudo apt update && sudo apt install -y docker

# update docker iptables for allowing LXD network traffic
# required after every reboot
# replace lxdbr0 with the actual LXD bridge name if it's not the default
sudo iptables -I DOCKER-USER -i lxdbr0 -j ACCEPT
sudo iptables -I DOCKER-USER -o lxdbr0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# start the minio container
sudo docker run -d --name minio -p 9000:9000 -p 9001:9001 -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin minio/minio server /data --console-address ":9001"

# create the bacula bucket
sudo docker exec minio mkdir -m 777 /data/bacula
```

When everything is set up, you should see output similar to the
following from `juju status`:

```
$ juju status
Model            Controller  Cloud/Region         Version  SLA          Timestamp
bacula-tutorial  lxd         localhost/localhost  3.6.2    unsupported  17:41:40+08:00

App            Version  Status   Scale  Charm          Channel      Rev  Exposed  Message
bacula-server           waiting      1  bacula-server  latest/edge    6  no       waiting for postgresql relation
s3-integrator           blocked      1  s3-integrator  1/stable     145  no       Missing parameters: ['access-key', 'secret-key']

Unit              Workload  Agent  Machine  Public address  Ports  Message
bacula-server/0*  waiting   idle   0        10.212.71.247          waiting for postgresql relation
s3-integrator/0*  blocked   idle   1        10.212.71.44           Missing parameters: ['access-key', 'secret-key']

Machine  State    Address        Inst id        Base          AZ  Message
0        started  10.212.71.247  juju-b6e2bb-0  ubuntu@24.04      Running
1        started  10.212.71.44   juju-b6e2bb-1  ubuntu@22.04      Running
```

The next step is to configure the `s3-integrator` charm. Run the
following commands to configure it. All configuration values are static
except the endpoint, which should be the LXD network gateway address (
this varies depending on your setup). In this example it's
`10.212.71.1`.

```
juju config s3-integrator bucket=bacula endpoint=http://10.212.71.1:9000 s3-uri-style=path
juju run s3-integrator/leader sync-s3-credentials access-key=minioadmin secret-key=minioadmin
```

Now integrate the `bacula-server` charm with the `s3-integrator` charm:

```
juju integrate s3-integrator bacula-server
```

## Deploy and integrate a PostgreSQL database <a name="deploy-and-integrate-database"></a>

The Bacula server charm also requires a PostgreSQL database to store
backup metadata. We'll use the [
`postgresql`](https://charmhub.io/postgresql) charm.

The following commands deploy the `postgresql` charm and integrate it
with the `bacula-server` charm.

```
juju deploy postgresql --channel 14/stable
juju integrate postgresql bacula-server
```

Run `juju status` to see the current status of the deployment. The
output should be similar to the following:

```
Model            Controller  Cloud/Region         Version  SLA          Timestamp
bacula-tutorial  lxd         localhost/localhost  3.6.2    unsupported  18:01:26+08:00

App            Version  Status  Scale  Charm          Channel      Rev  Exposed  Message     
bacula-server           active      1  bacula-server  latest/edge    6  no                                            
postgresql     14.19    active      1  postgresql     14/stable    936  no     
s3-integrator           active      1  s3-integrator  1/stable     145  no     

Unit              Workload  Agent  Machine  Public address  Ports                    Message
bacula-server/0*  active    idle   0        10.212.71.247   9095-9096,9101,9103/tcp                           
postgresql/0*     active    idle   2        10.212.71.237   5432/tcp                 Primary
s3-integrator/0*  active    idle   1        10.212.71.44           

Machine  State    Address        Inst id        Base          AZ  Message
0        started  10.212.71.247  juju-b6e2bb-0  ubuntu@24.04      Running
1        started  10.212.71.44   juju-b6e2bb-1  ubuntu@22.04      Running
2        started  10.212.71.237  juju-b6e2bb-2  ubuntu@22.04      Running
```

## Access the Baculum web interface

To access the Baculum web interface, first create a Baculum web account
by running the `create-web-user` action on the `bacula-server` leader:

```
juju run bacula-server/leader create-web-user username=admin                                          
```

The username and password are shown in the command output, for example:

```
Running operation 3 with 1 task
  - task 4 on unit-bacula-server-0

Waiting for task 4...
password: Waz4TS5Y4lSJDYF_GHAlTQ
username: admin                                                                                                                                                                  
```

If you deployed the test environment on your host machine, you can
directly access Baculum at `http://10.212.71.247:9095/web/` using the
username and password you just created. The IP address may vary in your
deployment.

If you deployed the test environment inside a Multipass VM, use `socat`
to forward external traffic to the `bacula-server` with the following
command:

```
socat TCP-LISTEN:9095,reuseaddr,fork TCP:10.212.71.247:9095
```

Then access Baculum at `http://<multipass-vm-ip>:9095/web/`.
