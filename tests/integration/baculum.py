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

    def run_backup(self, *, name: str) -> list[str]:
        job = self.show_job(name=name)
        payload = {
            "name": name,
            "level": "F",  # Full backup
            "client": job["client"],
            "storage": job["storage"],
            "pool": job["pool"],
            "fileset": job["fileset"],
        }
        response = self._session.post(f"{self._base}/jobs/run", json=payload)
        return self._extract_output(f"run backup '{name}'", response)

    def list_job_runs(self, name: str) -> list[dict]:
        job = self.show_job(name=name)
        params = {
            "name": name,
            "client": job["client"],
        }
        response = self._session.get(f"{self._base}/jobs", params=params)
        return self._extract_output(f"list jobs '{name}'", response)

    def run_restore(
        self,
        *,
        name: str,
        job_id: int,
    ) -> list[str]:
        job = self.show_job(name=name)
        payload = {
            "id": job_id,
            "restorejob": name,
            "client": job["client"],
            "fileset": job["fileset"],
            "where": "/",
            "replace": "always",
            "full": True,
        }
        response = self._session.post(f"{self._base}/jobs/restore", json=payload)
        return self._extract_output(f"restore '{name}' from backup {job_id}", response)

    def list_job_names(self) -> list[str]:
        response = self._session.get(f"{self._base}/jobs/resnames")
        result = self._extract_output("list job names", response)
        return list(result.values())[0]

    def show_job(self, name: str) -> dict:
        params = {"name": name, "output": "json"}
        r = self._session.get(f"{self._base}/jobs/show", params=params)
        return self._extract_output(f"show job '{name}' detail", r)

