# M5-A1L unsent clarification request — Manager review only

**Draft only. No message, issue or permission request has been sent. Chief's explicit approval is required before contact.**

Subject: File-specific licence clarification for a small libvgm PSG evaluation

Hello,

We are evaluating a small Sega PSG backend using `emu/cores/sn76496.c` at commit `a6eed945ecf4e5a25cf82004779c6f7e4fd5c319`. That file explicitly declares BSD-3-Clause. We would retain all applicable notices and contributor attribution.

Our reference integration also uses `emu/Resampler.c`, `emu/Resampler.h`, `emu/logging.c`, `emu/logging.h`, `_stdbool.h`, `common_def.h`, `stdtype.h`, `emu/EmuCores.h`, `emu/EmuHelper.h`, `emu/EmuStructs.h`, `emu/snddef.h`, `emu/cores/sn76496.h` and `emu/cores/sn764intf.h`. We have not established a separate licence governing those exact files. We are not assuming that absent header text means no other licence exists, or that the PSG declaration licenses all of libvgm.

Could you identify the existing applicable licence/grant, its scope and required notices for those files and that revision? If none is currently specified, would the relevant rights holders consider an explicit permissive grant for this narrowly listed set? Please also identify any third-party portions or contributors whose permission is not covered by your response. A versioned licence file or an unambiguous written grant identifying the files/revision would be especially helpful.

We have not distributed a runtime containing the unclear helpers. A separately authored rational resampler has small numerical differences from the reference, so clarification of the exact reference resampler would let us evaluate preserving its sample behavior without assuming rights.

Thank you.

---

Manager decision needed: approve contact, accept the newly measured resampler behavior, or retain HOLD. Do not send this draft automatically. Prefer existing documented permission over asking for a new grant if the maintainer identifies one.
