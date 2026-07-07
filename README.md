# Godot for VR (MQ3) visualization unde Python3.10 conda environment

ToDo


Command to launch godot, under the "pyvr" conda environment:

'' ~/Documents/godot/godot-bin/Godot_v4.7-stable_linux.x86_64 -e --path ~/Documents/godot/hello-world/


cd ~/Documents/godot/godot-bin/
export XR_RUNTIME_JSON=$HOME/Documents/godot/godot-bin/openxr_wivrn.json
export PYTHONPATH=~/miniconda3/envs/pyvr/lib/python3.10/site-packages:$PYTHONPATH

./Godot_v4.7-stable_linux.x86_64 --path ~/Documents/godot/hello-world/
