"""Record observed joint minima and maxima during an active session.

This module is intentionally separate from the fixed hardcoded limits so that a
runtime session can gather the actual movement envelope and save it as JSON. The
resulting file can then be used by `limits.py` as an optional override.
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Mapping, Sequence

import numpy as np

from ...simulation.constants import QP_ORDER

__all__ = ["SessionLimitRecorder"]


class SessionLimitRecorder:
    """Track the minimum and maximum observed values for each DOF.

    Example:
        recorder = SessionLimitRecorder()
        recorder.update(q_vector)
        recorder.update({"BR": 0.10, "RR": 0.20, ...})
        recorder.save("session_limits.json")
    """

    def __init__(
        self,
        labels: Sequence[str] = QP_ORDER,
        output_path: str | Path = "session_limits.json",
    ) -> None:
        self.labels = tuple(labels)
        self.output_path = Path(output_path)
        self._lower = np.full(len(self.labels), np.inf, dtype=np.float64)
        self._upper = np.full(len(self.labels), -np.inf, dtype=np.float64)
        self._has_values = False

    def _as_array(self, q: Mapping[str, float] | Sequence[float] | np.ndarray) -> np.ndarray:
        if isinstance(q, Mapping):
            values = [float(q.get(label, 0.0)) for label in self.labels]
            return np.asarray(values, dtype=np.float64)

        arr = np.asarray(q, dtype=np.float64)
        if arr.shape != (len(self.labels),):
            raise ValueError(
                f"expected q shape {(len(self.labels),)}, got {arr.shape}"
            )
        return arr

    def update(self, q: Mapping[str, float] | Sequence[float] | np.ndarray) -> dict[str, dict[str, float]]:
        """Update the observed min/max bounds with one new configuration."""
        arr = self._as_array(q)
        if not self._has_values:
            self._lower = arr.copy()
            self._upper = arr.copy()
            self._has_values = True
        else:
            self._lower = np.minimum(self._lower, arr)
            self._upper = np.maximum(self._upper, arr)
        return self.snapshot()

    def snapshot(self) -> dict[str, dict[str, float]]:
        """Return the current min and max values keyed by joint label."""
        if not self._has_values:
            return {label: {"min": 0.0, "max": 0.0} for label in self.labels}

        lower = {label: float(min_value) for label, min_value in zip(self.labels, self._lower)}
        upper = {label: float(max_value) for label, max_value in zip(self.labels, self._upper)}
        return {
            "lower": lower,
            "upper": upper,
        }

    def save(self, path: str | Path | None = None) -> Path:
        """Write the current min/max values to JSON."""
        target = Path(path) if path is not None else self.output_path
        target.parent.mkdir(parents=True, exist_ok=True)

        payload = self.snapshot()
        with target.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

        return target

    def append_to_history(self, history_path: str | Path) -> Path:
        """Append the current session snapshot to a JSONL history file."""
        if not self._has_values:
            return Path(history_path)

        target = Path(history_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(self.snapshot(), sort_keys=True) + "\n")
        return target

    @staticmethod
    def load_session_history(path: str | Path) -> list[dict[str, dict[str, float]]]:
        """Load all saved session snapshots from a JSONL history file."""
        target = Path(path)
        if not target.exists():
            return []

        sessions: list[dict[str, dict[str, float]]] = []
        with target.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = line.strip()
                if not payload:
                    continue
                sessions.append(json.loads(payload))
        return sessions

    @staticmethod
    def aggregate_sessions(
        sessions: Sequence[Mapping[str, Mapping[str, float]]],
        method: str = "median",
    ) -> dict[str, dict[str, float]]:
        """Aggregate multiple recorded sessions into a single limit set."""
        if not sessions:
            return {"lower": {}, "upper": {}}

        labels = sorted({label for session in sessions for label in session.get("lower", {})})
        lower: dict[str, float] = {}
        upper: dict[str, float] = {}

        for label in labels:
            lower_values = [float(session["lower"].get(label, 0.0)) for session in sessions]
            upper_values = [float(session["upper"].get(label, 0.0)) for session in sessions]

            if method == "median":
                lower[label] = float(median(lower_values))
                upper[label] = float(median(upper_values))
            elif method == "mean":
                lower[label] = float(np.mean(lower_values))
                upper[label] = float(np.mean(upper_values))
            else:
                raise ValueError(f"Unsupported aggregation method: {method!r}")

        return {"lower": lower, "upper": upper}

    def save_aggregated_history(
        self,
        history_path: str | Path,
        output_path: str | Path | None = None,
        method: str = "median",
    ) -> dict[str, dict[str, float]]:
        """Build final limits from all sessions in a JSONL history file."""
        sessions = self.load_session_history(history_path)
        if not sessions:
            return self.snapshot()

        aggregated = self.aggregate_sessions(sessions, method=method)
        target = Path(output_path) if output_path is not None else self.output_path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            json.dump(aggregated, handle, indent=2, sort_keys=True)
        return aggregated

    def reset(self) -> None:
        """Clear all recorded values."""
        self._lower = np.full(len(self.labels), np.inf, dtype=np.float64)
        self._upper = np.full(len(self.labels), -np.inf, dtype=np.float64)
        self._has_values = False


def record_session_limits(
    q_stream,
    output_path: str | Path = "session_limits.json",
    labels: Sequence[str] = QP_ORDER,
    history_path: str | Path | None = None,
    method: str = "median",
) -> dict[str, dict[str, float]]:
    """Convenience helper for recording bounds from a stream of q samples.

    Parameters
    ----------
    q_stream:
        Iterable of q values or dictionaries, one sample per update.
    output_path:
        File path used for the JSON export.
    labels:
        Joint order used to interpret the q vectors.
    history_path:
        Optional JSONL file used to accumulate multiple sessions.
    method:
        Aggregation strategy for multiple sessions: "median" or "mean".
    """
    recorder = SessionLimitRecorder(labels=labels, output_path=output_path)
    for sample in q_stream:
        recorder.update(sample)

    if history_path is not None:
        recorder.append_to_history(history_path)
        return recorder.save_aggregated_history(history_path, output_path=output_path, method=method)

    recorder.save()
    return recorder.snapshot()
