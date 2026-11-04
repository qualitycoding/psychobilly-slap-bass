
## D-028 — Listening round branches and statistical interpretation

Each actual listening round uses orphan branch `evidence/G-004-round-N`, matching frozen T-051; the marker remains `[gate-evidence G-004]`. Twelve pairs are constructed from the seven pinned reference files; therefore source recordings are reused and pair outcomes are not claimed to be twelve independent acoustic samples. The one-sided binomial p-value is descriptive only, never evidence of realism or population generalisation. Balanced assignment, <=8/12 numeric condition and qualitative override remain binding.

## D-029 — Initial native performance baselines

The first fully green implementation run on each native principal runner records its seven raw RTF values and median in `performance/baselines.json`, keyed by runner OS/architecture and environment-lock hash. Before that record exists, only the absolute maximum RTF <=0.25 gate applies and the step passes if absolute performance succeeds. A later toolchain/lock change establishes a new explicitly keyed baseline without replacing historical data. Any attempt to loosen an existing same-key baseline by more than D-018's 10% bootstrap allowance requires G-005; deleting or regenerating a baseline to hide a regression is forbidden.

## D-030 — Evidence access is an implementation prerequisite

S-000 must verify that the implementing identity can create orphan evidence branches and that the user can receive the resulting bundle through a reachable repository archive/raw route or another explicitly provided accessible route. If the repository is private and no accessible route is available, S-100 blocks rather than claiming delivery. No credential or listener-identifying metadata enters evidence.

## D-031 — Review artifacts before implementation

Planning-time `reviews/CODE_REVIEW.md` and `reviews/ADVERSARIAL_REVIEW.md` contain plan cold-read results only and explicitly report zero executed code findings because no implementation exists. S-REVIEW and S-ADVERSARIAL replace them with implementation review records; their planning-time zero counts are never represented as implementation review coverage.
