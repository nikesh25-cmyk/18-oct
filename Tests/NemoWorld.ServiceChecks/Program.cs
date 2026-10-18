using NemoWorld.Service;

var root = Path.Combine(Path.GetTempPath(), "nemoworld-service-check-" + Guid.NewGuid().ToString("N"));
Directory.CreateDirectory(root);
try
{
    var store = new ArrivalStore(Path.Combine(root, "arrivals.json"));
    var initial = store.Get("fixture-player");
    Check(initial is null, "missing player should have no position");
    var first = store.Set(new ArrivalCommand("fixture-player", "cmd-1", "harr", 1.5, 2, -3));
    Check(first.Status == ArrivalStatus.Accepted, "first command accepted");
    var repeat = store.Set(new ArrivalCommand("fixture-player", "cmd-1", "harr", 1.5, 2, -3));
    Check(repeat.Status == ArrivalStatus.Duplicate && repeat.Position == first.Position, "retry is idempotent");
    var conflict = store.Set(new ArrivalCommand("fixture-player", "cmd-1", "harr", 9, 2, -3));
    Check(conflict.Status == ArrivalStatus.Conflict, "reused command id with changed payload rejected");
    var bad = store.Set(new ArrivalCommand("fixture-player", "cmd-2", "harr", double.NaN, 0, 0));
    Check(bad.Status == ArrivalStatus.Invalid, "nonfinite coordinate rejected");
    var far = store.Set(new ArrivalCommand("fixture-player", "cmd-3", "harr", 1_000_001, 0, 0));
    Check(far.Status == ArrivalStatus.Invalid, "out of bounds coordinate rejected");
    var reopened = new ArrivalStore(Path.Combine(root, "arrivals.json"));
    Check(reopened.Get("fixture-player") == first.Position, "saved position survives restart");
    Check(reopened.Set(new ArrivalCommand("fixture-player", "cmd-1", "harr", 1.5, 2, -3)).Status == ArrivalStatus.Duplicate, "command history survives restart");
    Check(reopened.Get("another-player") is null, "identities do not share positions");
    Console.WriteLine("7 NemoWorld service checks passed");
}
finally { Directory.Delete(root, true); }

static void Check(bool ok, string message) { if (!ok) throw new Exception(message); }
