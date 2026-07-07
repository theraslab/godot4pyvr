from py4godot.classes import gdclass
from py4godot.classes.Node3D import Node3D
from py4godot.classes.XRServer import XRServer

@gdclass
class XRSetup(Node3D):

	def _ready(self) -> None:
		xr_server = XRServer.get_singleton()
		xr_interface = xr_server.find_interface("OpenXR")
		
		if xr_interface and xr_interface.is_initialized():
			print("SUCCESS: WiVRn OpenXR Pipeline Fully Confirmed via Python!")
		else:
			print("ERROR: OpenXR interface could not be initialized.")
