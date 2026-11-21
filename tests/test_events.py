# FROZEN — DO NOT MODIFY
import json
import unittest

import numpy as np

from stubs.psb_contract import render, validate_event_document
from tests._support import ARTICULATIONS, DEFAULTS, SEED, articulation_events, note_events


class EventAndRenderTests(unittest.TestCase):
    def document(self, seed=SEED, schema=1, articulation="pluck"):
        header = {"schema": schema, "seed": seed, "sample_rate": 48000, "render_seconds": 2.0, "controls": DEFAULTS}
        events = note_events() if schema == 1 else articulation_events(articulation)
        return "\n".join([json.dumps(header, sort_keys=True)] + [json.dumps(event, sort_keys=True) for event in events]) + "\n"

    def test_t020_event_schema_accepts_canonical_document(self):
        """T-020: SC-007/SC-008; D-024 freeze JSONL header/event schema and ordering."""
        for schema in (1, 2):
            for articulation in (ARTICULATIONS if schema == 2 else ("pluck",)):
                with self.subTest(schema=schema, articulation=articulation):
                    result = validate_event_document(self.document(schema=schema, articulation=articulation))
                    self.assertTrue(result["accepted"])
                    self.assertEqual(result["event_count"], 2)
                    self.assertEqual(result["schema"], schema)

    def test_t021_event_validation_rejects_bad_inputs(self):
        """T-021: SC-007/SC-009; D-012/D-024 reject malformed events and resource excess."""
        documents = ["", "{}\n", self.document().replace('"schema": 1', '"schema": 3'),
                     self.document(schema=2).replace('"articulation": "pluck"', '"articulation": "unknown"'),
                     self.document(schema=2).replace(', "articulation": "pluck"', ""),
                     self.document(schema=2).replace('"type": "note_off"', '"articulation": "pluck", "type": "note_off"'),
                     self.document().replace('"sample": 0', '"sample": -1'),
                     self.document().replace('"note": 33', '"note": 128'),
                     self.document().replace('"velocity": 0.55', '"velocity": 2'),
                     self.document().replace('"type": "note_on"', '"type": "unknown"'),
                     self.document() + json.dumps({"sample": 0, "type": "note_on", "channel": 1, "note": 40, "velocity": 0.5}) + "\n"]
        for text in documents:
            with self.subTest(text=text[:80]):
                self.assertFalse(validate_event_document(text)["accepted"])
        self.assertFalse(validate_event_document("x" * 1048577)["accepted"])

    def test_t022_render_is_deterministic_and_provenance_complete(self):
        """T-022: SC-007/SC-010; D-024/D-025 require identical samples and complete provenance."""
        events = note_events()
        first = render(events, 48000, DEFAULTS, SEED)
        second = render(events, 48000, DEFAULTS, SEED)
        self.assertTrue(np.array_equal(first.samples, second.samples))
        required = {"git_commit", "environment_lock_sha256", "seed", "controls", "input_sha256", "event_sha256",
                    "wav_sha256", "sample_rate", "frames", "peak", "rms", "utc_timestamp", "hardware", "thread_count", "normalisation_applied"}
        self.assertEqual(required - set(first.metadata), set())
        self.assertEqual(first.metadata["event_sha256"], second.metadata["event_sha256"])
        self.assertEqual(first.metadata["wav_sha256"], second.metadata["wav_sha256"])
        self.assertEqual(first.metadata["seed"], SEED)
        self.assertFalse(first.metadata["normalisation_applied"])

    def test_t023_output_level_is_in_shipped_path_not_render_normalisation(self):
        """T-023: SC-003/SC-006/SC-007; D-016/D-024 ensure output gain cannot be hidden by normalisation."""
        low = dict(DEFAULTS, output_level=0.25)
        high = dict(DEFAULTS, output_level=0.75)
        first = render(note_events(), 48000, low, SEED)
        second = render(note_events(), 48000, high, SEED)
        low_rms = float(np.sqrt(np.mean(first.samples ** 2)))
        high_rms = float(np.sqrt(np.mean(second.samples ** 2)))
        self.assertAlmostEqual(high_rms / low_rms, 4.0, places=5)
        self.assertFalse(first.metadata["normalisation_applied"])
        self.assertFalse(second.metadata["normalisation_applied"])


if __name__ == "__main__":
    unittest.main()
