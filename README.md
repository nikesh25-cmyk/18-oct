# NemoWorld Unity migration

## Migration in progress

For migration work, clone `codex/nemoworld-unity-migration` from `nikesh25-cmyk/18-oct`. The earlier `codex/agent-district-prototype` branch contains only the editor demo.

The owner has asked to migrate the complete NemoWorld/Harr product from its Veloren implementation to Unity, preserving accounts, saved world state, missions, residents, history and the peaceful mission. This branch records that work. The existing `Main.unity` Agent District demo remains available as an editor and control prototype; it is **not** NemoWorld parity.

Open `Assets/Scenes/HarrPreview.unity` for the first data-driven city preview. Its package contains 362 current authored Harr groups plus 25 saved groups recovered from pinned historical manifest revision `616a0a868e`, all placed using the saved world record. Unity batch import compiled the earlier 362-group package; the expanded 387-group package still needs a new Unity import and visual Play-mode walkthrough. The desktop editor stopped responding during the prior scene-open check. The preview code renders structural cuboids and cyan placeholders for props; clearing operations, residents, gameplay, private-data import and the Unity-to-C# connection are not implemented yet. Do not use it as a replacement for the paused old world.

The [migration design](docs/superpowers/specs/2026-10-18-nemoworld-unity-migration-design.md), [parity ledger](docs/migration/parity-ledger.md), [source inventory](docs/migration/source-inventory.json), and [city export report](docs/migration/city-export-report.json) state exactly what has been accounted for and what remains. The original installation and a private verified backup are kept outside this repository; no private player data is committed here.

### Local C# arrival fixture

The first .NET 10 service slice is in `service/NemoWorld.Service`. It binds only to `127.0.0.1:8776` and stores **disposable fixture positions**, keyed by player and command ID. It rejects nonfinite/out-of-range coordinates and conflicting command replays. Its JSON file is not the preserved NemoWorld database; authentication, account import, missions and economy are not connected. Never expose this fixture service publicly or use real player identifiers with it.

With .NET 10 installed, run its checks with `dotnet run --project Tests/NemoWorld.ServiceChecks`, or start it with `NEMOWORLD_FIXTURE_PATH=/path/to/disposable/arrivals.json dotnet run --project service/NemoWorld.Service`. The endpoints are `GET /health`, `GET /api/v1/players/{playerId}/arrival`, and `POST /api/v1/arrival` with `{ "playerId": "fixture-player", "commandId": "cmd-1", "placeId": "harr", "x": 1.5, "y": 2, "z": -3 }`.

## Agent District editor demo

An original Unity prototype for a mobile city where AI agents perform work as visible gameplay. The current slice has a small procedural district, walking, a drivable car, three role-based agents, and a scripted research demo. An optional DeepSeek backend can analyze two fetched public sources for one bounded live task; the three-agent handoff is still demo-only.

## Open and play

1. On the Mac, install [Unity Hub](https://unity.com/download). In Hub, install Unity 6.0.85f1 or a newer compatible Unity 6 editor. The editor alone is enough for this Mac first run; Android Build Support and iOS Build Support can be added later when making phone builds.
2. Clone the prototype branch on the Mac with `git clone --branch codex/agent-district-prototype https://github.com/nikesh25-cmyk/18-oct.git`, then run `bash scripts/mac-first-run.sh` from the new `18-oct` folder. The script checks the Mac and editor and opens the project in Unity. Alternatively, use Unity Hub's **Add project from disk** to select that folder.
3. If Unity prompts to upgrade the project to a newer Unity 6 editor, accept. Wait for the first import and for the Console to show no compile errors. Open `Assets/Scenes/Main.unity` and press Play. The world is generated in memory when the scene starts, so the scene file is intentionally nearly empty. The Mac first run was verified with Unity 6.0.85f1.
4. On desktop, use WASD to move, mouse to look, Shift to run, and E to enter or exit the red car. Use the work board at the top right to start the demo task.
5. On a phone, drag on the left side to move or drive and on the right side to look or turn. Use the on-screen car and work board buttons. The prototype is landscape-oriented.

The demo job sends the Scout to the library, then the Analyst and Reviewer to the office. Its two evidence links are fixed sample sources from Kenney repositories. The result prominently says **DEMO** because no live web research has occurred.

The first Mac play session needs no AI key or backend. Install Xcode and platform build modules only when you are ready to make mobile builds.

## Local research backend

From the repository root, start the key-free HTTP demo in another terminal:

```sh
PYTHONPATH=server python3 -m agent_server --provider demo
```

To try the bounded live DeepSeek task, configure `DEEPSEEK_API_KEY` **only in the backend environment**, then run:

```sh
PYTHONPATH=server python3 -m agent_server --provider deepseek
```

The backend listens on `127.0.0.1:8765`; the Unity **TRY LIVE DEEPSEEK TASK** button connects to that local address. It therefore works from the Mac editor, while a phone build uses its own loopback and cannot reach the Mac backend yet. Do not put an AI key into Unity, the repository, or a phone build. A hosted authenticated backend is required for live research on phones.

The live task is currently restricted to comparing the documented Kenney City Builder and Racing starter kits. The backend fetches their public README files, asks DeepSeek to analyze that supplied text, and records the source links. It does not perform open-ended web search or independent fact verification. Other goals fail rather than being answered from unrelated sources.

## Local core checks

With .NET 8 installed:

```sh
dotnet run --project Tests/AgentDistrict.CoreChecks/AgentDistrict.CoreChecks.csproj
```

Run backend checks with:

```sh
PYTHONPATH=server python3 -m unittest discover -s server/tests -v
```

The checks exercise agent handoffs, evidence URLs, demo labeling, cancellation, API routes, and the DeepSeek adapter with fake transport. The Unity scene has also been opened and entered Play mode on a Mac with no Console errors. The live DeepSeek call still requires a backend credential and a separate test.

## Project boundaries

- `Assets/Scripts/Core/` contains engine-independent job rules.
- `Assets/Scripts/Game/` generates and controls the current Unity graybox.
- `server/agent_server/` contains the local job API and optional DeepSeek adapter. It binds to loopback only and is not a production service.
- `replica/` contains reference research and screenshots; these files are **not** game assets and must not ship in a build.
- `docs/asset-ledger.csv` records candidate third-party assets and license evidence. None has been imported into the Unity prototype yet.

See [build plan](docs/build-plan.md) for the next playable milestones.
