---
id: L-20261103T231500Z-credential-cache-socket-mount
title: Git credential-cache rejected the durable mount's socket-directory permissions
status: active
supersedes: []
recurrence_of: null
occurrences: 2
severity: Medium
tags: [tech:github, phase:research, kind:environment]
recorded_by: planner
run: gen-20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-03T23:15:00Z
---
## Trigger
Git credential-cache is configured with its socket on the sandbox's durable FUSE-style mount.
## What went wrong
The daemon refused to start because it considered the socket directory permissions too loose, even after a chmod request.
## Correction
Moved only the credential-cache socket to a mode-0700 temporary directory and verified a redacted credential lookup.
## Prevention rule
Place Git credential-cache sockets in a mode-0700 temporary directory, never in repository artifacts or on a mount whose permissions cannot be tightened.
## Detection check
A redacted `git credential fill` returns a username and password without exposing the secret and without a daemon warning.
## Evidence
Successful redacted credential lookup after the socket moved to `/tmp`; no credential value is reproduced here.
