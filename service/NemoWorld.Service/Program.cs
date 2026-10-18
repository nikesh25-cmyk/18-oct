using NemoWorld.Service;

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls("http://127.0.0.1:8776");
var dataPath = Environment.GetEnvironmentVariable("NEMOWORLD_FIXTURE_PATH")
    ?? Path.Combine(AppContext.BaseDirectory, "fixture-arrivals.json");
builder.Services.AddSingleton(new ArrivalStore(dataPath));
var app = builder.Build();
app.MapGet("/health", () => Results.Ok(new { status = "ok", mode = "fixture-only" }));
app.MapGet("/api/v1/players/{playerId}/arrival", (string playerId, ArrivalStore store) =>
    store.Get(playerId) is { } position ? Results.Ok(position) : Results.NotFound());
app.MapPost("/api/v1/arrival", (ArrivalCommand command, ArrivalStore store) =>
{
    var result = store.Set(command);
    return result.Status switch
    {
        ArrivalStatus.Accepted => Results.Ok(result),
        ArrivalStatus.Duplicate => Results.Ok(result),
        ArrivalStatus.Conflict => Results.Conflict(result),
        _ => Results.BadRequest(result)
    };
});
app.Run();
