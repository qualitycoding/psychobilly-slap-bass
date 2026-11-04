# FROZEN — DO NOT MODIFY
import unittest

from stubs.psb_contract import host_contract, parameter_contract, state_roundtrip, validate_state
from tests._support import DEFAULTS


class HostContractTests(unittest.TestCase):
    def test_t001_parameter_ids_ranges_defaults(self):
        """T-001: SC-003/SC-008; C-017/C-018; D-020/D-021 freeze eight host parameters."""
        contract = parameter_contract()
        self.assertEqual(set(contract), set(DEFAULTS))
        for parameter_id, default in DEFAULTS.items():
            self.assertEqual(contract[parameter_id], {"minimum": 0.0, "maximum": 1.0, "default": default})

    def test_t002_vst3_identity_bus_and_editor(self):
        """T-002: SC-001/SC-008; C-005/C-017; D-007/D-020 require VST3 stereo synth without editor."""
        contract = host_contract()
        self.assertEqual(contract["format"], "VST3")
        self.assertEqual(contract["name"], "Psychobilly Slap Bass")
        self.assertEqual(contract["manufacturer"], "QualityCoding")
        self.assertEqual(contract["version"], "0.1.0")
        self.assertEqual(contract["plugin_code"], "Psb1")
        self.assertEqual(contract["bundle_id"], "com.qualitycoding.psychobillyslapbass")
        self.assertTrue(contract["is_synth"])
        self.assertTrue(contract["accepts_midi"])
        self.assertFalse(contract["produces_midi"])
        self.assertEqual(contract["input_channels"], 0)
        self.assertEqual(contract["output_channels"], 2)
        self.assertFalse(contract["has_editor"])
        self.assertIsNone(contract["create_editor"])

    def test_t003_state_roundtrip_is_canonical(self):
        """T-003: SC-008; C-017/C-018; D-008/D-022 require canonical complete state roundtrip."""
        xml = ('<PsychobillySlapBass schema="1">' + ''.join(
            f'<PARAM id="{key}" value="{value}"/>' for key, value in DEFAULTS.items()) + '</PsychobillySlapBass>').encode()
        self.assertEqual(state_roundtrip(xml), xml)

    def test_t004_state_rejects_malformed_and_future_schema(self):
        """T-004: SC-008/SC-009; C-019; D-012/D-022 reject malformed state without changing sound."""
        invalid = [b"", b"not xml", b"<PsychobillySlapBass schema=\"2\"/>",
                   b"<PsychobillySlapBass schema=\"1\"><PARAM id=\"unknown\" value=\"0.5\"/></PsychobillySlapBass>",
                   b"<PsychobillySlapBass schema=\"1\"><PARAM id=\"sustain\" value=\"nan\"/></PsychobillySlapBass>",
                   b"<PsychobillySlapBass schema=\"1\"><PARAM id=\"sustain\" value=\"1.1\"/></PsychobillySlapBass>",
                   b"<PsychobillySlapBass schema=\"1\"><PARAM id=\"sustain\" value=\"0.5\"><nested/></PARAM></PsychobillySlapBass>"]
        for data in invalid:
            with self.subTest(data=data):
                result = validate_state(data)
                self.assertFalse(result["accepted"])
                self.assertTrue(result["active_state_unchanged"])
        self.assertFalse(validate_state(b"x" * 65537)["accepted"])

    def test_t005_midi_pitch_bend_and_channel_contract(self):
        """T-005: SC-004; C-017; D-020/D-023 freeze omni MIDI and +/-2-semitone 14-bit bend."""
        contract = host_contract()
        self.assertEqual(contract["midi_channels"], "omni")
        self.assertEqual(contract["pitch_bend_semitones"], 2.0)
        self.assertEqual(contract["pitch_bend_center"], 8192)
        self.assertTrue(contract["note_on_zero_is_note_off"])
        self.assertFalse(contract["mpe_enabled"])


if __name__ == "__main__":
    unittest.main()
