# FROZEN — DO NOT MODIFY
"""Shared deterministic fixtures for frozen tests."""
from stubs.psb_contract import render

DEFAULTS = {
    "pluck_slap": 0.35,
    "slap_brightness": 0.55,
    "body_resonance": 0.45,
    "sustain": 0.70,
    "string_tension": 0.50,
    "attack_noise": 0.20,
    "mechanical_noise": 0.15,
    "output_level": 0.75,
}
SEED = 0x50534C41


def note_events(note=33, velocity=0.55, sample_rate=48000, duration=1.8):
    return [
        {"sample": 0, "type": "note_on", "channel": 1, "note": note, "velocity": velocity},
        {"sample": int(duration * sample_rate), "type": "note_off", "channel": 1, "note": note, "velocity": 0.0},
    ]


def render_note(note=33, velocity=0.55, sample_rate=48000, controls=None, seed=SEED):
    return render(note_events(note, velocity, sample_rate), sample_rate,
                  dict(DEFAULTS if controls is None else controls), seed)


def midi_hz(note):
    return 440.0 * 2.0 ** ((note - 69.0) / 12.0)
