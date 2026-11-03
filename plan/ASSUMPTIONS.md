# Intake and assumptions

The user answered the single intake batch with ‘I think juice 9 is available otherwise proceed’. This adopts every proposed default, with JUCE 9 substituted when its existence is verified. ‘Juice’ is interpreted as JUCE because the intake item explicitly concerned the JUCE framework.

- **A-001 — Goal:** create a source-built VST3 instrument specialising in psychobilly slap double bass. AU, AAX, standalone and sample-player modes are out of scope.
- **A-002 — Platforms:** Windows 11 x64, macOS 15+ Apple Silicon and Ubuntu 24.04 x64. ARM64 Linux and AU are out of scope.
- **A-003 — Sound:** four physically modelled strings with pluck, fingerboard slap, body resonance, sympathetic vibration, velocity response and controlled performance variation; not a clean jazz-bass preset.
- **A-004 — Controls:** pluck/slap balance, slap brightness, body resonance, sustain, string tension, attack noise, mechanical noise and output level; MIDI velocity and pitch bend.
- **A-005 — Framework:** C++20, CMake and JUCE 9. JUCE 9.0.5 was verified at tag commit `d60b7a78030661574a615b586d9325ba7a7fa7dd`. The initially proposed GPL-3.0 licensing was not carried forward because JUCE 9's open licence is AGPL-3.0; see D-001.
- **A-006 — Polyphony and realtime safety:** eight-note polyphony; no allocation, locking, file access or network access on the audio thread; exercise 48 kHz at 64- and 128-sample buffers. The CI performance ceiling is an unmeasured default until a planning spike measures it.
- **A-007 — Validation:** automated DSP and plug-in tests, reproducible demos and blind A/B listening against lawfully redistributable slap-double-bass references. The user is the listener. A missing reference set invokes a pre-decided fallback, never fabricated validation.
- **A-008 — Release:** version `0.1.0`; source and CI artifacts only. Public binary release requires G-002.
- **A-009 — Privacy and maintenance:** no accounts, telemetry, network features or retained user data; best-effort maintenance.
- **A-010 — Users:** psychobilly musicians and producers using a VST3-compatible desktop host.
- **A-011 — Runtime:** desktop VST3 host; stereo output; sample rates 44.1, 48, 88.2 and 96 kHz tested, with 48 kHz the demonstration rate.
- **A-012 — Threat model:** untrusted MIDI, automation, preset/state blobs and malformed offline-render event files; no authentication boundary, secret handling or sensitive user data.
- **A-013 — Data handling:** plug-in state is supplied by the host; event files and renders are local; no retention outside the user's machine or CI evidence branch.
- **A-014 — Versioning:** Semantic Versioning, starting at 0.1.0.
- **A-015 — Stores:** lessons `https://github.com/qualitycoding/Lessons` at `c96e2d87d71cdbc73f4218f19fe6b9fd8dfe4911`; knowledge `https://github.com/qualitycoding/knowledge` at `e25f1c8a8e0a26850ffb006c8b4275ddf5272899`; both readable and writable.
- **A-016 — Subject tags:** `domain:audio`, `tech:juce`, `tech:cpp`, `tech:cmake`, `tech:github-actions`, `subject:psychobilly-slap-bass`, `subject:vst3`.
- **A-017 — Reproducibility:** fixed-seed event renders must be bit-identical on repeated runs in the same pinned environment; cross-platform comparison uses explicit floating-point tolerances rather than a claim of bitwise identity.
- **A-018 — Reference licensing:** only references whose licence and redistribution terms can be verified may enter the public evidence bundle. Candidate sources remain open until research completes.
