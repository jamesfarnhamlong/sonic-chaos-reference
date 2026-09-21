# Contributing research

Every behavioral claim should record:

1. ROM revision/hash and file offset; include bank and CPU address where relevant.
2. Entry conditions, state/flags read, and fields changed.
3. Source evidence and any CPU fixture or gameplay capture used.
4. Remaining uncertainty and the limits of the test.

Keep raw fields when their purpose is unknown. Do not replace a table entry with a plausible value, cap a profile without an instruction that does so, or treat Sonic 2 names as proof of Chaos meanings.

For a code change, regenerate affected data/assembly and run the relevant original-ROM comparison. Use `build_verify.py` when generated assembly changes. The ROM is supplied locally and excluded from commits. Public CI can check repository structure, but it cannot claim the ROM-based tests ran without that input.

Changes to the GameMaker prototype should cite the rule implemented and a matching fixture. Per-location repairs belong in experimental branches until justified by original data or code.
