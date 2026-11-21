# FROZEN — DO NOT MODIFY
import json
import unittest

import numpy as np

from stubs.psb_contract import analyse, render, validate_event_document
from tests._support import DEFAULTS, SEED, midi_hz


def _rms(x):
    return float(np.sqrt(np.mean(np.square(np.asarray(x, dtype=np.float64)))))


def _gesture_events(note=48, velocity=0.9, gesture="pluck", sample_rate=48000, duration=1.8):
    return [
        {"sample": 0, "type": "note_on", "channel": 1, "note": note,
         "velocity": velocity, "gesture": gesture},
        {"sample": int(duration * sample_rate), "type": "note_off", "channel": 1,
         "note": note, "velocity": 0.0},
    ]


def _document(gesture="slap", schema=2):
    header = {"schema": schema, "seed": SEED, "sample_rate": 48000,
              "render_seconds": 1.0, "controls": DEFAULTS}
    events = _gesture_events(duration=1.0)
    lines = [json.dumps(header, sort_keys=True)]
    if gesture is not None:
        events[0]["gesture"] = gesture
    lines += [json.dumps(event, sort_keys=True) for event in events]
    return "\n".join(lines) + "\n"


class ArticulationContractTests(unittest.TestCase):
    def test_t016_onset_glide_direction_and_velocity_separation(self):
        """T-016: SC-014; D-034 hard pluck/pop glide down; soft stays near static inharmonicity."""
        rate = 48000
        hard = render(_gesture_events(velocity=0.95, gesture="pop"), rate, dict(DEFAULTS), SEED)
        soft = render(_gesture_events(velocity=0.15, gesture="pluck"), rate, dict(DEFAULTS), SEED)
        mono = np.mean(hard.samples, axis=1)
        onset_pitch = analyse(mono[: int(0.030 * rate)], rate, midi_hz(48))["pitch_hz"]
        steady_pitch = analyse(mono[int(0.300 * rate): int(0.600 * rate)], rate, midi_hz(48))["pitch_hz"]
        glide_cents = 1200.0 * np.log2(onset_pitch / steady_pitch)
        self.assertGreaterEqual(glide_cents, 10.0)
        self.assertLessEqual(glide_cents, 300.0)
        soft_mono = np.mean(soft.samples, axis=1)
        soft_onset = analyse(soft_mono[: int(0.030 * rate)], rate, midi_hz(48))["pitch_hz"]
        soft_steady = analyse(soft_mono[int(0.300 * rate): int(0.600 * rate)], rate, midi_hz(48))["pitch_hz"]
        soft_glide = 1200.0 * np.log2(soft_onset / soft_steady)
        self.assertLess(abs(soft_glide), abs(glide_cents) * 0.5)

    def test_t017_gesture_direction_collision_ghost_and_energy(self):
        """T-017: SC-013; D-032/D-033 gesture identity, bounded collision, ghost, retrigger."""
        rate = 48000
        base = dict(DEFAULTS)
        slap = render(_gesture_events(gesture="slap"), rate, base, SEED)
        pluck = render(_gesture_events(gesture="pluck"), rate, base, SEED)
        pop = render(_gesture_events(gesture="pop"), rate, base, SEED)
        ghost = render(_gesture_events(gesture="ghost"), rate, base, SEED)
        self.assertGreater(_rms(slap.components["contact"]), _rms(pluck.components["contact"]))
        self.assertGreater(_rms(pop.components["contact"]), _rms(pluck.components["contact"]))
        self.assertLess(_rms(ghost.samples), _rms(pluck.samples))
        contact = np.mean(slap.components["contact"], axis=1)
        early = _rms(contact[: int(0.100 * rate)])
        late = _rms(contact[int(0.900 * rate): int(1.000 * rate)])
        self.assertLess(late, 0.5 * early)
        # same-string retrigger preserves energy unless the gesture damps it
        retrigger = [
            {"sample": 0, "type": "note_on", "channel": 1, "note": 33, "velocity": 0.9, "gesture": "pluck"},
            {"sample": int(0.9 * rate), "type": "note_on", "channel": 1, "note": 33, "velocity": 0.9, "gesture": "pluck"},
            {"sample": int(1.8 * rate), "type": "note_off", "channel": 1, "note": 33, "velocity": 0.0},
        ]
        dual = render(retrigger, rate, base, SEED)
        single = render(_gesture_events(duration=0.9), rate, base, SEED)
        win = slice(int(0.05 * rate), int(0.85 * rate))
        self.assertGreaterEqual(_rms(dual.samples[win]), 0.70 * _rms(single.samples[win]))

    def test_t018_independent_pitch_and_slap_buses(self):
        """T-018: SC-015; D-035/D-036 pitch and slap buses route independently without new params."""
        rate = 48000
        base = dict(DEFAULTS, pluck_slap=0.0)
        slap = render(_gesture_events(gesture="slap"), rate, base, SEED)
        pluck = render(_gesture_events(gesture="pluck"), rate, base, SEED)
        for component in ("pitched", "contact", "body"):
            self.assertIn(component, slap.components)
        self.assertGreater(_rms(slap.components["contact"]), 1e-6)
        self.assertLess(_rms(pluck.components["contact"]), 0.05 * _rms(slap.components["contact"]))
        self.assertGreater(_rms(slap.components["pitched"]), 1e-6)
        self.assertGreater(_rms(slap.components["body"]), 1e-6)
        self.assertFalse(np.array_equal(slap.components["pitched"], slap.components["contact"]))
        self.assertEqual(set(DEFAULTS), set(("pluck_slap", "slap_brightness", "body_resonance",
                                             "sustain", "string_tension", "attack_noise",
                                             "mechanical_noise", "output_level")))

    def test_t052_event_schema_two_gestures_and_articulation_bundle(self):
        """T-052: SC-016; D-037/D-039 schema-2 gestures and sealed articulation bundle contract."""
        accepted = validate_event_document(_document(gesture="slap", schema=2))
        self.assertTrue(accepted["accepted"])
        self.assertEqual(accepted["schema"], 2)
        for gesture in ("pluck", "pop", "slap", "ghost"):
            self.assertTrue(validate_event_document(_document(gesture=gesture, schema=2))["accepted"])
        self.assertFalse(validate_event_document(_document(gesture="bow", schema=2))["accepted"])
        self.assertFalse(validate_event_document(_document(gesture="slap", schema=1))["accepted"])
        from stubs.psb_contract import make_blind_pairs
        bundle = make_blind_pairs("fixtures/articulation-references", "build/listening/articulation-candidates",
                                  "build/listening/articulation-round-1", SEED, "articulation")
        self.assertEqual(bundle["pair_count"], 12)
        self.assertEqual(bundle["reference_a_count"], 6)
        self.assertEqual(bundle["reference_b_count"], 6)
        self.assertEqual(bundle["articulation_family_counts"], {"pluck": 3, "pop": 3, "slap": 3, "ghost": 3})
        self.assertTrue(bundle["key_base64_sealed"])
        for attribution in bundle["attributions"]:
            self.assertIn(attribution["licence"], {"CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0"})
            self.assertNotIn("commercial", attribution["licence"].lower())


if __name__ == "__main__":
    unittest.main()
