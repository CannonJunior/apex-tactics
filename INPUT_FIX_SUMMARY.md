# Input Fix for Modular Apex Tactics Demo

## Problem Identified

The modular demo was not responding to keyboard input (WASD, 1/2/3, Space, Tab, ESC) or mouse input (drag to rotate camera), while button clicks were working. This was because Ursina expects global `input()` and `update()` functions but the demo was using class methods.

## Root Cause

In the original `apex-tactics.py`, input was handled by global functions:

```python
def input(key):
    # Handle input
    game.camera_controller.handle_input(key)

def update():
    # Update camera and game state
    game.camera_controller.handle_mouse_input()
    game.camera_controller.update_camera()

app.run()  # Ursina automatically finds these global functions
```

In the modular demo, I was trying to use class methods and `self.app.update`, but Ursina specifically looks for global functions named `input` and `update`.

## Solution Implemented

Added proper global function registration in the `ModularApexTacticsDemo` class:

### 1. Global Function Registration
```python
def _register_global_functions(self):
    """Register global functions that Ursina expects"""
    demo = self
    
    # Create global input function (must be named 'input' in global scope)
    def global_input(key):
        demo._handle_input(key)
    
    # Create global update function  
    def global_update():
        demo._handle_update()
    
    # Register with the main module's globals (where Ursina will look)
    import __main__
    __main__.input = global_input
    __main__.update = global_update
```

### 2. Input Handler
```python
def _handle_input(self, key):
    """Handle input events"""
    # Camera controls
    self.camera_controller.handle_input(key)
    
    # Demo controls
    if key == 'escape':
        self._exit_demo()
    elif key == 'space':
        self._end_turn()
    elif key == 'tab':
        self._show_ecs_statistics()
    elif key == '1':
        self.camera_controller.camera_mode = 0
        print("Camera: Orbit mode")
    # ... etc
```

### 3. Update Handler
```python
def _handle_update(self):
    """Handle update events"""
    # Update camera
    self.camera_controller.update_camera()
    self.camera_controller.handle_mouse_input()
    
    # WASD camera movement (like phase4_visual_demo.py)
    camera_speed = 5
    camera_move = Vec3(0, 0, 0)
    if held_keys['w']:
        camera_move += camera.forward * time.dt * camera_speed
    if held_keys['s']:
        camera_move += camera.back * time.dt * camera_speed
    if held_keys['a']:
        camera_move += camera.left * time.dt * camera_speed
    if held_keys['d']:
        camera_move += camera.right * time.dt * camera_speed
    
    camera.position += camera_move
    
    # Update visual entities from game entities
    for visual_entity in self.visual_entities:
        visual_entity.update_from_entity()
```

### 4. Registration on Run
```python
def run(self):
    """Start the demo"""
    try:
        # Set initial camera
        self.camera_controller.update_camera()
        
        # Register global input and update functions for Ursina
        self._register_global_functions()
        
        # Run Ursina app
        self.app.run()
```

## Fixed Functionality

After this fix, the following input should now work:

### ✅ Keyboard Input
- **WASD**: Camera movement (same as phase4_visual_demo.py)
- **1/2/3**: Camera mode switching (Orbit/Free/Top-down)
- **Space**: End turn and refresh all units
- **Tab**: Show ECS statistics and performance metrics
- **ESC**: Exit demo

### ✅ Mouse Input
- **Left Drag**: Rotate camera (orbit mode)
- **Scroll Wheel**: Zoom in/out (orbit mode)
- **Left Click**: Select units and tiles (existing functionality preserved)

### ✅ Camera Integration
- **CameraController**: Preserved exact functionality from apex-tactics.py
- **Multiple Modes**: Orbit, Free, and Top-down camera modes
- **Smooth Controls**: Same responsive feel as original

## Testing

To verify the fix works:

```bash
uv run run_modular_demo.py
```

The demo should now respond to all keyboard and mouse input as documented. The camera should move smoothly with WASD, rotate with mouse drag, and switch modes with number keys.

## Technical Notes

- **Global Scope**: Ursina specifically looks for `input` and `update` in `__main__` module globals
- **Function Bridging**: The global functions act as bridges to class methods
- **State Preservation**: All demo state remains in the class instance
- **Compatibility**: This approach matches the pattern used in apex-tactics.py

The fix maintains the modular ECS architecture while ensuring Ursina's input system works correctly.