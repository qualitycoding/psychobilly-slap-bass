# FROZEN — DO NOT MODIFY
import unittest

from stubs.psb_contract import performance


class PerformanceTests(unittest.TestCase):
    def test_t040_eight_voice_realtime_budget_per_runner(self):
        """T-040: SC-005/SC-006; C-028; D-018 gate 96k/64 eight-voice work at RTF 0.25 and 10% regression."""
        result = performance({"sample_rate": 96000, "block_size": 64, "voices": 8,
                              "seconds_per_repeat": 5.0, "repeats": 7, "controls": "all_ones"})
        self.assertEqual(result["runs"], 7)
        self.assertTrue(result["finite"])
        self.assertLessEqual(result["rtf_max"], 0.25)
        self.assertLessEqual(result["baseline_regression"], 0.10)
        self.assertIn(result["runner_label"], {"ubuntu-24.04", "windows-2025", "macos-15"})
        self.assertTrue(result["baseline_recorded"])
        self.assertTrue(result["no_allocation_in_process"])


if __name__ == "__main__":
    unittest.main()
