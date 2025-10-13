# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""A simple Baculum API client for testing."""
import typing

import requests


class BaculumApiError(Exception):
    """Baculum API error."""

    def __init__(self, message: str, output: str, errno: int) -> None:
        """Initialize BaculumApiError.

        Args:
            message: error message.
            output: Baculum API output.
            errno: Baculum API error number.
        """
        super().__init__(f"{message}: {output} (error: {errno})")
        self.output = output
        self.errno = errno


class Baculum:
    """Baculum API client."""

    def __init__(self, base_url: str, username: str, password: str, timeout: int = 60):
        """Initialize Baculum API client.

        Args:
            base_url: Baculum API base URL.
            username: Baculum API username.
            password: Baculum API password.
            timeout: Baculum API request timeout.
        """
        self._base = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.timeout = timeout
        self._session.auth = (username, password)
        self._session.headers.update({"Content-Type": "application/json"})

    def _extract_output(self, operation: str, response: requests.Response) -> typing.Any:
        """Extract output from Baculum API response.

        Args:
            operation: Baculum API operation name.
            response: Baculum API response object.
        """
        response.raise_for_status()
        result = response.json()
        output, error = result["output"], result["error"]
        if error:
            raise BaculumApiError(f"failed to {operation}", output, error)
        return output

    def run_backup_job(self, name: str) -> str:
        """Run a full backup job.

        Args:
            name: backup job name.

        Returns:
            Backup job output.
        """
        job = self.get_job(job=name)
        payload = {
            "name": name,
            "level": "F",  # Full backup
            "client": job["client"],
            "storage": job["storage"],
            "pool": job["pool"],
            "fileset": job["fileset"],
        }
        response = self._session.post(f"{self._base}/jobs/run", json=payload)
        return "\n".join(self._extract_output(f"run backup '{name}'", response))

    def run_restore_job(
        self,
        name: str,
        backup_job_id: int,
    ) -> str:
        """Run a restore job.

        Args:
            name: restore job name.
            backup_job_id: backup job run ID to restore.

        Returns:
            Baculum API output.
        """
        job = self.get_job(job=name)
        payload = {
            "id": backup_job_id,
            "restorejob": name,
            "client": job["client"],
            "fileset": job["fileset"],
            "where": "/",
            "replace": "always",
            "full": True,
        }
        response = self._session.post(f"{self._base}/jobs/restore", json=payload)
        return "\n".join(
            self._extract_output(f"restore '{name}' from backup {backup_job_id}", response)
        )

    def list_job_runs(self, name: str) -> list[dict]:
        """List job runs.

        Args:
            name: job name.

        Returns:
            A list of job run objects.
        """
        job = self.get_job(job=name)
        params = {
            "name": name,
            "client": job["client"],
        }
        response = self._session.get(f"{self._base}/jobs", params=params)
        return self._extract_output(f"list jobs '{name}'", response)

    def list_job_names(self) -> list[str]:
        """List job names.

        Returns:
            A list of job names.
        """
        response = self._session.get(f"{self._base}/jobs/resnames")
        result = self._extract_output("list job names", response)
        return list(result.values())[0]

    def get_job(self, job: str) -> dict:
        """Get job details.

        Args:
            job: job name.

        Returns:
            Job details object.
        """
        params = {"name": job, "output": "json"}
        r = self._session.get(f"{self._base}/jobs/show", params=params)
        return self._extract_output(f"show job '{job}' detail", r)

    def list_clients(self) -> list[dict]:
        """List clients.

        Returns:
            A list of client objects.
        """
        response = self._session.get(f"{self._base}/clients")
        return self._extract_output("list clients", response)

    def get_client_status(self, client_id: int) -> str:
        """Get client status.

        Args:
            client_id: client ID.

        Returns:
            Client status.
        """
        response = self._session.get(f"{self._base}/clients/{client_id}/status")
        return "\n".join(self._extract_output(f"get client (id: {client_id}) status", response))
