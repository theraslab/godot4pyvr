extends Node3D
## Static, open-ended lumen wall: a straight cylinder joined to a 180-degree bend.
## Dimensions use the same millimetre-scale model coordinates as STRAS geometry.

const TubeMeshBuilder = preload("res://robot_control/stras/visualization/geometry/tube_mesh_builder.gd")
const TUBE_TEXTURE: Texture2D = preload("res://01-example.jpg")
const GUIDE_RADIUS_MM := 1.2

## Start behind the model's instrument-channel bases (z ~= -34 mm).
@export_range(-500.0, 500.0, 1.0) var start_z_mm: float = -40.0
@export_range(1.0, 1000.0, 1.0) var straight_length_mm: float = 300.0
@export_range(1.0, 1000.0, 1.0) var bend_radius_mm: float = 280.0
## Clearance for the endoscope's maximum 90-degree bend excursion (~118 mm).
## The large straight lumen keeps the camera inside even at full head-bend input.
@export_range(1.0, 500.0, 1.0) var inner_radius_mm: float = 220.0
@export_range(3, 128, 1) var straight_segments: int = 24
@export_range(8, 128, 1) var bend_segments: int = 48
@export_range(6, 64, 1) var radial_segments: int = 24
@export_range(20.0, 1000.0, 10.0) var texture_repeat_mm: float = 100.0
@export var robot_to_godot: Basis = Basis.IDENTITY
## Optional placement adjustment in the robot anchor's local frame.
@export var local_offset: Transform3D = Transform3D.IDENTITY

var _wall: MeshInstance3D
var _guide_line: MeshInstance3D


func _ready() -> void:
	_wall = MeshInstance3D.new()
	_wall.name = "LumenWall"
	# Keep the source geometry out of the headset's main world. The display
	# copies this mesh into its isolated floating-screen viewport.
	_wall.visible = false
	_wall.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_wall)
	_guide_line = MeshInstance3D.new()
	_guide_line.name = "TubeCurveGuide"
	_guide_line.visible = false
	_guide_line.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_guide_line)
	_rebuild_material()
	_rebuild_guide_material()
	rebuild()


func set_robot_basis(value: Basis) -> void:
	robot_to_godot = value
	rebuild()


func place_at_anchor(anchor_transform: Transform3D) -> void:
	# Set once when the robot is anchored. This node is a sibling of the robot,
	# so it remains fixed in the world rather than following robot updates.
	global_transform = anchor_transform * local_offset


func rebuild() -> void:
	if _wall == null:
		return
	if straight_length_mm <= 0.0 or bend_radius_mm <= inner_radius_mm or inner_radius_mm <= 0.0:
		push_error("Tube environment requires positive dimensions and bend_radius_mm > inner_radius_mm.")
		_wall.mesh = null
		_sync_floating_views()
		return

	var centerline := PackedVector3Array()
	var guide_points := PackedVector3Array()
	for i in range(straight_segments + 1):
		var fraction := float(i) / float(straight_segments)
		var point := robot_to_godot * Vector3(
			0.0, 0.0, start_z_mm + straight_length_mm * fraction)
		centerline.append(point)
		guide_points.append(point + robot_to_godot * Vector3.UP * (
			inner_radius_mm - GUIDE_RADIUS_MM - 0.3))

	# The upper semicircle starts tangent to +Z and bends toward +X.
	for i in range(1, bend_segments + 1):
		var angle := PI * float(i) / float(bend_segments)
		var point := Vector3(
			bend_radius_mm * (1.0 - cos(angle)),
			0.0,
			start_z_mm + straight_length_mm + bend_radius_mm * sin(angle))
		point = robot_to_godot * point
		centerline.append(point)
		guide_points.append(point + robot_to_godot * Vector3.UP * (
			inner_radius_mm - GUIDE_RADIUS_MM - 0.3))

	_wall.mesh = TubeMeshBuilder.build_tube(
		centerline, inner_radius_mm, radial_segments, false, false,
		texture_repeat_mm)
	_guide_line.mesh = TubeMeshBuilder.build_tube(
		guide_points, GUIDE_RADIUS_MM, 8, false, false)
	_sync_floating_views()


func _sync_floating_views() -> void:
	var robot_geometry := get_parent().get_node_or_null("RobotGeometry") as Node
	if robot_geometry != null:
		robot_geometry.call("set_static_environment", _wall.mesh, _wall.material_override,
			_guide_line.mesh, _guide_line.material_override)


func _rebuild_material() -> void:
	var material := StandardMaterial3D.new()
	material.albedo_texture = TUBE_TEXTURE
	material.albedo_color = Color.WHITE
	# Pixel lighting lets the bend's changing surface normals read as depth.
	material.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.roughness = 0.75
	_wall.material_override = material


func _rebuild_guide_material() -> void:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = Color(0.1, 0.95, 1.0)
	material.emission_enabled = true
	material.emission = Color(0.05, 0.65, 0.8)
	_guide_line.material_override = material
