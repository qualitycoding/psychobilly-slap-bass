"""Planning stubs for the frozen contract tests.

The implementing agent replaces these functions with adapters to the compiled JUCE/C++
engine and offline tools. Public product contracts are fixed in plan/DECISIONS.md.
"""
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class RenderResult:
    samples: np.ndarray
    sample_rate: int
    metadata: dict[str, Any]
    components: dict[str, np.ndarray]


def _not_implemented():
    raise NotImplementedError("planning stub: implement the compiled-engine adapter")


def parameter_contract() -> dict[str, Any]:
    _not_implemented()


def host_contract() -> dict[str, Any]:
    _not_implemented()


def render(events: list[dict[str, Any]], sample_rate: int, controls: dict[str, float], seed: int) -> RenderResult:
    _not_implemented()


def analyse(samples: np.ndarray, sample_rate: int, expected_f0: float | None = None) -> dict[str, float]:
    _not_implemented()


def validate_state(data: bytes) -> dict[str, Any]:
    _not_implemented()


def state_roundtrip(data: bytes) -> bytes:
    _not_implemented()


def validate_event_document(text: str) -> dict[str, Any]:
    _not_implemented()


def voice_lifecycle(events: list[dict[str, Any]]) -> dict[str, Any]:
    _not_implemented()


def performance(workload: dict[str, Any]) -> dict[str, Any]:
    _not_implemented()


def make_blind_pairs(reference_dir: str, candidate_dir: str, output_dir: str, seed: int, window: str) -> dict[str, Any]:
    _not_implemented()


def score_blind(bundle_dir: str, answers: list[str]) -> dict[str, Any]:
    _not_implemented()


def security_audit() -> dict[str, Any]:
    _not_implemented()


def operational_audit() -> dict[str, Any]:
    _not_implemented()
