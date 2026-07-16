import uuid

import httpx

from nodewatch_agent.config import AgentConfig


class AgentRequestError(Exception):
    def __init__(self, message: str, retryable: bool, authentication_error: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.authentication_error = authentication_error


class AgentClient:
    def __init__(self, config: AgentConfig) -> None:
        self.client = httpx.Client(
            base_url=config.server_url.rstrip("/"),
            headers={"Authorization": f"Bearer {config.agent_token}"},
            timeout=config.request_timeout_seconds,
            verify=config.verify_tls,
            trust_env=False,
        )

    def _post(self, path: str, payload: dict) -> dict:
        try:
            response = self.client.post(path, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            raise AgentRequestError(
                f"服务端返回 HTTP {status_code}",
                retryable=status_code >= 500 or status_code == 429,
                authentication_error=status_code in (401, 403, 409),
            ) from exc
        except httpx.RequestError as exc:
            raise AgentRequestError("无法连接服务端", retryable=True) from exc

    def bootstrap(self, instance_id: uuid.UUID, system_info: dict[str, object]) -> dict:
        return self._post(
            "/api/v1/agent/bootstrap",
            {
                "agent_instance_id": str(instance_id),
                "agent_version": system_info["agent_version"],
                "hostname": system_info["hostname"],
            },
        )

    def send_system_info(self, instance_id: uuid.UUID, system_info: dict[str, object]) -> None:
        self._post(
            "/api/v1/agent/system-info",
            {"agent_instance_id": str(instance_id), **system_info},
        )

    def send_metric(self, metric: dict[str, object]) -> dict:
        return self._post("/api/v1/agent/metrics", metric)

    def send_metrics(self, metrics: list[dict[str, object]]) -> dict:
        return self._post("/api/v1/agent/metrics/batch", {"samples": metrics})

    def close(self) -> None:
        self.client.close()
