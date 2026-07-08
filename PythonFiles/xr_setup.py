from py4godot.enums.enums import *
from py4godot.core import *
from py4godot.classes.Node3D import Node3D
from py4godot.classes.MeshInstance3D import MeshInstance3D
from py4godot.classes.SphereMesh import SphereMesh
from py4godot.classes.StandardMaterial3D import StandardMaterial3D

class XRSetup(Node3D):
    
    def _ready(self):
        pass

    def initialize_spheres(self, left_hand_node, right_hand_node):
        print("Python: Core initialization hook received.")
        
        if left_hand_node and right_hand_node:
            self.attach_colored_sphere(left_hand_node, Color(0, 1, 0, 1))   # Green Sphere
            self.attach_colored_sphere(right_hand_node, Color(0, 0, 1, 1))  # Blue Sphere
            print("Python: Tracking indicators attached successfully.")
        else:
            print("Python: Error - Received invalid tracking node pointers.")

    def attach_colored_sphere(self, parent_node, color_value):
        mesh_instance = MeshInstance3D.new()
        sphere_mesh = SphereMesh.new()
        sphere_mesh.set_radius(0.05)
        sphere_mesh.set_height(0.1)
        
        material = StandardMaterial3D.new()
        material.set_albedo(color_value)
        material.set_shading_mode(0) # Unlit tracking color
        
        sphere_mesh.surface_set_material(0, material)
        mesh_instance.set_mesh(sphere_mesh)
        
        parent_node.add_child(mesh_instance)
