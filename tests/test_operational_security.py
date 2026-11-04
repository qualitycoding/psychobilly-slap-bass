# FROZEN — DO NOT MODIFY
import unittest

from stubs.psb_contract import operational_audit, security_audit


class OperationalSecurityTests(unittest.TestCase):
    def test_t030_operational_startup_shutdown_and_resume(self):
        """T-030: SC-006/SC-007/SC-010; D-025 require graceful startup, failure, shutdown and resume."""
        result = operational_audit()
        self.assertTrue(result["startup_without_display"])
        self.assertTrue(result["invalid_configuration_fails_closed"])
        self.assertTrue(result["resource_limit_fails_without_corruption"])
        self.assertTrue(result["graceful_shutdown"])
        self.assertTrue(result["resume_from_checkpoint"])
        self.assertTrue(result["partial_output_rejected"])

    def test_t031_no_network_secrets_or_vulnerable_dependencies(self):
        """T-031: SC-009; D-013/D-026 enforce privacy, secret and dependency boundaries."""
        result = security_audit()
        self.assertFalse(result["runtime_network_enabled"])
        self.assertFalse(result["telemetry_enabled"])
        self.assertEqual(result["secret_scan_matches"], [])
        self.assertEqual(result["dependency_vulnerabilities"], [])
        self.assertTrue(result["agpl_notice_present"])
        self.assertTrue(result["juce_notice_present"])
        self.assertTrue(result["vst3_mit_notice_present"])
        self.assertTrue(result["source_commit_recorded"])


if __name__ == "__main__":
    unittest.main()
