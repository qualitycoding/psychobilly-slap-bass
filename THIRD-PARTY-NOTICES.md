# Third-party notices

## JUCE

This project uses JUCE 9.0.5 (tag commit `d60b7a78030661574a615b586d9325ba7a7fa7dd`),
Copyright (c) Raw Material Software Limited, licensed under the
GNU Affero General Public License v3.0 (AGPL-3.0) or a commercial JUCE licence.
Fetched at configure time via CMake FetchContent; its licence notice is included
in the fetched source tree under `JUCE/LICENSE.md` (spdx: AGPL-3.0-only or
LicenseRef-JUCE-Commercial). JUCE is configured here under the AGPL-3.0.

## VST3 SDK

JUCE 9.0.5 bundles the VST3 SDK version 3.8.0, copyright Steinberg Media
Technologies GmbH, licensed under the MIT License (per the JUCE 9.0.5 SPDX
inventory; see knowledge/K-20261104T005100Z-vst3-sdk-mit-sbom.md).

## NumPy / SciPy / SoundFile / pip-audit (CI and test tooling only)

- NumPy (BSD-3-Clause), Copyright (c) NumPy Developers.
- SciPy (BSD-3-Clause), Copyright (c) SciPy Developers.
- python-soundfile (BSD-3-Clause), Copyright (c) Bastian Bechtold.
- pip-audit (Apache-2.0), Copyright (c) Trail of Bits.

These are test/analysis tooling; they do not link into the shipped VST3.

## Reference recordings (listening evidence only)

VSCO 2 Community Edition (CC0-1.0), Solo Contrabass Pizz recordings,
repository `sgossner/VSCO-2-CE` at commit
`440300901dfe9275fd84e0b7763af1f8443ae62e`. Used only as ordinary-pluck
listening references (D-070/D-071); never as slap-realism evidence.
