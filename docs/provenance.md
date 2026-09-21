# Provenance and evidence

## Sources

- **Original game:** Sonic Chaos, Master System. All engine behavior here is tied to the supplied ROM hash below. “SMS 1.2” is the revision name used in the supplied offset notes; the hash is the authoritative identifier for the tools.
- **Partial disassembly:** RF / Ravenfreak / Amber Davis, as credited in `SonicChaos.asm` and `Sonic Chaos.txt`. The supplied notes also credit Hivebrain. This research continues from that material; it does not claim authorship of the original disassembly or game code.
- **Earlier local continuation:** [`SonicChaos_Disassembly_Continuation_01`](../archive/continuation-01/README.md), which recovered springs, loops, moving platforms, and twist entry/dispatch. Its complete 22-file package, including `verification.json`, is archived unmodified in [`archive/continuation-01/`](../archive/continuation-01/).
- **Navigation aid:** [Sonic Retro's Sonic 2 SMS disassembly](https://github.com/sonicretro/s2smsdisasm). Similarity helped locate concepts, but Chaos addresses and behavior were checked against Chaos bytes.
- **User evidence:** original-game map/video, prototype bug reports, and the supplied sound offset list. Visual evidence motivates tests; it does not replace ROM evidence.

ROM size: 524,288 bytes. SHA-256:

```text
eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607
```

No ROM, binary bank, commercial artwork, or audio recording is included. The generated assembly contains recovered original instructions; decoded data and annotations are identified as such. See [NOTICE.md](../NOTICE.md) for attribution scope.

## Verification levels

| Level | What it means | What it does not mean |
|---|---|---|
| Decoded data | Exported from a version-checked ROM at recorded offsets | Every field has a known semantic meaning |
| Byte-verified assembly | Assembled recovered code equals the original bytes | Every comment or function name is proven |
| Source-traced behavior | Branches/operands support the stated rule | All calling contexts were tested |
| Differential subroutine test | Original Z80 code and readable translation agree for stated inputs | Full hardware emulation or all reachable game states |
| Controlled trace | Original routine executed through multiple explicit updates | Full animation scheduler, camera system, or input polling replay |
| Gameplay-verified | Reserved for emulator/Windows testing with recorded evidence | Not claimed for this release's new porting proposals |

## Tools and reconstruction

- `z80dis` 1.0.6 decodes instructions for `recover.py`.
- [kosarev/z80](https://github.com/kosarev/z80), Python package 1.2.0, executes the original CPU routines.
- [WLA-DX](https://github.com/vhelin/wla-dx), built from commit `e0d9e74e9a8cbe1abd120770472789f6ee6f0fe8`; assembler reports 10.8a.

The current reconstruction uses original-ROM gaps plus regenerated assembly for the recovered regions. It verifies those assembly bytes and the final file. The historical continuation used a different method: overlaying source into the partial-disassembly tree. The archive is preserved for provenance; run the commands in the root README for current verification.

The CPU harness implements the mapper writes needed by the tested routines and ignores writes to ROM. It supplies a row-stride table, RAM, state and inputs explicitly. It does not model VDP, PSG, interrupts, a full frame scheduler, RAM mirroring, controller polling, or the complete animation interpreter. Tests stop at controlled return/breakpoint addresses.

## Corrections policy

New verified findings override old POC assumptions. The earlier +`$20` upright-spring gravity claim, capped height interpretation, and generic mask-based wall handling are specifically superseded. Historical notes remain historical; use the current README commands and current source manifest for reproduction.
