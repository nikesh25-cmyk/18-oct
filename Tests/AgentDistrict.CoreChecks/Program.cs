using AgentDistrict.Core;

static void Check(bool condition, string message)
{
    if (!condition) throw new Exception(message);
}

var job = new ResearchJob();
Check(job.Status == JobStatus.Idle, "A new job must be idle.");
Check(job.AssignDemoTask(), "Demo task must be assignable once.");
Check(!job.AssignDemoTask(), "An active job must reject duplicate assignment.");
Check(job.Status == JobStatus.Traveling && job.ActiveAgent == AgentRole.Scout,
    "The scout should travel first.");

var seenRoles = new HashSet<AgentRole>();
for (var i = 0; i < 30 && job.Status != JobStatus.Completed; i++)
{
    seenRoles.Add(job.ActiveAgent);
    job.Tick(1f);
}
Check(job.Status == JobStatus.Completed, "The demo job must finish.");
Check(seenRoles.SetEquals(new[] { AgentRole.Scout, AgentRole.Analyst, AgentRole.Reviewer }),
    "All three agents must participate.");
Check(job.Evidence.Count >= 2, "The report must retain at least two evidence links.");
Check(job.Evidence.All(e => Uri.TryCreate(e.Url, UriKind.Absolute, out var uri)
    && uri.Scheme == Uri.UriSchemeHttps), "Evidence links must be HTTPS URLs.");
Check(job.Report.Contains("DEMO", StringComparison.Ordinal),
    "Mock work must be labeled as demo, not presented as live research.");
Check(!job.AssignDemoTask(), "A finished job should require reset before reassignment.");

var cancelled = new ResearchJob();
cancelled.AssignDemoTask();
cancelled.Tick(1f);
Check(cancelled.Cancel(), "An active job must be cancellable.");
cancelled.Tick(99f);
Check(cancelled.Status == JobStatus.Cancelled && cancelled.Evidence.Count == 0,
    "Cancellation must stop progress and prevent a false report.");
Check(cancelled.Reset() && cancelled.Status == JobStatus.Idle,
    "A cancelled job should reset for another assignment.");

Console.WriteLine("Core checks passed: progression, evidence, demo labeling, cancellation, reset.");
