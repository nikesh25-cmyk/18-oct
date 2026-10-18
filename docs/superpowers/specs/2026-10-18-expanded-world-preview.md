# Expanded Unity world preview

Date: 2026-10-18. Owner direction: expand the world and keep working autonomously while preserving everything from NemoWorld. This is an incremental navigable preview, not a parity claim.

## Source and boundary

The pinned NemoWorld `src/global-map.js` has one finite outdoor map: 23 named regions in a 288 × 208 tile extent. Stored positions use a region ID plus local coordinates; global coordinates are derived. Interiors and Harr's Veloren city are separate place systems. The frontier has a separate finite 768 × 768 metre registry. The Unity build must not invent a claim that those coordinate systems are already stitched together.

## Selected design

Keep Harr's 387 saved construction groups in its existing scene. Add a second, read-only Unity World Atlas scene driven by an exported copy of the 23 source rectangles. Each region is a visibly labeled terrain preview, with themed color and simple landmarks; sea/unallocated space remains visibly distinct. Free-flight navigation and an overview map let a person see the entire extent. The scene links back to Harr, but no gateway or player position is persisted until the authoritative service and import mapping are complete. New decorative terrain is marked as generated preview, not saved world geometry.

The atlas's numeric extents and IDs are copied from the pinned source revision, with source hash. Export fails on duplicate IDs, overlaps, out-of-bounds rectangles or incorrect region count. Unity validates the package before rendering. Geometry generation is bounded: one root per region with a small fixed number of meshes, not one object per tile. The current Harr HUD's stale 25-group warning is removed and replaced with accurate provenance.

## Visual direction and limits

Build a clean visual foundation: coherent terrain colors, soft light, readable boundaries and a camera that starts at a useful overview. Detailed assets, weather, animation, HDRP conversion and a photoreal art pipeline are later visual-production tasks. GTA-level quality is an ambition, not a claim supported by generated geometry.

## Acceptance

- Exported atlas matches all 23 source rectangles and 288 × 208 bounds, with a traceable source hash.
- Unity compiles and loads the atlas package; a Mac GUI Play walkthrough shows all regions and movement.
- Harr still loads 387 saved groups and HUD does not report the recovered 25 as unresolved.
- No private data or new land rights are committed or minted by the preview.
