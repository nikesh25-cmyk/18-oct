using System.Text.Json;

namespace NemoWorld.Service;

public record ArrivalCommand(string PlayerId, string CommandId, string PlaceId, double X, double Y, double Z);
public record WorldPosition(string PlaceId, double X, double Y, double Z);
public enum ArrivalStatus { Accepted, Duplicate, Conflict, Invalid }
public record ArrivalResult(ArrivalStatus Status, WorldPosition? Position);

public sealed class ArrivalStore
{
    private readonly string path;
    private readonly object gate = new();
    private StoreData data;
    private sealed class StoreData
    {
        public Dictionary<string, WorldPosition> Positions { get; set; } = new();
        public Dictionary<string, ArrivalCommand> Commands { get; set; } = new();
    }

    public ArrivalStore(string path)
    {
        this.path = path;
        data = File.Exists(path) ? JsonSerializer.Deserialize<StoreData>(File.ReadAllText(path)) ?? new() : new();
    }

    public WorldPosition? Get(string playerId)
    {
        lock (gate) return data.Positions.GetValueOrDefault(playerId);
    }

    public ArrivalResult Set(ArrivalCommand command)
    {
        lock (gate)
        {
            if (!Valid(command)) return new(ArrivalStatus.Invalid, null);
            var key = command.PlayerId + "\u001f" + command.CommandId;
            if (data.Commands.TryGetValue(key, out var prior))
                return new(prior == command ? ArrivalStatus.Duplicate : ArrivalStatus.Conflict,
                    data.Positions.GetValueOrDefault(command.PlayerId));
            var position = new WorldPosition(command.PlaceId, command.X, command.Y, command.Z);
            data.Commands[key] = command;
            data.Positions[command.PlayerId] = position;
            Persist();
            return new(ArrivalStatus.Accepted, position);
        }
    }

    private static bool Valid(ArrivalCommand c) =>
        !string.IsNullOrWhiteSpace(c.PlayerId) && c.PlayerId.Length <= 128 &&
        !string.IsNullOrWhiteSpace(c.CommandId) && c.CommandId.Length <= 128 &&
        c.PlaceId == "harr" &&
        Within(c.X) && Within(c.Y) && Within(c.Z);

    private static bool Within(double value) => double.IsFinite(value) && Math.Abs(value) <= 1_000_000;

    private void Persist()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        var tmp = path + ".tmp";
        File.WriteAllText(tmp, JsonSerializer.Serialize(data));
        File.Move(tmp, path, true);
    }
}
