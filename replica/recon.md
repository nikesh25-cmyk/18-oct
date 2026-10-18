# Recon map: OpenCity (desktop Godot prototype)

Scope: walking, driving, entering/exiting vehicles, and traversing a small procedural city. This is a mechanics reference for an original Unity mobile game, not a complete app to copy.

For: a standalone phone game where the player assigns useful work to embodied AI agents.

Date: 2026-10-18

## Sources

| # | Source | URL | Evidence and limit |
| --- | --- | --- | --- |
| 1 | Project README | https://github.com/webgl-games/opencity/blob/main/README.md | Documented controls, systems, project scope, and limitations. |
| 2 | On-foot screenshot | https://github.com/webgl-games/opencity/blob/main/screenshots/walk.png | Visible street, character, HUD, and keyboard hints. |
| 3 | Driving screenshot | https://github.com/webgl-games/opencity/blob/main/screenshots/drive.png | Reference for vehicle camera/HUD; no phone state shown. |
| 4 | Flying screenshot | https://github.com/webgl-games/opencity/blob/main/screenshots/fly.png | Reference for optional vehicle mode. |
| 5 | Asset credits | https://github.com/webgl-games/opencity/blob/main/CREDITS.md | Separates MIT project work from one CC0 third-party character model. |

The inventory below is based on the README and public screenshots. States not shown are marked unobserved. No gameplay session or mobile build was available for this recon.

## Core loop

Walk through a city, enter a nearby vehicle, drive through traffic, exit, and explore again. Our new game's work assignments and RPG progression will extend this loop; OpenCity does not document those systems.

## Screens or modes

| ID | Mode | How to reach | Purpose | Key components | States seen |
| --- | --- | --- | --- | --- | --- |
| S01 | On-foot city | Game start or exit vehicle | Walk, run, jump, find a vehicle | Character, camera, street, pedestrians, contextual HUD | Filled screenshot; near-vehicle prompt documented; empty/error/mobile unobserved |
| S02 | Driving city | Press E near a parked vehicle | Drive, brake, boost, navigate roads | Vehicle, chase camera, speed HUD, traffic | Driving screenshot; boost documented; collision/error/mobile unobserved |
| S03 | Helicopter flight | Enter helicopter at helipad | Fly through world | Helicopter, chase camera, HUD | Flying screenshot; landing/error/mobile unobserved |

## Flows

```text
F01 Walk and drive
    S01 -> S02 -> S01
    documented input count: approach vehicle, E enter, drive, E exit
    edge: no vehicle in range; exiting into blocked space (behavior unobserved)

F02 Walk and fly
    S01 -> S03 -> S01
    documented input count: reach helipad, E enter, fly, E exit
    edge: helicopter unavailable or landing blocked (behavior unobserved)
```

The README describes keyboard controls. These are input steps, not measured mobile tap counts.

## Components

| Component | Variants | States | Modes |
| --- | --- | --- | --- |
| Third-person camera | On foot, vehicle chase | Following controlled object | S01, S02, S03 |
| Context prompt | Enter, exit | Shown near vehicle; absent otherwise | S01, S02, S03 |
| Speed/state HUD | On foot, vehicle speed, boost | Normal, boosting | S01, S02, S03 |
| City block | Roads, sidewalks, buildings, props | Day scene shown | All |
| Ambient actor | Traffic car, pedestrian | Moving; reactions not directly observed | All |

## Inferred data model

```text
PlayerState  position, active_vehicle, movement_mode
             evidence: README controls and on-foot/driving screenshots
             confidence: medium
Vehicle      kind, position, speed, occupied, boosting
             evidence: README vehicle and control descriptions
             confidence: medium
CityBlock    road_segments, sidewalks, buildings, props
             evidence: README procedural city description and screenshots
             confidence: medium
```

These are conceptual game-state entities, not claims about OpenCity's storage schema.

## Feature matrix

See `features.csv`. Must: 7; should: 5; could: 2; skip: 2. Rows describe our target product; the `original` column records whether OpenCity documents that feature.

## Out of scope from the reference

- OpenCity's name, exact map/layout, screenshots, and art are reference material, not product identity.
- Helicopter flight is optional for the new product.
- GTA and San Andreas game data are not sources for product assets.

## Size

Documented modes: 3. Documented flows: 2. Conceptual entities: 3. Hard parts for our adaptation: touch controls, phone performance, and agent work visualization. Reference slice size: M. Full proposed product: XL, so implementation proceeds in independently testable phases.
