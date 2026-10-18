# Expanded World Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make NemoWorld's 23-region finite outdoor map navigable in Unity while preserving Harr as a separate saved city preview.

**Architecture:** A deterministic exporter copies region rectangles from the pinned NemoWorld map module into a checked public JSON contract. A Unity atlas scene renders bounded thematic terrain meshes and navigation, with no data writes. Harr's HUD uses package provenance rather than stale hard-coded warnings.

**Tech Stack:** Node.js for source-module export, Python unittest for package contract checks, Unity 6 C# for renderer.

**Spec:** `docs/superpowers/specs/2026-10-18-expanded-world-preview.md`

## Global Constraints

- NemoWorld source HEAD `f982347e0ab217fe8ca3476f53b1db1349d79328` remains the baseline.
- All new world geometry is explicitly preview only; private saved records remain untouched.
- Map IDs and rectangles are exact and finite; Harr and frontier coordinate systems are not silently merged.

## Review Focus

- Duplicate or overlapping regions must fail export.
- Bounds must remain 288 × 208; no infinite/invented land.
- GUI Play mode must have a usable initial camera and readable labels.
- 23 region roots must render without per-tile GameObject explosion.
- Harr's 387 saved group count and legacy provenance remain intact.

---

### Task 1: World atlas package

- [x] Write a failing package-contract test for count, bounds, overlap, IDs and source hash.
- [x] Implement source export from the pinned map module, run test green, commit JSON and exporter.

### Task 2: Unity atlas scene

- [x] Add C# package validation and deterministic region rendering with bounded roots.
- [x] Add navigation and on-screen overview; compile in Unity and inspect standalone Mac Play mode.

### Task 3: Harr clarity and release gate

- [x] Replace stale 25-group HUD message with current/legacy provenance counts.
- [x] Recheck both scenes, tests and ledger; commit and push migration branch.
