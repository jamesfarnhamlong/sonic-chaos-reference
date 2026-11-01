# Sonic Chaos AUDIT-0 — Historical Issue Reconciliation
**Date:** 2026-10-30  
**Purpose:** recover, deduplicate and classify historical defects/observations before any cleanup implementation.

## Evidence basis
- Seven supplied Manager-thread Markdown files.
- **88,359 lines / 1,386 messages / 3,782,434 characters.**
- Current `sonic-chaos-reference` management documents (`AGENTS.md`, `MEMORY.md`, `ROADMAP.md`) at Research `main` **52b68536d656a98eb74b280e8c297eabe6d122ef**.
- Archived `archive/management/planning-20261022-v0.1/FIDELITY_REGISTER.md`.

A dedicated **Manager #4 thread was not supplied**. Exact historical provenance for the user-recalled **KPH end-of-zone mechanic** and **Robotnik-over-black-widescreen-bar** issue was not found in the seven-file corpus. They are therefore marked **SOURCE GAP**, not guessed open/closed.

## Result
After obvious duplicate aliases were removed, AUDIT-0 contains **93 distinct issue records**:

- **CLOSED: 55**
- **CANONICAL / QoL: 14**
- **OPEN: 7**
- **RETEST: 7**
- **DEFERRED: 3**
- **ACTIVE M5: 2**
- **SOURCE GAP: 2**
- **TEST EXCEPTION: 2**
- **INFRASTRUCTURE: 1**

## Important reconciliations
- **Goal exit:** the historical Sonic-running/falling-off-screen behaviour is treated as closed by later state-$20/camera/victory-run work. **Goal-sign centring is not the same issue**: the archived fidelity register keeps it as a known widescreen adapter/QoL question.
- **Canonical oddities:** do not move them into the defect queue just because they look broken. Examples include state `$14` no-air-steering/strip pass-through, strict Special Stage junction behaviour, some loop-entry instability and the Tails frame `$5E` hazard.
- **MGHZ3 staged reveal:** still a real presentation item and intentionally deferred to M6.
- **Slope / rebound / oscillation family:** several observations remain open or require a modern targeted reproduction; they should be treated as a causal family rather than patched individually.
- **M5 audio:** remains the active current milestone. Do not mix audio completion with the later M6 fidelity cleanup.
- **Raw test exceptions:** stay visible and must not be described as green gameplay tests.

## AUDIT-1 recommendation
Do **not** give one agent “fix all bugs.” Use the ledger as a no-code verification queue:

1. **Frontend/results/opening:** KPH, Robotnik/bar draw order, goal framing, title-card widescreen.
2. **Player/contact:** rebound variation, slope sticking/oscillation, SS3 monitor, static/moving spikes.
3. **Zone presentation:** MGHZ3 reveal, AQZ ring animation, priority/layering, remaining breakable presentation.
4. **Canonical/QoL review:** decide explicitly which authentic quirks should remain and which deserve labelled QoL adapters.
5. **Audio:** finish separately under the current M5 authority.

Every AUDIT-1 row should end with one of:
`Verified resolved`, `Still present`, `Partial`, `No code change needed`, `Needs Windows retest`, `Source gap`, or `Superseded`.

Only after AUDIT-1 should we authorize a **batched spot-fix milestone**.