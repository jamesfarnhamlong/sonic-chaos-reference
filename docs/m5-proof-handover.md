# Manager handover — M5-P0/P1 proof: HOLD full production

24 October 2026. Authorized follow-up to accepted M5-R1
`7d700d0f2d51812d48d9743443e688bc1f9c5793`, isolated branch
`research/m5-p0-p1-proof`. **Do not begin P2/P3 or Designer integration.**

The bounded work is complete as a proof/failure report. It does **not** meet
the complete P0/P1 parity gate: scheduling/ownership passes, while fixed-rate
noise composition loses real held PSG output. No new synthesis, arbitrary-phase
fade bank, GameMaker source/assets, full Sound Test or long-track production
was undertaken. Accepted M4 code and PCM remain unchanged.

## Deliverables and conclusions

| Deliverable | Result | Evidence |
|---|---|---|
| PCM-independent dispatcher/ownership model | bounded projection PASS; complete output-state proof HOLD | [driver report](m5-proof-driver.md), [model](../tools/m5p0_model.py), [original comparison tool](../tools/m5p0_proof.py), [counts/failures](../data/m5-proof/p0-result.json) |
| Small P1 solo production | format/determinism/pitch/reconstruction PASS;1 A3 startup duration-proxy FAIL retained | [audio report](m5-proof-audio.md), [safe metrics](../data/m5-proof/p1-library.json) |
| Continuous versus composed controls | composition parity FAIL; held-noise class blocks expansion | [per-class metrics](../data/m5-proof/coupled-noise.json), [diagnostics](../data/m5-proof/diagnostics.json) |
|4096-tick chunks | exact byte/addressing and corruption controls PASS; native performance untested | [chunk/budget report](m5-proof-chunks-budget.md), [chunk receipt](../data/m5-proof/chunk-proof.json) |
| Measured production budget | bounded workload within disk/time limits | [preflight](../data/m5-proof/budget-preflight.json), [measurements](../data/m5-proof/measured-budget.json) |
| Private proof package | ZIP CRC and every member SHA verified; overall HOLD marked inside | [safe hash receipt](../data/m5-proof/private-package-receipt.json); actual private path supplied separately in chat |

P0 predicts all1,369 ordered SFX pairs and the111 additional restart/music/reset
cases without consulting combined oracle traces. It matches111 recovery cases
(159 release/reader facts),4,864 priority selections,192 M4 interruption controls,
four M4 loop controls and15 new extended collision/fade/finite controls. New
regressions also cover Stop during pause and manifest trust/address validation.
The intrinsic event programs come from solo original-driver execution and stay
PRIVATE; this is not an independent note/envelope decoder or hardware proof.

The green projection covers active/suppressed/fixed-noise flags, priority,
tempo/mailbox/fade state and named recovery events. It excludes ordinary
envelope/rest bit4 and full PSG register output. The top-level [gate](../data/m5-proof/gate.json)
therefore says **HOLD**, despite raw projected `p0-result.status=PASS`.

## Blocking finding, not an accepted approximation

B8 at30 then BC at35 leaves original fixed-rate noise sounding at attenuation2
for104 ticks after tone2 effect completion at63. F2 inhibits subsequent noise
writes but does not mute the noise register; envelope completion finally emits
off at167. The candidate selector equates write inhibition with silence and
loses that segment. Its mix-envelope correlation is0.806784; noise-only
correlation0.37463. This is a concrete incorrect emission model, not merely
M4's accepted fresh-oscillator/noise phase limitation.

The failure was investigated from existing captures, with no additional
rendering afterward. Original code paths and a fresh original-driver unit
test establish the held-register cause. A B6 tone1 attenuation-projection tick
remains unresolved; keep it in the next focused diagnostic set. Preserve all
unlike waveforms and large envelope differences, including BA partial replacement,
instead of asserting composition parity because pitch or ownership matches.

P1 produced only the eight requested IDs and one diagnostic-only B8 required
to exercise fixed-rate noise. BF/A6 assets were reused. Four-voice residual
assignment to tone0 reconstructs solo mixes exactly but can add tiny residuals
to an otherwise silent tone0 effect voice; it remains an experiment. No native
listening/audibility acceptance is claimed. The one A3 first-tick gate failure
has measured constant-DC output, not a silently corrected file.

## Recommendation

**HOLD full M5 production and integration.** A reasonable next authorization
is a bounded P0 output/emission-model correction: distinguish suppressed writes,
held PSG registers, explicit off and stream completion; resolve the B6 boundary;
then rerun only the failed fixed-rate/partial-replacement compositions. First
prove register/emission semantics independently of PCM. No new synthesis engine,
giant phase bank or full catalogue render is justified by this result.

Storage is feasible independently of that fidelity blocker. Chunk reconstruction
and4,064 address checks pass. Native cache performance still belongs to a later
Designer assignment, preserving the accepted owner/queue/pause/shutdown machinery.

## Reproduction and preservation

Use the existing M4 NumPy dependency directory and existing pinned renderer.
All private output stays below ignored `build/m5-proof`. From a fresh checkout,
run the P0 proof before any P1 command. On this completed checkout, prefer the
read-only-audio review/tests; do not automatically re-render the failing set.

```powershell
$env:SONIC_CHAOS_ROM = 'PRIVATE_VERIFIED_ROM.sms'
$env:PYTHONPATH = 'EXISTING_M4_NUMPY_DEPENDENCY_DIRECTORY'
python tools/m5p0_proof.py $env:SONIC_CHAOS_ROM
# Only for explicit reproduction of this bounded proof, never bulk production:
$env:AUDIO1B_VGM2WAV = 'EXISTING_PINNED_MAME_vgm2wav.exe'
python tools/m5p1_proof.py $env:SONIC_CHAOS_ROM --m4 PRIVATE_M4_PRODUCTION --poc PRIVATE_ACCEPTED_M4_CHECKOUT
# Existing-payload review: no rendering, no ROM or POC writes:
python tools/m5_proof_review.py
python -m unittest discover -s tests -p test_m5_proof.py -v
python -m unittest discover -s tests -p test_m5_audio_contract.py -v
python -m unittest discover -s tests -p test_m4_audio.py -v
```

The private manifest contains no ROM or renderer binary. Package reference
and failing compositions are labeled, with a FINAL_GATE_HOLD document.
Before/after hashes verify47 M4 preparation/runtime payloads unchanged, and
the accepted POC worktree remains clean. No management document or inherited
R1/M4 evidence file was modified. No Research main merge.

Final unit results: **13 new proof tests +16 inherited M5-R1 +9 inherited M4 =
38 PASS**, zero skips, errors or unit failures with private inputs supplied.
Python compilation and whitespace checks pass. The suite deliberately verifies
the preserved composition FAIL and A3 duration-proxy FAIL;38 passing regressions
are not a green production gate. No broad gameplay suite or native build ran.

Exact added-file inventory, text-file hashes and private archive receipt are
recorded in [verification.json](../data/m5-proof/verification.json). Final commit/remote SHA
and worktree status are supplied after publication. Passing unit tests verify
the recorded successes **and preserved failures**; they do not override HOLD.
