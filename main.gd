extends Node3D

func _enter_tree() -> void:
	# _enter_tree fires BEFORE _ready, instantly hooking the XR pipeline
	get_viewport().use_xr = true
