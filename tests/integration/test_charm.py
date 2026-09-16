#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import json
import logging
import time

import jubilant

logger = logging.getLogger(__name__)


def wait_job_complete(baculum, job_name, timeout=300) -> dict:
    """Wait for a bacula job to complete.

    Args:
        baculum: baculum API client.
        job_name: bacula job name.
        timeout: timeout in seconds.

    Returns:
        completed job run object.

    Raises:
        TimeoutError: When timeout is reached.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        job_run = baculum.list_job_runs(job_name)[0]
        logger.info("%s job run status: %s", job_name, job_run)
        if job_run["jobstatus"] == "T":
            return job_run
        time.sleep(1)
    raise TimeoutError(f"Timed out waiting for job '{job_name}' completion")


def select_table(juju) -> str:
    """Select all content from the test postgresql table.

    Args:
        juju: jubilant.Juju object.

    Returns:
        Table content.
    """
    return juju.ssh(
        "ubuntu/0", "sudo -u postgres psql -P pager=off -d ubuntu -c 'SELECT * FROM release;'"
    )


def list_objects(juju: jubilant.Juju, bucket: str) -> list[str]:
    """List all objects in a s3 bucket.

    Args:
        juju: jubilant.Juju object.
        bucket: S3 bucket name.

    Returns:
        List of object names.
    """
    output = juju.ssh(
        "minio/0",
        f"""\
/opt/moto/bin/python - <<'PY'
import boto3
import botocore.config
import json

s3 = boto3.client(
    "s3",
    endpoint_url="http://127.0.0.1:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
    config=botocore.config.Config(s3={{"addressing_style": "path"}}),
)
page = s3.list_objects_v2(Bucket={bucket!r})
print(json.dumps([obj["Key"] for obj in page.get("Contents", [])]))
PY""",
    )
    return json.loads(output)


def test_list_jobs(baculum):
    """
    arrange: deploy and integrate backup charms.
    act: list bacula jobs using baculum API
    assert: bacula-server should have the correct number of jobs
    """
    assert len(baculum.list_job_names()) == 3


def test_client_name(baculum):
    """
    arrange: deploy and integrate backup charms.
    act: get client names using baculum API
    assert: client names should contain the principal charm name.
    """
    clients = baculum.list_clients()
    for client in clients:
        client_name = client["name"]
        if client_name.startswith("relation"):
            assert "ubuntu" in client_name


def test_connect_client(baculum):
    """
    arrange: deploy and integrate backup charms.
    act: get client status using baculum API
    assert: client should show normal status.
    """
    clients = baculum.list_clients()
    assert len(clients) == 2
    for client in clients:
        assert "Daemon started" in baculum.get_client_status(client_id=client["clientid"])


def test_backup_restore_database(juju: jubilant.Juju, baculum):
    """
    arrange: deploy and integrate backup charms.
    arrange: run a backup and restore.
    assert: the backup and restore should work as intended.
    """
    assert "Noble Numbat" in select_table(juju)
    assert len(list_objects(juju, "bacula")) == 0

    backup_job = [j for j in baculum.list_job_names() if j.endswith("-backup")][0]
    logger.info("run backup job: %s", backup_job)
    output = baculum.run_backup_job(name=backup_job)
    logger.info("run backup job output: %s", output)
    backup_job_run = wait_job_complete(baculum, backup_job)
    objects = list_objects(juju, "bacula")
    logger.info("s3 objects: %s", objects)
    assert len(objects) > 1

    output = juju.ssh("ubuntu/0", "sudo -u postgres psql -d ubuntu -c 'TRUNCATE release;'")
    logger.info("truncate database table 'release': %s", output)
    assert "Noble Numbat" not in select_table(juju)

    restore_job = [j for j in baculum.list_job_names() if j.endswith("-restore")][0]
    output = baculum.run_restore_job(name=restore_job, backup_job_id=backup_job_run["jobid"])
    logger.info("run restore job output: %s", output)
    wait_job_complete(baculum, restore_job)
    assert "Noble Numbat" in select_table(juju)
