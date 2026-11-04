---
id: K-20261104T013000Z-pip-audit-pinned-offline-flags
statement: "pip-audit 2.10.0 supports Python 3.10+ and provides --no-deps, --disable-pip, --strict, JSON formatting and an output file for auditing fully pinned requirements without dependency resolution."
status: current
supersedes: []
tags: [tech:python, subject:dependency-security, phase:verification]
applies_to_version: "pip-audit 2.10.0"
source: { url: "https://pypi.org/pypi/pip-audit/2.10.0/json", doi: "", title: "PyPI pip-audit 2.10.0 metadata and documentation", locator: "info.requires_python and embedded usage documentation", accessed: "2026-11-04", tier: 1 }
confidence: verified
derived_from: [C-029]
discovered_by: planner
run: 20261103T230504Z-psychobilly-slap-bass
recorded_at: 2026-11-04T01:30:00Z
---
The flags avoid resolving unpinned transitive dependencies during the audit itself; they do not make the installation lock unnecessary and do not scan native JUCE/VST3 code.
