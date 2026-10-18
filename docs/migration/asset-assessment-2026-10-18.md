# Unity asset assessment — 18 October 2026

## Decision for the two supplied local packages

The files named `ModernCity_HDRP_2021.3.6f1.unitypackage` and `ModernCity_URP_2021.3.6f1.unitypackage` are **Stylized Sci-Fi Modern City** by stylArts/Leartes, not Miami Vice City. Archive inspection found 744 HDRP assets and 739 URP assets. The URP file wraps a second Unity package; it is not an empty or corrupt archive. The archives contain FBX meshes, textures, materials, prefabs, shaders and two example scenes for each pipeline; they contain no C# scripts.

The adjacent `___www.unityassetcollection.com___.txt` identifies a third-party redistribution site as the source. [The publisher lists this as a paid product](https://cosmos.leartesstudios.com/environments/stylized-modern-city). The presence of a file on the Mac does not establish a license to redistribute it in this repository or game. Keep both archives outside the project until a Unity Asset Store or publisher purchase/entitlement is verified. Do not upload either archive or extracted content to GitHub. This is a provenance hold, not a finding that the user lacks a license.

The current Unity 6.0 project uses the Built-in render pipeline (`ProjectSettings/GraphicsSettings.asset` has no custom render pipeline and `Packages/manifest.json` has no URP or HDRP package). Neither supplied package is directly compatible as-is. When licensed, choose **one** target pipeline and import into a disposable Unity 6 copy first. Verify shaders, material conversion, lightmaps, prefab dependencies, editor upgrade and Mac performance before selecting modules for the saved Harr city. The HDRP pack is the more visually ambitious desktop option; URP offers a broader performance range. Pipeline choice needs a project-wide migration, not only an asset import.

The supplied pack is stylized science fiction. It could dress a bounded future district but would not by itself produce realistic GTA-level visuals or implement the NemoWorld mission, residents, persistence or economy. The existing authored world coordinates and service authority must remain intact.

## Imported now

Five models were fetched from [Poly Haven](https://polyhaven.com/license), whose asset files are CC0, through its official API and download host at 1K resolution. `Assets/Resources/Visual/SOURCES.json` records exact URLs and hashes. Harr now uses urban facade modules on selected saved buildings, factory facade modules on the workshop hall, and bench, planter and crate models in place of selected proxy props. All are visual interpretations; source group IDs, coordinates, and authoritative state remain unchanged. This remains a preview rather than a finished art pass.

## Candidate packages researched

| Package | Possible role | Current decision |
| --- | --- | --- |
| [Miami Vice City](https://cosmos.leartesstudios.com/environments/miami-vice-city) | Coastal street art for a future Harr district | Separate paid product; no verified local copy or entitlement. |
| [EasyRoads3D Pro](https://marketplace.unity.com/packages/tools/terrain/easyroads3d-pro-v3-469) | Road authoring after real Unity terrain and road layout exist | Candidate; verify entitlement and test in a separate project. |
| [DreamOS](https://michsky.com/portfolio/dreamos-modern-os-ui/) | Optional in-world computer interface | Candidate for later interaction design; not a world art solution. |
| [Face Analyzer](https://assetstore.unity.com/listing?f-ec_category=add-ons) | Facial/demographic inference | Exclude from current art and mission scope. |
| [Flora](https://assetstore.unity.com/packages/tools/terrain/flora-323661) | Vegetation placement | Hold until render pipeline and performance budget are settled. |
| [Industrial Factory](https://marketplace.unity.com/packages/3d/environments/industrial/industrial-factory-factory-warehouse-industrial-factory-modular--370044) | Workshop/factory district art | Candidate with verified license; current factory facade is CC0. |
| [Real Landscapes: Valley Forest](https://assetstore.unity.com/packages/3d/environments/landscapes/real-landscapes-valley-forest-194338) | Forest biome art | Candidate with verified license; evaluate scale, shading and performance. |
| [City Action TPS](https://assetstore.unity.com/packages/templates/packs/city-action-tps-game-kit-for-mobile-pc-311519) | Study third-person/vehicle implementation | Candidate for a licensed, isolated study; do not replace NemoWorld world and mission authority with kit logic. |

The previously supplied `incern.org` pages point to third-party downloads of paid packs. They are reference leads only, not approved asset sources. Obtain paid packages from the official publisher or Unity Asset Store and record each entitlement before integration.
