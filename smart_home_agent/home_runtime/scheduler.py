"""State-backed scheduler for delayed runtime service calls."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .models import utc_now
from .service_registry import ServiceRegistry


class Scheduler:
    def __init__(self, jobs: list[dict[str, Any]], services: ServiceRegistry) -> None:
        self._jobs = jobs
        self._services = services

    def schedule(
        self,
        service: str,
        args: dict[str, Any],
        *,
        delay_seconds: int = 0,
        run_at: str | None = None,
        job_id: str | None = None,
        reason: str = "",
    ) -> dict[str, Any]:
        when = run_at or (datetime.now(timezone.utc) + timedelta(seconds=max(0, delay_seconds))).isoformat(timespec="seconds")
        job = {
            "id": job_id or f"job-{len(self._jobs) + 1:04d}",
            "service": service,
            "args": dict(args or {}),
            "run_at": when,
            "status": "pending",
            "reason": reason,
            "created_at": utc_now(),
        }
        self._jobs.append(job)
        return dict(job)

    def cancel(self, job_id: str) -> bool:
        for job in self._jobs:
            if job.get("id") == job_id and job.get("status") == "pending":
                job["status"] = "canceled"
                job["canceled_at"] = utc_now()
                return True
        return False

    def pending(self) -> list[dict[str, Any]]:
        return [dict(job) for job in self._jobs if job.get("status") == "pending"]

    def run_due(self, context: dict[str, Any], *, now: datetime | None = None) -> list[dict[str, Any]]:
        current = now or datetime.now(timezone.utc)
        executed: list[dict[str, Any]] = []
        for job in self._jobs:
            if job.get("status") != "pending":
                continue
            try:
                due = datetime.fromisoformat(str(job.get("run_at")))
                if due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                job["status"] = "error"
                job["message"] = "invalid run_at"
                continue
            if due > current:
                continue
            result = self._services.call(str(job.get("service")), dict(job.get("args") or {}), context)
            job["status"] = "completed" if result.get("status", "success") == "success" else "error"
            job["executed_at"] = utc_now()
            job["result"] = result
            executed.append(dict(job))
        return executed
