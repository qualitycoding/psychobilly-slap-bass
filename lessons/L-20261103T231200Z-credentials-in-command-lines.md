---
id: L-20261103T231200Z-credentials-in-command-lines
title: Credential was interpolated into planning shell commands instead of using Git's credential client
status: active
supersedes: []
recurrence_of: L-20261007T150100Z-no-credentials-in-command-lines
occurrences: 5
severity: High
tags: [tech:github, phase:research, kind:security]
recorded_by: planner
run: gen-20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-03T23:12:00Z
---
## Trigger
A user supplies a GitHub personal-access token and repository access must be used from shell-only tooling.
## What went wrong
The token was placed in shell command text for API and Git authentication, repeating the loaded no-credentials-in-command-lines lesson.
## Correction
Configured Git's credential-cache client and supplied the credential through its standard input; subsequent Git operations contain no token.
## Prevention rule
Authenticate through the tool's credential client using standard input, and never place a credential in a URL, command argument, header argument, repository file or user-facing output.
## Detection check
Run `git grep -nE 'github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}'` and inspect command/output records; neither may contain a credential.
## Evidence
Planning shell history in this run; no credential was committed to the repository. No token value is reproduced here.
