extends Node3D

func _enter_tree() -> void:
	# DO NOT force use_xr here anymore to avoid the deadlock
	get_viewport().transparent_bg = true
	print("Native: Viewport background transparency configured.")
