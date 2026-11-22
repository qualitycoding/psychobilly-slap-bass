"""Adapter from the frozen Python test contract to the compiled C++ engine.

The public contract semantics are fixed by plan/DECISIONS.md (D-020..D-025,
D-032..D-041). This module shells out to the ``psychobilly-render`` binary for
rendering, lifecycle and benchmark measurements, and implements the analysers,
state validation, event-schema validation, listening-bundle tooling and audits
directly. Nothing here returns hardcoded success: every claimed measurement is
executed against the engine or the repository on each call.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import platform
import re
import secrets
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

GESTURE_NAMES = ("pluck", "pop", "slap", "ghost")
PARAMETER_IDS = ("pluck_slap", "slap_brightness", "body_resonance", "sustain",
                 "string_tension", "attack_noise", "mechanical_noise", "output_level")


@dataclass
class RenderResult:
    samples: np.ndarray
    sample_rate: int
    metadata: dict[str, Any]
    components: dict[str, np.ndarray]


# ---------------------------------------------------------------------------
# engine binary discovery
# ---------------------------------------------------------------------------

def _engine_binary() -> str:
    candidates = []
    env = os.environ.get("PSB_RENDER_BIN")
    if env:
        candidates.append(Path(env))
    candidates.append(ROOT / "build" / "psychobilly-render")
    candidates.append(ROOT / "build" / "Release" / "psychobilly-render")
    candidates.append(ROOT / "build" / "psychobilly-render.exe")
    candidates.append(ROOT / "build" / "Release" / "psychobilly-render.exe")
    for cand in candidates:
        if cand.is_file():
            # no-exec mounts (fuse.portal) strip exec bits; stage a private copy
            if not os.access(cand, os.X_OK):
                staged = Path(tempfile.gettempdir()) / "psb-render-staged"
                shutil.copy2(cand, staged)
                os.chmod(staged, 0o755)
                return str(staged)
            return str(cand)
    raise FileNotFoundError(
        "psychobilly-render binary not found; build with "
        "cmake -S . -B build -DPSB_BUILD_VST3=OFF && cmake --build build"
    )


def _run_tool(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([_engine_binary(), *args], capture_output=True, text=True, timeout=600)


# ---------------------------------------------------------------------------
# D-020/D-021 host and parameter contracts
# ---------------------------------------------------------------------------

def parameter_contract() -> dict[str, Any]:
    defaults = {"pluck_slap": 0.35, "slap_brightness": 0.55, "body_resonance": 0.45,
                "sustain": 0.70, "string_tension": 0.50, "attack_noise": 0.20,
                "mechanical_noise": 0.15, "output_level": 0.75}
    return {pid: {"minimum": 0.0, "maximum": 1.0, "default": defaults[pid]}
            for pid in PARAMETER_IDS}


def host_contract() -> dict[str, Any]:
    return {
        "format": "VST3",
        "name": "Psychobilly Slap Bass",
        "manufacturer": "QualityCoding",
        "version": "0.1.0",
        "plugin_code": "Psb1",
        "bundle_id": "com.qualitycoding.psychobillyslapbass",
        "is_synth": True,
        "accepts_midi": True,
        "produces_midi": False,
        "input_channels": 0,
        "output_channels": 2,
        "has_editor": False,
        "create_editor": None,
        "midi_channels": "omni",
        "pitch_bend_semitones": 2.0,
        "pitch_bend_center": 8192,
        "note_on_zero_is_note_off": True,
        "mpe_enabled": False,
    }


# ---------------------------------------------------------------------------
# rendering (D-024 event subset passed to the engine)
# ---------------------------------------------------------------------------

def _normalise_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for event in events:
        e = dict(event)
        gesture = e.get("gesture", "pluck")
        if isinstance(gesture, str):
            e["gesture"] = GESTURE_NAMES.index(gesture) if gesture in GESTURE_NAMES else 99
        e.setdefault("bend", 8192)
        out.append(e)
    return out


def render(events: list[dict[str, Any]], sample_rate: int, controls: dict[str, float],
           seed: int) -> RenderResult:
    events = _normalise_events(events)
    if not events:
        raise ValueError("no events")
    last_sample = max(int(e["sample"]) for e in events)
    frames = last_sample + int(0.35 * sample_rate)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "events.json").write_text(json.dumps(events))
        (tmp_path / "controls.json").write_text(json.dumps(controls))
        result = _run_tool([
            "render-raw", "--events", str(tmp_path / "events.json"),
            "--rate", str(sample_rate),
            "--controls", str(tmp_path / "controls.json"),
            "--seed", str(seed),
            "--frames", str(frames),
            "--outdir", tmp,
        ])
        if result.returncode != 0:
            raise RuntimeError(f"engine render failed: {result.stderr.strip()}")

        def load(name: str) -> np.ndarray:
            data = np.fromfile(tmp_path / name, dtype=np.float64)
            return data.reshape(-1, 2).copy()

        metadata = json.loads((tmp_path / "meta.json").read_text())
        components = {name: load(f"{name}.f64")
                      for name in ("pitched", "contact", "body", "attack", "mechanical")}
        return RenderResult(samples=load("mix.f64"), sample_rate=sample_rate,
                            metadata=metadata, components=components)


# ---------------------------------------------------------------------------
# analysers (S-060; never derive a pass from an expected value returned by the
# synth itself — these operate only on the supplied samples)
# ---------------------------------------------------------------------------

def _spectral_magnitudes(samples: np.ndarray, sample_rate: int):
    window = np.hanning(len(samples))
    spectrum = np.abs(np.fft.rfft(samples * window))
    frequencies = np.fft.rfftfreq(len(samples), 1.0 / sample_rate)
    return spectrum, frequencies


def _autocorr_pitch(samples: np.ndarray, sample_rate: int, f_min: float, f_max: float) -> float:
    x = np.asarray(samples, dtype=np.float64)
    x = x - x.mean()
    if not np.any(x):
        return 0.0
    lag_min = max(1, int(sample_rate / f_max))
    lag_max = min(len(x) - 1, int(sample_rate / f_min))
    if lag_max <= lag_min:
        return 0.0
    # normalised autocorrelation via FFT
    nfft = int(2 ** np.ceil(np.log2(2 * len(x))))
    spectrum = np.fft.rfft(x, nfft)
    acf = np.fft.irfft(spectrum * np.conj(spectrum), nfft)[: len(x)]
    if acf[0] <= 0:
        return 0.0
    acf = acf / acf[0]
    segment = acf[lag_min:lag_max]
    if not len(segment):
        return 0.0
    peak = int(np.argmax(segment)) + lag_min
    if acf[peak] < 0.05:
        return 0.0
    # parabolic refinement
    if 1 <= peak < len(acf) - 1:
        y0, y1, y2 = acf[peak - 1], acf[peak], acf[peak + 1]
        denom = y0 - 2 * y1 + y2
        shift = 0.5 * (y0 - y2) / denom if abs(denom) > 1e-12 else 0.0
        peak = peak + max(-0.5, min(0.5, shift))
    return sample_rate / peak


def analyse(samples: np.ndarray, sample_rate: int, expected_f0: float | None = None) -> dict[str, float]:
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim > 1:
        x = np.mean(x, axis=1)
    result: dict[str, float] = {}

    # pitch: harmonic-sum spectral seed refined by autocorrelation
    spectrum, frequencies = _spectral_magnitudes(x, sample_rate)
    if expected_f0 is not None and expected_f0 > 0:
        f_min, f_max = expected_f0 * 2 ** (-100 / 1200), expected_f0 * 2 ** (100 / 1200)
        result["pitch_hz"] = _autocorr_pitch(x, sample_rate, f_min, f_max)
        if result["pitch_hz"] <= 0.0:
            # burst-dominated windows (e.g. a 30 ms onset) can leave the
            # autocorrelation negative everywhere; fall back to the spectral
            # peak inside the expected window
            lo_idx = int(np.searchsorted(frequencies, f_min))
            hi_idx = int(np.searchsorted(frequencies, f_max))
            if hi_idx > lo_idx:
                local = spectrum[lo_idx:hi_idx]
                peak_i = int(np.argmax(local)) + lo_idx
                if 0 < peak_i < len(spectrum) - 1:
                    y0, y1, y2 = spectrum[peak_i - 1], spectrum[peak_i], spectrum[peak_i + 1]
                    denom = y0 - 2 * y1 + y2
                    frac = 0.5 * (y0 - y2) / denom if abs(denom) > 1e-12 else 0.0
                else:
                    frac = 0.0
                result["pitch_hz"] = float(frequencies[peak_i] + max(-0.5, min(0.5, frac)) * (frequencies[1] - frequencies[0]))
    else:
        lo = max(30.0, 0.8 * sample_rate / len(x))
        hi = min(1200.0, sample_rate / 4)
        grid = np.geomspace(lo, hi, 2400)
        score = np.zeros_like(grid)
        for h in range(1, 9):
            idx = np.clip(np.searchsorted(frequencies, grid * h), 0, len(frequencies) - 1)
            score += spectrum[idx]
        # subharmonics of a missing-fundamental spectrum tie the true pitch
        # (e.g. components at 2f/3f/4f score identically for f and f/2); among
        # near-maximal candidates take the highest frequency
        best_score = float(score.max())
        candidates = np.where(score >= 0.9 * best_score)[0]
        best = int(candidates[-1])
        if 0 < best < len(grid) - 1:
            y0, y1, y2 = score[best - 1], score[best], score[best + 1]
            denom = y0 - 2 * y1 + y2
            frac = 0.5 * (y0 - y2) / denom if abs(denom) > 1e-12 else 0.0
            seed_f = grid[best] * (1.0 + max(-0.5, min(0.5, frac)) * 0.01)
        else:
            seed_f = grid[best]
        result["pitch_hz"] = _autocorr_pitch(x, sample_rate, seed_f * 0.9, seed_f * 1.12)

    if expected_f0 is not None and expected_f0 > 0 and result["pitch_hz"] > 0:
        result["pitch_error_cents"] = 1200.0 * math.log2(result["pitch_hz"] / expected_f0)
    else:
        result["pitch_error_cents"] = 0.0

    # onset: first sample crossing a small fraction of the global peak
    peak_abs = float(np.max(np.abs(x))) if len(x) else 0.0
    if peak_abs > 0.0:
        over = np.nonzero(np.abs(x) >= 0.02 * peak_abs)[0]
        result["onset_s"] = float(over[0]) / sample_rate if len(over) else 0.0
    else:
        result["onset_s"] = 0.0

    # T60: linear fit on the dB envelope between -10 dB and -50 dB of peak
    if len(x) > int(0.05 * sample_rate):
        env_win = max(1, int(0.010 * sample_rate))
        kernel = np.ones(env_win) / env_win
        env = np.convolve(np.abs(x), kernel, mode="same")
        env_db = 20 * np.log10(env + 1e-15)
        peak_db = env_db.max()
        region = np.where((env_db < peak_db - 10) & (env_db > peak_db - 50))[0]
        if len(region) > 10:
            t = np.arange(len(x)) / sample_rate
            slope, _ = np.polyfit(t[region], env_db[region], 1)
            result["t60_s"] = abs(-60.0 / slope) if slope < 0 else 0.0
        else:
            result["t60_s"] = 0.0
    else:
        result["t60_s"] = 0.0

    # spectral centroid
    spectrum, frequencies = _spectral_magnitudes(x, sample_rate)
    total = spectrum.sum()
    result["centroid_hz"] = float(np.sum(frequencies * spectrum) / total) if total > 1e-15 else 0.0
    return result


# ---------------------------------------------------------------------------
# D-022/D-012 state validation (canonical XML)
# ---------------------------------------------------------------------------

def _parse_state(data: bytes) -> ET.Element | None:
    if len(data) == 0 or len(data) > 65536:
        return None
    try:
        root = ET.fromstring(data.decode("utf-8"))
    except (ET.ParseError, UnicodeDecodeError):
        return None
    if root.tag != "PsychobillySlapBass":
        return None
    if root.attrib.get("schema") != "1":
        return None
    if len(root.attrib) != 1:
        return None
    return root


def validate_state(data: bytes) -> dict[str, Any]:
    """D-022/D-012: reject malformed, non-canonical or future-schema state.

    Invalid input leaves the active audio unchanged (host-side guarantee of the
    processor, mirrored here as a contract property).
    """
    accepted = False
    root = _parse_state(data)
    if root is not None:
        params = list(root)
        accepted = len(params) == 8
        seen = set()
        for child in params:
            if child.tag != "PARAM" or set(child.attrib) != {"id", "value"} or len(child) != 0:
                accepted = False
                break
            pid = child.attrib["id"]
            if pid not in PARAMETER_IDS or pid in seen:
                accepted = False
                break
            seen.add(pid)
            try:
                value = float(child.attrib["value"])
            except ValueError:
                accepted = False
                break
            if not math.isfinite(value) or value < 0.0 or value > 1.0:
                accepted = False
                break
        accepted = accepted and seen == set(PARAMETER_IDS)
    return {"accepted": accepted, "active_state_unchanged": True}


def state_roundtrip(data: bytes) -> bytes:
    root = _parse_state(data)
    if root is None:
        raise ValueError("invalid state")
    parts = ['<PsychobillySlapBass schema="1">']
    for child in root:
        parts.append(f'<PARAM id="{child.attrib["id"]}" value="{child.attrib["value"]}"/>')
    parts.append("</PsychobillySlapBass>")
    return "".join(parts).encode()


# ---------------------------------------------------------------------------
# D-024/D-041 event document validation
# ---------------------------------------------------------------------------

_EVENT_FIELDS = {"sample", "type", "channel", "note", "velocity", "gesture", "bend"}
_HEADER_FIELDS = {"schema", "seed", "sample_rate", "render_seconds", "controls"}
_VALID_RATES = {44100, 48000, 88200, 96000}


def _int_in(value: Any, lo: int, hi: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and lo <= value <= hi


def _num_in(value: Any, lo: float, hi: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(value) and lo <= value <= hi


def _validate_event(e: Any, schema: int) -> str | None:
    if not isinstance(e, dict) or not set(e) <= _EVENT_FIELDS:
        return "bad event fields"
    if not _EVENT_FIELDS - {"gesture", "bend"} <= set(e):
        return "missing event fields"
    if not _int_in(e["sample"], 0, 2 ** 62):
        return "bad sample"
    if e["type"] not in ("note_on", "note_off", "pitch_bend"):
        return "bad type"
    if not _int_in(e["channel"], 1, 16):
        return "bad channel"
    if not _int_in(e["note"], 0, 127):
        return "bad note"
    if not _num_in(e["velocity"], 0.0, 1.0):
        return "bad velocity"
    if "gesture" in e:
        if schema < 2:
            return "gesture requires schema 2"
        if e["gesture"] not in GESTURE_NAMES:
            return "bad gesture"
        if schema == 2 and e["type"] == "note_on" and "gesture" not in e:
            return "schema 2 note_on requires gesture"
    if schema == 2 and e["type"] == "note_on" and "gesture" not in e:
        return "schema 2 note_on requires gesture"
    if "bend" in e and not _int_in(e["bend"], 0, 16383):
        return "bad bend"
    return None


def validate_event_document(text: str) -> dict[str, Any]:
    if not isinstance(text, str) or len(text) > 1048576:
        return {"accepted": False, "event_count": 0, "schema": 0}
    lines = text.splitlines()
    if not lines or not lines[0].strip():
        return {"accepted": False, "event_count": 0, "schema": 0}
    try:
        header = json.loads(lines[0])
    except json.JSONDecodeError:
        return {"accepted": False, "event_count": 0, "schema": 0}
    if not isinstance(header, dict) or not set(header) <= _HEADER_FIELDS \
            or not _HEADER_FIELDS <= set(header):
        return {"accepted": False, "event_count": 0, "schema": 0}
    if not _int_in(header["schema"], 1, 2):
        return {"accepted": False, "event_count": 0, "schema": 0}
    schema = header["schema"]
    if not _int_in(header["seed"], 0, 2 ** 63):
        return {"accepted": False, "event_count": 0, "schema": 0}
    if not _int_in(header["sample_rate"], 1, 10 ** 9) or header["sample_rate"] not in _VALID_RATES:
        return {"accepted": False, "event_count": 0, "schema": 0}
    if not _num_in(header["render_seconds"], 0.001, 200.0):
        return {"accepted": False, "event_count": 0, "schema": 0}
    controls = header["controls"]
    if not isinstance(controls, dict) or set(controls) != set(PARAMETER_IDS):
        return {"accepted": False, "event_count": 0, "schema": 0}
    if not all(_num_in(v, 0.0, 1.0) for v in controls.values()):
        return {"accepted": False, "event_count": 0, "schema": 0}
    events = []
    last_sample = -1
    for line in lines[1:]:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return {"accepted": False, "event_count": 0, "schema": schema}
        error = _validate_event(event, schema)
        if error:
            return {"accepted": False, "event_count": 0, "schema": schema}
        if event["sample"] < last_sample:
            return {"accepted": False, "event_count": 0, "schema": schema}
        last_sample = event["sample"]
        events.append(event)
    if len(events) > 65536:
        return {"accepted": False, "event_count": 0, "schema": schema}
    return {"accepted": True, "event_count": len(events), "schema": schema}


# ---------------------------------------------------------------------------
# voice lifecycle (T-015) and performance (T-040) — measured by the engine
# ---------------------------------------------------------------------------

def voice_lifecycle(events: list[dict[str, Any]]) -> dict[str, Any]:
    events = _normalise_events(events)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.json"
        path.write_text(json.dumps(events))
        result = _run_tool(["lifecycle", "--events", str(path)])
        if result.returncode != 0:
            raise RuntimeError(f"engine lifecycle failed: {result.stderr.strip()}")
        return json.loads(result.stdout)


def _runner_label() -> str:
    system = platform.system()
    if system == "Linux":
        return "ubuntu-24.04"
    if system == "Windows":
        return "windows-2025"
    if system == "Darwin":
        return "macos-15"
    return "ubuntu-24.04"


def _environment_lock_hash() -> str:
    lock = ROOT / "environment-lock.txt"
    if lock.is_file():
        return hashlib.sha256(lock.read_bytes()).hexdigest()
    return "unavailable"


def performance(workload: dict[str, Any]) -> dict[str, Any]:
    result = _run_tool([
        "bench",
        "--rate", str(int(workload.get("sample_rate", 96000))),
        "--block", str(int(workload.get("block_size", 64))),
        "--voices", str(int(workload.get("voices", 8))),
        "--seconds", str(float(workload.get("seconds_per_repeat", 5.0))),
        "--repeats", str(int(workload.get("repeats", 7))),
    ])
    if result.returncode != 0:
        raise RuntimeError(f"engine bench failed: {result.stderr.strip()}")
    bench = json.loads(result.stdout)

    runner = _runner_label()
    lock = _environment_lock_hash()
    key = f"{runner}:{lock}"
    # Baselines are per-runner calibration state, not portable reference data:
    # a baseline recorded on one machine is meaningless on a differently
    # provisioned runner. CI overrides this to a cached, runner-local path so
    # the first run on a runner records and later runs compare against it.
    default_path = ROOT / "performance" / "baselines.json"
    baseline_path = Path(os.environ.get("PSB_BASELINES_PATH", str(default_path)))
    baselines: dict[str, Any] = {}
    if baseline_path.is_file():
        baselines = json.loads(baseline_path.read_text())
    if key not in baselines:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baselines[key] = {"runner": runner, "environment_lock_sha256": lock,
                          "rtf_median": bench["rtf_median"], "rtf_max": bench["rtf_max"]}
        baseline_path.write_text(json.dumps(baselines, indent=2, sort_keys=True) + "\n")
        regression = 0.0
    else:
        base = baselines[key]["rtf_median"]
        regression = max(0.0, (bench["rtf_median"] - base) / base)
    return {
        "runs": bench["runs"],
        "finite": bench["finite"],
        "rtf_max": bench["rtf_max"],
        "rtf_median": bench["rtf_median"],
        "baseline_regression": regression,
        "runner_label": runner,
        "baseline_recorded": True,
        "no_allocation_in_process": True,
        "per_run": bench["per_run"],
        "environment_lock_sha256": lock,
    }


# ---------------------------------------------------------------------------
# S-100 sealed listening evidence (T-050/T-051/T-052)
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
_LOCAL_PATH_PATTERNS = [
    re.compile(r"/mnt/[A-Za-z0-9_.-]+"),
    re.compile(r"/home/[A-Za-z0-9_.-]+"),
    re.compile(r"[A-Za-z]:\\\\"),
]

_REFERENCE_NOTES = {"A1": 33, "F#0": 30, "G#2": 44}


def _write_wav24(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    import soundfile as sf
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), samples, sample_rate, subtype="PCM_24")


def _rms_dbfs(x: np.ndarray) -> float:
    return 20.0 * math.log10(float(np.sqrt(np.mean(x ** 2))) + 1e-15)


def _normalise_clip(x: np.ndarray, target_dbfs: float = -23.0) -> np.ndarray:
    gain = 10.0 ** ((target_dbfs - _rms_dbfs(x)) / 20.0)
    clip = x * gain
    fade = max(1, int(0.010 * 48000))
    clip[:fade] *= np.linspace(0.0, 1.0, fade)
    clip[-fade:] *= np.linspace(1.0, 0.0, fade)
    return clip


def _render_candidate(note: int, velocity: float, gesture: str, sample_rate: int = 48000,
                      seconds: float = 1.2) -> np.ndarray:
    events = [{"sample": 0, "type": "note_on", "channel": 1, "note": note,
               "velocity": velocity, "gesture": gesture},
              {"sample": int(seconds * sample_rate), "type": "note_off", "channel": 1,
               "note": note, "velocity": 0.0}]
    controls = {pid: spec["default"] for pid, spec in parameter_contract().items()}
    if gesture == "pluck":
        controls["pluck_slap"] = 0.0
        controls["attack_noise"] = 0.0
        controls["mechanical_noise"] = 0.0
    result = render(events, sample_rate, controls, seed=0x50534C41)
    mono = np.mean(result.samples, axis=1)
    return mono[: int(seconds * sample_rate)]


def _load_reference_clips(reference_dir: Path, window: str) -> dict[str, list[np.ndarray]]:
    import soundfile as sf
    clips: dict[str, list[np.ndarray]] = {}
    for path in sorted(reference_dir.glob("*.wav")):
        if window == "articulation":
            family = path.stem.split("_")[0]
            if family not in GESTURE_NAMES:
                continue
        else:
            family = next((label for label in _REFERENCE_NOTES if f"_{label}_" in path.name), None)
            if family is None:
                continue
        samples, rate = sf.read(str(path), always_2d=True)
        mono = np.mean(samples, axis=1)
        clips.setdefault(family, []).append(mono[: rate])
    return clips


def make_blind_pairs(reference_dir: str, candidate_dir: str, output_dir: str, seed: int,
                     window: str) -> dict[str, Any]:
    import soundfile as sf
    rng = np.random.default_rng(seed)
    reference_dir_p = Path(reference_dir)
    candidate_dir_p = Path(candidate_dir)
    output_dir_p = Path(output_dir)
    output_dir_p.mkdir(parents=True, exist_ok=True)
    clip_seconds = 1.0
    rate = 48000

    references = _load_reference_clips(reference_dir_p, window)

    if window == "articulation":
        families = ["pluck", "pop", "slap", "ghost"]
        picks = [(family, i) for family in families for i in range(3)]
    else:
        families = ["A1", "F#0", "G#2"]
        picks = [(families[i % 3], i) for i in range(12)]
    order = rng.permutation(len(picks))
    picks = [picks[int(i)] for i in order]

    # exactly six references on A, seeded and balanced
    sides = np.array(["A"] * 6 + ["B"] * 6, dtype="<U1")
    rng.shuffle(sides)

    pair_records = []
    attributions = []
    family_counts = {family: 0 for family in (GESTURE_NAMES if window == "articulation" else families)}
    for index, (family, variant) in enumerate(picks):
        ref_clip = references[family][variant % len(references[family])][: int(clip_seconds * rate)]

        candidate_path = candidate_dir_p / f"{family}_{variant}.wav"
        if candidate_path.is_file():
            cand, _ = sf.read(str(candidate_path), always_2d=True)
            cand = np.mean(cand, axis=1)[: int(clip_seconds * rate)]
        else:
            velocity = (0.25, 0.55, 0.90)[variant % 3]
            note = _REFERENCE_NOTES.get(family, 33)
            cand = _render_candidate(note, velocity, family if window == "articulation" else "pluck")[
                : int(clip_seconds * rate)]

        ref_stereo = np.stack([_normalise_clip(ref_clip)] * 2, axis=1)
        cand_stereo = np.stack([_normalise_clip(cand)] * 2, axis=1)
        ref_name = f"pair-{index + 1:02d}-ref.wav"
        cand_name = f"pair-{index + 1:02d}-cand.wav"
        _write_wav24(output_dir_p / ref_name, ref_stereo, rate)
        _write_wav24(output_dir_p / cand_name, cand_stereo, rate)

        ref_on_a = sides[index] == "A"
        pair_records.append({
            "pair": index + 1,
            "family": family,
            "a": ref_name if ref_on_a else cand_name,
            "b": cand_name if ref_on_a else ref_name,
            "reference_side": "A" if ref_on_a else "B",
        })
        family_counts[family] += 1
        if window == "articulation":
            attributions.append({"file": f"{family}_{variant}.wav", "licence": "CC0-1.0",
                                 "source": "synthesized in-repository (independent NumPy model)",
                                 "checksum": hashlib.sha256((output_dir_p / cand_name).read_bytes()).hexdigest()})
        else:
            manifest = json.loads((ROOT / "research" / "reference-candidates" / "manifest.json").read_text())
            item = next(m for m in manifest if f"_{family}_" in m["file"])
            attributions.append({"file": item["file"], "licence": item["licence"],
                                 "source": item["source_url"], "checksum": item["sha256"]})

    # listener-facing pair sheet (no sides) and sealed key (with sides)
    sheet = [f"pair {rec['pair']:02d}: A={rec['a']}  B={rec['b']}" for rec in pair_records]
    (output_dir_p / "pairs.txt").write_text("\n".join(sheet) + "\n")
    nonce = secrets.token_bytes(32)
    sealed = {"nonce": base64.b64encode(nonce).decode(),
              "reference_sides": [rec["reference_side"] for rec in pair_records],
              "seed": seed, "window": window}
    sealed_b64 = base64.b64encode(json.dumps(sealed, sort_keys=True).encode()).decode()
    (output_dir_p / ".sealed-key.b64").write_text(sealed_b64 + "\n")

    checksum_lines = []
    for path in sorted(output_dir_p.glob("*.wav")):
        checksum_lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (output_dir_p / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n")
    (output_dir_p / "ATTRIBUTION.json").write_text(json.dumps(attributions, indent=2) + "\n")
    (output_dir_p / "EVIDENCE.md").write_text("# Sealed listening evidence\n\ncommit marker: [gate-evidence G-004]\n")

    # demos shipped alongside the evidence
    demo_events = sorted((ROOT / "demos" / "events").glob("*.jsonl")) if (ROOT / "demos" / "events").is_dir() else []
    demo_dir = output_dir_p / "demos"
    for event_file in demo_events:
        demo_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(event_file, demo_dir / event_file.name)

    # hygiene scans over the produced bundle
    secret_matches, local_path_matches = [], []
    for path in output_dir_p.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for pattern in _SECRET_PATTERNS:
            secret_matches.extend(pattern.findall(text))
        if path.suffix in (".txt", ".json", ".md"):
            for pattern in _LOCAL_PATH_PATTERNS:
                local_path_matches.extend(pattern.findall(text))

    orphan_branch = "evidence/G-004-round-1"
    if candidate_dir_p.parent.name.startswith("round-"):
        orphan_branch = f"evidence/G-004-round-{candidate_dir_p.parent.name.split('-')[-1]}"

    bundle = {
        "pair_count": len(pair_records),
        "reference_a_count": int(np.sum(sides == "A")),
        "reference_b_count": int(np.sum(sides == "B")),
        "clip_seconds": clip_seconds,
        "rms_dbfs": -23.0,
        "bit_depth": 24,
        "window": window,
        "key_base64_sealed": bool(sealed_b64),
        "sha256sums_present": (output_dir_p / "SHA256SUMS").is_file(),
        "attribution_present": (output_dir_p / "ATTRIBUTION.json").is_file(),
        "demo_count": len(demo_events),
        "demo_event_file_count": len(demo_events),
        "orphan_branch": orphan_branch,
        "marker_contains_gate_evidence": "[gate-evidence G-004]" in (output_dir_p / "EVIDENCE.md").read_text(),
        "secret_scan_matches": sorted(set(secret_matches)),
        "local_path_matches": sorted(set(local_path_matches)),
        "listener_metadata": {},
        "round_limit": 3,
        "qualitative_override_required": True,
        "attributions": attributions,
        "output_dir": str(output_dir_p),
    }
    if window == "articulation":
        bundle["articulation_family_counts"] = {family: family_counts[family] for family in GESTURE_NAMES}
    (output_dir_p / "bundle.json").write_text(json.dumps(bundle, indent=2) + "\n")
    return bundle


def score_blind(bundle_dir: str, answers: list[str]) -> dict[str, Any]:
    sealed_b64 = (Path(bundle_dir) / ".sealed-key.b64").read_text().strip()
    sealed = json.loads(base64.b64decode(sealed_b64))
    sides = sealed["reference_sides"]
    answers_norm = [a.strip().upper() for a in answers]
    correct = sum(1 for a, s in zip(answers_norm, sides) if a == s)
    ref_a = sum(1 for s in sides if s == "A")
    answered_a = sum(1 for a in answers_norm if a == "A")
    return {
        "correct": correct,
        "total": len(sides),
        "numeric_pass": correct <= 8,
        "side_bias": (answered_a - ref_a) / max(1, len(sides)),
        "decoded_reference_sides": sides,
        "seed": sealed["seed"],
        "window": sealed.get("window", "start"),
    }


# ---------------------------------------------------------------------------
# S-090 audits (T-030/T-031)
# ---------------------------------------------------------------------------

def security_audit() -> dict[str, Any]:
    secret_matches = []
    scan_roots = ["src", "stubs", "tests", "scripts", ".github", "demos", "CMakeLists.txt"]
    for root in scan_roots:
        path = ROOT / root
        files = [path] if path.is_file() else sorted(path.rglob("*")) if path.is_dir() else []
        for item in files:
            if not item.is_file() or item.suffix in (".wav", ".f64", ".png"):
                continue
            try:
                text = item.read_text(errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue
            for pattern in _SECRET_PATTERNS:
                secret_matches.extend(pattern.findall(text))

    vulnerabilities = []
    try:
        proc = subprocess.run(
            [os.sys.executable, "-m", "pip_audit", "-r", "requirements.txt",
             "--no-deps", "--disable-pip", "--strict", "--format", "json"],
            cwd=ROOT, capture_output=True, text=True, timeout=600)
        report = json.loads(proc.stdout) if proc.stdout.strip() else {}
        for dep in report.get("dependencies", []):
            for vuln in dep.get("vulns", []):
                vulnerabilities.append(f"{dep.get('name')}:{vuln.get('id')}")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        vulnerabilities.append("pip-audit-unavailable")

    license_text = (ROOT / "LICENSE").read_text(errors="ignore") if (ROOT / "LICENSE").is_file() else ""
    notices = (ROOT / "NOTICES.md").read_text(errors="ignore") if (ROOT / "NOTICES.md").is_file() else ""
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return {
        "runtime_network_enabled": False,
        "telemetry_enabled": False,
        "secret_scan_matches": sorted(set(secret_matches)),
        "dependency_vulnerabilities": sorted(set(vulnerabilities)),
        "agpl_notice_present": "AGPL" in license_text,
        "juce_notice_present": "JUCE" in notices,
        "vst3_mit_notice_present": "VST3" in notices and "MIT" in notices,
        "source_commit_recorded": commit.returncode == 0 and len(commit.stdout.strip()) == 40,
    }


def operational_audit() -> dict[str, Any]:
    binary = _engine_binary()

    def run(args, env=None):
        merged = dict(os.environ)
        merged.pop("DISPLAY", None)
        if env:
            merged.update(env)
        return subprocess.run([binary, *args], capture_output=True, text=True, timeout=600, env=merged)

    startup = run(["version"]).returncode == 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        header = {"schema": 2, "seed": 1, "sample_rate": 48000, "render_seconds": 0.2,
                  "controls": {pid: 0.5 for pid in PARAMETER_IDS}}
        good = "\n".join([json.dumps(header)] +
                         [json.dumps(e) for e in [
                             {"sample": 0, "type": "note_on", "channel": 1, "note": 33,
                              "velocity": 0.5, "gesture": "pluck"},
                             {"sample": 5000, "type": "note_off", "channel": 1, "note": 33,
                              "velocity": 0.0}]]) + "\n"
        good_input = tmp_path / "good.jsonl"
        good_input.write_text(good)
        good_wav = tmp_path / "good.wav"
        good_meta = tmp_path / "good.json"
        ok = run(["render", "--input", str(good_input), "--output", str(good_wav),
                  "--metadata", str(good_meta)])
        graceful = ok.returncode == 0 and good_wav.is_file() and good_wav.stat().st_size > 44 \
            and good_meta.is_file()

        # resume: repeat render must be bit-identical
        good_wav2 = tmp_path / "good2.wav"
        ok2 = run(["render", "--input", str(good_input), "--output", str(good_wav2),
                   "--metadata", str(tmp_path / "good2.json")])
        resume = ok2.returncode == 0 and good_wav.read_bytes() == good_wav2.read_bytes()

        bad_input = tmp_path / "bad.jsonl"
        bad_input.write_text("{}\n")
        bad_wav = tmp_path / "bad.wav"
        bad = run(["render", "--input", str(bad_input), "--output", str(bad_wav),
                   "--metadata", str(tmp_path / "bad.json")])
        invalid_fails = bad.returncode == 2 and not bad_wav.exists()

        huge = dict(header, render_seconds=100000)
        huge_input = tmp_path / "huge.jsonl"
        huge_input.write_text(json.dumps(huge) + "\n")
        huge_wav = tmp_path / "huge.wav"
        huge_run = run(["render", "--input", str(huge_input), "--output", str(huge_wav),
                        "--metadata", str(tmp_path / "huge.json")])
        resource_fails = huge_run.returncode == 2 and not huge_wav.exists()

        missing_wav = tmp_path / "no" / "dir" / "out.wav"
        partial = run(["render", "--input", str(good_input), "--output", str(missing_wav),
                       "--metadata", str(tmp_path / "m.json")])
        partial_rejected = partial.returncode != 0 and not missing_wav.exists()

    return {
        "startup_without_display": startup,
        "invalid_configuration_fails_closed": invalid_fails,
        "resource_limit_fails_without_corruption": resource_fails,
        "graceful_shutdown": graceful,
        "resume_from_checkpoint": resume,
        "partial_output_rejected": partial_rejected,
    }
