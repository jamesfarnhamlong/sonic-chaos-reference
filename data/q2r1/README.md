# Q2-R1 evidence

Read `docs/q2-r1-campaign-defect-triage.md` and the Windows observation cards first.

| File | Meaning |
|---|---|
| `dash-traces.json.gz` | 24 seeded local movement slices; fixed-point positions/velocities in 1/256 px units; current/requested states decimal; input and presentation events; reduced canonical facing oracle only through release |
| `ss3-traces.json.gz` | Gzipped JSON: actual census placements, two cached-input natural route replays (near-contact updates retained), 28 seeded local upper-left approaches (all 60 updates retained) |
| `gate/` | Raw existing monitor verifier output and result; elapsed milliseconds are informational |
| `register.json` | Evidence-ranked findings, exact source SHA-256 hashes, limits and one future package proposal |
| `q1-acceptance-receipt.json` | Manager/Chief aggregate acceptance report; not a new Research Windows run |

Reproduction tools are `tools/q2r1_dash.js`, `q2r1_ss3.js`, `q2r1_gate.js`, `q2r1_manifest.js`, then `q2r1_validate.js`. Each accepts the accepted POC checkout as its first argument. The manifest hashes the bytes in the current checkout (line-ending conversions may change those hashes on another host); immutable commits and ROM addresses remain the authority. No ROM payload, image, audio or executable is included. Seeded player states and local camera starts are not claimed to be natural input routes.
