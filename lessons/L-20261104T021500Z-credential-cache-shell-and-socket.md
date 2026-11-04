---
id: L-20261104T021500Z-credential-cache-shell-and-socket
title: Credential-cache stdin and socket setup must match the actual shell
status: active
supersedes: []
recurrence_of: null
occurrences: 2
severity: Low
tags: [tech:git, phase:delivery, kind:environment]
recorded_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T02:15:00Z
---
## Trigger
A non-interactive `/bin/sh` script supplies credential-client input and starts a cache daemon under `/tmp`.
## What went wrong
The first script used Bash-only `read -d` under Dash. The next attempt reached the cache client but its parent socket directory had permissions looser than the daemon accepts.
## Correction
Use a POSIX here-document with command substitution for standard input and set the socket parent directory to mode 0700 before approving credentials.
## Prevention rule
Check the executing shell and enforce a private socket directory before any non-interactive credential-cache operation.
## Detection check
`git credential approve` produces no syntax or socket-permission error, and the subsequent push authenticates without prompting.
## Evidence
The successful push verified remote SHA `ba77add86f3d51b3125fa3a76ea3b3e7ac867faf`; this record contains no credential.
