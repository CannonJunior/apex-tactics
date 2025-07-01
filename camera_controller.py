#!/usr/bin/env python3
"""
CameraController - Standalone camera system extracted from apex-tactics.py

Provides three camera modes:
- Orbit: Camera orbits around a target point
- Free: First-person style movement
- Top-down: Fixed overhead view

Usage:
    from camera_controller import CameraController
    
    camera_controller = CameraController(grid_width=8, grid_height=8)
    
    # In your input handler:
    camera_controller.handle_input(key)
    
    # In your update loop:
    camera_controller.handle_mouse_input()
    camera_controller.update_camera()
"""

import math
from ursina import *

class CameraController:
    """
    Standalone camera controller extracted from apex-tactics.py
    
    Provides three camera modes with full input handling:
    - Mode 0 (Orbit): Camera orbits around target with mouse/keyboard rotation
    - Mode 1 (Free): First-person camera with WASD movement  
    - Mode 2 (Top-down): Fixed overhead view with target movement
    """
    
    def __init__(self, grid_width=8, grid_height=8, control_panel=None):
        """
        Initialize camera controller
        
        Args:
            grid_width: Width of the game grid (for centering)
            grid_height: Height of the game grid (for centering)
            control_panel: Optional control panel for UI updates
        """
        self.grid_center = Vec3(grid_width/2 - 0.5, 0, grid_height/2 - 0.5)
        self.camera_target = Vec3(self.grid_center.x, self.grid_center.y, self.grid_center.z)
        self.camera_distance = 8
        self.camera_angle_x = 30
        self.camera_angle_y = 0
        self.camera_mode = 0  # 0: orbit, 1: free, 2: top-down
        self.move_speed = 0.5
        self.rotation_speed = 50
        
        # Optional control panel for UI updates
        self.control_panel = control_panel
        
    def update_camera(self):
        """Update camera position and rotation based on current mode"""
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
            camera.position = (self.camera_target.x, 12, self.camera_target.z)
            camera.rotation = (90, 0, 0)
    
    def handle_input(self, key):
        """
        Handle keyboard input for camera controls
        
        Args:
            key: The key that was pressed
        """
        # Camera mode switching
        if key == '1':
            self.camera_mode = 0
            print("Orbit Camera Mode")
            if self.control_panel:
                self.control_panel.update_camera_mode(0)
        elif key == '2':
            self.camera_mode = 1
            print("Free Camera Mode")
            if self.control_panel:
                self.control_panel.update_camera_mode(1)
        elif key == '3':
            self.camera_mode = 2
            print("Top-down Camera Mode")
            if self.control_panel:
                self.control_panel.update_camera_mode(2)
        
        # Orbit camera controls
        elif self.camera_mode == 0:
            if key == 'scroll up':
                self.camera_distance = max(3, self.camera_distance - 0.5)
            elif key == 'scroll down':
                self.camera_distance = min(15, self.camera_distance + 0.5)
        
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
        """Handle mouse input for camera controls"""
        if self.camera_mode == 0:  # Orbit mode
            if held_keys['left mouse']:
                self.camera_angle_y += mouse.velocity.x * 50
                self.camera_angle_x = max(-80, min(80, self.camera_angle_x - mouse.velocity.y * 50))
            
            # Keyboard rotation
            rotation_speed = self.rotation_speed * time.dt
            if held_keys['left arrow']:
                self.camera_angle_y -= rotation_speed
            elif held_keys['right arrow']:
                self.camera_angle_y += rotation_speed
            elif held_keys['up arrow']:
                self.camera_angle_x = max(-80, self.camera_angle_x - rotation_speed)
            elif held_keys['down arrow']:
                self.camera_angle_x = min(80, self.camera_angle_x + rotation_speed)
        
        elif self.camera_mode == 1:  # Free camera mode
            if held_keys['left mouse']:
                camera.rotation_y += mouse.velocity.x * 40
                camera.rotation_x -= mouse.velocity.y * 40
                camera.rotation_x = max(-90, min(90, camera.rotation_x))
    
    def get_mode_name(self):
        """Get the name of the current camera mode"""
        mode_names = ["Orbit", "Free", "Top-down"]
        return mode_names[self.camera_mode]
    
    def set_mode(self, mode):
        """
        Set camera mode directly
        
        Args:
            mode: Camera mode (0=Orbit, 1=Free, 2=Top-down)
        """
        if 0 <= mode <= 2:
            self.camera_mode = mode
            print(f"{self.get_mode_name()} Camera Mode")
            if self.control_panel:
                self.control_panel.update_camera_mode(mode)
    
    def reset_to_default(self):
        """Reset camera to default orbit mode settings"""
        self.camera_mode = 0
        self.camera_distance = 8
        self.camera_angle_x = 30
        self.camera_angle_y = 0
        self.camera_target = Vec3(self.grid_center.x, self.grid_center.y, self.grid_center.z)
        print("Camera reset to default orbit mode")


# Optional: Create a simple control panel class for testing
class SimpleCameraControlPanel:
    """Simple control panel for testing the camera controller"""
    
    def __init__(self):
        self.current_mode = 0
        
    def update_camera_mode(self, mode):
        """Update camera mode display"""
        self.current_mode = mode
        mode_names = ["Orbit", "Free", "Top-down"]
        print(f"Control Panel: Camera mode changed to {mode_names[mode]}")


# Test function to verify the camera controller works
def test_camera_controller():
    """Test the standalone camera controller"""
    print("Testing CameraController...")
    
    # Create a simple app for testing
    app = Ursina()
    
    # Create a simple scene
    ground = Entity(model='plane', texture='white_cube', color=color.green, scale=(10, 1, 10))
    cube = Entity(model='cube', color=color.red, scale=(1, 1, 1), position=(2, 1, 2))
    
    # Create camera controller with test control panel
    control_panel = SimpleCameraControlPanel()
    camera_controller = CameraController(grid_width=8, grid_height=8, control_panel=control_panel)
    
    # Test input handling
    def input(key):
        camera_controller.handle_input(key)
        
        if key == 'escape':
            application.quit()
        elif key == 't':
            print(f"Current mode: {camera_controller.get_mode_name()}")
        elif key == 'r':
            camera_controller.reset_to_default()
    
    # Test update loop
    def update():
        camera_controller.handle_mouse_input()
        camera_controller.update_camera()
    
    print("Camera Controller Test")
    print("Controls:")
    print("  1/2/3 - Switch camera modes")
    print("  WASD - Move camera (mode dependent)")
    print("  Mouse - Look around")
    print("  T - Show current mode")
    print("  R - Reset to default")
    print("  ESC - Exit")
    
    # Set initial camera position
    camera_controller.update_camera()
    
    app.run()


if __name__ == "__main__":
    test_camera_controller()