import json

from robot_control.stras.input.mapping_and_limits.limits import RobotLimits


def test_session_limits_override(tmp_path):
    session_path = tmp_path / "session_limits.json"
    payload = {
        "lower": {
            "BR": -0.5,
            "RR": -1.0,
            "TR": -2.0,
            "BL": -0.5,
            "RL": -1.0,
            "TL": -2.0,
            "EBV": -0.25,
            "EBH": -0.25,
            "ER": -0.75,
            "ET": -4.0,
        },
        "upper": {
            "BR": 0.5,
            "RR": 1.0,
            "TR": 2.0,
            "BL": 0.5,
            "RL": 1.0,
            "TL": 2.0,
            "EBV": 0.25,
            "EBH": 0.25,
            "ER": 0.75,
            "ET": 4.0,
        },
    }
    session_path.write_text(json.dumps(payload), encoding="utf-8")

    limits = RobotLimits.default(session_path)
    br_index = limits.virtual_cs.labels.index("BR")

    assert limits.virtual_cs.lower[br_index] == -0.5
    assert limits.virtual_cs.upper[br_index] == 0.5
