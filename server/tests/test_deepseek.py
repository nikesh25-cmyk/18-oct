import unittest

from agent_server.deepseek_provider import DeepSeekProvider, DEMO_GOAL


class DeepSeekProviderTests(unittest.TestCase):
    def test_compares_fetched_sources_with_model(self):
        calls = []

        def fetch(url):
            calls.append(("fetch", url))
            return "Assets included in this package are CC0 licensed."

        def chat(prompt, key):
            calls.append(("chat", prompt, key))
            return "Both starter kits document CC0 assets; test imports separately."

        result = DeepSeekProvider("test-key", fetch=fetch, chat=chat).research(DEMO_GOAL)
        self.assertEqual(len(result.evidence), 2)
        self.assertEqual(len([call for call in calls if call[0] == "fetch"]), 2)
        self.assertIn("CC0 licensed", calls[-1][1])
        self.assertIn(DEMO_GOAL, calls[-1][1])
        self.assertEqual(calls[-1][2], "test-key")
        self.assertIn("CC0", result.report)

    def test_rejects_unrelated_goal_without_relevant_sources(self):
        provider = DeepSeekProvider("test-key", fetch=lambda url: "x",
                                    chat=lambda prompt, key: "answer")
        with self.assertRaises(ValueError):
            provider.research("Research the latest traffic laws")

    def test_missing_key_is_rejected_before_fetching(self):
        provider = DeepSeekProvider("", fetch=lambda url: self.fail("fetched"),
                                    chat=lambda prompt, key: self.fail("called"))
        with self.assertRaises(ValueError):
            provider.research(DEMO_GOAL)


if __name__ == "__main__":
    unittest.main()
