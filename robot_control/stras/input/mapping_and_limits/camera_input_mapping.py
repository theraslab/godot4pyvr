"""Map head orientation to endoscope bending without mapping head translation."""
from __future__ import annotations

import math
from typing import Mapping

from ...simulation.constants import QP_ORDER
from .limits import JointLimits
from .mapping_math import (
    HEAD_BEND_FULL_SCALE_RAD,
    YAW_FULL_SCALE_RAD,
    read_vector,
    scaled_offset,
)


class CameraInputMapper:
    """Map look direction to bending; leave endoscope insertion fixed."""

    def __init__(self, limits: JointLimits):
        self._limits = limits
        self._neutral_angles: tuple[float, float, float] | None = None

    @property
    def neutral_yaw(self) -> float:
        if self._neutral_angles is None:
            raise RuntimeError("camera neutral pose has not been captured")
        return self._neutral_angles[1]

    @staticmethod
    def _read_pose(camera: Mapping) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        if not isinstance(camera, Mapping):
            raise ValueError("camera must be an object")
        if "position" not in camera:
            raise ValueError("camera.position is required")
        if "yaw" not in camera:
            raise ValueError("camera.yaw is required")
        position = read_vector(camera["position"], ("x", "y", "z"),
                               "camera.position")
        angles = []
        for axis in ("pitch", "yaw", "roll"):
            angle = camera.get(axis, 0.0)
            if isinstance(angle, bool) or not isinstance(angle, (int, float)):
                raise ValueError(f"camera.{axis} must be a finite number")
            angle = float(angle)
            if not math.isfinite(angle):
                raise ValueError(f"camera.{axis} must be a finite number")
            angles.append(angle)
        return position, (angles[0], angles[1], angles[2])

    def reset(self) -> None:
        """Clear the captured neutral pose; the next update captures a new one."""
        self._neutral_angles = None

    def recenter(self, camera: Mapping) -> None:
        """Capture the current head orientation as neutral; ignore its position."""
        _, self._neutral_angles = self._read_pose(camera)

    def update(self, camera: Mapping) -> dict[str, float]:
        _, angles = self._read_pose(camera)
        if self._neutral_angles is None:
            self._neutral_angles = angles

        pitch_delta, yaw_delta, roll_delta = (
            (current - neutral + math.pi) % (2.0 * math.pi) - math.pi
            for current, neutral in zip(angles, self._neutral_angles)
        )
        values: dict[str, float] = {"EBH": 0.0, "EBV": 0.0, "ER": 0.0, "ET": 0.0}
        for joint, delta, full_scale in (
            # Godot's positive yaw turns the view left, while positive EBH
            # bends the model right; invert yaw to keep movement intuitive.
            ("EBH", -yaw_delta, HEAD_BEND_FULL_SCALE_RAD),
            ("EBV", pitch_delta, HEAD_BEND_FULL_SCALE_RAD),
            ("ER", roll_delta, YAW_FULL_SCALE_RAD),
        ):
            index = QP_ORDER.index(joint)
            values[joint] = scaled_offset(
                delta, full_scale,
                float(self._limits.lower[index]),
                float(self._limits.upper[index]))

        # EBH and EBV bend in perpendicular planes. Limit their combined
        # curvature to one joint's maximum so diagonal head poses cannot exceed
        # a 90-degree endoscope bend and point the camera back out of the tube.
        bend_norm = math.hypot(values["EBH"], values["EBV"])
        bend_limit = min(
            abs(float(self._limits.lower[QP_ORDER.index("EBH")])),
            float(self._limits.upper[QP_ORDER.index("EBH")]),
            abs(float(self._limits.lower[QP_ORDER.index("EBV")])),
            float(self._limits.upper[QP_ORDER.index("EBV")]),
        )
        if bend_norm > bend_limit:
            scale = bend_limit / bend_norm
            values["EBH"] *= scale
            values["EBV"] *= scale
        return values