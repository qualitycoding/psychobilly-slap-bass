# Third-Party Notices

## JUCE

This project uses JUCE (https://juce.com/), Copyright (c) Raw Material
Software Limited, licensed under the terms of the GNU Affero General
Public License v3 or later, with a commercial licensing alternative.
JUCE is fetched at build time at pinned commit
d60b7a78030661574a615b586d9325ba7a7fa7dd (see CMakeLists.txt).

## VST3 SDK

This project builds a VST3 plugin using the VST3 SDK, Copyright (c)
Steinberg Media Technologies GmbH. The VST3 SDK is licensed under the
MIT license:

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject
    to the following conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
    IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
    IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

## Reference recordings

The files under fixtures/references/ are solo contrabass pizzicato
recordings from VSCO 2 Community Edition (sgossner/VSCO-2-CE), used as
CC0 reference material for regression metrics only. See
research/reference-candidates/manifest.json for per-file source and
licence details.

The files under fixtures/articulation-references/ are synthesized
in-repository by an independent NumPy model and released under CC0-1.0.
