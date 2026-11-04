# Human gates

No gate may be self-approved by the implementing agent. Each response is recorded in `GATE-<id>.md` with the exact question, evidence links, UTC time and responder. Silence is not approval.

## G-002 — Public binary release

**When:** only after implementation, CI, reviews and G-004 are complete. Source pushes and private CI artifacts do not require this gate.

**Question:** “May the named `0.1.0` VST3 artifacts and their licence notices be published to the proposed public release target?”

**Allowed responses:** `release-to: <target>`, `do-not-release`, `iterate: <notes>`.

**Rule:** only an explicit `release-to` authorises the external publication. No release workflow or upload may run before it. A later version or different artifact requires a new gate.

## G-003 — Lessons and knowledge transfer

**When:** after S-RETRO; this holds back only the store pushes, not implementation completion.

**Question:** “Push the listed lessons and knowledge items to the proposed stores?” Proposed targets are `qualitycoding/Lessons` (`lessons/`) and `qualitycoding/knowledge` (`knowledge/`).

**Allowed responses:** `push-to-proposed`, `push-to: <lesson-target> [knowledge-target]`, `do-not-push`.

**Rule:** follow S-KNOW for indexed pushes, rejected-push retries and bundle fallback. Never embed credentials in a target.

## G-004 — Blind listening

**When:** after S-REVIEW and S-ADVERSARIAL, green CI on the pushed candidate, and S-100 construction of the sealed blind bundle.

**Question:** “After listening to the twelve pairs and ten demos, how should the project proceed? You may request identification of the preferred clips after recording your choices.”

**Allowed responses:** `proceed`, `iterate: <notes>`, `proceed-with-rescope: <text>`, `stop`.

**Numeric pass:** at most 8/12 correct identifications of the reference in a sealed round. This is only a necessary numeric condition: any qualitative report that the candidate lacks the intended slap attack, body, pitch clarity or musical usability overrides the numeric pass and requires `iterate`, rescope or stop. Ordinary-pluck reference pairs do not validate slap realism; the slap judgement is demos-only.

**Iteration:** disclose the key only after choices are recorded, generate a new seed, correct the implementation without changing frozen tests except through the unfreeze/red/refreeze procedure, and repeat all affected CI/reviews. Maximum three disclosed rounds. A fourth requested round escalates to `proceed-with-rescope` or `stop`.

## G-005 — Performance, security or target rescope

**When:** a native CI target cannot meet D-018, a Critical/High security finding cannot be fixed without changing scope, or a declared OS/architecture can no longer be built or tested.

**Question:** “The pinned target or budget cannot be met as specified. May the attached measured evidence and exact proposed change replace it?”

**Allowed responses:** `proceed-with-rescope: <text>`, `iterate: <notes>`, `stop`.

**Rule:** never relax a threshold, drop a platform, disable a validator test or suppress a security finding unilaterally. An approved change adds a D-record, updates traceability, and re-freezes affected tests before work resumes.
