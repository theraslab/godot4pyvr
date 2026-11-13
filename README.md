# Godot VR / STRAS visualization

This project renders a simulation-only STRAS model driven by XR input. It does not control a physical robot; instead, it maps headset/controller motion into a virtual robot configuration, computes forward kinematics, and streams the resulting geometry back to Godot for visualization.

## Overview

The runtime is split into two parts:

- Godot handles XR capture and UDP transport.
- Python handles the STRAS model, forward kinematics, and geometry output.

The active pipeline is:

XR poses -> simulated q -> STRAS forward kinematics -> VirtualFollower state -> Godot geometry

This is intentionally a local simulation loop. No robot commands are sent to hardware.


## Input mapping summary

The mapping is absolute and based on the first tracked neutral pose. The values are not integrated over time and do not use velocity estimates.

| Input | Mapped joint(s) / description |
| --- | --- |
| Right controller lateral + vertical offset | `BR` bend, `RR` yaw/rotation, `TR` insertion along the right arm axis |
| Left controller lateral + vertical offset | `BL` bend, `RL` yaw/rotation, `TL` insertion along the left arm axis |
| XR camera yaw | `EBH` horizontal endoscope bend; left/right camera look changes the endoscope heading |
| XR camera pitch | `EBV` vertical endoscope bend; up/down look changes the endoscope pitch |
| XR camera roll | `ER` endoscope roll; head roll rotates the camera around its forward axis |
| XR camera position | Ignored for the current mapping; keeps the virtual endoscope inside the tube and is not used to drive `ET` |
| Endoscope insertion | `ET` stays fixed in the current mapping and is not driven by controller position, so the camera remains centered in the tube |

The q order is:

`BR, RR, TR, BL, RL, TL, EBV, EBH, ER, ET`

Meaning by joint:

- `BR` / `BL`: right/left arm bend angle
- `RR` / `RL`: right/left arm rotation/yaw
- `TR` / `TL`: right/left arm insertion/translation
- `EBV`: endoscope vertical bend
- `EBH`: endoscope horizontal bend
- `ER`: endoscope roll
- `ET`: endoscope translation/insertion (currently fixed in the runtime mapping)

Translations are in millimetres, rotations are in radians, and bend values are curvature values.


## Normalized input conventions

This project treats input values as normalized control signals before they are mapped into robot joint space.

- Trigger and grip values are normalized to the range `[0, 1]`.
- Primary and secondary stick axes are preserved as signed values in `[-1, 1]` and only clamped, not rescaled to `[0, 1]`.
- The Python runner also supports a normalized `joints` payload for scripted tests: every one of the ten joint labels must be present and each value must be finite and within `[0, 1]`.
- Those normalized values are converted back to the virtual robot range by `normalized_joints_to_q(...)` before forward kinematics runs.

This is important because the Godot side sends raw XR/controller data, while the Python FK side expects normalized control conventions before converting to physical `q` values.

## Teleop HUD and normalized arm state

The geometry stream includes a `hud` field that reports the arm state in normalized form for debugging and HUD display.

- The HUD values are computed for `BL`, `RL`, `TL`, `BR`, `RR`, and `TR`.
- Each joint is normalized against its virtual calibration range and then clamped to `[0, 1]`.
- This makes the HUD easy to visualize, while the actual robot model still keeps its raw joint values in physical units.
- The teleop UI is not the same as the headset’s real XR view; it is a secondary visualization layer for the simulated endoscope/arm state.


## Project layout

- `main.tscn` and `main.gd`: Godot entry scene and runtime glue
- `mock_input.tscn` and `mock_input.gd`: headset-free UDP mock input for smoke testing
- `robot_control/`: Python simulation backend and STRAS logic
- `robot_control/tests/`: Python regression tests for input mapping, kinematics, and client/server behavior
- `module_main/`: model/calibration data and robot geometry utilities

## Requirements

- Godot 4 with OpenXR enabled
- WiVRn or another OpenXR runtime for VR tracking
- Conda environment named `pyvr` for the Python runner
- Python scientific dependencies installed in that environment, including `liegroups` for the model utilities
- Linux NVIDIA setup is assumed in the commands below; adjust as needed for your machine

Important:

- Godot does not need the Python environment for this project.
- The `pyvr` environment is for the Python runner only.
- Py4Godot is not used here; do not install scientific dependencies into the bundled Godot Python.

## Quick start


### Runtime mode vs calibration mode

The simulator supports two operating modes:

- Runtime mode (default): uses the existing `session_limits.json` if it exists and does not rewrite the calibration history.
- Calibration mode: enabled with `--calibration-mode`; records the observed movement envelope, appends it to `session_history.jsonl`, and rebuilds `session_limits.json` from the accumulated sessions.

Use runtime mode for normal operation:

```bash
conda activate pyvr
python -m robot_control.stras_vr_simulator
```

This listens for XR snapshots on `127.0.0.1:9000` and streams geometry back to `127.0.0.1:9100`.

The runner sends geometry at up to 30 FPS by default and samples the newest available input. It keeps the internal `VirtualFollower` updated and does not send hardware commands.

Use calibration mode only when you want to re-estimate the movement limits, such as after changing the setup or robot configuration:

```bash
conda activate pyvr
python -m robot_control.stras_vr_simulator --calibration-mode
```

The runner prints the active mode at startup so it is clear which path is being used.

Calibration mode is intended as a deliberate one-off process. Once a stable `session_limits.json` file is available, normal execution should remain in runtime mode instead of repeatedly recalibrating.


## Linux + WiVRn launch notes

For Linux setups using WiVRn, use the commands below to start the runtime and Godot. These are the platform-specific launch commands for the quick start above.

### Terminal 1: launch WiVRn

```bash
flatpak override --user --device=all --share=ipc io.github.wivrn.wivrn
```

```bash
flatpak run \
  --env=__NV_PRIME_RENDER_OFFLOAD=1 \
  --env=__GLX_VENDOR_LIBRARY_NAME=nvidia \
  io.github.wivrn.wivrn
```

### Terminal 2: launch Godot with the OpenXR runtime

```bash
cd ~/Documents/godot/godot-bin

# 1. Clear out Intel Mesa targets from the loader scope completely
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json

# 2. Enforce standard XR & Python variables
export XR_RUNTIME_JSON=$HOME/Documents/godot/godot-bin/openxr_wivrn.json
export PYTHONPATH=~/miniconda3/envs/pyvr/lib/python3.10/site-packages:$PYTHONPATH

# 3. Apply standard PRIME hardware parameters
export __NV_PRIME_RENDER_OFFLOAD=1
export __NV_PRIME_RENDER_OFFLOAD_PROVIDER=NVIDIA-G0
export __GLX_VENDOR_LIBRARY_NAME=nvidia

# 4. Open the editor; press F5 to run the project
./Godot_v4.7-stable_linux.x86_64 -e --path ~/Documents/godot/hello-world/
```

Or run directly without the editor:

```bash
cd ~/Documents/godot/godot-bin

export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
export __NV_PRIME_RENDER_OFFLOAD=1
export __NV_PRIME_RENDER_OFFLOAD_PROVIDER=NVIDIA-G0
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export CUDA_CACHE_DISABLE=0
export XR_RUNTIME_JSON=$HOME/Documents/godot/godot-bin/openxr_wivrn.json

./Godot_v4.7-stable_linux.x86_64 --path ~/Documents/godot/hello-world/ --xr-mode on --rendering-method forward_plus
```

### Optional: enable runner statistics

In the Python runner terminal, use this command instead of the standard runner command in Quick start to print cumulative input/FK counters every second:

```bash
conda activate pyvr
python -m robot_control.stras_vr_simulator --stats-interval 1
```


## Smoke test without VR hardware

You can validate the UDP flow without a headset by running the mock input server and the mock scene.

### Start the UDP listener

```bash
conda activate pyvr
python -m robot_control.stras.input.transport_and_validation.input_server
```

### Run the mock scene in Godot

- Open `mock_input.tscn`
- Use Run Current Scene (F6)

The mock scene sends neutral frames for one second, then holds the simulated grip and moves the right stick upward. Watch the terminal for increasing sequence numbers and `R.grip=1.0` output.

Do not run this test server at the same time as `stras_vr_simulator`; both bind to port `9000`.

## Notes for development

- The project renders the simulation-only model; it does not send commands to a physical STRAS robot.
- The first tracked poses establish the neutral frame.
- The robot-to-Godot basis can be adjusted visually as a rendering setting.
- The endoscope camera viewport is a preview overlay; it does not replace the user’s actual headset view.
- The runner also supports normalized `joints` payloads for scripted tests, provided all ten labels are present in the `[0, 1]` range.


### Calibration history and final limits

The calibration flow is intentionally split into two files:

- `session_history.jsonl`: append-only log containing one JSON snapshot per calibration session. Each line stores the lower/upper bounds observed during that run. This gives you a persistent record of all measured movement envelopes.
- `session_limits.json`: the final consolidated limit set used at runtime. It is rebuilt from the history file using a robust aggregation strategy, currently `median`, and then written back as the active runtime override.

The relationship is:

```text
calibration session -> append to session_history.jsonl -> aggregate -> write session_limits.json -> runtime uses session_limits.json
```

This design keeps the calibration process auditable and prevents each run from silently discarding the previous data. In normal runtime operation, the system should prefer the final generated `session_limits.json` instead of re-measuring every time.

The relevant Python support code lives in `robot_control/stras/input/mapping_and_limits/session_limits.py`, and the runtime override logic is handled in `robot_control/stras/input/mapping_and_limits/limits.py`.

## Troubleshooting

- If the Python runner cannot bind to the input port, another process may already be using `9000`.
- If you see no geometry, confirm that the Godot scene is running with OpenXR enabled and that the Python runner is alive.
- If imports fail with `ModuleNotFoundError: No module named 'liegroups'`, activate the `pyvr` environment and install the project’s scientific dependencies there.
- For simpler debugging, run the simulator with `--stats-interval 1`.
- If you are using the mock input path, remember to stop the full simulator before launching the mock listener because both use the same UDP port.

## Tests

Run the project tests from the repo root:

```bash
pytest -q
```

This validates the input protocol, mapping logic, kinematics, and client/server behavior.

