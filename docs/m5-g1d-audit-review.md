# G1-D scoped acceptance and Audio Audit Review — 29 October 2026

**Management decision:** source checkpoint G1-D published at `SonicChaos_POC@029757ad2f4d6d9136eb31a37f1fcba0b32c92e6`; Chief's five supported multi-zone F5 test groups PASS with four OPEN issues. M5 remains OPEN; native Z80 remains opt-in. Original private ZIP unchanged per Designer; Manager did not hash private local archive.

The 29 October local audit `m5-audio-lineage-audit.md` (provided by Chief) was reviewed without reproducing its six local GameMaker runs. Use its actual `experiments/m5-audio-audit/evidence` receipts and private source only locally; do not claim this decision file replicates raw timelines.

## Observed source and effect ledger
- 37 original SFX: 5 observed in recorded natural gameplay (A3/A6/B1/B7/BF), 21 source-wired but not fully natural-path verified, 8 mapped numeric event omissions (A1/A2/A4/A5/A7/AA/B8/BC), 3 original triggers unknown (A8/B2/C1). EEZ intermediary `cp_c.sound=A5/BA` currently not forwarded because adapter only handles sentinel1/2; title/ending/menu fallback coverage partial. Chief's unidentified effect intentionally remains unspecified.
- Driver admission/priority suppression, absent writer, inaudible output and scene router HOLD are distinct statuses; 63 native F2 entries mean playable programmes, NOT complete real-event wiring.
- Original Rocket/Invincibility power timer restoration must use `UpdateMusic` source-derived $189B table at $18BA with original D4A3 gate, DE04/D4A4 ordering, skips and selector rules. Current hardcoded $81 and unconsumed flag are not valid ordinary-zone replacements.

## Measured startup findings (three default / three Z80 short routes)
- 65.66 MiB / 11 M4 PCM stems still loaded in BOTH modes. Reading and MD5 verification ~134–138ms, not the 2–3s black-screen dominant cause.
- Shared A3V init ~2.666–2.941s before level first Draw; 1.697–1.728s from byte-wise policy JSON construction/parsing, ~0.667–0.676s bank/authentication, ~0.302–0.330s policy read/hash. Z80 additional bank/DLL ~0.355–0.371s; CPU context <0.2ms.
- Choice scene intentionally waits 6+29+90 ticks (~2.08s), distinct from synchronous stall. Opening cue first generated samples 1.12–1.56ms after request; absolute scene creation at GameMaker timer 1.00–1.18s; acoustic onset and initial audio-device queue not directly measured. Late opening cue remains OPEN.

## Keep / retire posture
- KEEP Open Sonic SMS-derived gameplay framework and shared A1L PSG owner/60Hz/735 samples/eight queue.
- KEEP M4 PCM title/choice/opening at present; KEEP A3V+policy+C10 for default/F2; KEEP five F2 'P' preview sounds, legacy names and registration until dependency audit resolves them.
- KEEP G1-D opt-in Z80 backend and private authenticated banks. G1-B union banks/policy, G1D diagnostic cases, legacy sample sound resources are **potential later release-package exclusions only**, NOT now approved for deletion.
- NO mass delete, source history rewrite, unverified external MP3 substitution or new CPU architecture. Separate eventual disposable packaging branch must preserve standard F2, F2-P, title, Z80/gameplay, rollback.

## Next gate: G1-E defect correction, not new research
One Designer campaign with two separate internal checkouts: (1) source-equivalent efficient A3V policy text read/hash and staged first-use setup, paired cold default/Z80 measurements and original/PCM/F2 preservation; (2) authentic numeric gameplay SFX and Rocket/Invincibility restore fixes with real room event verification. ONE Chief candidate when both gates complete. Source remains on its own branch and private assets local; no POC main merge or default swap. Agent coordination via GitHub pinned refs and Chief/Manager ONLY, no cross-chat.
