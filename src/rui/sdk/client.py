"""RUI Python SDK — typed client over the REST API (with optional in-process mode)."""

from __future__ import annotations

from typing import Any, Optional

import httpx


class RUIClient:
    """Synchronous client for RUI."""

    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "RUIClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        r = self._client.get("/health")
        r.raise_for_status()
        return r.json()

    def status(self) -> dict[str, Any]:
        r = self._client.get("/v1/status")
        r.raise_for_status()
        return r.json()

    def start_task(self, task: str, tokens: int = 60000) -> dict[str, Any]:
        r = self._client.post("/v1/tree/start", json={"task": task, "tokens": tokens})
        r.raise_for_status()
        return r.json()

    def spawn(self, parent_id: str, task: str) -> dict[str, Any]:
        r = self._client.post("/v1/tree/spawn", json={"parent_id": parent_id, "task": task})
        r.raise_for_status()
        return r.json()

    def tree(self) -> dict[str, Any]:
        r = self._client.get("/v1/tree")
        r.raise_for_status()
        return r.json()

    def kill(self, node_id: str, reason: str = "sdk") -> dict[str, Any]:
        r = self._client.post(f"/v1/tree/{node_id}/kill", json={"reason": reason})
        r.raise_for_status()
        return r.json()

    def audit(self, limit: int = 50) -> list[dict[str, Any]]:
        r = self._client.get("/v1/audit", params={"limit": limit})
        r.raise_for_status()
        return r.json()

    def constitution(self) -> dict[str, bool]:
        r = self._client.get("/v1/constitution")
        r.raise_for_status()
        return r.json()

    def workflow(
        self,
        goal: str,
        agents: Optional[list[str]] = None,
        budget_tokens: int = 30000,
    ) -> dict[str, Any]:
        payload = {
            "goal": goal,
            "agents": agents or ["planner", "worker", "critic"],
            "budget_tokens": budget_tokens,
        }
        r = self._client.post("/v1/workflows", json=payload)
        r.raise_for_status()
        return r.json()
