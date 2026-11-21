---
id: L-20261122T032000Z-raw-github-unreachable-jsdelivr-mirror
title: raw.githubusercontent.com failed with SSL_ERROR_SYSCALL and the pinned files were fetched via the jsdelivr CDN mirror instead
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [tech:network, phase:implementation, kind:environment]
recorded_by: implementer
run: impl-20261122T000000Z-psychobilly-slap-bass
recorded_at: 2026-11-22T03:20:00Z
---
## Trigger
Seven pinned CC0 reference WAVs had to be downloaded from raw.githubusercontent.com during S-060.
## What went wrong
Every curl attempt to raw.githubusercontent.com failed with `SSL_ERROR_SYSCALL`; a detached 8-attempt retry loop did not recover.
## Correction
Fetched the same pinned blobs through `cdn.jsdelivr.net/gh/<owner>/<repo>@<full-commit>/<path>` and verified each file's SHA-256 against the planning manifest before accepting it.
## Prevention rule
For pinned GitHub raw content, pre-approve the jsdelivr mirror URL form (rewrite host, insert `@` before the commit) and always verify content hashes from the mirror exactly as for the primary source; never weaken pins because a host is flaky.
## Detection check
Every fetched artifact's SHA-256 must equal the manifest pin; a mirror is only a transport, never a source of new trust.
## Evidence
S-060 row in psychobilly-slap-bass EXECUTION_LOG.md; hashes verified in fixtures/references.
