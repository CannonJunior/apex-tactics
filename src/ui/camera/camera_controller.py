import math
from ursina import *

class CameraController:
    def __init__(self, grid_width=8, grid_height=8):
        # Use master UI configuration for camera settings
        from src.core.ui.ui_config_manager import get_ui_config_manager
        self.ui_config = get_ui_config_manager()
        
        self.grid_center = Vec3(grid_width/2 - 0.5, 0, grid_height/2 - 0.5)
        self.camera_target = Vec3(self.grid_center.x, self.grid_center.y, self.grid_center.z)
        
        # Load camera settings from master config
        self.camera_distance = self.ui_config.get('camera.controls.distance', 8)
        self.camera_angle_x = self.ui_config.get('camera.controls.angle_x', 30)
        self.camera_angle_y = self.ui_config.get('camera.controls.angle_y', 0)
        self.camera_mode = 0  # 0: orbit, 1: free, 2: top-down
        self.move_speed = self.ui_config.get('camera.controls.move_speed', 0.5)
        self.rotation_speed = self.ui_config.get('camera.controls.rotation_speed', 50)
        
        # Load limits from config
        self.distance_min = self.ui_config.get('camera.controls.distance_limits.min', 3)
        self.distance_max = self.ui_config.get('camera.controls.distance_limits.max', 15)
        self.angle_min = self.ui_config.get('camera.controls.angle_limits.min', -80)
        self.angle_max = self.ui_config.get('camera.controls.angle_limits.max', 80)
        
        # Load sensitivity settings
        self.orbit_sensitivity = self.ui_config.get('camera.controls.mouse_sensitivity.orbit', 50)
        self.free_sensitivity = self.ui_config.get('camera.controls.mouse_sensitivity.free', 40)
        self.scroll_step = self.ui_config.get('camera.controls.scroll_sensitivity.step_size', 0.5)
        
        # Load free camera limits
        self.free_angle_min = self.ui_config.get('camera.controls.free_camera_limits.angle_x.min', -90)
        self.free_angle_max = self.ui_config.get('camera.controls.free_camera_limits.angle_x.max', 90)
        
        # Drag state tracking to disable camera during UI drags
        self.is_ui_dragging = False
        self.drag_source = None
        
    def update_camera(self):
        if self.camera_mode == 0:  # Orbit mode
            rad_y = math.radians(self.camera_angle_y)
            rad_x = math.radians(self.camera_angle_x)
            
            x = self.camera_target.x + self.camera_distance * math.cos(rad_x) * math.sin(rad_y)
            y = self.camera_target.y + self.camera_distance * math.sin(rad_x)
            z = self.camera_target.z + self.camera_distance * math.cos(rad_x) * math.cos(rad_y)
            
            camera.position = (x, y, z)
            camera.look_at(self.camera_target)
        
        elif self.camera_mode == 1:  # Free camera mode
            pass  # Handled by input functions
        
        elif self.camera_mode == 2:  # Top-down mode
            top_down_distance = self.ui_config.get('camera.modes.top_down.distance', 12)
            top_down_rotation = self.ui_config.get('camera.modes.top_down.rotation', {'x': 90, 'y': 0, 'z': 0})
            camera.position = (self.camera_target.x, top_down_distance, self.camera_target.z)
            camera.rotation = (top_down_rotation['x'], top_down_rotation['y'], top_down_rotation['z'])
    
    def set_ui_dragging(self, is_dragging: bool, source: str = None):
        """Set UI dragging state to disable/enable camera movement."""
        self.is_ui_dragging = is_dragging
        self.drag_source = source
        if is_dragging:
            print(f"🔒 Camera disabled - {source} drag started")
        else:
            print(f"🔓 Camera enabled - {source or 'drag'} ended")
    
    def handle_input(self, key, control_panel=None):
        # Always allow camera mode switching regardless of drag state
        if key == '1':
            self.camera_mode = 0
            print("Orbit Camera Mode")
            if control_panel:
                control_panel.update_camera_mode(0)
        elif key == '2':
            self.camera_mode = 1
            print("Free Camera Mode")
            if control_panel:
                control_panel.update_camera_mode(1)
        elif key == '3':
            self.camera_mode = 2
            print("Top-down Camera Mode")
            if control_panel:
                control_panel.update_camera_mode(2)
        
        # Skip camera movement if UI is being dragged
        elif self.is_ui_dragging:
            return  # Ignore all camera movement inputs during UI drag
        
        # Orbit camera controls
        elif self.camera_mode == 0:
            if key == 'scroll up':
                self.camera_distance = max(self.distance_min, self.camera_distance - self.scroll_step)
            elif key == 'scroll down':
                self.camera_distance = min(self.distance_max, self.camera_distance + self.scroll_step)
        
        # Free camera controls
        elif self.camera_mode == 1:
            if key == 'w':
                camera.position += camera.forward * self.move_speed
            elif key == 's':
                camera.position -= camera.forward * self.move_speed
            elif key == 'a':
                camera.position -= camera.right * self.move_speed
            elif key == 'd':
                camera.position += camera.right * self.move_speed
            elif key == 'q':
                camera.position += camera.up * self.move_speed
            elif key == 'e':
                camera.position -= camera.up * self.move_speed
        
        # Top-down camera movement
        elif self.camera_mode == 2:
            if key == 'w':
                self.camera_target.z -= self.move_speed
            elif key == 's':
                self.camera_target.z += self.move_speed
            elif key == 'a':
                self.camera_target.x -= self.move_speed
            elif key == 'd':
                self.camera_target.x += self.move_speed
    
    def handle_mouse_input(self):
        # Skip all mouse camera controls if UI is being dragged
        if self.is_ui_dragging:
            return
            
        if self.camera_mode == 0:  # Orbit mode
            if held_keys['left mouse']:
                self.camera_angle_y += mouse.velocity.x * self.orbit_sensitivity
                self.camera_angle_x = max(self.angle_min, min(self.angle_max, self.camera_angle_x - mouse.velocity.y * self.orbit_sensitivity))
            
            # Keyboard rotation
            rotation_speed = self.rotation_speed * time.dt
            if held_keys['left arrow']:
                self.camera_angle_y -= rotation_speed
            elif held_keys['right arrow']:
                self.camera_angle_y += rotation_speed
            elif held_keys['up arrow']:
                self.camera_angle_x = max(self.angle_min, self.camera_angle_x - rotation_speed)
            elif held_keys['down arrow']:
                self.camera_angle_x = min(self.angle_max, self.camera_angle_x + rotation_speed)
        
        elif self.camera_mode == 1:  # Free camera mode
            if held_keys['left mouse']:
                camera.rotation_y += mouse.velocity.x * self.free_sensitivity
                camera.rotation_x -= mouse.velocity.y * self.free_sensitivity
                camera.rotation_x = max(self.free_angle_min, min(self.free_angle_max, camera.rotation_x))