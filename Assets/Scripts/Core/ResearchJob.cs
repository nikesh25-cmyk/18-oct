using System;
using System.Collections.Generic;

namespace AgentDistrict.Core
{
    public enum JobStatus
    {
        Idle,
        Traveling,
        Working,
        Reviewing,
        Completed,
        Failed,
        Cancelled
    }

    public enum AgentRole { Scout, Analyst, Reviewer }

    public sealed class EvidenceRecord
    {
        public string Title { get; }
        public string Url { get; }

        public EvidenceRecord(string title, string url)
        {
            Title = title;
            Url = url;
        }
    }

    // Deterministic demo workflow. It never calls a network service or claims live research.
    public sealed class ResearchJob
    {
        private const float PhaseSeconds = 2.5f;
        private readonly List<EvidenceRecord> _evidence = new List<EvidenceRecord>();
        private readonly List<string> _events = new List<string>();
        private int _phase;
        private float _phaseElapsed;

        public JobStatus Status { get; private set; } = JobStatus.Idle;
        public AgentRole ActiveAgent => _phase < 2 ? AgentRole.Scout
            : _phase < 4 ? AgentRole.Analyst : AgentRole.Reviewer;
        public int Phase => _phase;
        public float PhaseProgress => Math.Min(1f, _phaseElapsed / PhaseSeconds);
        public IReadOnlyList<EvidenceRecord> Evidence => _evidence;
        public IReadOnlyList<string> Events => _events;
        public string Goal { get; private set; } = string.Empty;
        public string Report { get; private set; } = string.Empty;

        public bool AssignDemoTask()
        {
            if (Status != JobStatus.Idle) return false;
            Goal = "Compare open-license starter assets for a mobile city game";
            _phase = 0;
            _phaseElapsed = 0f;
            Status = JobStatus.Traveling;
            _events.Add("Scout is heading to the library.");
            return true;
        }

        public void Tick(float seconds)
        {
            if (seconds <= 0f || Status == JobStatus.Idle || Status == JobStatus.Cancelled
                || Status == JobStatus.Completed || Status == JobStatus.Failed) return;

            while (seconds > 0f && Status != JobStatus.Completed)
            {
                var remaining = PhaseSeconds - _phaseElapsed;
                var step = Math.Min(seconds, remaining);
                _phaseElapsed += step;
                seconds -= step;
                if (_phaseElapsed < PhaseSeconds) break;
                CompletePhase();
                _phaseElapsed = 0f;
            }
        }

        private void CompletePhase()
        {
            switch (_phase)
            {
                case 0:
                    Status = JobStatus.Working;
                    _events.Add("Scout arrived and is checking documented sources.");
                    break;
                case 1:
                    _evidence.Add(new EvidenceRecord("Kenney City Builder starter kit",
                        "https://github.com/KenneyNL/Starter-Kit-City-Builder"));
                    _evidence.Add(new EvidenceRecord("Kenney Racing starter kit",
                        "https://github.com/KenneyNL/Starter-Kit-Racing"));
                    Status = JobStatus.Traveling;
                    _events.Add("Scout saved two demo sources; Analyst is heading to the office.");
                    break;
                case 2:
                    Status = JobStatus.Working;
                    _events.Add("Analyst arrived and is comparing the demo sources.");
                    break;
                case 3:
                    Status = JobStatus.Traveling;
                    _events.Add("Analyst finished; Reviewer is heading to the office.");
                    break;
                case 4:
                    Status = JobStatus.Reviewing;
                    _events.Add("Reviewer arrived and is checking the report.");
                    break;
                case 5:
                    Report = "DEMO RESULT — no live AI or web research ran. "
                        + "The Kenney City Builder and Racing starter kits are documented as "
                        + "including CC0 assets. Verify each file and test Unity import before use.";
                    Status = JobStatus.Completed;
                    _events.Add("Demo report completed with source links.");
                    break;
            }
            if (Status != JobStatus.Completed) _phase++;
        }

        public bool Cancel()
        {
            if (Status != JobStatus.Traveling && Status != JobStatus.Working
                && Status != JobStatus.Reviewing) return false;
            Status = JobStatus.Cancelled;
            _events.Add("Task cancelled. No report was produced.");
            return true;
        }

        public bool Reset()
        {
            if (Status != JobStatus.Completed && Status != JobStatus.Cancelled
                && Status != JobStatus.Failed) return false;
            Status = JobStatus.Idle;
            Goal = string.Empty;
            Report = string.Empty;
            _phase = 0;
            _phaseElapsed = 0f;
            _events.Clear();
            _evidence.Clear();
            return true;
        }
    }
}
