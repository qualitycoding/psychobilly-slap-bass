#!/usr/bin/env python3
"""Engine finiteness sweep: drives the headless engine across sample rates,
block sizes, notes, gestures and velocities, holding many voices ringing so
the D-019 sympathetic coupling is exercised at its worst (clustered high
notes on shared voices). Fails if any output sample is non-finite.

Regression harness for the pluginval "Infs found in buffer" failure: the
correlated 8-voice sympathetic mode has closed-loop gain > 1 and used to
run away exponentially. The delay-line state ceiling keeps every signal
bounded; this sweep proves it across the hostile corner space.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HARNESS = r"""
#include "psb/engine.h"
#include <cmath>
#include <cstdio>
#include <vector>
int main()
{
    const double rates[] = {44100.0, 48000.0, 88200.0, 96000.0};
    const int blocks[] = {64, 128, 256, 512, 1024};
    long bad = 0;
    for (double rate : rates)
        for (int block : blocks)
        {
            psb::Engine engine;
            engine.setSeed(5265473);
            engine.prepare(rate, block);
            for (int note = 0; note <= 127; note += 7)
                for (int gesture = 0; gesture < 4; ++gesture)
                    for (double vel : {0.1, 0.5, 0.9, 1.0})
                    {
                        psb::Event on{};
                        on.type = psb::Event::Type::note_on;
                        on.sample = 0; on.channel = 1; on.note = note;
                        on.velocity = vel; on.bend = 8192; on.gesture = gesture;
                        psb::Event off = on;
                        off.type = psb::Event::Type::note_off;
                        off.velocity = 0.0;
                        std::string err;
                        if (!engine.addEvent(on, &err))
                        {
                            std::fprintf(stderr, "addEvent rejected: %s\n", err.c_str());
                            return 2;
                        }
                        std::vector<double> l((size_t) block), r((size_t) block);
                        for (int b = 0; b < 8; ++b)
                        {
                            engine.fillBlock(block, l.data(), r.data());
                            for (int i = 0; i < block; ++i)
                                if (!std::isfinite(l[(size_t) i]) || !std::isfinite(r[(size_t) i]))
                                {
                                    std::fprintf(stderr,
                                        "non-finite: rate=%g block=%d note=%d gesture=%d "
                                        "vel=%g block=%d sample=%d\n",
                                        rate, block, note, gesture, vel, b, i);
                                    ++bad;
                                    goto next;
                                }
                        }
                        next:;
                        engine.addEvent(off, nullptr);
                    }
        }
    std::printf("finiteness sweep: %ld non-finite combos\n", bad);
    return bad == 0 ? 0 : 1;
}
"""


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "sweep.cpp").write_text(HARNESS)
        exe = tmp / ("sweep.exe" if sys.platform == "win32" else "sweep")
        compile_cmd = ["c++", "-std=c++20", "-O2", "-ffp-contract=off",
                       "-I", str(ROOT / "src"),
                       str(tmp / "sweep.cpp"), str(ROOT / "src" / "psb" / "engine.cpp"),
                       "-o", str(exe)]
        subprocess.run(compile_cmd, check=True)
        proc = subprocess.run([str(exe)])
        return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
