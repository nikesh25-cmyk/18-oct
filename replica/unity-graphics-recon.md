# Unity visual reference recon for NemoWorld

Date: 2026-10-18. Method: public screenshots, official case studies and documentation only. This is a clean-room review of visible rendering patterns and published workflow; no game files, code or proprietary art were copied.

| Reference | Public evidence | Applicable observation | NemoWorld response |
| --- | --- | --- | --- |
| Unity, *Gallipoli* case study | https://preview-web.hexagon.unity.com/resources/how-blackmill-games-enhanced-visual-fidelity-and-performance-in-gallipoli | Detailed meshes, HDRP, atlas textures and decals contribute to visual density. | The saved Harr cuboids need authored building meshes, façades, trims, decals and set dressing. Texture changes alone cannot remove their blocky silhouette. |
| Unity, terrain demo scenes | https://unity.com/blog/games/experience-the-new-unity-terrain-demo-scenes-for-hdrp-and-urp | Sculpted terrain, layered materials, vegetation and instancing support a convincing large environment. | Replace the atlas's rectangular preview slabs with continuous terrain, biome transitions, water and vegetation, while keeping the 23 saved region IDs and 288 × 208 bounds authoritative. |
| Unity, rapid design with kitbashing | https://unity.com/blog/games/realizing-rapid-conceptual-design-with-kitbashing | Blockout, modular assets, lighting and effects are successive art passes. | Treat the current geometry as a preserved layout/blockout; create a modular NemoWorld kit around it. |
| Unity, 2024 games roundup (*V Rising*) | https://unity.com/blog/2024-unity-games-content-roundup-2024 | A published large-world Unity example uses HDRP and DOTS. | Assess rendering and world streaming against measured Mac hardware and content scale before adopting a pipeline. |

## Current visual state

The October 18 Mac preview opens in Harr and uses verified CC0 Poly Haven asphalt, concrete, metal, HDR sky and street-lamp assets. It preserves 387 saved group positions and source IDs. Other source props are marked visual proxies. The atlas now has generated, textured terrain under the same 23 source region rectangles; it remains a read-only map preview. The visual pass does not claim GTA-class fidelity, a seamless playable world, or migration parity.

## Production gaps exposed by the recon

1. Create a distinct art direction and modular building kit for Harr, then map saved group IDs and placements to meshes without changing authoritative records.
2. Produce a continuous outdoor terrain with biome materials, water, vegetation, road network, lighting and streaming across the source atlas bounds.
3. Replace remaining 3D prop proxies and add animated residents, vehicles, interiors and environmental audio with verified asset rights.
4. Profile the target Mac hardware, choose the render pipeline, and set measured frame-rate, memory and loading budgets before claiming a fidelity target.
5. Connect the Unity client to the authenticated C# authority and import private saved accounts, world state, missions and records before declaring the migration complete.

Asset provenance: https://polyhaven.com/license and `Assets/Resources/Visual/SOURCES.json`. Poly Haven files are CC0; their source hashes are checked by `tools/fetch_visual_assets.py` before import.
