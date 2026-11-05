# Sonic Chaos — S3 Boss Rush Zone Development Sprint
**5 November 2026 · Manager-san #10 · CHIEF-CONFIRMED ARENA-REUSE DESIGN · ONE SUBSTANTIAL DEVELOPMENT SPRINT GO**

## Binding Chief design
Chief prefers a **new Electric Egg-inspired themed Boss Rush Zone** instead of a standalone list of arena fights. Use **the existing original six boss arenas in full**: do NOT rebuild fight geometry, move spawn triggers, alter boss attack state machines, change camera locks, reorder mechanic phases, or reshape hazards to fit a new map. Adapt only the **environment palette/presentation** into an Electric Egg-inspired look. Compose **short interstitial paths, preferably borrowed from existing original zone chunks**, and join six encounters with title cards/transitions modeled on SMS1's Boss Mode. Nominal rings available; possible **no new rings between encounters 5 and 6**. The intention is six fights that feel like one compact bonus zone, **not one huge GameMaker room**.

**Chief's exact clarification (5 Nov):** “use the existing arenas, change the palette so that camera rules, transitions and mechs stay the same - we'd only need to build the interstitial parts (And we could just take chunks from their zones)”. This overrides any earlier speculation that Designer should reconstruct every arena in EEZ style.

## Safe source and accepted ancestry
- Chief-accepted Enhanced S2 local source: `0809ef9cbc9ea9c1fda3bc0ead45aa9aa749a5a7` on `enhancement/s2-data-select-20261105`; Chief tested Sonic/Tails zones, save persistence, two Sonic Emeralds, slot wipe, all controls, intact Classic. **Verify this exact local commit and H: source/Git recovery before branching**; private GitHub remote may not have local S2.
- Accepted S1 Enhanced display: `56c767e8b4f0f73c41f2d8ec41ca471d7a90e746`; S1 Sharp/Integer/CRT all default OFF; final product defaults deferred. Preserve both archives.
- Frozen original Classic private tag `classic-core-20261105` points to `3a58912659b48573ac7f2c5c96a02a2211d5e4da`; never mutate/retag/overwrite; Classic and ordinary Enhanced saved campaigns must behave as before. No automatic merge, remote push or public assets.

## S3 deliverable
One clearly entered **Enhanced-only Boss Rush Zone** with six coherent short playable segments and preserved boss arenas in canonical order:

| Encounter | Source arena to retain | New work permitted |
|---|---|---|
| 1 | THZ3 | Short themed entry, palette skin, transition/title card |
| 2 | GPZ3 | Interstitial chunk, palette skin, transition/title card |
| 3 | SEZ3 | Interstitial chunk, palette skin, transition/title card |
| 4 | MGHZ3 | Interstitial chunk, palette skin; keep original spike-gated reveal |
| 5 | AQZ3 | Interstitial chunk, palette skin; preserve water/terrain/hazards |
| 6 | EEZ3 | Short final approach, same final arena and authentic end-fight state chain |

Use original camera boundaries and original boss-position coordinates **within each encounter**. Designer can implement distinct internal GameMaker rooms (likely simpler for room-based `chaos_is_*` routing) that are presented as a single new zone, or safe controlled reuse of the original arena rooms under a challenge-session guard. A separate transition/connector room is acceptable **if it preserves absolute arena coordinates** and gives the player a coherent handoff. **Do not demand single-room world-space continuity at the expense of exact boss behaviour.**

## Workstream A — Proven arena extraction without rebuilding
1. Map each original Act3 arena's actual source layout, trigger approach, object registrations, tile/collision flags, camera locks, terrain flags and transitions. The accepted boss scripts are notably **room-specific** and may use absolute X/Y conditions. Do not infer that a different room name will satisfy original `chaos_is_*` gating.
2. Preserve and run **the existing boss arenas**, with their original coordinate basis and exact collision metadata. Ideally retain only the minimal approach and original camera/trigger corridor leading to each boss, but any shortened segment must leave all boss prerequisites intact. Use guarded arena-context selectors only if a new room otherwise breaks canonical dispatch. Do **not** transplant sprites and hand-craft approximate boss rooms.
3. Conduct an internal focused feasibility proof before constructing all six connector paths: first THZ3 and one coordinate-sensitive encounter, then test MGHZ3 spike/tree reveal, AQZ3 water and EEZ3 ending. A routine proof build belongs inside S3, not a new Chief-facing micro-candidate.

## Workstream B — Unified Electric Egg-inspired presentation
- Stage background and environmental tiles may receive a **challenge-only Electric Egg palette or new privately duplicated palette-safe tile presentation**, using the source game's existing assets. Keep original terrain/collision flags, water volumes, actual boss sprite animation/state palettes, pickups and hazards intact. If full EEZ palette makes spikes, waterline or another effect misleading, give that effect an explicit contrast-safe fallback.
- Reuse existing original scenery/tile chunks for short interstitial passages; keep them traversable, short and varied enough to feel intentionally connected. This is **where new level design goes**, not inside original arenas. Avoid original unrelated enemies and gimmicks unless their low-risk use improves the connectors.
- Use existing stage-title card/fades and camera transition conventions wherever possible. Maintain original PC Wide 348×196, Retro 290×218 and controlled SMS256 reference, S1 integer display renderer and pause/results/death lifecycle.

## Workstream C — Challenge session and balance
- Clearly expose Boss Rush as an **additional Enhanced-only challenge entry** accessible without hacking a save file, while preserving the five-card Sonic 3-style Data Select layout and title-to-saved-campaign flow. A separate accessible Boss Rush option near/after the Enhanced title is preferable to modifying the five save slots into a sixth slot. Routine sensible menu placement delegated; if a truly intrusive frontend redesign is required, stop with one substantive proposal.
- **Three lives**, **no continues**, no save-state checkpoints and ring placement purposely scarce are **working challenge-balance defaults** modeled on Chief's SMS1 reference. Allow three lives for either character in challenge, regardless of their regular starting lives. Do not silently persist any ongoing challenge state into S2 save JSON. Present one consistent way to restart challenge and return to title after game over or clear.
- Limited rings before the early bosses, **no new rings placed between boss 5 (AQZ3) and boss 6 (EEZ3)** as Chief suggested; test that carry-over of any existing rings and native 100-ring life/SS triggers cannot create an unintended bypass. Do not alter general ring/scatter/extra-life/Special Stage logic to fix challenge routing: use guarded challenge-only entry eligibility if essential.
- Both Sonic and Tails should be playable using native movement/attacks. The normal final EEZ boss has character/Emerald-dependent behaviour. **Before finalizing** investigate the exact Sonic all-5 Emerald path versus zero-emerald/partial path, and Tails original route. A full Sonic EEZ boss is a plausible Boss Rush highlight, but **must be achieved without altering S2 save ownership/earned Emerald state**; if safe temporary challenge-only eligibility is unavailable, retain actual canonical route and explicitly disclose the difference rather than fabricate an all-fight promise. Ask Chief only if this is a materially different gameplay experience choice.
- No ordinary campaign completion, zone frontier, slot wipe, S2 Emerald claim, sixth Emerald or ending record may be changed by challenge participation. Challenge result/clear may be displayed in memory only; a new persistent Boss Rush record is **not** necessary for S3 and should not complicate the S2 save schema. Keep original native audio driver/sound effect flow and separate challenge ownership.

## Workstream D — S3 integrated verification and one Chief acceptance
- During development run targeted source-host and native tests at real original camera/collision coordinates. Compare each fight's starting map/actors, boss state changes, damage/recoil, projectile/hazard trajectories, boss defeat timing, camera locks/unlocks, pause/results/death transitions and relevant audio requests with accepted S2 in the original unmodified arena, noting the new environmental palette difference. Preserve MGHZ3 spike gate and no premature boss reveal.
- Test all six encounters for both characters using genuine scripted boss entries and controlled deterministic event probes. Confirm healthy path, player death/restart, failed fight, ring carry, forced last-fight transition without new ring stash, final boss exit, return to title and no softlock. Do not claim unrun natural full campaigns.
- Reopen accepted S2 saves and hash snapshot all five save JSON records **before/after a Boss Rush session**; confirm byte-for-byte unchanged, no campaign unlock, no Emerald state write. Check original Classic and ordinary Enhanced S2 flow, saved slots and S1 graphical toggles at least in a focused smoke. No developer level select exposure/new F keys.
- Final private deliverable **one integrated Windows ZIP** + complete source ZIP, exact Git commit/change inventory, S2 and Classic source parity gates, boss arena/camera state comparison logs, original-versus-EEZ palette screenshot pairs, H: independent recovery and SHA-256 receipt, one concise Chief controller/play/listening checklist. Avoid one Chief package per boss or connector. No default display changes, no GPZ3 art bug fix, no Data Select beautification in this sprint.

## Explicit S3 exclusions
- Reconstructed or redesigned boss arenas; altered canonical boss attack patterns, physics, lives outside challenge, ROM source mappings or global viewport rules.
- S2 Data Select six-item visual queue (Tails head/crop, running animation, static TV, thumbnails, Emerald icon palette, character foot alignment); that remains a future **single visual-polish batch**.
- New Super Sonic, advanced CRT/Lola, shared fullscreen settings and Pause Level Select removal (endgame UI polish), ring-scatter QoL, E1 Windows frame pacing, Classic GPZ3 art repair, native audio redesign, Vita port or ROM decomp.

## Sprint operating contract
**One substantial S3 job.** Designer may research, implement, correct routine errors and internally compile/instrument as needed without repeated Manager signoffs. Small guarded challenge-only hooks in original GML may be made on the successor branch if Classic and ordinary Enhanced paths demonstrably remain unchanged, with exact diff inventory and no modification of frozen tags/accepted packages. Stop only if exact arena reuse requires a major original-core rewrite, S2 save-data safety cannot be proven, authentic boss geometry/state changes, or a material product choice is irreducibly ambiguous. Otherwise finish one compiled, integrated, Chief-testable private candidate. This reflects Chief's preference for meaty sprints.

**Status: S3 DESIGN CONFIRMED / GO for implementation from accepted S2 once local provenance verified; no existing S3 Windows build claimed.**
