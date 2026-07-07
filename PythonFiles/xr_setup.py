from py4godot.classes import gdclass
from py4godot.classes.Node3D import Node3D
from py4godot.classes.XRServer import XRServer
from py4godot.classes.Label3D import Label3D
import time
import math

@gdclass
class XRSetup(Node3D):

	def _ready(self) -> None:
		# 1. Fetch the absolute Root Viewport Window from the main SceneTree
		scene_tree = self.get_tree()
		if scene_tree:
			root_viewport = scene_tree.get_root()
			if root_viewport:
				root_viewport.set_use_xr(True)
				print("SUCCESS: Explicitly marked Root Viewport with use_xr via SceneTree!")

		# 2. Proceed with standard interface initialization
		xr_server = XRServer.get_singleton()
		xr_interface = xr_server.find_interface("OpenXR")
		
		if xr_interface and xr_interface.is_initialized():
			print("SUCCESS: WiVRn OpenXR Pipeline Fully Confirmed via Python!")
			self.hud_label = Label3D.cast(self.get_node("XRCamera3D/HUDLabel"))
			self.start_time = time.time()
			self.frame_count = 0
		else:
			print("ERROR: OpenXR interface could not be initialized.")
			self.hud_label = None

	def _process(self, delta: float) -> None:
		if self.hud_label:
			self.frame_count += 1
			current_time = time.time() - self.start_time
			
			velocity = 50.0 + 10.0 * math.sin(self.frame_count * 0.05)
			altitude = 150.0 + (self.frame_count * 0.1)
			status = "NOMINAL" if (self.frame_count % 100 < 95) else "WARNING_OVERHEATING"
			
			hud_text = (
				f"PYTHON SIMULATION HUD\n"
				f"=====================\n"
				f"Sim Time: {current_time:.2f}s\n"
				f"Velocity: {velocity:.2f} m/s\n"
				f"Altitude: {altitude:.1f} m\n"
				f"Status:   {status}"
			)
			
			self.hud_label.set_text(hud_text)
