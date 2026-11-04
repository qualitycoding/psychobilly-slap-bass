#!/usr/bin/env python3
"""Generate the ten frozen D-024 demo event documents under demos/events/.

Walking/psychobilly phrases on the four double-bass strings (E1=28, A1=33,
D2=38, G2=43, with upper reach to G#2=44 and beyond for the high demo).
"""
import json
from pathlib import Path

DEFAULTS = {
    "pluck_slap": 0.35, "slap_brightness": 0.55, "body_resonance": 0.45,
    "sustain": 0.70, "string_tension": 0.50, "attack_noise": 0.20,
    "mechanical_noise": 0.15, "output_level": 0.75,
}
SR = 48000
OUT = Path(__file__).resolve().parents[1] / "demos" / "events"
OUT.mkdir(parents=True, exist_ok=True)


def header(seed, seconds, controls):
    return {"schema": 1, "seed": seed, "sample_rate": SR,
            "render_seconds": seconds, "controls": controls}


def note_on(sample, note, velocity, channel=1):
    return {"sample": sample, "type": "note_on", "channel": channel,
            "note": note, "velocity": velocity}


def note_off(sample, note, channel=1):
    return {"sample": sample, "type": "note_off", "channel": channel,
            "note": note, "velocity": 0.0}


def phrase(events, seconds, seed, name, controls=None):
    doc = [json.dumps(header(seed, seconds, dict(DEFAULTS, **(controls or {}))),
                      sort_keys=True)]
    doc += [json.dumps(e, sort_keys=True) for e in events]
    (OUT / f"{name}.jsonl").write_text("\n".join(doc) + "\n")


def beat(b):  # one beat at 132 BPM in samples
    return int(b * 60.0 / 132.0 * SR)


# 1. Walking/psychobilly melodic phrase across the four strings.
events = []
t = 0
melody = [(28, 1.0), (33, 0.5), (38, 0.5), (43, 1.0), (40, 0.5), (36, 0.5),
          (33, 1.0), (31, 0.5), (28, 1.5)]
for i, (note, dur) in enumerate(melody):
    events.append(note_on(t, note, 0.55 + 0.1 * (i % 3)))
    events.append(note_off(t + int(dur * beat(1)) - 2400, note))
    t += int(dur * beat(1))
phrase(events, 6.0, 0xD0101, "demo-01-short-melody")

# 2. Dense sixteenth-note alternate-string figure with retrigger/stealing stress.
events = []
t = 0
for i in range(64):
    note = (28, 43)[i % 2] if i % 4 < 2 else (33, 38)[i % 2]
    events.append(note_on(t, note, 0.4 + 0.45 * ((i * 7) % 10) / 10))
    events.append(note_off(t + beat(0.25) - 600, note))
    t += beat(0.25)
phrase(events, 8.0, 0xD0102, "demo-02-fast-passage")

# 3. Matched phrase at softest through loudest velocities.
events = []
t = 0
for vel in (0.1, 0.3, 0.55, 0.8, 1.0):
    for note, dur in ((33, 0.5), (38, 0.5), (43, 1.0)):
        events.append(note_on(t, note, vel))
        events.append(note_off(t + int(dur * beat(1)) - 2400, note))
        t += int(dur * beat(1))
    t += beat(0.5)
phrase(events, 12.0, 0xD0103, "demo-03-dynamics")

# 4. Long sustained notes, note-off and sympathetic decay.
events = []
t = 0
for note, dur in ((28, 4.0), (35, 4.0), (43, 4.0)):
    events.append(note_on(t, note, 0.7))
    events.append(note_off(t + int(dur * beat(1)) - 1200, note))
    t += int(dur * beat(1)) + beat(0.5)
phrase(events, 16.0, 0xD0104, "demo-04-slow-sustain")

# 5. Fixed phrase sweeping pluck_slap through all five frozen values.
events = []
t = 0
for value in (0.0, 0.25, 0.5, 0.75, 1.0):
    for note, dur in ((33, 0.5), (28, 0.5), (38, 1.0)):
        events.append(note_on(t, note, 0.75))
        events.append(note_off(t + int(dur * beat(1)) - 2000, note))
        t += int(dur * beat(1))
    t += beat(0.5)
phrase(events, 14.0, 0xD0105, "demo-05-pluck-slap")

# 6. Separate slap_brightness and body_resonance sweeps.
events = []
t = 0
for value in (0.0, 0.25, 0.5, 0.75, 1.0):
    for note in (28, 33):
        events.append(note_on(t, note, 0.8))
        events.append(note_off(t + beat(0.5) - 1200, note))
        t += beat(0.5)
phrase(events, 12.0, 0xD0106, "demo-06-brightness-body",
       {"slap_brightness": 0.0, "body_resonance": 0.0})

# 7. Separate string_tension and sustain sweeps with pitch-bend centre/range checks.
events = []
t = 0
for value in (0.0, 0.5, 1.0):
    for note, dur in ((33, 1.0), (40, 1.0)):
        events.append(note_on(t, note, 0.65))
        events.append(note_off(t + beat(dur) - 1200, note))
        t += beat(dur)
phrase(events, 10.0, 0xD0107, "demo-07-tension-sustain",
       {"string_tension": 0.25, "sustain": 0.5})

# 8. Separate attack/mechanical noise and output-level sweeps.
events = []
t = 0
for note, dur in ((28, 0.5), (33, 0.5), (38, 0.5), (43, 1.0)):
    events.append(note_on(t, note, 0.85))
    events.append(note_off(t + int(dur * beat(1)) - 1500, note))
    t += int(dur * beat(1))
phrase(events, 6.0, 0xD0108, "demo-08-noises-output",
       {"attack_noise": 0.6, "mechanical_noise": 0.55, "output_level": 0.6})

# 9. Lowest supported notes, open-string-like resonance, collision-heavy playing.
events = []
t = 0
for i, note in enumerate((24, 26, 28, 24, 28, 26)):
    vel = 0.9 if i % 2 == 0 else 0.45
    events.append(note_on(t, note, vel))
    events.append(note_off(t + beat(0.75) - 1500, note))
    t += beat(0.75)
phrase(events, 8.0, 0xD0109, "demo-09-low-register",
       {"pluck_slap": 0.8, "string_tension": 0.35})

# 10. Highest supported notes, fast release, exposed weak slap/collision mode.
events = []
t = 0
for i, note in enumerate((55, 57, 60, 62, 60, 57, 55, 52)):
    events.append(note_on(t, note, 0.5))
    events.append(note_off(t + beat(0.5) - 800, note))
    t += beat(0.5)
phrase(events, 6.0, 0xD0110, "demo-10-high-register",
       {"pluck_slap": 0.05, "sustain": 0.35, "slap_brightness": 0.2})

print("wrote", len(list(OUT.glob('*.jsonl'))), "demo documents")
