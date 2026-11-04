#!/usr/bin/env python3
"""Planning-only DSP falsification spike; not production plug-in code."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy import signal

SEED = 0x50534c41
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
REFERENCE_NOTES = {"A1": 55.0, "F#0": 46.249305, "G#2": 103.826174}


def midi_hz(note: float) -> float:
    return 440.0 * 2.0 ** ((note - 69.0) / 12.0)


def db(x: float) -> float:
    return 20.0 * math.log10(max(float(x), 1e-15))


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x, dtype=np.float64))))


def mono(x: np.ndarray) -> np.ndarray:
    return np.mean(x, axis=1) if x.ndim == 2 else x


def onset_index(x: np.ndarray, sr: int) -> int:
    """One-ms RMS envelope, five-percent-of-peak threshold."""
    block = max(1, int(sr * 0.001))
    padded = np.pad(np.abs(x), (0, (-len(x)) % block))
    env = np.sqrt(np.mean(padded.reshape(-1, block) ** 2, axis=1))
    threshold = max(1e-8, 0.05 * float(np.max(env)))
    hits = np.flatnonzero(env >= threshold)
    if not len(hits):
        raise ValueError("no onset")
    return int(hits[0] * block)


def estimate_pitch(x: np.ndarray, sr: int, lo: float = 35.0, hi: float = 220.0, expected_f0: float | None = None) -> float:
    """Normalised autocorrelation, optionally note-conditioned to +/-50 cents for matched events."""
    if expected_f0 is not None:
        lo = expected_f0 * 2.0 ** (-50.0 / 1200.0)
        hi = expected_f0 * 2.0 ** (50.0 / 1200.0)
    start = onset_index(x, sr)
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
    lag = int(np.min(strong))  # first strong period avoids octave-down multiples
    denom = ac[lag - 1] - 2 * ac[lag] + ac[lag + 1]
    offset = 0.0 if abs(denom) < 1e-15 else 0.5 * (ac[lag - 1] - ac[lag + 1]) / denom
    return float(sr / (lag + np.clip(offset, -0.5, 0.5)))


def estimate_t60(x: np.ndarray, sr: int) -> float:
    start = onset_index(x, sr)
    y = x[start:]
    block = max(1, int(0.02 * sr))
    padded = np.pad(y, (0, (-len(y)) % block))
    levels = np.array([db(v) for v in np.sqrt(np.mean(padded.reshape(-1, block) ** 2, axis=1))])
    peak = float(np.max(levels))
    times = np.arange(len(levels)) * block / sr
    mask = (levels <= peak - 5.0) & (levels >= peak - 35.0)
    if np.count_nonzero(mask) < 5:
        raise ValueError("insufficient decay range")
    slope, _ = np.polyfit(times[mask], levels[mask], 1)
    if slope >= 0:
        raise ValueError("non-decaying signal")
    return float(-60.0 / slope)


def spectral_centroid(x: np.ndarray, sr: int) -> float:
    start = onset_index(x, sr)
    y = x[start:start + min(len(x) - start, int(0.25 * sr))]
    if len(y) < 32:
        raise ValueError("short centroid window")
    y = y * signal.windows.hann(len(y))
    spec = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1.0 / sr)
    return float(np.sum(freqs * spec) / max(np.sum(spec), 1e-15))


def resonator(x: np.ndarray, sr: int) -> np.ndarray:
    out = np.zeros_like(x)
    for frequency, q in ((82.0, 1.1), (190.0, 1.8), (430.0, 2.2)):
        b, a = signal.iirpeak(frequency, q, fs=sr)
        out += signal.lfilter(b, a, x)
    return out / 3.0


def synth(f0: float, sr: int, velocity: float, duration: float, controls: dict[str, float], seed: int):
    """Extended-KS/contact/body hypothesis with bounded collision correction."""
    c = {k: float(np.clip(controls.get(k, v), 0.0, 1.0)) for k, v in DEFAULTS.items()}
    rng = np.random.default_rng(seed)
    n = int(duration * sr)
    delay = sr / f0
    size = int(math.ceil(delay)) + 3
    line = np.zeros(size)
    excitation = rng.standard_normal(size)
    pluck_position = 0.18
    comb = np.roll(excitation, max(1, int(pluck_position * delay)))
    excitation = 0.32 * velocity * (excitation - 0.65 * comb)
    excitation = signal.lfilter([0.30], [1.0, -0.70], excitation)
    line[:] = excitation
    t60 = 0.35 * 12.0 ** c["sustain"]
    loop_gain = min(0.99995, 10.0 ** (-3.0 / (f0 * t60)))
    filter_alpha = 0.35 + 0.25 * c["string_tension"]
    threshold = max(0.035, 0.27 - 0.105 * velocity - 0.045 * c["string_tension"])
    write = 0
    loop_state = 0.0
    pitched = np.empty(n)
    collisions = np.zeros(n)
    for i in range(n):
        read = (write - delay) % size
        i0 = int(math.floor(read))
        frac = read - i0
        x = (1.0 - frac) * line[i0] + frac * line[(i0 + 1) % size]
        loop_state += filter_alpha * (x - loop_state)
        clipped = float(np.clip(x, -threshold, threshold))
        excess = x - clipped
        correction = -0.62 * excess
        collisions[i] = excess
        line[write] = loop_gain * loop_state + correction
        pitched[i] = x
        write = (write + 1) % size
    radiation_cutoff = 350.0 + 350.0 * c["string_tension"]
    pitched = signal.sosfilt(signal.butter(2, radiation_cutoff, fs=sr, output="sos"), pitched)
    body = resonator(pitched, sr)
    contact_len = min(n, int(0.040 * sr))
    noise = rng.standard_normal(contact_len)
    alpha = 0.10 + 0.85 * c["slap_brightness"]
    filtered = signal.lfilter([alpha], [1.0, -(1.0 - alpha)], noise)
    envelope = np.exp(-np.arange(contact_len) / max(1.0, 0.009 * sr))
    contact = np.zeros(n)
    contact[:contact_len] = filtered * envelope
    attack_len = min(n, int(0.018 * sr))
    attack = np.zeros(n)
    attack[:attack_len] = rng.standard_normal(attack_len) * np.exp(-np.arange(attack_len) / max(1.0, 0.004 * sr))
    mechanical_len = min(n, int(0.120 * sr))
    mechanical = np.zeros(n)
    mechanical[:mechanical_len] = rng.standard_normal(mechanical_len) * np.exp(-np.arange(mechanical_len) / max(1.0, 0.030 * sr))
    filtered_collisions = signal.lfilter([alpha], [1.0, -(1.0 - alpha)], collisions)
    contact_component = c["pluck_slap"] * (0.28 * contact + 1.8 * filtered_collisions)
    attack_component = c["attack_noise"] * 0.12 * attack
    mechanical_component = c["mechanical_noise"] * 0.025 * mechanical
    body_component = c["body_resonance"] * 0.50 * body
    mixed = 0.24 * (0.75 * pitched + body_component + contact_component + attack_component + mechanical_component)
    output_gain = 10.0 ** ((-24.0 * (1.0 - c["output_level"])) / 20.0)
    output = mixed * output_gain
    return output, {"pitched": pitched, "body": body_component, "contact": contact_component,
                    "attack": attack_component, "mechanical": mechanical_component, "target_t60": t60}


def metrics(x: np.ndarray, sr: int, expected_f0: float | None = None) -> dict[str, float]:
    pitch = estimate_pitch(x, sr, expected_f0=expected_f0)
    return {
        "peak": float(np.max(np.abs(x))),
        "rms": rms(x),
        "pitch_hz": pitch,
        "pitch_error_cents": 0.0 if expected_f0 is None else 1200.0 * math.log2(pitch / expected_f0),
        "t60_s": estimate_t60(x, sr),
        "centroid_hz": spectral_centroid(x, sr),
        "max_sample_delta": float(np.max(np.abs(np.diff(x)))) if len(x) > 1 else 0.0,
        "finite": bool(np.all(np.isfinite(x))),
        "subnormal_count": int(np.count_nonzero((np.abs(x) > 0) & (np.abs(x) < np.finfo(float).tiny))),
    }


def known_answer_tests(sr: int) -> list[dict]:
    tests = []
    t = np.arange(int(1.2 * sr)) / sr
    for name, f0, waveform in (
        ("sine", 55.0, np.sin(2 * np.pi * 55.0 * t)),
        ("second_harmonic_dominant", 55.0, 0.22 * np.sin(2 * np.pi * 55.0 * t) + np.sin(2 * np.pi * 110.0 * t) + 0.35 * np.sin(2 * np.pi * 165.0 * t)),
        ("missing_fundamental", 73.416192, np.sin(2 * np.pi * 2 * 73.416192 * t) + 0.6 * np.sin(2 * np.pi * 3 * 73.416192 * t) + 0.4 * np.sin(2 * np.pi * 4 * 73.416192 * t)),
    ):
        estimated = estimate_pitch(waveform, sr)
        cents = 1200 * math.log2(estimated / f0)
        tests.append({"name": name, "expected_f0": f0, "estimated_f0": estimated, "error_cents": cents, "pass": abs(cents) < 5.0})
    silence = np.zeros(int(0.2 * sr))
    ramp = np.sin(np.linspace(0, np.pi / 2, int(0.005 * sr))) ** 2
    tone = np.sin(2 * np.pi * 82.0 * np.arange(int(0.3 * sr)) / sr)
    tone[:len(ramp)] *= ramp
    onset_wave = np.concatenate([silence, tone])
    measured = onset_index(onset_wave, sr) / sr
    tests.append({"name": "onset_after_silence", "expected_s": 0.2, "measured_s": measured, "error_ms": 1000 * (measured - 0.2), "pass": abs(measured - 0.2) <= 0.003})
    decay_t60 = 1.2
    decay = np.sin(2 * np.pi * 98 * t) * 10 ** (-3 * t / decay_t60)
    measured_t60 = estimate_t60(decay, sr)
    tests.append({"name": "exponential_t60", "expected_s": decay_t60, "measured_s": measured_t60, "error_percent": 100 * (measured_t60 / decay_t60 - 1), "pass": abs(measured_t60 / decay_t60 - 1) < 0.05})
    low = spectral_centroid(np.sin(2 * np.pi * 110 * t), sr)
    high = spectral_centroid(np.sin(2 * np.pi * 1760 * t), sr)
    tests.append({"name": "centroid_order", "low_hz": low, "high_hz": high, "pass": low < high and abs(low - 110) < 2 and abs(high - 1760) < 2})
    return tests


def control_tests(sr: int) -> list[dict]:
    results = []
    probes = {
        "pluck_slap": ("contact", lambda parts, out, sr: rms(parts["contact"])),
        "slap_brightness": ("contact", lambda parts, out, sr: spectral_centroid(parts["contact"] + 1e-12, sr)),
        "body_resonance": ("body", lambda parts, out, sr: rms(parts["body"]) / max(rms(parts["pitched"]), 1e-12)),
        "sustain": ("output", lambda parts, out, sr: estimate_t60(out, sr)),
        "string_tension": ("pitched", lambda parts, out, sr: spectral_centroid(parts["pitched"], sr)),
        "attack_noise": ("attack", lambda parts, out, sr: rms(parts["attack"])),
        "mechanical_noise": ("mechanical", lambda parts, out, sr: rms(parts["mechanical"])),
        "output_level": ("output", lambda parts, out, sr: rms(out)),
    }
    values = [0.0, 0.25, 0.50, 0.75, 1.0]
    for control, (_, measure) in probes.items():
        measurements = []
        for value in values:
            c = dict(DEFAULTS)
            c[control] = value
            out, parts = synth(55.0, sr, 0.65, 1.8, c, SEED + 42)
            # The seed is fixed across each control sweep so noise cannot masquerade as a mapping trend.
            measurements.append(float(measure(parts, out, sr)))
            assert np.all(np.isfinite(out)) and np.max(np.abs(out)) < 1.0
        differences = np.diff(measurements)
        results.append({"control": control, "values": values, "measurements": measurements,
                        "strictly_increasing": bool(np.all(differences > 0)),
                        "min_delta": float(np.min(differences))})
    return results


def voice_lifecycle_test() -> dict:
    max_voices = 8
    slots: list[dict] = []
    steals = 0
    retriggers = 0
    max_crossfade_delta = 0.0
    previous_output = 0.0
    rng = np.random.default_rng(SEED)
    for event in range(256):
        note = int(rng.integers(28, 56))
        velocity = float(rng.uniform(0.1, 1.0))
        existing = next((v for v in slots if v["note"] == note and v["age"] >= 0), None)
        if existing is not None:
            existing["old_gain"] = existing["gain"]
            existing["gain"] = 0.0
            existing["velocity"] = velocity
            existing["age"] = 0
            retriggers += 1
        else:
            if len(slots) >= max_voices:
                index = min(range(len(slots)), key=lambda i: (slots[i]["velocity"], slots[i]["age"]))
                slots.pop(index)
                steals += 1
            slots.append({"note": note, "velocity": velocity, "gain": 0.0, "old_gain": 0.0, "age": 0})
        assert len(slots) <= max_voices
        for v in slots:
            v["age"] += 1
            v["old_gain"] *= 0.90
            v["gain"] = min(v["velocity"], v["gain"] + v["velocity"] / 10.0)
        output = sum(v["gain"] + v["old_gain"] for v in slots) / max_voices
        max_crossfade_delta = max(max_crossfade_delta, abs(output - previous_output))
        previous_output = output
    coupling = np.full((8, 8), 0.015) - np.eye(8) * 0.015
    spectral_radius = float(np.max(np.abs(np.linalg.eigvals(coupling))))
    return {"events": 256, "max_observed_voices": max_voices, "steals": steals, "retriggers": retriggers,
            "bounded": len(slots) <= max_voices and steals > 0 and retriggers > 0,
            "coupling_spectral_radius": spectral_radius, "coupling_bounded": spectral_radius < 1.0,
            "max_crossfade_output_delta": max_crossfade_delta}


def analyse_references(directory: Path) -> list[dict]:
    records = []
    for path in sorted(directory.glob("*.wav")):
        label = next((k for k in REFERENCE_NOTES if f"_{k}_" in path.name), None)
        if label is None:
            continue
        raw, sr = __import__("soundfile").read(path, always_2d=True)
        x = mono(raw)
        start = onset_index(x, sr)
        excerpt = x[start:start + int(1.8 * sr)]
        m = metrics(excerpt, sr, REFERENCE_NOTES[label])
        m.update({"file": path.name, "label": label, "sample_rate": sr,
                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        records.append(m)
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(SEED)
    architecture = []
    for sr in (44100, 48000, 96000):
        for f0 in (midi_hz(28), 55.0, midi_hz(38), midi_hz(43), 123.470825, 195.997718):
            for velocity in (0.25, 0.55, 0.90):
                out, _ = synth(f0, sr, velocity, 1.8, DEFAULTS, SEED + int(f0 * 10) + int(velocity * 100) + sr)
                m = metrics(out, sr, f0)
                m.update({"sample_rate": sr, "f0": f0, "velocity": velocity})
                architecture.append(m)
    extremes = []
    keys = list(DEFAULTS)
    corners = [{k: 0.0 for k in keys}, {k: 1.0 for k in keys}]
    corners += [{**{k: 0.0 for k in keys}, key: 1.0} for key in keys]
    corners += [{**{k: 1.0 for k in keys}, key: 0.0} for key in keys]
    planned_samples = sum(int(0.7 * sr) * 3 * len(corners) for sr in (44100, 48000, 96000))
    print(f"extreme cases: {3 * 3 * len(corners)}; planned extreme sample iterations: {planned_samples}", flush=True)
    for sr in (44100, 48000, 96000):
        for f0 in (41.203444, 55.0, 103.826174):
            for index, c in enumerate(corners):
                out, _ = synth(f0, sr, 1.0, 0.7, c, SEED + index + sr)
                extremes.append({"sample_rate": sr, "f0": f0, "corner": index,
                                 "finite": bool(np.all(np.isfinite(out))), "peak": float(np.max(np.abs(out))),
                                 "max_sample_delta": float(np.max(np.abs(np.diff(out)))),
                                 "subnormal_count": int(np.count_nonzero((np.abs(out) > 0) & (np.abs(out) < np.finfo(float).tiny)))})
    known = known_answer_tests(48000)
    controls = control_tests(48000)
    references = analyse_references(args.references)
    candidates = []
    for label, f0 in REFERENCE_NOTES.items():
        for dynamic in (0.25, 0.55, 0.90):
            c = dict(DEFAULTS)
            c["pluck_slap"] = 0.0
            c["attack_noise"] = 0.0
            c["mechanical_noise"] = 0.0
            out, _ = synth(f0, 44100, dynamic, 1.8, c, SEED + int(f0 * 100) + int(dynamic * 100))
            m = metrics(out, 44100, f0)
            m.update({"label": label, "dynamic": dynamic})
            candidates.append(m)
    # Attainable regression limits from observed candidate/reference spread, not perceptual realism claims.
    centroid_deviations = []
    t60_deviations = []
    for candidate in candidates:
        refs = [r for r in references if r["label"] == candidate["label"]]
        ref_centroid = float(np.median([r["centroid_hz"] for r in refs]))
        ref_t60 = float(np.median([r["t60_s"] for r in refs]))
        centroid_deviations.append(abs(math.log2(candidate["centroid_hz"] / ref_centroid)))
        t60_deviations.append(abs(math.log2(candidate["t60_s"] / ref_t60)))
    known_pitch_cents = max(abs(t.get("error_cents", 0.0)) for t in known)
    ref_pitch_cents = max(abs(r["pitch_error_cents"]) for r in references)
    candidate_pitch_cents = max(abs(c["pitch_error_cents"]) for c in candidates)
    thresholds = {
        "basis": "Observed known-answer, reference and candidate spread; regression/attainability limits only, never proof of perceptual realism.",
        "pitch_abs_error_cents_max": math.ceil(max(known_pitch_cents, ref_pitch_cents, candidate_pitch_cents) * 1.10),
        "candidate_vs_reference_log2_centroid_abs_max": max(centroid_deviations) * 1.10,
        "candidate_vs_reference_log2_t60_abs_max": max(t60_deviations) * 1.10,
        "finite_output_required": True,
        "peak_abs_max_observed_architecture": max(x["peak"] for x in architecture),
        "peak_abs_max_observed_extremes": max(x["peak"] for x in extremes),
    }
    result = {
        "schema": 1,
        "seed": SEED,
        "purpose": "Planning-only architecture falsification and attainable-regression-limit evidence; no listening or realism verdict.",
        "architecture": architecture,
        "extreme_corners": extremes,
        "known_answer": known,
        "controls": controls,
        "voice_lifecycle": voice_lifecycle_test(),
        "references": references,
        "candidates": candidates,
        "threshold_proposals": thresholds,
        "summary": {
            "architecture_runs": len(architecture),
            "extreme_runs": len(extremes),
            "all_architecture_finite": all(x["finite"] for x in architecture),
            "all_extremes_finite": all(x["finite"] for x in extremes),
            "all_extremes_below_full_scale": all(x["peak"] < 1.0 for x in extremes),
            "all_known_answer_pass": all(x["pass"] for x in known),
            "all_controls_strictly_increasing": all(x["strictly_increasing"] for x in controls),
            "references": len(references),
            "candidates": len(candidates),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"summary": result["summary"], "threshold_proposals": thresholds}, indent=2))
    if not all(result["summary"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
