# Godot for VR (MQ3) visualization unde Python3.10 conda environment

ToDo


Command to launch godot, under the "pyvr" conda environment.


**Terminal sesion 1**

- Step 1: Grant Device Permissions to WiVRn:

```console
flatpak override --user --device=all --share=ipc io.github.wivrn.wivrn
```

- Step 2:  Launch WiVRn under the discrete NVIDIA graphic card, by the command:
```console
flatpak run \
  --env=__NV_PRIME_RENDER_OFFLOAD=1 \
  --env=__GLX_VENDOR_LIBRARY_NAME=nvidia \
  io.github.wivrn.wivrn
```

**Terminal sesion 2**

- Step 1: Go to the path of the binaries of the godot executable:
```console
cd ~/Documents/godot/godot-bin
```

- Step 2A: Launch godot while explicitly pointing out the path:
```console
cd ~/Documents/godot/godot-bin/

# 1. Clear out Intel Mesa targets from the loader scope completely
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json

# 2. Enforce standard XR & Python variables
export XR_RUNTIME_JSON=$HOME/Documents/godot/godot-bin/openxr_wivrn.json
export PYTHONPATH=~/miniconda3/envs/pyvr/lib/python3.10/site-packages:$PYTHONPATH

# 3. Apply standard PRIME hardware parameters
export __NV_PRIME_RENDER_OFFLOAD=1
export __NV_PRIME_RENDER_OFFLOAD_PROVIDER=NVIDIA-G0
export __GLX_VENDOR_LIBRARY_NAME=nvidia

# 4. Fire up the Editor
./Godot_v4.7-stable_linux.x86_64 -e --path ~/Documents/godot/hello-world/
```

- Step 2B: Launch godot while explicity pointing out the path and overwritting the video card without the explorer:
```console
cd ~/Documents/godot/godot-bin/

export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
export __NV_PRIME_RENDER_OFFLOAD=1
export __NV_PRIME_RENDER_OFFLOAD_PROVIDER=NVIDIA-G0
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export CUDA_CACHE_DISABLE=0

export XR_RUNTIME_JSON=$HOME/Documents/godot/godot-bin/openxr_wivrn.json
export PYTHONPATH=~/miniconda3/envs/pyvr/lib/python3.10/site-packages:$PYTHONPATH

./Godot_v4.7-stable_linux.x86_64 --path ~/Documents/godot/hello-world/ --xr-mode on
```
