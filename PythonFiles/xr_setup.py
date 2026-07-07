from py4godot.enums.enums import *
from py4godot.core import *
from py4godot.classes.Node3D import Node3D
from py4godot.classes.XRServer import XRServer
from py4godot.classes.MeshInstance3D import MeshInstance3D
from py4godot.classes.SphereMesh import SphereMesh
from py4godot.classes.StandardMaterial3D import StandardMaterial3D

class XRSetup(Node3D):
	
	def _ready(self):
		print("Python: Activating Passthrough Blend Mode...")
		
		# 1. Set up Passthrough
		xr_server = XRServer.get_instance()
		xr_interface = xr_server.find_interface("OpenXR")
		if xr_interface:
			xr_interface.set_environment_blend_mode(4) # Alpha Blend Mode

		# 2. Grab your existing hand nodes from the scene tree
		# We look up the tree from PythonXRManager to find XROrigin3D's children
		self.left_hand = self.get_node("../XROrigin3D/lefthand")
		self.right_hand = self.get_node("../XROrigin3D/righthand")

		if self.left_hand and self.right_hand:
			print("Python: Located tracking nodes. Attaching visual telemetry spheres...")
			# 3. Attach your spheres directly to them
			self.attach_colored_sphere(self.left_hand, Color(0, 1, 0, 1))   # Green
			self.attach_colored_sphere(self.right_hand, Color(0, 0, 1, 1))  # Blue
		else:
			print("Python: Error - Could not find the left or right hand nodes in the scene tree.")

	def attach_colored_sphere(self, parent_node, color_value):
		mesh_instance = MeshInstance3D.new()
		sphere_mesh = SphereMesh.new()
		sphere_mesh.set_radius(0.05)
		sphere_mesh.set_height(0.1)
		
		material = StandardMaterial3D.new()
		material.set_albedo(color_value)
		material.set_shading_mode(0) 
		
		sphere_mesh.surface_set_material(0, material)
		mesh_instance.set_mesh(sphere_mesh)
		
		parent_node.add_child(mesh_instance)
