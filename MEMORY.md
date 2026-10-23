# Sonic Chaos — MEMORY.md

**Management handover | updated 23 October 2026 | Manager-san #5**

This is a **Git-tracked project handover**, not an automatic ChatGPT Memory store. Always read [AGENTS.md](AGENTS.md) for binding team rules, then [ROADMAP.md](ROADMAP.md) for milestones. Read this document from Research `main` even while working on an old isolated topic branch. Historical observations do not grant implementation authority.

## Immediate situation

**Frozen accepted POC:** `jamesfarnhamlong/SonicChaos_POC` branch `poc/q3-p1-world-presentation`, SHA `7476affc6ed7626dabf69b446cdab0c9c3d7492e`. 348×196 Windows acceptance; Sonic 18-act continuous campaign, five Emerald stages, good ending, credits and title passed. Q3 fixed THZ3 wide patrol, SS4 clock seam and authentic SEZ/AQZ/SS4 fragments. Do not modify accepted runtime except through the explicitly commissioned isolated M2 worktree.

**Private M2 Tails Package B:** Chief tested six focused items successfully on 23 Oct: Shift+T highlighted-act launch, underwater gameplay, Rocket→Ring monitor with +10 rings, Spring Shoes, jump feel, Continue. THZ1–3 boss also passed earlier Package A. Package B is not committed or final Windows-accepted. Designer-reported checks: 19 adjacent PASS / 3 inherited raw FAIL, no new IDs, source-only ZIP `SonicChaos_M2_20261023_B_PRIVATE.zip`, SHA-256 `3ee8ed903df63ceedd6de2298df936bd41ef357f1598311c5a48bd64cd5f68a3`. Private path/archive has not been independently opened by Manager.

**New blockers from Chief's B test:**
- AQZ Tails renders as dark red/brown silhouette or “shadow Tails” against normally coloured stage artwork. Chief supplied a screenshot `image(20261023-060154).png`. Exact underwater/above-water palette phase not yet established; avoid guessing. Original AQZ uses zone-specific palettes, underwater replacements and a separate split-IRQ CRAM mechanism.
- Certain spear-like AQZ spikes apparently have no hitbox/damage, but other placements do. Specific tile/position/plane and direction currently unknown. Existing AQZ foundation reports terrain type5 in AQZ1/2, with blocks $3C/$3D; THZ static spikes have approach-specific side/floor/rising behaviour. These facts do **not** prove the observed objects are those tiles or that a general collision subsystem is defective.
- Both observations are **OPEN** and prevent M2 final acceptance. No full natural 18-act Tails campaign should be demanded until the targeted resolution.

**M2-R1 exceptional branch:** Original Tails state $20 selector chooses frame $5E with side-contact bit, mapping pointer $0785 truly resolves to code and malformed tile reads. Forced source harness corrupts display; three arrival-assisted sign routes avoid it, but natural reachability remains unresolved. Manager approved only a strict type2/state20/frame5E **no-draw diagnostic exception**, with original phase/timing/callback retained. A *natural* event blocks final closure. Current B run log not supplied; status **UNVERIFIED**, not zero.

**M2-R2 Research completed:** `research/m2r2-tails-interaction-audit@cd417c16b9e4ae614a3592f5b851a351af786afa`, based on M2-R1 `d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98`. Thirty tests reported PASS, with explicit scope limits; character-difference matrix independently verified Rocket monitor becomes Ring **before** graphics, rewards +10; life monitor portrait changes; Spring Shoes belong to both characters. This Research result validates key Package B changes, not the full M2 milestone.

**M2-R3 AQZ Research:** Investigation brief prepared but user paused its launch to fix AGENTS first. Do not claim it has started or produced results. Work should identify root cause of shadow palette and placement-specific spear spike contacts with original ROM positive/negative controls. Chief intends to attach the screenshot to that research task.

## Project timeline / authority graph

- M0/M1 combined Research: `research/m0-m1-roadmap-tails-frontend@5b7f5a10232f4f6511c3a7b9d9b4deaea5842182`. Authentic Tails mapping census, original character-choice screen, audio readiness. Root current Windows AGENTS had been read during M0; older planning drafts were later superseded by v0.2 on this branch.
- M2-R1 Research: `research/m2r1-tails-frame5e@d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98`. Pointer/forced behaviour proven, natural reachability open.
- M2-R2 Research: `research/m2r2-tails-interaction-audit@cd417c16b9e4ae614a3592f5b851a351af786afa`. Character-difference audit complete, topic branch not merged to Research `main`.
- POC Package A: source ZIP SHA `75efdd127ea38f7b35d16c914859acc22e20e0fafa86e6f80b28581b37f2310b`. Initial THZ movement/flight/animation/death PASS, Shift+T faulty.
- POC Package B: fixed competing room requests and progression index, Rocket monitor icon+reward. Six B focused Windows items PASS, AQZ silhouette/spike observations newly opened. No B commit.
- Research `main` prior to management docs was `b6467ba0ad79fad0937f750083a5261e7ea64e8f`. Management docs may advance main **without** merging Research topic branches. Do not use new main as the source parent for an ongoing isolated M2-R3 branch unless explicitly approved.

## Cautions and outstanding verification

- **Complete feature lifecycle**, not just “eligibility.” The M1/Manager miss was interpreting “Tails cannot use Rocket Shoes” as a dead monitor, when the original converts it to +10-ring Ring monitor. Every character difference must trace art, state, activation, effect, teardown and natural reachability. Manager must reconcile Research+Designer+Chief.
- Use **original-ROM/source vs native Windows** labels. High assertion counts do not substitute for natural F5. No generic jump gravity patch: Designer's bounded source tests matched original tap (~47.1px) and held (~95.8px) jumps, not all natural contacts/frame pacing.
- AQZ palette may be split-waterline stage-specific and differs from static sprite palette. Do not manually recolour or pretend one palette fits all zones.
- AQZ spear-like spikes: identify actual original object/tile and exact placement/approach first, then compare positive and negative ROM outcomes. No new generic physics/collision overhaul without evidence.
- Historical raw failures: `verify_ss5_play.js` camera-X at256 up to2px; `verify_thz3_boss_clear.js:113` obsolete cap; M2 scoped gate adds `verify_u5a_player_presentation.js:149` inherited JSON equality mismatch. Older GPZ sprite-ID and MGHZ timeout retained; not globally green.
- Other open issues include historical spring/Badnik large oscillation (not explained by tiny canonical 1/16px cycle), slope sticking, SS3 invincibility monitor embed, MGHZ3 staged pit/tree entrance, unidentified “SLZ1” priority, breakable fragments in remaining zones, goal pan constraints, state20 lag and atypical width spike phase.

## After the AQZ research

1. Review M2-R3 contract and M2-R2 with Designer's **actual B runtime** and Chief's screenshot/routes; no inferred collisions or static recolours.
2. If warranted, authorise **one tightly focused M2 Package C** with protected six B passes, source-backed palette/hazard corrections and Sonic paired regression.
3. Chief Windows tests C first (early screenshots okay); then authorise natural Tails all-18-act campaign, own ending/credits/title, protected Sonic New Game, and complete per-run `m2-tails-fidelity.jsonl` coverage.
4. If any natural frame5E event occurs, withhold closure and investigate exact route. Without a natural event, scoped acceptance can proceed but the original forced-branch exception remains OPEN.
5. Only after Chief's explicit Windows acceptance: Designer commit single direct child of Q3, verify remote 0/0, create source-only private FINAL archive and receipt; Manager updates root docs.

## Original-game completion sequence

M2 Tails accepted → M3 original title and separate character choice → M4 live audio dispatcher pilot → M5 full authenticated original music/SFX → M6 remaining important original presentation/contact/attract → M7 optional PC QoL/production release → M8 extra modes/ports parked. This is a **plan, not automatic authorisation**. Original title is inherited and currently launches Sonic publicly; Sound Test's five preview files aren't live in-game music.

## Document and archive authority

- **Current coordination:** [AGENTS.md](AGENTS.md), this MEMORY, [ROADMAP.md](ROADMAP.md) on Research `main`.
- **Detailed current topic plans:** [M0/M1 plan](https://github.com/jamesfarnhamlong/sonic-chaos-reference/tree/5b7f5a10232f4f6511c3a7b9d9b4deaea5842182/planning) and [M2-R1 Fidelity register](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98/planning/FIDELITY_REGISTER.md). Topic work is still separate from main.
- **Current character matrix:** [M2-R2](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/cd417c16b9e4ae614a3592f5b851a351af786afa/docs/m2r2-character-interaction-matrix.md).
- **Historical Windows root coordination text:** [archive/management/AGENTS_20261023_WINDOWS_UPLOAD.md](archive/management/AGENTS_20261023_WINDOWS_UPLOAD.md); backup ZIP inventory [here](archive/management/AGENTS_BACKUP_MANIFEST_20261023.md). No archived hash should be used as if it identified the current main AGENTS.

**End of handover.** The next agent should review this state against newly reported Research/Windows results before proposing changes.
