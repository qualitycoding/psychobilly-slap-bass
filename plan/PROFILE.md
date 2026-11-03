# Profile record

- Active profiles: `software`.
- Mode flags: `audio = true`; `software.deploys = false`; `math.exploration = false`; `courseware = false`.
- Environment: `ephemeral` (Kimi cloud sandbox; only `/mnt/agents` is durable).
- Justification: the deliverable is maintained VST3 source code that produces audio. Public binary release is gated separately and is not deployment of a running service.
- Model availability: no subagent spawning or Fable/Opus/Sonnet/Haiku tiers are exposed. All assigned tiers fall back to the available Kimi K3.1 agent; sequential fresh-review passes substitute where possible and the limitation is recorded in the checkpoint.

## Not applicable

- Sections 2A and all mathematical artifacts: no `math` profile.
- Sections 2C and all figure artifacts: no `computational` or `publication` profile.
- Section 2D and all manuscript artifacts: no `publication` profile.
- Section 3.11 and `G-LEARN`: no `courseware` flag.
- `plan/OPERATIONS.md` and deployment tests: `software.deploys = false`.
- Numerical V&V categories reserved for `computational`: not separately applicable; deterministic DSP unit, integration and reproducibility tests remain required under `software` and `audio`.
