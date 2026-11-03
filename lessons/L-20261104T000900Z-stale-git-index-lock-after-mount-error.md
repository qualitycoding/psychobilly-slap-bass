---
id: L-20261104T000900Z-stale-git-index-lock-after-mount-error
title: A mount write error can leave a stale zero-length Git index lock
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [tech:git, phase:research, kind:environment]
recorded_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T00:09:00Z
---
## Trigger
On the network-mounted worktree, `git add` reports an `index.lock` write error and subsequently leaves a zero-length lock file.
## What went wrong
The failed staging operation left `.git/index.lock`, which would make an unchanged retry fail for a different reason.
## Correction
Confirmed no Git operation was running, inspected the zero-length stale lock, removed only that lock, and retried the staging operation.
## Prevention rule
After a Git index-lock write failure, verify that no Git process is active and inspect the lock before retrying; remove only a confirmed stale lock, never an active operation's lock.
## Detection check
`git status` succeeds and `.git/index.lock` is absent before the retry.
## Evidence
R2 staging on 2026-11-04; no repository data or credentials involved.
