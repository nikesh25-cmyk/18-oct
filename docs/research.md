# Research notes: embodied AI work game

Checked on 18 October 2026. This is a feasibility and reuse survey, not a license clearance for a finished game. Source links point to project repositories and their own documentation.

## The product to learn from these sources

A standalone mobile 3D world with driving and light RPG progression. The player assigns practical work to several AI agents. Agents travel to places, use workstations and tools, coordinate, and return inspectable results. The visible game actions should correspond to real task state; animation must not imply that research occurred when it did not.

The initial release is a private prototype. Public release and fundraising remain possible goals. Assume internet access for AI research tasks; a local offline sandbox can still demonstrate navigation and scripted tasks. A fully offline research assistant is a separate feasibility project.

## Existing work

| Source | Verified contribution | What to learn or reuse | Limit |
| --- | --- | --- | --- |
| [AI Town](https://github.com/a16z-infra/ai-town) | Open source virtual town with persistent shared state, simulation, and AI characters. Root code license is MIT. | Agent scheduling, memory, world state, and how to make activity visible. | Its README describes characters who chat and socialize in a 2D web town. It is not a Unity mobile city or a work execution system. Its README credits external art separately; its MIT code license does not clear every image or sound. |
| [Voyager](https://github.com/MineDojo/Voyager) | MIT-licensed code for a Minecraft agent with a skill library, environment feedback, and self-verification. | Typed reusable skills, observing action results, retry limits, and progression through acquired abilities. | The game integration targets Minecraft; the code is not a Unity NPC controller or a source of GTA-style assets. Minecraft assets are separate. |
| [Unity ML-Agents](https://github.com/Unity-Technologies/ml-agents) | Unity toolkit for training agents, including cooperative multi-agent scenarios. | Later experiments with driving, navigation, or group behavior once deterministic gameplay exists. | Reinforcement learning is not the initial solution for web research, task planning, or LLM tool use. |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Framework for durable, stateful agent workflows, memory, and human intervention. | A candidate for long-running research jobs if plain jobs and state machines prove insufficient. | Adds infrastructure complexity; assess after the first complete job loop. |
| [Veloren](https://github.com/veloren/veloren) | Open-world RPG with characters and skills. README says the project is GPL-3.0. | Reference for progression and activity in a world. | Voxel fantasy look, desktop-first, no city driving. Do not import code or art into Unity without a separate license and compatibility review. |
| [SuperTuxKart](https://github.com/supertuxkart/stk-code) | Android-capable driving game. README identifies GPL code; credits say assets have Creative Commons and other licenses. | Reference for mobile driving controls and performance testing. | Kart racing rather than walking, workplaces, or research tasks. Each proposed asset would need its own license check. |
| [Godot Open RPG](https://github.com/GDQuest/godot-open-rpg) | 2D RPG demo; [credits](https://github.com/GDQuest/godot-open-rpg/blob/main/CREDITS.md) identify several CC0 assets. | Reference for inventory, progression, dialogue structure, and asset provenance. | 2D turn-based game, not a 3D city asset base. |
| [OpenCity](https://github.com/webgl-games/opencity) | MIT-licensed Godot city prototype with walking, driving, traffic, pedestrians, and a procedural city. Its [credits](https://github.com/webgl-games/opencity/blob/main/CREDITS.md) identify a CC0 Quaternius character model. | Closest cleanly licensed reference for the first walk/drive district; useful for Replica recon. | Desktop controls and placeholder geometry; no mobile build, workplaces, RPG, or AI work loop documented. Godot scenes/scripts do not drop into Unity. |
| [San Andreas Unity](https://github.com/GTA-ASM/SanAndreasUnity) | MIT-licensed engine reimplementation; README says it requires an owned GTA installation and original game data. | Evidence that an engine reimplementation and reusable game assets are different things. | Not an asset source for our standalone product. |
| [Kenney City Builder starter kit](https://github.com/KenneyNL/Starter-Kit-City-Builder) | Official Kenney Godot starter kit. README says included 3D models, sprites, and sounds are CC0; repo contains road, pavement, building, and greenery GLB models. | Coherent prototype city asset set that can be evaluated for Unity import. | Small stylized set, not a realistic GTA-like city. Godot scripts are not Unity components. |
| [Kenney Racing starter kit](https://github.com/KenneyNL/Starter-Kit-Racing) | Official Kenney Godot starter kit. README says included 3D models and sounds are CC0; repo contains motorcycle and truck GLB models. | Coherent prototype vehicle asset set. | Arcade racing look and mechanics; no pedestrian city integration. |
| [Kenney 3D Platformer starter kit](https://github.com/KenneyNL/Starter-Kit-3D-Platformer) | Official Kenney Godot starter kit. README says included 3D models and sounds are CC0; repo contains a GLB character. | Prototype player avatar and movement reference. | Platformer design; rig, animation, and city visual fit need review. |

## Decision

OpenCity is the best surveyed **mechanics reference**, but no surveyed game is a sound whole-game base for the stated Unity mobile product. Use Replica to document behavior and UX patterns; implement original game systems. License assets individually and record provenance before import. Start with one coherent city/character/vehicle visual set. A mismatched collection of free assets would make the world feel less convincing than a smaller consistent district.

The three official Kenney starter kits are the strongest verified **prototype asset set** found so far: CC0 models for city blocks, vehicles, and a character, with relatively consistent stylized art. They establish a legal prototype path, not the final visual direction. Their Godot source code remains under MIT terms and would need a separate Unity implementation.

## Research still needed before importing assets

1. Evaluate three city asset sets, two character sets, and two vehicle sets for mobile polygon/texture budgets, rig compatibility, visual coherence, and Unity import quality.
2. Record each exact asset URL, creator, license text/version, attribution, redistribution terms, and whether the asset can be used in a commercial standalone game. Check third-party dependencies separately.
3. Benchmark a sample scene on the target iPhone and Android device. Desktop appearance is insufficient evidence.
4. Recon the chosen reference game's public gameplay flows without copying its code, protected art, names, or map. Candidate references can differ by flow: driving, walking/social interaction, and RPG progression.
