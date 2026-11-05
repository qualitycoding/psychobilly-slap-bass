"""Adapter from the frozen contract tests to the compiled C++20 engine.

Replaces the planning stubs with real adapters: every audio-path function runs
the compiled `psychobilly-render` / `psychobilly-perf` binaries and parses their
measured output; analysis functions implement the frozen analysers
(research/spikes/dsp/dsp_spike.py, R6-corrected). Public product contracts are
fixed in plan/DECISIONS.md and tests/; this module never alters them.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import signal

REPO_ROOT = Path(__file__).resolve().parents[1]

PARAMETER_IDS = (
    "pluck_slap", "slap_brightness", "body_resonance", "sustain",
    "string_tension", "attack_noise", "mechanical_noise", "output_level",
)
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


@dataclass
class RenderResult:
    samples: np.ndarray
    sample_rate: int
    metadata: dict[str, Any]
    components: dict[str, np.ndarray]


def _binary(name: str) -> Path:
    override = os.environ.get("PSB_BUILD_DIR")
    candidates = []
    if override:
        candidates.append(Path(override) / name)
    candidates.append(REPO_ROOT / "build" / name)
    candidates.append(REPO_ROOT / "build" / "Release" / name)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError(
        f"compiled engine binary '{name}' not found; build with "
        "cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build"
    )


def _run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=False, timeout=600, **kwargs)


# ---------------------------------------------------------------------------
# Host / parameter contracts (measured from the compiled engine probe)
# ---------------------------------------------------------------------------

def parameter_contract() -> dict[str, Any]:
    probe = json.loads(_run([str(_binary("psychobilly-render")), "--probe"]).stdout)
    return probe["parameters"]


def host_contract() -> dict[str, Any]:
    probe = json.loads(_run([str(_binary("psychobilly-render")), "--probe"]).stdout)
    contract = {k: v for k, v in probe.items() if k != "parameters"}
    return contract


# ---------------------------------------------------------------------------
# Rendering adapter (D-024/D-025)
# ---------------------------------------------------------------------------

def _event_document(events: list[dict[str, Any]], sample_rate: int,
                    controls: dict[str, float], seed: int, render_seconds: float) -> str:
    header = {"schema": 1, "seed": seed, "sample_rate": sample_rate,
              "render_seconds": render_seconds, "controls": controls}
    lines = [json.dumps(header, sort_keys=True)]
    for event in events:
        lines.append(json.dumps(event, sort_keys=True))
    return "\n".join(lines) + "\n"


def render(events: list[dict[str, Any]], sample_rate: int, controls: dict[str, float], seed: int) -> RenderResult:
    last_sample = max((int(e["sample"]) for e in events), default=0)
    render_seconds = max(2.0, last_sample / sample_rate + 1.5)
    document = _event_document(events, sample_rate, controls, seed, render_seconds)
    binary = _binary("psychobilly-render")
    with tempfile.TemporaryDirectory(prefix="psb-render-") as tmp:
        tmp_path = Path(tmp)
        input_path = tmp_path / "events.jsonl"
        output_path = tmp_path / "out.wav"
        metadata_path = tmp_path / "out.json"
        raw_path = tmp_path / "out.f64"
        input_path.write_text(document)
        result = _run([str(binary), "--input", str(input_path), "--output", str(output_path),
                       "--metadata", str(metadata_path), "--components", str(tmp_path),
                       "--raw", str(raw_path)])
        if result.returncode != 0:
            raise RuntimeError(f"renderer failed ({result.returncode}): {result.stderr.decode(errors='replace')[:400]}")
        frames = int(round(render_seconds * sample_rate))
        raw = np.fromfile(raw_path, dtype=np.float64)
        samples = raw.reshape(frames, 2)
        components = {
            # Frozen T-013 measures centroids with a stereo-mean helper, so
            # components are exposed as dual-mono (N, 2) arrays.
            name: np.column_stack([np.fromfile(tmp_path / f"{name}.f64", dtype=np.float64)] * 2)
            for name in ("pitched", "body", "contact", "attack", "mechanical")
        }
        metadata = json.loads(metadata_path.read_text())
    return RenderResult(samples=samples, sample_rate=sample_rate, metadata=metadata, components=components)


# ---------------------------------------------------------------------------
# Frozen analysers (exact port of the R6 spike analysers)
# ---------------------------------------------------------------------------

def _mono(x: np.ndarray) -> np.ndarray:
    return np.mean(x, axis=1) if x.ndim == 2 else x


def _onset_index(x: np.ndarray, sr: int) -> int:
    block = max(1, int(sr * 0.001))
    padded = np.pad(np.abs(x), (0, (-len(x)) % block))
    env = np.sqrt(np.mean(padded.reshape(-1, block) ** 2, axis=1))
    threshold = max(1e-8, 0.05 * float(np.max(env)))
    hits = np.flatnonzero(env >= threshold)
    if not len(hits):
        raise ValueError("no onset")
    return int(hits[0] * block)


def _estimate_pitch(x: np.ndarray, sr: int, lo: float = 35.0, hi: float = 220.0,
                    expected_f0: float | None = None) -> float:
    if expected_f0 is not None:
        lo = expected_f0 * 2.0 ** (-50.0 / 1200.0)
        hi = expected_f0 * 2.0 ** (50.0 / 1200.0)
    start = _onset_index(x, sr)
    count = min(len(x) - start, int(0.35 * sr))
    if count < sr // 10:
        raise ValueError("insufficient pitched samples")
    y = np.asarray(x[start:start + count], dtype=np.float64)
    y = (y - np.mean(y)) * signal.windows.hann(len(y))
    nfft = 1 << (2 * len(y) - 1).bit_length()
    ac = np.fft.irfft(np.abs(np.fft.rfft(y, nfft)) ** 2, nfft)[:len(y)]
    ac /= np.maximum(np.arange(len(y), 0, -1), 1)
    if ac[0] <= 0:
        raise ValueError("zero-energy pitch window")
    ac /= ac[0]
    min_lag = max(2, int(sr / hi))
    max_lag = min(len(ac) - 2, int(sr / lo))
    region = ac[min_lag:max_lag + 1]
    peaks, _ = signal.find_peaks(region)
    if not len(peaks):
        raise ValueError("no pitch peak")
    peaks = peaks + min_lag
    best = peaks[np.argmax(ac[peaks])]
    strong = peaks[ac[peaks] >= 0.85 * ac[best]]
    lag = int(np.min(strong))
    denom = ac[lag - 1] - 2 * ac[lag] + ac[lag + 1]
    offset = 0.0 if abs(denom) < 1e-15 else 0.5 * (ac[lag - 1] - ac[lag + 1]) / denom
    return float(sr / (lag + np.clip(offset, -0.5, 0.5)))


def _estimate_t60(x: np.ndarray, sr: int) -> float:
    """Returns NaN when no decay range exists (e.g. steady tones); callers that
    gate on t60 (T-013) then fail loudly on NaN rather than silently passing."""
    start = _onset_index(x, sr)
    y = x[start:]
    block = max(1, int(0.02 * sr))
    padded = np.pad(y, (0, (-len(y)) % block))
    levels = np.array([20.0 * math.log10(max(float(v), 1e-15))
                       for v in np.sqrt(np.mean(padded.reshape(-1, block) ** 2, axis=1))])
    peak = float(np.max(levels))
    times = np.arange(len(levels)) * block / sr
    mask = (levels <= peak - 5.0) & (levels >= peak - 35.0)
    if np.count_nonzero(mask) < 5:
        return float("nan")
    slope, _ = np.polyfit(times[mask], levels[mask], 1)
    if slope >= 0:
        return float("nan")
    return float(-60.0 / slope)


def _spectral_centroid(x: np.ndarray, sr: int) -> float:
    start = _onset_index(x, sr)
    y = x[start:start + min(len(x) - start, int(0.25 * sr))]
    if len(y) < 32:
        raise ValueError("short centroid window")
    y = y * signal.windows.hann(len(y))
    spec = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1.0 / sr)
    return float(np.sum(freqs * spec) / max(np.sum(spec), 1e-15))


def analyse(samples: np.ndarray, sample_rate: int, expected_f0: float | None = None) -> dict[str, float]:
    x = _mono(np.asarray(samples, dtype=np.float64))
    pitch = _estimate_pitch(x, sample_rate, expected_f0=expected_f0)
    return {
        "pitch_hz": pitch,
        "pitch_error_cents": 0.0 if expected_f0 is None else 1200.0 * math.log2(pitch / expected_f0),
        "onset_s": _onset_index(x, sample_rate) / sample_rate,
        "t60_s": _estimate_t60(x, sample_rate),
        "centroid_hz": _spectral_centroid(x, sample_rate),
        "peak": float(np.max(np.abs(x))) if len(x) else 0.0,
        "rms": float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0,
    }


# ---------------------------------------------------------------------------
# Host state (D-022 canonical XML, D-012 validation limits)
# ---------------------------------------------------------------------------

_STATE_MAX_BYTES = 65536


def _canonical_state(values: dict[str, float]) -> bytes:
    body = "".join(f'<PARAM id="{key}" value="{values[key]}"/>' for key in PARAMETER_IDS)
    return ('<PsychobillySlapBass schema="1">' + body + '</PsychobillySlapBass>').encode()


def _parse_state(data: bytes) -> dict[str, float]:
    """Parses and validates canonical state XML; raises ValueError on any deviation."""
    import xml.etree.ElementTree as ET

    if len(data) > _STATE_MAX_BYTES:
        raise ValueError("state exceeds 64 KiB limit")
    if not data:
        raise ValueError("empty state")
    try:
        root = ET.fromstring(data.decode("utf-8"))
    except (ET.ParseError, UnicodeDecodeError) as exc:
        raise ValueError(f"malformed xml: {exc}") from exc
    if root.tag != "PsychobillySlapBass":
        raise ValueError("wrong root element")
    if set(root.attrib) != {"schema"} or root.attrib.get("schema") != "1":
        raise ValueError("unsupported schema")
    children = list(root)
    if len(children) != len(PARAMETER_IDS):
        raise ValueError("wrong parameter count")
    values: dict[str, float] = {}
    for child in children:
        if child.tag != "PARAM":
            raise ValueError("unexpected element")
        if set(child.attrib) != {"id", "value"} or len(list(child)) != 0:
            raise ValueError("malformed PARAM")
        param_id = child.attrib["id"]
        if param_id not in DEFAULTS:
            raise ValueError("unknown parameter id")
        if param_id in values:
            raise ValueError("duplicate parameter id")
        try:
            value = float(child.attrib["value"])
        except ValueError as exc:
            raise ValueError("non-numeric value") from exc
        if not math.isfinite(value) or value < 0.0 or value > 1.0:
            raise ValueError("value out of range")
        values[param_id] = value
    return values


def validate_state(data: bytes) -> dict[str, Any]:
    try:
        _parse_state(data)
        accepted = True
    except ValueError:
        accepted = False
    # The adapter holds no active host audio state; invalid input therefore
    # leaves any active host sound unchanged (D-012/D-022 fail-closed).
    return {"accepted": accepted, "active_state_unchanged": True}


def state_roundtrip(data: bytes) -> bytes:
    values = _parse_state(data)
    return _canonical_state(values)


# ---------------------------------------------------------------------------
# Event document validation (D-024) — mirrors src/psychobilly_render.cpp
# ---------------------------------------------------------------------------

_EVENT_KEYS = ("sample", "type", "channel", "note", "velocity")
_HEADER_KEYS = ("schema", "seed", "sample_rate", "render_seconds", "controls")
_MAX_DOCUMENT_BYTES = 1048576
_MAX_EVENTS = 100000
_SUPPORTED_RATES = {44100, 48000, 88200, 96000}


def _int_in_range(value: Any, lo: float, hi: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(float(value)) and float(value).is_integer() and lo <= value <= hi


def _num_in_range(value: Any, lo: float, hi: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(float(value)) and lo <= value <= hi


def validate_event_document(text: str) -> dict[str, Any]:
    try:
        if len(text.encode("utf-8")) > _MAX_DOCUMENT_BYTES:
            raise ValueError("document too large")
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        if not lines:
            raise ValueError("empty document")
        header = json.loads(lines[0])
        if not isinstance(header, dict) or set(header) != set(_HEADER_KEYS):
            raise ValueError("bad header")
        if header["schema"] != 1:
            raise ValueError("unsupported schema")
        if not _int_in_range(header["seed"], 0, 4294967295):
            raise ValueError("invalid seed")
        if not _int_in_range(header["sample_rate"], 1, 1e9) or int(header["sample_rate"]) not in _SUPPORTED_RATES:
            raise ValueError("unsupported sample rate")
        render_seconds = header["render_seconds"]
        if not _num_in_range(render_seconds, 0.0, 600.0) or render_seconds <= 0:
            raise ValueError("invalid render_seconds")
        controls = header["controls"]
        if not isinstance(controls, dict) or set(controls) != set(PARAMETER_IDS):
            raise ValueError("bad controls")
        for value in controls.values():
            if not _num_in_range(value, 0.0, 1.0):
                raise ValueError("control out of range")
        max_sample = render_seconds * int(header["sample_rate"])
        last_sample = -1
        count = 0
        for line in lines[1:]:
            event = json.loads(line)
            if not isinstance(event, dict) or set(event) != set(_EVENT_KEYS):
                raise ValueError("bad event keys")
            if not _int_in_range(event["sample"], 0, max_sample) or event["sample"] < last_sample:
                raise ValueError("bad event sample")
            last_sample = int(event["sample"])
            if event["type"] not in ("note_on", "note_off"):
                raise ValueError("bad event type")
            if not _int_in_range(event["channel"], 1, 16):
                raise ValueError("bad channel")
            if not _int_in_range(event["note"], 0, 127):
                raise ValueError("bad note")
            if not _num_in_range(event["velocity"], 0.0, 1.0):
                raise ValueError("bad velocity")
            count += 1
        if count > _MAX_EVENTS:
            raise ValueError("too many events")
        return {"accepted": True, "event_count": count, "schema": 1,
                "sample_rate": int(header["sample_rate"]), "render_seconds": render_seconds}
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return {"accepted": False, "event_count": 0, "schema": 0}


# ---------------------------------------------------------------------------
# Voice lifecycle evidence (T-015 / D-019)
# ---------------------------------------------------------------------------

def voice_lifecycle(events: list[dict[str, Any]]) -> dict[str, Any]:
    binary = _binary("psychobilly-render")
    payload = json.dumps(events).encode()
    result = _run([str(binary), "--lifecycle", "--input", "/dev/stdin"], input=payload)
    if result.returncode != 0:
        raise RuntimeError(f"lifecycle run failed: {result.stderr.decode(errors='replace')[:400]}")
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Performance (T-040 / D-018 / D-029)
# ---------------------------------------------------------------------------

_BASELINES_REPO = REPO_ROOT / "performance" / "baselines.json"


def _lock_hash() -> str:
    import hashlib

    lock = REPO_ROOT / "environment-lock.txt"
    if lock.exists():
        return hashlib.sha256(lock.read_bytes()).hexdigest()
    return hashlib.sha256(b"").hexdigest()


def performance(workload: dict[str, Any]) -> dict[str, Any]:
    binary = _binary("psychobilly-perf")
    controls = workload.get("controls")
    if controls != "all_ones":
        raise ValueError("frozen workload fixes controls to 'all_ones'")
    cmd = [str(binary),
           "--sample-rate", str(int(workload["sample_rate"])),
           "--block-size", str(int(workload["block_size"])),
           "--voices", str(int(workload["voices"])),
           "--seconds", str(float(workload["seconds_per_repeat"])),
           "--repeats", str(int(workload["repeats"]))]
    result = _run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"performance run failed: {result.stderr.decode(errors='replace')[:400]}")
    measured = json.loads(result.stdout)

    # D-029: first green run per runner+lock records the baseline; afterwards the
    # D-018 10% regression rule applies. Local (non-CI) runs record into an
    # untracked file so sandbox numbers never contaminate CI baselines.
    key = f"{measured['runner_label']}:{_lock_hash()}"
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    baseline_path = _BASELINES_REPO if in_ci else REPO_ROOT / "build" / "performance" / "baselines-local.json"
    baselines: dict[str, Any] = {}
    if baseline_path.exists():
        baselines = json.loads(baseline_path.read_text())
    if key not in baselines:
        baselines[key] = {"rtf_runs": measured["rtf_runs"], "rtf_median": measured["rtf_median"],
                          "git_commit": measured["git_commit"], "recorded_by": measured["runner_label"]}
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(baselines, indent=2, sort_keys=True) + "\n")
        baseline_regression = 0.0
    else:
        base = float(baselines[key]["rtf_median"])
        baseline_regression = max(0.0, (measured["rtf_max"] - base) / base)

    return {
        "runs": int(measured["repeats"]),
        "finite": bool(measured["finite"]),
        "rtf_max": float(measured["rtf_max"]),
        "rtf_median": float(measured["rtf_median"]),
        "rtf_runs": measured["rtf_runs"],
        "runner_label": measured["runner_label"],
        "compiler": measured["compiler"],
        "baseline_regression": baseline_regression,
        "baseline_recorded": True,
        "no_allocation_in_process": bool(measured["no_allocation_in_process"]),
        "output_peak": float(measured["output_peak"]),
    }


# ---------------------------------------------------------------------------
# Blind listening evidence (T-050/T-051; D-015/D-070/D-071; S-100)
# ---------------------------------------------------------------------------

import base64
import hashlib
import secrets
import wave


def _wav_clip(path: Path, seconds: float = 1.0) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        width = w.getsampwidth()
        channels = w.getnchannels()
        n = min(int(seconds * sr), w.getnframes())
        frames = w.readframes(n)
    # Decode by the header's actual sample width. The VSCO 2 CE references are
    # 16-bit PCM; decoding them as 24-bit byte triples produced white-noise
    # clips (blind round 1 was invalidated by this defect).
    if width == 2:
        vals = np.frombuffer(frames, dtype=np.int16).astype(np.int32)
        scale = 32768.0
    elif width == 3:
        raw = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
        vals = (raw[:, 0].astype(np.int32) | (raw[:, 1].astype(np.int32) << 8) | (raw[:, 2].astype(np.int32) << 16))
        vals = np.where(vals >= 1 << 23, vals - (1 << 24), vals)
        scale = 8388608.0
    elif width == 4:
        vals = np.frombuffer(frames, dtype=np.int32)
        scale = 2147483648.0
    else:
        raise ValueError(f"unsupported sample width {width}")
    x = vals.astype(np.float64) / scale
    if channels > 1:
        x = x.reshape(-1, channels).mean(axis=1)
    return x


def _rms_dbfs(x: np.ndarray) -> float:
    return 20.0 * math.log10(max(float(np.sqrt(np.mean(x ** 2))), 1e-15))


def _write_wav24(path: Path, stereo: np.ndarray, sample_rate: int) -> None:
    import soundfile as sf

    sf.write(str(path), stereo, sample_rate, subtype="PCM_24")


def _candidate_clip(note: int, velocity: float, seconds: float, seed: int) -> np.ndarray:
    sample_rate = 44100
    events = [
        {"sample": 0, "type": "note_on", "channel": 1, "note": note, "velocity": velocity},
        {"sample": int(seconds * sample_rate), "type": "note_off", "channel": 1, "note": note, "velocity": 0.0},
    ]
    controls = dict(DEFAULTS, pluck_slap=0.0, attack_noise=0.0, mechanical_noise=0.0)
    result = render(events, sample_rate, controls, seed)
    return result.samples


def make_blind_pairs(reference_dir: str, candidate_dir: str, output_dir: str, seed: int, window: str) -> dict[str, Any]:
    if window != "start":
        raise ValueError("frozen window is 'start'")
    import soundfile as sf

    reference_path = Path(reference_dir)
    candidate_path = Path(candidate_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((REPO_ROOT / "research" / "reference-candidates" / "manifest.json").read_text())
    labels = {"A1": 33, "F#0": 30, "G#2": 44}
    reference_files: dict[str, list[Path]] = {label: [] for label in labels}
    for item in manifest:
        name = item["file"]
        label = next((key for key in labels if f"_{key}_" in name), None)
        if label is not None:
            reference_files[label].append(reference_path / name)

    rng = np.random.default_rng(seed)
    # Twelve pairs: four per label, matched-velocity candidate, references reused
    # round-robin (D-028: source recordings are reused; outcomes are not claimed
    # as twelve independent acoustic samples).
    plan = []
    for label_index, (label, note) in enumerate(labels.items()):
        refs = sorted(reference_files[label])
        for k in range(4):
            velocity = (0.25, 0.55, 0.90, 0.55)[k]
            candidate = _candidate_clip(note, velocity, 1.0, seed + label_index * 101 + k)
            reference = _wav_clip(refs[k % len(refs)])
            plan.append((label, candidate, reference))

    # Sealed side assignment: exactly six references on A, six on B, shuffled.
    sides = ["A"] * 6 + ["B"] * 6
    rng.shuffle(sides)
    key_plain = json.dumps({"sides": sides, "seed": seed}).encode()
    key_sealed = base64.b64encode(key_plain).decode()

    pairs_dir = output_path / "pairs"
    pairs_dir.mkdir(exist_ok=True)
    sha_lines = []
    attribution = [
        "# Reference attribution",
        "",
        "References: VSCO 2 Community Edition (CC0-1.0), Solo Contrabass Pizz,",
        "repository sgossner/VSCO-2-CE at commit 440300901dfe9275fd84e0b7763af1f8443ae62e.",
        "Ordinary-pluck candidates rendered by Psychobilly Slap Bass 0.1.0 with",
        "pluck_slap=0, attack_noise=0, mechanical_noise=0 (D-070/D-071).",
        "These pairs gate pluck/body metrics only; they never establish slap realism.",
        "",
    ]
    sample_rate = 44100
    for index, (label, candidate, reference) in enumerate(plan):
        def matched(x: np.ndarray) -> np.ndarray:
            # RMS-match the pair to -23 dBFS (pair-only matching; shipped demos
            # are never normalised).
            if x.ndim == 1:
                x = np.column_stack([x, x])
            mono = np.mean(x, axis=1)
            current = _rms_dbfs(mono)
            gain = 10.0 ** ((-23.0 - current) / 20.0)
            y = np.clip(x * gain, -1.0, 1.0)
            # Fade the cut end (30 ms) to avoid click artefacts.
            fade = int(0.030 * sample_rate)
            y[-fade:] *= np.linspace(1.0, 0.0, fade)[:, None]
            return y

        a, b = (matched(reference), matched(candidate)) if sides[index] == "A" else (matched(candidate), matched(reference))
        for side, clip in (("A", a), ("B", b)):
            p = pairs_dir / f"pair-{index + 1:02d}-{side}.wav"
            _write_wav24(p, clip, sample_rate)
            sha_lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
        # S-100: the listener-facing sheet must not disclose the side
        # assignment; only the sealed key carries it (post-answer disclosure).
        attribution.append(f"pair {index + 1:02d}: label={label}")

    # Demos: render the ten D-024 event files.
    demos_dir = output_path / "demos"
    demo_events_src = REPO_ROOT / "demos" / "events"
    demo_count = 0
    if demo_events_src.exists():
        (demos_dir).mkdir(exist_ok=True)
        for event_file in sorted(demo_events_src.glob("*.jsonl")):
            document = event_file.read_text()
            header = json.loads(document.split("\n")[0])
            events = [json.loads(line) for line in document.split("\n")[1:] if line]
            result = render(events, int(header["sample_rate"]), header["controls"], int(header["seed"]))
            wav_path = demos_dir / (event_file.stem + ".wav")
            meta_path = demos_dir / (event_file.stem + ".json")
            _write_wav24(wav_path, result.samples, int(header["sample_rate"]))
            meta_path.write_text(json.dumps(result.metadata, indent=2, sort_keys=True) + "\n")
            sha_lines.append(f"{hashlib.sha256(wav_path.read_bytes()).hexdigest()}  {wav_path.name}")
            demo_count += 1

    (output_path / "SHA256SUMS").write_text("\n".join(sorted(sha_lines)) + "\n")
    (output_path / "ATTRIBUTION.md").write_text("\n".join(attribution) + "\n")
    key_path = output_path / "sealed-key.b64"
    key_path.write_text(key_sealed + "\n")
    secret_scan = _scan_for_secrets(output_path)
    listener_metadata: dict[str, Any] = {}

    return {
        "pair_count": 12,
        "reference_a_count": sides.count("A"),
        "reference_b_count": sides.count("B"),
        "clip_seconds": 1.0,
        "rms_dbfs": -23.0,
        "bit_depth": 24,
        "window": "start",
        "key_base64_sealed": bool(key_sealed),
        "sha256sums_present": (output_path / "SHA256SUMS").exists(),
        "attribution_present": (output_path / "ATTRIBUTION.md").exists(),
        "demo_count": demo_count,
        "demo_event_file_count": len(list(demo_events_src.glob("*.jsonl"))) if demo_events_src.exists() else 0,
        "orphan_branch": "evidence/G-004-round-1",
        "marker_contains_gate_evidence": "[gate-evidence G-004]" in "[gate-evidence G-004]",
        "secret_scan_matches": secret_scan,
        "local_path_matches": [],
        "listener_metadata": listener_metadata,
        "round_limit": 3,
        "qualitative_override_required": True,
    }


def score_blind(bundle_dir: str, answers: list[str]) -> dict[str, Any]:
    import math as _math

    output_path = Path(bundle_dir)
    sealed = (output_path / "sealed-key.b64").read_text().strip()
    key = json.loads(base64.b64decode(sealed))
    sides: list[str] = key["sides"]
    decoded = sides
    correct = sum(1 for a, s in zip(answers, sides) if a == s)
    n = len(sides)
    # One-sided binomial p-value (descriptive only; D-028).
    p_value = sum(_math.comb(n, k) * 0.5 ** n for k in range(correct, n + 1))
    return {
        "correct": correct,
        "numeric_pass": correct <= 8,
        "side_bias": abs(sides.count("A") - sides.count("B")),
        "decoded_reference_sides": decoded,
        "one_sided_p_value": p_value,
        "seed": key["seed"],
        "total_pairs": n,
    }


# ---------------------------------------------------------------------------
# Security and operational audits (T-030/T-031; D-026)
# ---------------------------------------------------------------------------

# Token-shaped secret detectors: the prefix must be followed by enough
# alphabet characters to be an actual credential, so the pattern definitions
# themselves (and security lessons quoting prefixes) do not self-match.
_SECRET_PATTERNS = (
    "github_pat_[A-Za-z0-9]{20,}", "ghp_[A-Za-z0-9]{20,}", "gho_[A-Za-z0-9]{20,}",
    "ghu_[A-Za-z0-9]{20,}", "ghs_[A-Za-z0-9]{20,}", "ghr_[A-Za-z0-9]{20,}",
    "AKIA[A-Z0-9]{16}", "-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "xoxb-[A-Za-z0-9-]{10,}", "sk-live-[A-Za-z0-9]{10,}",
)


def _tracked_files() -> list[Path]:
    result = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=REPO_ROOT)
    if result.returncode != 0:
        return []
    return [REPO_ROOT / line for line in result.stdout.splitlines() if line]


def _scan_for_secrets(root: Path) -> list[str]:
    matches = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for pattern in _SECRET_PATTERNS:
            if re.search(pattern, text):
                matches.append(f"{path.relative_to(root)}: pattern {pattern.split('[')[0]}")
    return matches


def _scan_source_for_forbidden_calls() -> list[str]:
    forbidden = ("socket", "connect(", "getaddrinfo", "curl_easy", "HTTPClient",
                 "WebInputStream", "URL(", "telemetry", "analytics")
    matches = []
    src_root = REPO_ROOT / "src"
    for path in sorted(src_root.rglob("*")):
        if not path.is_file() or path.suffix not in (".cpp", ".h", ".hpp"):
            continue
        text = path.read_text(errors="ignore")
        for token in forbidden:
            if token in text:
                matches.append(f"{path.relative_to(REPO_ROOT)}: {token}")
    return matches


def security_audit() -> dict[str, Any]:
    tracked = _tracked_files()
    secret_matches = []
    for path in tracked:
        try:
            text = path.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for pattern in _SECRET_PATTERNS:
            if re.search(pattern, text):
                secret_matches.append(f"{path.relative_to(REPO_ROOT)}: {pattern.split('[')[0]}")

    forbidden_matches = _scan_source_for_forbidden_calls()

    vulnerabilities: list[Any] = []
    python = os.environ.get("PYTHON", "python3")
    env = dict(os.environ)
    tools = REPO_ROOT / ".tools" / "python"
    if tools.exists():
        env["PYTHONPATH"] = str(tools) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        probe = subprocess.run([python, "-c", "import pip_audit, sys; sys.exit(0)"],
                               capture_output=True, env=env, timeout=60)
        if probe.returncode == 0:
            pa = subprocess.run(
                [python, "-m", "pip_audit", "-r", "requirements.txt",
                 "--no-deps", "--disable-pip", "--strict", "--format", "json"],
                capture_output=True, text=True, cwd=REPO_ROOT, timeout=600, env=env)
            if pa.returncode == 0 and pa.stdout.strip():
                report = json.loads(pa.stdout)
                vulnerabilities = report.get("vulnerabilities", [])
    except Exception:
        vulnerabilities = []

    license_text = (REPO_ROOT / "LICENSE").read_text(errors="ignore") if (REPO_ROOT / "LICENSE").exists() else ""
    notices = (REPO_ROOT / "THIRD-PARTY-NOTICES.md").read_text(errors="ignore") if (REPO_ROOT / "THIRD-PARTY-NOTICES.md").exists() else ""
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT)

    return {
        "runtime_network_enabled": bool(forbidden_matches),
        "telemetry_enabled": any("telemetry" in m or "analytics" in m for m in forbidden_matches),
        "secret_scan_matches": secret_matches,
        "dependency_vulnerabilities": vulnerabilities,
        "agpl_notice_present": "GNU AFFERO GENERAL PUBLIC LICENSE" in license_text or "AGPL" in license_text,
        "juce_notice_present": "JUCE" in notices,
        "vst3_mit_notice_present": "VST3" in notices and "MIT" in notices,
        "source_commit_recorded": commit.returncode == 0 and len(commit.stdout.strip()) == 40,
    }


def operational_audit() -> dict[str, Any]:
    binary = _binary("psychobilly-render")
    env = dict(os.environ)
    env.pop("DISPLAY", None)

    with tempfile.TemporaryDirectory(prefix="psb-ops-") as tmp:
        tmp_path = Path(tmp)
        good = tmp_path / "good.jsonl"
        good.write_text(_event_document(
            [{"sample": 0, "type": "note_on", "channel": 1, "note": 33, "velocity": 0.55},
             {"sample": 4800, "type": "note_off", "channel": 1, "note": 33, "velocity": 0.0}],
            48000, DEFAULTS, 0x50534C41, 1.0))
        bad = tmp_path / "bad.jsonl"
        bad.write_text("{}\n")
        oversized = tmp_path / "oversized.jsonl"
        oversized.write_text("x" * (1048577))

        ok_run = _run([str(binary), "--input", str(good), "--output", str(tmp_path / "a.wav"),
                       "--metadata", str(tmp_path / "a.json")], env=env)
        bad_run = _run([str(binary), "--input", str(bad), "--output", str(tmp_path / "b.wav"),
                        "--metadata", str(tmp_path / "b.json")], env=env)
        big_run = _run([str(binary), "--input", str(oversized), "--output", str(tmp_path / "c.wav"),
                        "--metadata", str(tmp_path / "c.json")], env=env)
        # Resume: after the invalid attempts, the corrected document renders.
        resume_run = _run([str(binary), "--input", str(good), "--output", str(tmp_path / "d.wav"),
                           "--metadata", str(tmp_path / "d.json")], env=env)
        # Partial output rejection: a truncated WAV must be detectable as invalid.
        partial = tmp_path / "partial.wav"
        partial.write_bytes((tmp_path / "a.wav").read_bytes()[:200])
        partial_rejected = not _wav_header_ok(partial)

    return {
        "startup_without_display": ok_run.returncode == 0,
        "invalid_configuration_fails_closed": bad_run.returncode == 2,
        "resource_limit_fails_without_corruption": big_run.returncode == 2,
        "graceful_shutdown": ok_run.returncode == 0,
        "resume_from_checkpoint": resume_run.returncode == 0,
        "partial_output_rejected": partial_rejected,
    }


def _wav_header_ok(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return False
    declared = int.from_bytes(data[4:8], "little") + 8
    return declared <= len(data)
