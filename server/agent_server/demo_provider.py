"""Key-free source example; refuses requests outside its one documented sample."""

from .jobs import Evidence, ResearchResult


DEMO_GOAL = "Compare open-license starter assets for a mobile city game"


class DemoProvider:
    def research(self, goal: str) -> ResearchResult:
        if goal != DEMO_GOAL:
            raise ValueError("Demo mode only supports its sample asset comparison.")
        return ResearchResult(
            report=("DEMO RESULT — no live AI or web research ran. "
                    "Kenney's City Builder and Racing starter kits document CC0 assets. "
                    "Inspect exact files and test Unity import before use."),
            evidence=[
                Evidence("Kenney City Builder", "https://github.com/KenneyNL/Starter-Kit-City-Builder"),
                Evidence("Kenney Racing", "https://github.com/KenneyNL/Starter-Kit-Racing"),
            ],
        )
