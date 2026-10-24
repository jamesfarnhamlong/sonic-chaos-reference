# M5-P1C carrier/context feasibility — Manager handover

**Recommendation: HOLD for an architecture decision.** Exact original-driver emission passes all nine selected controls (1,027 ticks). Finite per-request carriers with attenuation control cannot preserve every required shared-clock history. No full production or GameMaker implementation is recommended.

Authority: direct research parent `210ca93d2672f82ce2dc9a1203b6637f6e1247bc`; management read at `0c495dbe47f0235276437480f847cd6bafd92770`. Accepted POC remains `11bff34356d5f5d979218896dc95fdc4bb265eae`. Original ROM and renderer hashes are in the machine-readable evidence. All scenarios are controlled requests to original Z80 execution, not natural gameplay observations.

## Decisive findings

* **A3 → BC, matched reset entry:** A3 at tick 1, BC at 6. The original and model emit exactly the same writes and physical registers. Tone2 changes while noise is muted during ticks 6–33. The static A3 carrier follows its solo clock through those 28 ticks. At resumption 34 its register values agree but its noise history does not. Noise correlation is 0.999998876 before interruption and 0.055473879 across ticks 34–48; sign disagreement is 48.7075%. RMS is 1660.130 versus 1660.869 LSB. Similar envelope is insufficient evidence of continuous oscillator fidelity. This is a history introduced after matched entry, not an arbitrary initial-entry phase explanation.
* **Finite $88 + AC at 30 + A0 at 35 + seeded fade at 40:** emission remains exact. Fade cancels a stream while its physical noise remains on for eight voice-ticks 40–47. The candidate lacks an authenticated continuing source there. There are also 24 audible tone/source-clock mismatches from 40. Tick 40 original periods are 180/34/55, noise 7, attenuations 3/3/3/4. The diagnostic intentionally exposes missing output; it is not an accepted composition. This is additional to retained generic-fade approximation.
* **B8 fixed noise, B6/BA saved context:** prior P0R corrections are reused, not re-rendered or reclassified as general successes. B8 retains all 104 held ticks. B6 and BA remain context-sensitive to DE11 and data latch. Numeric DE11=0 may update the selected data register; it must not be interpreted as a noise-control command.
* B7 repeated periodic-noise F3, BF→B8→A3 clock change, and F8-off→fresh A3 demonstrate bounded approximations. They do not establish all entry phases or hidden clock histories. Candidates emit no samples after logical explicit-off. Resampler boundary remnants, A3 constant-DC startup and arbitrary-entry phase remain qualified.

No new emission correction was necessary. No previously passing assertion was weakened. No new broad pair scan, long track, phase bank, runtime synthesis or native listening acceptance was performed.

## Review materials

* [Coverage and exact-emission contract](m5-p1c-coverage-emission.md), [runtime policy and alternatives](m5-p1c-runtime-policy.md).
* [Complete per-class PCM measurements](../data/m5-p1c/pcm-feasibility.json): per-voice/full-mix correlation, envelope/RMS, noise spectra, pitch windows, timing, source-compatibility counts, process provenance and preservation checks.
* [Diagnostic segmentation and budget](../data/m5-p1c/diagnostics.json), [private integrity receipt](../data/m5-p1c/private-package-receipt.json).
* Reproduction: `python tools/m5p1c.py plan`, then `python tools/m5p1c.py gate --rom PRIVATE_ROM`; only after PASS, bounded `python tools/m5p1c_pcm.py PRIVATE_ROM`. With existing cache, `--analyze-existing` is prohibited from spawning any renderer. `tools/m5p1c_finalize.py` performs analysis/packaging only. Set the pinned renderer via `AUDIO1B_VGM2WAV`; NumPy and the existing emulator dependencies must be available. All binary paths are local/private and remain under ignored `build/`.

## Preservation and stop

All 47 accepted M4 asset hashes and all three earlier private archive hashes match before/after. Original P0/P1 and P0R failures remain in their original committed files and immutable archives. The only inherited source change adds optional IDs/input/output to the P0R intrinsic exporter; its default behavior is retained. Only $88 was newly exported for this proof. No GameMaker files were modified.

The private package contains continuous references, diagnostic compositions, finite carriers, exact private gate captures and a member-hash manifest. It is a temporary review proof, not a release. Path is reported privately in the task response; its safe hash receipt is public. Detailed port/read timelines and all WAV/VGM remain ignored/private.

Manager must decide whether to accept a larger shared-clock phase approximation, commission bounded oscillator-state architecture research, or restrict future production to explicitly compatible classes. Context enumeration cannot presently establish full M5 fidelity with a small fixed asset bank. **Stopped for Manager review; no P2/P3 or Designer implementation.**
