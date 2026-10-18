# Build plan: mobile world for AI agents that do work

## Product brief and assumptions

Build an original standalone Unity game for phones. The feel is an explorable city with driving and RPG progression. Its main loop is assigning useful work to multiple AI agents and watching meaningful parts of that work happen in the world. The player can inspect sources, results, and failures rather than receiving only a chatbot reply.

Assumptions to validate: initial users are the creator and testers; v1 AI research uses internet access and a server; private prototype comes before a public product; multiplayer is later. The game can open offline, but actual web research cannot complete offline without a separate local model and data source. The MacBook Air M5 with 16 GB RAM is the primary editor; the current cloud machine can host headless services and tests, but has no detected GPU for visual editor work.

The product's brand, original world, characters, gameplay implementation, and AI work loop should be independently created and controlled by the project owner. Third-party tools and assets retain their own licenses. The [asset ledger](asset-ledger.csv) records candidates and evidence; CC0 material is reusable but cannot become exclusive property. Do not include reference screenshots in a shipped build.

## What the first playable version proves

One compact district; walk and drive; two workplaces; three named agents with distinct roles; one research assignment; real source collection through approved tools; visible task progress; a cited result; failure/retry/cancel; save and resume. Avoid city-scale content until this loop is fun and the result is trustworthy.

Example loop: assign "Find three open-license city vehicle packs and compare them." A scout travels to the library, queries allowed sources, and records links. An analyst at an office compares license and platform constraints. A reviewer checks citations and flags unsupported claims. The player sees steps and evidence, can redirect the team, and receives a report with source links. Agent movement is driven by job state, not generated dialogue alone.

## Architecture

```text
Unity mobile client (world, controls, UI, animation, local save)
       | typed commands and state updates
Task API (auth, ownership, budgets, job state, event log)
       | queued jobs
Agent worker (plans, tool calls, validation, summaries)
       | approved search/fetch and chosen AI API
Evidence store (URLs, excerpts, timestamps) + project database
```

- **Unity client:** C#, Universal Render Pipeline, mobile input, scene streaming only when the first district needs it. Render agents from authoritative job events. Use deterministic behaviors for locomotion, interaction, and vehicle handling.
- **Task API:** start with a small Python/FastAPI service and Postgres when a shared/persistent server is needed. A local mock API runs without paid credentials for game development. Choose hosting after measured traffic and storage needs.
- **Agent worker:** a finite job state machine first (`queued`, `planning`, `traveling`, `using_tool`, `reviewing`, `completed`, `failed`, `cancelled`). LLMs choose among typed, permitted actions and write bounded summaries. They cannot directly mutate game state, spend unbounded tokens, or call arbitrary endpoints.
- **Work tools:** begin with one narrow research tool and citation capture. Keep source content and tool errors visible in the job record. Only connect external accounts with explicit permission and scoped credentials.
- **Memory and skills:** store job history, verified findings, player preferences, and reusable actions separately. A skill is a tested action sequence with preconditions and success checks, not merely a prompt.
- **Multiplayer later:** use server-authoritative movement and shared task state only after the single-player loop and mobile performance are proven.

## Build sequence and exit gates

| Phase | Deliverable | Exit gate |
| --- | --- | --- |
| 0. Reference and assets | Replica maps for walking/driving, RPG progression, and work interaction; asset inventory with license evidence; phone performance target | No protected reference assets in project; candidate art passes a small-device scene test |
| 1. Graybox world | One district, third-person movement, enterable workspaces, one drivable vehicle, touch controls, camera | A tester can navigate, drive, park, and enter both spaces on a phone without major control failures |
| 2. Deterministic work loop | Task board, three scripted agents, navigation, workstations, job events, progress UI, cancel/retry | A research assignment visibly completes through all states using a mock provider; save/resume preserves it |
| 3. Real research backend | API, queue, AI provider adapter, approved source tool, evidence store, source-linked report, budget caps | Result cites retrievable sources; unsupported or unavailable evidence is reported as failure; costs and latency are measured |
| 4. Multi-agent coordination | Scout/analyst/reviewer roles, handoffs, shared evidence, conflict resolution, skill unlocks | Two agents contribute different verifiable outputs to one job; cancellation and tool failure do not strand the job |
| 5. Game feel and RPG | Coherent licensed art, vehicles, ambient NPCs, skill progression, audio, polish | Players can explain why traveling and choosing workplaces matter to task success; phone frame time and memory stay within measured targets |
| 6. Private alpha | Onboarding, telemetry with consent, crash reporting, accessibility pass, device matrix, security and cost review | Testers finish the core loop, return for another assignment, and understand when work is genuinely done |
| 7. Public product decision | Pricing/cost model, platform compliance, moderation, account deletion, expanded world/content | Proceed only if retention, trust, performance, and unit economics support it |

## Key design rules

1. A useful completed task must have a verifiable artifact: evidence, a file, a decision record, or a tested in-game result. Movement and animation represent actual state, not pretend work.
2. The player assigns goals and can approve sensitive actions. Agents use explicit capabilities and bounded time, API calls, and spend.
3. Start with asynchronous tasks. A long research job should not freeze the game; the player can drive or assign another task while it runs.
4. Keep generated text separate from world authority. Validate tool outputs, handle malicious web text as data, and retain event logs for debugging.
5. Save scene and task state independently. A dropped connection must not erase agent work or produce a false completion.
6. Profile on a real phone early. Restrict district size, draw calls, textures, NPC count, and background network updates based on measurements rather than desktop appearance.

## Research questions and experiments

- **Does embodied work add value?** Compare a plain report screen with a report plus visible agent workflow. Measure task comprehension, trust, and repeat use.
- **What can agents really do?** Start with web research; test document analysis or coding only after defining safe tools and a visible in-world metaphor.
- **How much autonomy feels good?** Test full automation against player checkpoints before agents commit findings or spend resources.
- **What is the AI cost?** Log tokens, calls, failures, cache hits, latency, and cost per completed useful task. Set caps before adding more agents.
- **Can the world run on phones?** Benchmark controls, frame rate, memory, battery, loading, and connectivity on a target low-end Android and an iPhone.
- **How should skill progression work?** Unlock capabilities based on demonstrated completed tasks, not generated claims of expertise.

## Immediate next actions

1. Choose a concrete public reference game for each flow and run Replica recon, recording screen/flow IDs and evidence. Use the findings for mechanics, not asset copying.
2. Shortlist and license-check coherent Unity-ready city, character, vehicle, UI, and audio packs. Do not import assets with unclear rights.
3. Define one research task and its acceptance criteria, then prototype the entire job state machine with a mock worker before adding an AI API.
4. Create the Unity project on the Mac, measure a graybox district on a phone, and set a performance budget from actual results.
5. Build the first end-to-end research job, then decide whether AI Town, Voyager-style skills, or LangGraph offers enough value to adopt. Use those projects as references; none is required to ship the first slice.

Phase 0 progress: [OpenCity recon](../replica/recon.md) and [feature matrix](../replica/features.csv) are drafted from public documentation/screenshots. Official Kenney starter kits provide a license-documented prototype shortlist for city, vehicle, and character models. Import quality and phone performance have not yet been tested.

Build progress: the repository now contains an original Unity graybox scene generator, a deterministic three-agent demo job, a local research API, and a DeepSeek adapter for one source-bounded asset comparison. Core C# checks and Python backend tests run in the cloud. Unity compilation and phone playtesting still require the Mac; a live DeepSeek request requires the secure key binding and network draft to be activated. The backend is loopback-only, so a hosted authenticated service is still required for live phone jobs.

## Main risks

The hardest work is making real research legible as gameplay, controlling hallucinations and tool permissions, keeping API costs bounded with several agents, and making an appealing 3D world perform on phones. The first playable slice is designed to test those risks before the project commits to a large map or expensive art.
