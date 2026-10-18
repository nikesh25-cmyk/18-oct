import unittest

from agent_server.demo_provider import DemoProvider


class DemoProviderTests(unittest.TestCase):
    def test_marks_fixed_sample_as_demo(self):
        result = DemoProvider().research(
            "Compare open-license starter assets for a mobile city game")
        self.assertIn("DEMO", result.report)
        self.assertGreaterEqual(len(result.evidence), 2)

    def test_does_not_pretend_to_research_other_goals(self):
        with self.assertRaises(ValueError):
            DemoProvider().research("Find the latest local transit policy")


if __name__ == "__main__":
    unittest.main()
