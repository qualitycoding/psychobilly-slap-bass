# S-005 contract cold review

Scope: research-driven changes only. No production DSP, host adapter or renderer exists. This review does not inherit the planning-time claim of zero implementation findings.

## Findings and resolutions

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| S005-01 | High | Adding articulation as an APVTS parameter would silently break SC-002. | Articulation is versioned renderer data and latched MIDI keyswitches 24–27; the eight-parameter T-002 contract remains unchanged. |
| S005-02 | High | Accepting schema 2 in T-020 while retaining it as an invalid input in T-021 would be contradictory. | T-020 now covers schemas 1 and 2; T-021 rejects schema 3, unknown/missing articulation and articulation on note-off. |
| S005-03 | High | Four pairs per articulation would require sixteen pairs and conflict with T-052's twelve-pair gate. | Plan and D-043 specify three pairs each for pluck/pop/slap/ghost, twelve total, six reference-A and six reference-B. |
| S005-04 | High | Artist recordings could leak into a public evidence branch. | D-037/D-043, T-052, private-audio ignore rule and the reference route prohibit commercial audio and private consent forms. |
| S005-05 | Medium | A pitch-glide test based only on synthesiser output could tune the analyser around the synth. | T-016 includes independent known-answer exponential-chirp and statically stretched-partial signals before soft/hard synthesis comparisons. |
| S005-06 | Medium | Gesture metadata could become hardcoded success rather than measured state. | D-042 requires measured adapter diagnostics; implementation review must inspect derivations and adversarial review must falsify them. Metadata alone is not perceptual evidence. |
| S005-07 | Medium | A new bus could bypass the original output-level and peak tests. | T-018 requires diagnostic buses and no normalisation; existing T-011/T-023 remain binding on the shipped output. |
| S005-08 | Medium | Declaring a reference route could be mistaken for possessing reference audio. | REFERENCE_PLAN explicitly states that no articulation audio exists; S-025 must record and license it or block S-100/G-004. |

## Contract coverage

T-016 covers dynamic glide versus static inharmonicity. T-017 covers outward pluck/pop, inward slap/ghost, bounded collision counts, finite peaks, muted ghost balance and same-string residual/continuity. T-018 covers compact fitted body, three pickup model names and independent pitch/slap buses. T-052 covers cleared, sealed, balanced articulation evidence and an independent numeric gate. Existing T-050/T-051 continue to cover the ordinary-pluck bundle and ten demos.

## Result

No unresolved contract-documentation Critical/High finding remains. Physical plausibility, realtime safety of the eventual implementation, reference-audio availability and perceptual realism remain unproven and gated. The reviewed tests must fail through planning stubs before re-freeze; a green implementation suite is neither expected nor permitted at S-005.
