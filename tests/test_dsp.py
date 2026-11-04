# FROZEN — DO NOT MODIFY
import hashlib
import json
import math
import unittest
from pathlib import Path

import numpy as np

from stubs.psb_contract import analyse, render, voice_lifecycle
from tests._support import DEFAULTS, SEED, midi_hz, note_events, render_note


def mono(samples):
    return np.mean(samples, axis=1)


def rms(samples):
    return float(np.sqrt(np.mean(np.square(samples, dtype=np.float64))))


def centroid(samples, sample_rate):
    x = mono(samples)
    window = np.hanning(len(x))
    spectrum = np.abs(np.fft.rfft(x * window))
    frequencies = np.fft.rfftfreq(len(x), 1.0 / sample_rate)
    return float(np.sum(frequencies * spectrum) / max(np.sum(spectrum), 1e-15))


class DspTests(unittest.TestCase):
    def test_t010_architecture_is_finite_across_notes_dynamics_rates(self):
        """T-010: SC-002/SC-005/SC-006; C-023; D-016/D-017 exercise six notes, three dynamics and rates."""
        for rate in (44100, 48000, 96000):
            for note in (28, 33, 38, 43, 48, 60):
                for velocity in (0.25, 0.55, 0.90):
                    with self.subTest(rate=rate, note=note, velocity=velocity):
                        result = render_note(note, velocity, rate)
                        samples = result.samples
                        self.assertEqual(samples.ndim, 2)
                        self.assertEqual(samples.shape[1], 2)
                        self.assertTrue(np.all(np.isfinite(samples)))
                        self.assertEqual(np.count_nonzero((np.abs(samples) > 0) & (np.abs(samples) < np.finfo(float).tiny)), 0)
                        measured = analyse(mono(samples), rate, midi_hz(note))
                        self.assertLessEqual(abs(measured["pitch_error_cents"]), 21)

    def test_t011_extreme_controls_keep_peak_below_measured_budget(self):
        """T-011: SC-005/SC-006; C-023; D-016/D-017 use 18 deterministic corners and 0.34 peak ceiling."""
        keys = list(DEFAULTS)
        corners = [{k: 0.0 for k in keys}, {k: 1.0 for k in keys}]
        corners += [{**{k: 0.0 for k in keys}, key: 1.0} for key in keys]
        corners += [{**{k: 1.0 for k in keys}, key: 0.0} for key in keys]
        for rate in (44100, 48000, 96000):
            for note in (28, 33, 44):
                for index, controls in enumerate(corners):
                    with self.subTest(rate=rate, note=note, corner=index):
                        result = render_note(note, 1.0, rate, controls, SEED + index + rate)
                        self.assertTrue(np.all(np.isfinite(result.samples)))
                        self.assertLessEqual(float(np.max(np.abs(result.samples))), 0.34)

    def test_t012_analyser_known_answers(self):
        """T-012: SC-007; C-013/C-024; D-017 prevent spectral-max and octave shortcuts."""
        rate = 48000
        t = np.arange(int(1.2 * rate)) / rate
        cases = [
            (55.0, np.sin(2 * np.pi * 55.0 * t)),
            (55.0, 0.22 * np.sin(2 * np.pi * 55.0 * t) + np.sin(2 * np.pi * 110.0 * t) + 0.35 * np.sin(2 * np.pi * 165.0 * t)),
            (midi_hz(38), np.sin(2 * np.pi * 2 * midi_hz(38) * t) + 0.6 * np.sin(2 * np.pi * 3 * midi_hz(38) * t) + 0.4 * np.sin(2 * np.pi * 4 * midi_hz(38) * t)),
        ]
        for expected, samples in cases:
            measured = analyse(samples, rate)
            self.assertLessEqual(abs(1200 * math.log2(measured["pitch_hz"] / expected)), 5)
        onset = np.concatenate([np.zeros(int(0.2 * rate)), np.sin(2 * np.pi * 82 * np.arange(int(0.3 * rate)) / rate)])
        self.assertLessEqual(abs(analyse(onset, rate)["onset_s"] - 0.2), 0.003)
        decay = np.sin(2 * np.pi * 98 * t) * 10 ** (-3 * t / 1.2)
        self.assertLessEqual(abs(analyse(decay, rate)["t60_s"] / 1.2 - 1), 0.05)
        self.assertLessEqual(abs(analyse(np.sin(2 * np.pi * 110 * t), rate)["centroid_hz"] - 110), 2)

    def test_t013_all_control_mappings_are_strictly_increasing(self):
        """T-013: SC-003/SC-005; C-025; D-017/D-021 sweep every control at five fixed values."""
        measures = {
            "pluck_slap": lambda result: rms(result.components["contact"]),
            "slap_brightness": lambda result: centroid(result.components["contact"], result.sample_rate),
            "body_resonance": lambda result: rms(result.components["body"]) / max(rms(result.components["pitched"]), 1e-12),
            "sustain": lambda result: analyse(mono(result.samples), result.sample_rate, midi_hz(33))["t60_s"],
            "string_tension": lambda result: centroid(result.components["pitched"], result.sample_rate),
            "attack_noise": lambda result: rms(result.components["attack"]),
            "mechanical_noise": lambda result: rms(result.components["mechanical"]),
            "output_level": lambda result: rms(result.samples),
        }
        for control, measure in measures.items():
            values = []
            for value in (0.0, 0.25, 0.50, 0.75, 1.0):
                controls = dict(DEFAULTS)
                controls[control] = value
                values.append(measure(render_note(33, 0.65, 48000, controls, SEED + 42)))
            with self.subTest(control=control, values=values):
                self.assertTrue(np.all(np.diff(values) > 0))

    def test_t014_reference_hashes_and_spectral_regression(self):
        """T-014: SC-007; C-011/C-012/C-027; D-017/D-070/D-071 gate pluck/body metrics only, never slap realism."""
        import soundfile as sf
        labels = {"A1": (33, 55.0), "F#0": (30, 46.249305), "G#2": (44, 103.826174)}
        controls = dict(DEFAULTS, pluck_slap=0.0, attack_noise=0.0, mechanical_noise=0.0)
        candidate_metrics = []
        for label, (note, expected) in labels.items():
            for velocity in (0.25, 0.55, 0.90):
                candidate = render_note(note, velocity, 44100, controls)
                candidate_metrics.append((label, analyse(mono(candidate.samples), 44100, expected)))
        manifest = json.loads(Path("research/reference-candidates/manifest.json").read_text())
        reference_dir = Path("fixtures/references")
        reference_metrics = {key: [] for key in labels}
        for item in manifest:
            path = reference_dir / item["file"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
            samples, rate = sf.read(path, always_2d=True)
            label = next(key for key in labels if f"_{key}_" in path.name)
            reference_metrics[label].append(analyse(np.mean(samples, axis=1), rate, labels[label][1])["centroid_hz"])
        for label, measured in candidate_metrics:
            reference_centroid = float(np.median(reference_metrics[label]))
            self.assertLessEqual(abs(math.log2(measured["centroid_hz"] / reference_centroid)), 1.433155096971784)
            self.assertLessEqual(abs(measured["pitch_error_cents"]), 21)

    def test_t015_voice_steal_retrigger_and_coupling_are_bounded(self):
        """T-015: SC-005/SC-006; C-026; D-019 bound eight slots and sympathetic feedback."""
        events = [{"sample": i * 64, "type": "note_on", "channel": 1,
                   "note": int(28 + (i * 37) % 28), "velocity": 0.1 + 0.9 * ((i * 73) % 100) / 100}
                  for i in range(256)]
        result = voice_lifecycle(events)
        self.assertLessEqual(result["max_observed_voices"], 8)
        self.assertGreater(result["steals"], 0)
        self.assertGreater(result["retriggers"], 0)
        self.assertLess(result["coupling_spectral_radius"], 1.0)
        self.assertAlmostEqual(result["coupling_spectral_radius"], 0.105)
        self.assertEqual(result["crossfade_ms"], 10.0)
        self.assertTrue(result["no_allocation_in_process"])


if __name__ == "__main__":
    unittest.main()
