# DECOMP-1D-R4A - Reconciliation with the accepted Special Stage research

Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. Evidence: the `reconciliation` block of
`data/decomp1d/r4a-object-dispatch-closure.json`. No accepted file is edited or rewritten; this document records how the later R2/R3 statements relate
to the accepted work and which accepted proofs R4A reuses instead of repeating.

Sources read: `reports/special-stages-canonical-audit.md`, `docs/special-stages-{foundation,followup,traversal,powerups,goal-ring,progression}-audit.md`,
`data/rom-cache/special-stages/{implementation-manifest,object-census,followup}.json`, and the R2/R3 documents and evidence.

## 1. The act-3 question: three different statements

| Level | Question | Answer | Basis |
|---|---|---|---|
| Syntactically permitted | does the code allow a stage entry with act index 2? | **yes** | the entry gate `$178F` checks the character byte, the zone (< 6) and the emerald mask; it does not read the act index (accepted SS-A1 entry contract) |
| Reachable under forced state | does a forced entry at act index 2 return to act index 3? | **yes** | accepted progression audit (`$D298 += 1` on return); R2 proposition B; R3 `return_reload` |
| Reachable through original gameplay | can ordinary play enter a stage at act index 2? | **not established; the accepted census says no** | accepted follow-up census: maximum obtainable rings in an act-index-2 act is THZ3 19, GPZ3 19, SEZ3 42, MGHZ3 **83**, AQZ3 14, EEZ3 0; no act reaches 100; `$2A4F` zeroes `D29A` at every act load |

## 2. Discrepancies recorded

| # | Statement | Where | Relation to accepted work | Disposition |
|---|---|---|---|---|
| D1 | "Counterexample to B (normal play): ... collect 100 rings in act 2, finish the special stage, and the return path increments the act to 3" | R2 (`docs/decomp-1d-r2-zone-act-invariants.md`) | The route is the same control flow the accepted work calls *dormant*. R2 treated 100 rings as an unrestricted input (its inherited U6) and labelled the path "normal play" within its own model. The accepted census shows no act-index-2 act can supply 100 rings. | R2's verdict is **not** rewritten. Proposition B stays DISPROVEN as a statement about the syntactic and forced-state model. For original gameplay the accepted census governs: act 3 is dormant. |
| D2 | "100-ring collection (U6) ... free / adversarial" | R3 premise P6 | Consistent with the accepted work only as a modelling premise; R3 never claimed the 100-ring state is attainable, and its controlled harness forces entry. | no change; R3's "natural reachability is not established" stands, and for act 3 the accepted census adds a reason it is not natural |
| D3 | R3 frame-loop evidence lists `$5E6F $5E9A $6695` as computed jumps not followed; its prose names four open jumps (`$314F4 $6972 $6C98 $77EC`) | R3 (`creation.frame_loop`) | internal to the R2/R3 line, not the accepted work | recorded by R4A (section 4.1 of the main document); `$5E6F` is closed there, `$5E9A` and `$6695` stay open |

No discrepancy was found in object types, stage placements or terrain surfaces.

## 3. Agreement that is reused, not re-derived

| R3 item | Accepted proof | Check run by R4A |
|---|---|---|
| placed object types of the five stages (`$10 $26 $2F $31`) | `object-census.json` | R3's list parser on the five stage lists gives the census type counts exactly (`reconciliation.object_universe.all_stage_lists_equal`) |
| stage terrain surfaces | `implementation-manifest.json` `surfaces` (0, 1, 2, 3, 7, 9, 10, 12, 13, 19, 20, 22, 29) | the floor handler of each is the entry of the `$6973` table (`creation.stage_surface_creation`) |
| act-index-2 maximum 83 rings; dormant act 3 | `followup.json` `act_index2_reachability` | cited; the census is an upper bound over its recorded ring sources and is not re-derived |
| no enemies, signs, `$09` rings or hazard objects in any stage | canonical audit headline 7 | consistent with the closure containing no trigger type |

## 4. R3 open conditions: resolved by accepted work, or not

| R3 open condition | Status |
|---|---|
| which types the five stages place | **resolved by accepted work** (reused) |
| act-3 "normal play" counterexample | **reconciled** (section 2, D1) |
| `$314F4 $6972 $77EC $6C98` | **resolved in R4A** (main document) |
| `$5E9A`, `$6695` (not named by R3) | open |
| out-of-domain placement lists and loader records (U1-open, U3) | not resolved by accepted work: the accepted records cover only the five stages' own acts |
| termination of the graphics decompressor | R4B |

## 5. What the POC may rely on

The accepted manifest and audits remain the implementation contract. R4A adds nothing to the contract: none of the four residual dispatchers is reached by a stage layout,
and the act-3 aliasing remains a dormant quirk whose reproduction is optional.
