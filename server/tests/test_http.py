import json
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from agent_server.http_api import create_server
from agent_server.jobs import Evidence, JobManager, ResearchResult


class Provider:
    def research(self, goal):
        return ResearchResult("A source-linked report", [Evidence("Source", "https://example.org")])


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server("127.0.0.1", 0, JobManager(Provider()))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(1)

    def request(self, path, method="GET", payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(self.base + path, data=body, method=method,
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=2) as response:
            return response.status, json.load(response)

    def test_create_and_read_job(self):
        status, created = self.request("/jobs", "POST", {"goal": "Compare open city assets"})
        self.assertEqual(status, 201)
        for _ in range(100):
            _, job = self.request("/jobs/" + created["id"])
            if job["status"] == "completed":
                break
            time.sleep(0.01)
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["evidence"][0]["url"], "https://example.org")

    def test_reject_invalid_goal(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/jobs", "POST", {"goal": " "})
        self.assertEqual(error.exception.code, 400)

    def test_health(self):
        status, body = self.request("/health")
        self.assertEqual((status, body), (200, {"ok": True}))


if __name__ == "__main__":
    unittest.main()
