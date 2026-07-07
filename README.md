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

- Step 1:

```console
./Godot_v4.7-stable_linux.x86_64 -e --path ~/Documents/godot/hello-world/
```
