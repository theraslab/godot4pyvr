"""Joint limits used by the VR-driven STRAS simulation."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from ...simulation.constants import QP_ORDER

_ARM_BEND_LIMIT = np.pi / (2 * 18.5)
_ENDOSCOPE_BEND_LIMIT = np.pi / (2 * 185)

VIRTUAL_LOWER = {
    "BR": -_ARM_BEND_LIMIT,
    "RR": np.radians(-160),
    "TR": -10,
    "BL": -_ARM_BEND_LIMIT,
    "RL": np.radians(-160),
    "TL": -10,
    "EBV": -_ENDOSCOPE_BEND_LIMIT,
    "EBH": -_ENDOSCOPE_BEND_LIMIT,
    "ER": np.radians(-90),
    "ET": -100,
}
VIRTUAL_UPPER = {
    "BR": _ARM_BEND_LIMIT,
    "RR": np.radians(160),
    "TR": 72,
    "BL": _ARM_BEND_LIMIT,
    "RL": np.radians(160),
    "TL": 72,
    "EBV": _ENDOSCOPE_BEND_LIMIT,
    "EBH": _ENDOSCOPE_BEND_LIMIT,
    "ER": np.radians(90),
    "ET": 95,
}


@dataclass(frozen=True, eq=False)
class JointLimits:
    """Lower and upper bounds ordered by the corresponding joint labels."""

    labels: Sequence[str]
    lower: np.ndarray
    upper: np.ndarray

    def __post_init__(self) -> None:
        lower = np.asarray(self.lower, dtype=np.float64)
        upper = np.asarray(self.upper, dtype=np.float64)
        if len(self.labels) != len(lower) or len(self.labels) != len(upper):
            raise ValueError("labels, lower and upper must have equal length")
        if not np.all(np.isfinite(lower)) or not np.all(np.isfinite(upper)):
            raise ValueError("joint limits must be finite")
        if np.any(lower > upper):
            raise ValueError("each lower joint limit must be <= its upper limit")
        object.__setattr__(self, "labels", tuple(self.labels))
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)

    @classmethod
    def from_dicts(
        cls,
        lower: Mapping[str, float],
        upper: Mapping[str, float],
        order: Sequence[str] = QP_ORDER,
    ) -> JointLimits:
        labels = tuple(order)
        return cls(
            labels,
            np.array([lower[label] for label in labels], dtype=np.float64),
            np.array([upper[label] for label in labels], dtype=np.float64),
        )


@dataclass(frozen=True, eq=False)
class RobotLimits:
    """Virtual STRAS joint ranges; contains no physical-controller limits."""

    virtual_cs: JointLimits

    @staticmethod
    def _candidate_session_paths(session_path: str | Path | None = None) -> list[Path]:
        candidates: list[Path] = []
        if session_path is not None:
            candidates.append(Path(session_path))

        candidates.extend(
            [
                Path.cwd() / "session_limits.json",
                Path(__file__).resolve().parents[4] / "session_limits.json",
                Path(__file__).resolve().with_name("session_limits.json"),
            ]
        )

        unique: list[Path] = []
        seen: set[str] = set()
        for candidate in candidates:
            resolved = candidate if candidate.is_absolute() else (Path.cwd() / candidate).resolve()
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            unique.append(resolved)
        return unique

    @classmethod
    def from_session_file(cls, session_path: str | Path) -> RobotLimits:
        """Build limits from a session-generated JSON override, if present."""
        path = Path(session_path)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"session limits file not found: {path}")

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, Mapping):
            raise ValueError(f"session limits file must contain a JSON object: {path}")

        lower = payload.get("lower")
        upper = payload.get("upper")
        if not isinstance(lower, Mapping) or not isinstance(upper, Mapping):
            raise ValueError(f"session limits file must contain 'lower' and 'upper' mappings: {path}")

        combined_lower = {label: float(lower.get(label, VIRTUAL_LOWER[label])) for label in QP_ORDER}
        combined_upper = {label: float(upper.get(label, VIRTUAL_UPPER[label])) for label in QP_ORDER}
        return cls(JointLimits.from_dicts(combined_lower, combined_upper))

    @classmethod
    def default(cls, session_path: str | Path | None = None) -> RobotLimits:
        """Return the default hardcoded limits, or the session override if available."""
        for candidate in cls._candidate_session_paths(session_path):
            if not candidate.exists():
                continue
            try:
                return cls.from_session_file(candidate)
            except (FileNotFoundError, OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
        return cls(JointLimits.from_dicts(VIRTUAL_LOWER, VIRTUAL_UPPER))
