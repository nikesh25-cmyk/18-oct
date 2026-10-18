# NemoWorld Unity M0 Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a repeatable, privacy-safe baseline for the full NemoWorld/Harr to Unity migration.

**Architecture:** A Python standard-library CLI reads the two source Git heads, selected authored manifests, and a private tar archive. It emits counts, IDs, hashes and archive validation without exporting private records. The report feeds the parity ledger and subsequent Unity implementation.

**Tech Stack:** Python 3.9+ standard library, Git, tar, Unity 6 project.

**Spec:** `docs/superpowers/specs/2026-10-18-nemoworld-unity-migration-design.md`

## Global Constraints

- Old Harr installation remains stopped and unmodified.
- Never commit or print account, world, token or other private row data.
- The exact source revisions and archive digest must be recorded.
- Missing, duplicate, malformed or unsupported source material is a failure, not an implicit omission.
- Current source and planned handbook features have different parity status.

## Review Focus

- A tar archive containing `../` or absolute paths must be refused.
- A source manifest with duplicate IDs must fail before producing a parity report.
- A missing required save or manifest must fail with a specific file name.
- A failed command must leave no partial report.
- The public report must contain no private archive file content.

---

### Task 1: Source and archive inventory

**Files:**
- Create: `tools/migration_inventory.py`
- Create: `tests/test_migration_inventory.py`

**Interfaces:**
- CLI: `python3 tools/migration_inventory.py --nemoworld ROOT --veloren ROOT --archive FILE --output FILE`
- Produces a JSON report with `nemoworld_commit`, `veloren_commit`, `archive_sha256`, `archive_members`, `manifests`, and `errors`. No record contents.

- [ ] Step 1: Write failing tests for valid counts, duplicate IDs, missing manifest, unsafe tar member, missing save, and no partial output on failure.
- [ ] Step 2: Run `python3 -m unittest discover -s tests -p 'test_migration_inventory.py' -v`; confirm the expected failures.
- [ ] Step 3: Implement argument validation, Git head reads, manifest counts and duplicate checks, safe tar member checks, SHA-256, and atomic JSON output.
- [ ] Step 4: Run the focused suite, then run the CLI against the pinned 2026-10-18 sources and private archive. Inspect JSON keys and counts only.
- [ ] Step 5: Commit the CLI, tests and public report. Do not commit archive or paths to private records.

### Task 2: Complete parity register

**Files:**
- Create: `docs/migration/parity-ledger.md`
- Modify: `docs/superpowers/specs/2026-10-18-nemoworld-unity-migration-design.md` only if inventory proves a correction.

**Interfaces:**
- Each ledger row has: domain, source revision/file, old status, Unity target, data mapping, acceptance evidence, new status.

- [ ] Step 1: Enumerate implemented source domains and authored manifests from the two pinned checkouts; separate proposed handbook capabilities.
- [ ] Step 2: Map database, saved world, event, content and client-only state; note uncertain mappings explicitly.
- [ ] Step 3: Cross-check the ledger against the spec's ten domains and the source inventory report.
- [ ] Step 4: Commit the ledger as M0 evidence.

### Task 3: M1 kickoff contract

**Files:**
- Create: `docs/superpowers/plans/2026-10-18-m1-unity-city.md`

**Interfaces:**
- Defines Unity content loader and C# service contracts for arrival, view and movement; no account or reward authority in client.

- [ ] Step 1: Choose the exact current city manifests and coordinate conversion rules from pinned source.
- [ ] Step 2: Specify a small saved arrival journey and parity tests against old fixtures.
- [ ] Step 3: Specify performance, GUI and persistence gates before replacing the graybox.
- [ ] Step 4: Commit the M1 plan. Begin implementation only after M0 inventory and ledger are internally consistent.
