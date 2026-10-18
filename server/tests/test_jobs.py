import threading
import time
import unittest

from agent_server.jobs import Evidence, JobManager, ResearchResult


class ImmediateProvider:
    def research(self, goal):
        return ResearchResult(
            report=f"Checked: {goal}",
            evidence=[Evidence("Starter kit", "https://github.com/KenneyNL/Starter-Kit-City-Builder")],
        )


class NoEvidenceProvider:
    def research(self, goal):
        return ResearchResult(report="Unsupported answer", evidence=[])


class WaitingProvider:
    def __init__(self):
        self.entered = threading.Event()
        self.release = threading.Event()

    def research(self, goal):
        self.entered.set()
        self.release.wait(2)
        return ResearchResult("Late answer", [Evidence("Source", "https://example.org")])


def await_terminal(manager, job_id):
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        job = manager.get(job_id)
        if job["status"] in ("completed", "failed", "cancelled"):
            return job
        time.sleep(0.01)
    raise AssertionError("job did not reach a terminal state")


class JobManagerTests(unittest.TestCase):
    def test_finishes_with_https_evidence_links(self):
        manager = JobManager(ImmediateProvider())
        job_id = manager.start("Compare reusable city assets")
        job = await_terminal(manager, job_id)
        self.assertEqual(job["status"], "completed")
        self.assertEqual(len(job["evidence"]), 1)
        self.assertEqual(job["evidence"][0]["url"],
                         "https://github.com/KenneyNL/Starter-Kit-City-Builder")

    def test_rejects_report_without_evidence(self):
        manager = JobManager(NoEvidenceProvider())
        job = await_terminal(manager, manager.start("Find a source for city assets"))
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["report"], "")

    def test_cancelled_job_cannot_be_completed_by_late_provider(self):
        provider = WaitingProvider()
        manager = JobManager(provider)
        job_id = manager.start("Compare reusable city assets")
        self.assertTrue(provider.entered.wait(1))
        self.assertTrue(manager.cancel(job_id))
        provider.release.set()
        time.sleep(0.05)
        job = manager.get(job_id)
        self.assertEqual(job["status"], "cancelled")
        self.assertEqual(job["report"], "")

    def test_rejects_empty_goal(self):
        manager = JobManager(ImmediateProvider())
        with self.assertRaises(ValueError):
            manager.start("  ")


if __name__ == "__main__":
    unittest.main()
