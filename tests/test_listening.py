# FROZEN — DO NOT MODIFY
import unittest

from stubs.psb_contract import make_blind_pairs, score_blind
from tests._support import SEED


class ListeningEvidenceTests(unittest.TestCase):
    def test_t050_blind_pair_construction_and_scoring(self):
        """T-050: SC-007; D-015/D-070/D-071; G-004 require 12 balanced sealed pairs and <=8/12 pass."""
        bundle = make_blind_pairs("fixtures/references", "build/listening/candidates", "build/listening/round-1", SEED, "start")
        self.assertEqual(bundle["pair_count"], 12)
        self.assertEqual(bundle["reference_a_count"], 6)
        self.assertEqual(bundle["reference_b_count"], 6)
        self.assertEqual(bundle["clip_seconds"], 1.0)
        self.assertEqual(bundle["rms_dbfs"], -23.0)
        self.assertEqual(bundle["bit_depth"], 24)
        self.assertEqual(bundle["window"], "start")
        self.assertTrue(bundle["key_base64_sealed"])
        self.assertTrue(bundle["sha256sums_present"])
        self.assertTrue(bundle["attribution_present"])
        passing = score_blind("build/listening/round-1", ["A"] * 12)
        self.assertIn("side_bias", passing)
        self.assertLessEqual(passing["correct"], 8)
        self.assertTrue(passing["numeric_pass"])
        decoded = passing["decoded_reference_sides"]
        nine_correct = decoded[:9] + [("B" if side == "A" else "A") for side in decoded[9:]]
        failing = score_blind("build/listening/round-1", nine_correct)
        self.assertEqual(failing["correct"], 9)
        self.assertFalse(failing["numeric_pass"])

    def test_t051_evidence_bundle_has_demos_and_no_sensitive_data(self):
        """T-051: SC-007/SC-009; D-015/D-024/D-071 require demos, checksums and evidence hygiene."""
        bundle = make_blind_pairs("fixtures/references", "build/listening/candidates", "build/listening/round-1", SEED, "start")
        self.assertEqual(bundle["demo_count"], 10)
        self.assertEqual(bundle["demo_event_file_count"], 10)
        self.assertTrue(bundle["orphan_branch"].startswith("evidence/G-004-round-"))
        self.assertTrue(bundle["marker_contains_gate_evidence"])
        self.assertEqual(bundle["secret_scan_matches"], [])
        self.assertEqual(bundle["local_path_matches"], [])
        self.assertEqual(bundle["listener_metadata"], {})
        self.assertEqual(bundle["round_limit"], 3)
        self.assertTrue(bundle["qualitative_override_required"])


if __name__ == "__main__":
    unittest.main()
