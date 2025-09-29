import requests


class BaculumApiError(Exception):
    def __init__(self, message: str, output: str, errno: int):
        super().__init__(f"{message}: {output} (error: {errno})")
        self.output = output
        self.errno = errno


class Baculum:
    def __init__(self, base_url: str, username: str, password: str, timeout: int = 60):
        self._base = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.timeout = timeout
        self._session.auth = (username, password)
        self._session.headers.update({"Content-Type": "application/json"})

    def _extract_output(self, operation: str, response: requests.Response):
        response.raise_for_status()
        result = response.json()
        output, error = result["output"], result["error"]
        if error:
            raise BaculumApiError(f"failed to {operation}", output, error)
        return output

    def run_backup_job(self, name: str) -> str:
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
        job = self.get_job(job=name)
        params = {
            "name": name,
            "client": job["client"],
        }
        response = self._session.get(f"{self._base}/jobs", params=params)
        return self._extract_output(f"list jobs '{name}'", response)

    def list_job_names(self) -> list[str]:
        response = self._session.get(f"{self._base}/jobs/resnames")
        result = self._extract_output("list job names", response)
        return list(result.values())[0]

    def get_job(self, job: str) -> dict:
        params = {"name": job, "output": "json"}
        r = self._session.get(f"{self._base}/jobs/show", params=params)
        return self._extract_output(f"show job '{job}' detail", r)

    def list_clients(self) -> list[dict]:
        response = self._session.get(f"{self._base}/clients")
        return self._extract_output("list clients", response)

    def get_client_status(self, id: int) -> str:
        response = self._session.get(f"{self._base}/clients/{id}/status")
        return "\n".join(self._extract_output(f"get client (id: {id}) status", response))
