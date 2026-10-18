"""Bounded, thread-safe research job lifecycle independent of any AI provider."""

from dataclasses import dataclass
from threading import Lock, Thread
from typing import Protocol
from urllib.parse import urlsplit
from uuid import uuid4


@dataclass(frozen=True)
class Evidence:
    title: str
    url: str


@dataclass(frozen=True)
class ResearchResult:
    report: str
    evidence: list[Evidence]


class Provider(Protocol):
    def research(self, goal: str) -> ResearchResult: ...


class JobManager:
    def __init__(self, provider: Provider):
        self._provider = provider
        self._jobs: dict[str, dict] = {}
        self._lock = Lock()

    def start(self, goal: str) -> str:
        goal = goal.strip()
        if not 12 <= len(goal) <= 500:
            raise ValueError("Goal must be 12–500 characters.")
        job_id = uuid4().hex
        with self._lock:
            self._jobs[job_id] = {
                "id": job_id, "goal": goal, "status": "queued",
                "report": "", "evidence": [], "error": "",
            }
        Thread(target=self._run, args=(job_id, goal), daemon=True).start()
        return job_id

    def get(self, job_id: str) -> dict:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            job = self._jobs[job_id]
            return {**job, "evidence": [dict(item) for item in job["evidence"]]}

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            if self._jobs[job_id]["status"] not in ("queued", "researching"):
                return False
            self._jobs[job_id]["status"] = "cancelled"
            return True

    def _run(self, job_id: str, goal: str) -> None:
        with self._lock:
            if self._jobs[job_id]["status"] == "cancelled":
                return
            self._jobs[job_id]["status"] = "researching"
        try:
            result = self._provider.research(goal)
            evidence = self._check_result(result)
        except Exception as exc:
            with self._lock:
                if self._jobs[job_id]["status"] != "cancelled":
                    self._jobs[job_id]["status"] = "failed"
                    self._jobs[job_id]["error"] = str(exc)[:300]
            return
        with self._lock:
            if self._jobs[job_id]["status"] == "cancelled":
                return
            self._jobs[job_id]["report"] = result.report.strip()
            self._jobs[job_id]["evidence"] = evidence
            self._jobs[job_id]["status"] = "completed"

    @staticmethod
    def _check_result(result: ResearchResult) -> list[dict[str, str]]:
        if not result.report.strip() or not result.evidence:
            raise ValueError("The provider returned no report or source evidence.")
        unique = {}
        for item in result.evidence:
            parsed = urlsplit(item.url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username:
                raise ValueError("The provider returned an invalid source URL.")
            unique[item.url] = {"title": item.title[:150], "url": item.url}
        return list(unique.values())
