# NemoWorld Unity M1 City Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the unrelated Agent District graybox with a faithful, data-driven Unity preview of the saved Harr neon city and one persisted arrival journey.

**Architecture:** A deterministic exporter reads the pinned authored manifest plus the saved application record on a protected copy, validates IDs and anchors, and emits a public geometry package. Unity imports the package into chunked static meshes and draws residents from authored roster data. A C# service contract owns player position and actions; the first milestone uses a local disposable fixture, not the private live database.

**Tech Stack:** Python 3.9+ standard library for conversion; Unity 6.0.85f1 C#; .NET 8 for future authoritative service.

**Spec:** `docs/superpowers/specs/2026-10-18-nemoworld-unity-migration-design.md`

## Global Constraints

- The paused old world and private archive remain untouched.
- Preserve source group, resident and place IDs, source hashes and observed applied-state status.
- Distinguish current authored groups from 25 saved older road/light groups; record any geometry without a source op as unresolved rather than inventing it.
- No client button, dialogue or visual effect may produce a mission fact or economic receipt.
- The Unity preview is not parity for accounts, missions, economy or service work.

## Review Focus

- Missing or duplicate group IDs fail export; no partial package.
- An anchor without a saved application record is reported, not placed at an invented coordinate.
- Empty/huge cuboids are bounded; a malformed op cannot allocate excessive Unity objects.
- An old saved group without current source geometry remains in the unresolved list.
- Resize to a small Game view keeps the HUD readable and does not cover the world.

---

### Task 1: Reconciled city package

**Files:** Create `tools/export_harr_city.py`, `Tests/test_export_harr_city.py`, `Assets/StreamingAssets/NemoWorld/harr-city-v1.json`, `docs/migration/city-export-report.json`.

**Interfaces:** `export_city(manifest: Path, world_record: Path) -> dict` returns `{format, origin, groups, unresolved_saved_groups, missing_application_groups}`. Each group has stable `id`, local `anchor`, `ground`, `ops` and source digest. CLI accepts `--manifest --world-record --output --report` and writes atomically.

- [ ] Write tests for exact coordinate conversion, complete current-group coverage, saved orphan reporting, malformed op rejection and atomic failure.
- [ ] Run tests red, implement, run green.
- [ ] Export from the pinned `play/data/city-release-20261018-074622/manifest.json` and saved world record; compare 362 authored and 25 unresolved saved groups.
- [ ] Commit package and report without private player data.

### Task 2: Unity Harr scene preview

**Files:** Create `Assets/Scripts/Harr/CityPackage.cs`, `Assets/Scripts/Harr/HarrCityRenderer.cs`, `Assets/Scripts/Harr/HarrBootstrap.cs`; modify `Assets/Scripts/Game/DistrictBootstrap.cs` to stop auto-creating Agent District when Harr content is selected; add `.meta` files via Unity import.

**Interfaces:** `HarrCityRenderer.Load(TextAsset)` validates package and builds grouped static geometry with bounded counts. One authored group maps to one named Unity root. All source IDs remain inspectable.

- [ ] Add a pure C# package validation test using malformed IDs/ops.
- [ ] Implement importer and chunked rendering. Use deterministic colors from `rgb` and visible placeholders for sprites, labelled as placeholders.
- [ ] Open scene in Unity 6.0.85f1; require Console 0 compile errors and a visible city. Inspect at normal and narrow Game view.
- [ ] Commit with screenshot/evidence note and explicit unsupported systems.

### Task 3: Saved arrival contract

**Files:** Create a focused C# world-state domain and local persistence adapter, plus tests; add a Unity arrival and resume flow.

**Interfaces:** A player position change is accepted only by the local authoritative adapter; subsequent Unity launch reads that saved position. The adapter is replaceable by the C# service in M2.

- [ ] Test write, restart/read, invalid coordinate, repeated command and missing save.
- [ ] Implement small adapter and arrival UI; validate real keyboard navigation in Unity.
- [ ] Record parity gap: fixture persistence is not private database import.
- [ ] Commit.
