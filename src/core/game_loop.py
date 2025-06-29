"""
Game Loop Management

Central game loop coordinator that handles frame-by-frame updates of all major game systems.
Manages ECS World updates, camera updates, interaction systems, and UI panel updates.
"""

from typing import Optional, Any

try:
    from ursina import time
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


class GameLoopManager:
    """
    Central game loop manager that coordinates all game system updates.
    
    Handles frame-by-frame updates for:
    - ECS World system processing
    - Camera controller updates (mouse input and position)
    - Interaction manager updates
    - Control panel UI updates
    - Game panels UI updates
    """
    
    def __init__(self, game_reference: Any, control_panel: Optional[Any] = None, game_panels: Optional[Any] = None):
        """
        Initialize the game loop manager.
        
        Args:
            game_reference: Reference to the main game controller (TacticalRPG)
            control_panel: Optional reference to control panel UI
            game_panels: Optional reference to game panels manager
        """
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for GameLoopManager")
        
        self.game = game_reference
        self.control_panel = control_panel
        self.game_panels = game_panels
    
    def set_control_panel(self, control_panel: Any):
        """
        Set or update the control panel reference.
        
        Args:
            control_panel: Control panel instance
        """
        self.control_panel = control_panel
    
    def set_game_panels(self, game_panels: Any):
        """
        Set or update the game panels manager reference.
        
        Args:
            game_panels: Game panels manager instance
        """
        self.game_panels = game_panels
    
    def update(self):
        """
        Main update function called every frame.
        
        Coordinates updates across all major game systems in the correct order:
        1. ECS World system processing
        2. Camera controller updates
        3. Interaction manager updates
        4. UI panel updates
        """
        # Update ECS World - this processes all systems
        self._update_ecs_world()
        
        # Update camera
        self._update_camera()
        
        # Update interaction manager (if available)
        self._update_interaction_manager()
        
        # Update UI panels
        self._update_ui_panels()
    
    def _update_ecs_world(self):
        """Update the ECS World system with delta time."""
        if not self.game or not hasattr(self.game, 'world'):
            return
        
        try:
            self.game.world.update(time.dt)
        except Exception as e:
            print(f"⚠ ECS World update error: {e}")
    
    def _update_camera(self):
        """Update camera controller for mouse input and position."""
        if not self.game or not hasattr(self.game, 'camera_controller'):
            return
        
        try:
            self.game.camera_controller.handle_mouse_input()
            self.game.camera_controller.update_camera()
        except Exception as e:
            print(f"⚠ Camera update error: {e}")
    
    def _update_interaction_manager(self):
        """Update interaction manager if available."""
        if (not self.game or 
            not hasattr(self.game, 'interaction_manager') or 
            not self.game.interaction_manager):
            return
        
        try:
            self.game.interaction_manager.update(time.dt)
        except Exception as e:
            print(f"⚠ InteractionManager update error: {e}")
    
    def _update_ui_panels(self):
        """Update control panel and game panels with current game state."""
        self._update_control_panel()
        self._update_game_panels()
    
    def _update_control_panel(self):
        """Update control panel with current unit information."""
        if not self.control_panel or not self.game:
            return
        
        try:
            # Update control panel with current unit info when no unit is selected
            if (hasattr(self.game, 'turn_manager') and self.game.turn_manager and 
                hasattr(self.game.turn_manager, 'current_unit') and self.game.turn_manager.current_unit() and 
                not (hasattr(self.game, 'selected_unit') and self.game.selected_unit)):
                
                if hasattr(self.control_panel, 'update_unit_info'):
                    self.control_panel.update_unit_info(self.game.turn_manager.current_unit())
        except Exception as e:
            print(f"⚠ Control panel update error: {e}")
    
    def _update_game_panels(self):
        """Update game panels with character data."""
        if not self.game_panels or not self.game:
            return
        
        try:
            # Update game panels with current character data
            if hasattr(self.game, 'selected_unit') and self.game.selected_unit:
                # Priority to selected unit
                if hasattr(self.game_panels, 'update_character_data'):
                    self.game_panels.update_character_data(self.game.selected_unit)
            elif (hasattr(self.game, 'turn_manager') and self.game.turn_manager and 
                  hasattr(self.game.turn_manager, 'current_unit') and self.game.turn_manager.current_unit()):
                # Fallback to current turn unit
                if hasattr(self.game_panels, 'update_character_data'):
                    self.game_panels.update_character_data(self.game.turn_manager.current_unit())
        except Exception as e:
            print(f"⚠ Game panels update error: {e}")


def create_game_loop_manager(game_reference: Any, control_panel: Optional[Any] = None, 
                           game_panels: Optional[Any] = None) -> GameLoopManager:
    """
    Factory function to create a game loop manager instance.
    
    Args:
        game_reference: Reference to the main game controller
        control_panel: Optional reference to control panel UI
        game_panels: Optional reference to game panels manager
        
    Returns:
        Configured GameLoopManager instance
    """
    return GameLoopManager(game_reference, control_panel, game_panels)


# Utility function for backwards compatibility
def update_game_systems(game_reference: Any, control_panel: Optional[Any] = None, 
                       game_panels: Optional[Any] = None):
    """
    Utility function to update all game systems.
    
    This is a simplified interface for the game loop functionality.
    For more advanced usage, create a GameLoopManager instance.
    
    Args:
        game_reference: Reference to the main game controller
        control_panel: Optional reference to control panel UI
        game_panels: Optional reference to game panels manager
    """
    manager = GameLoopManager(game_reference, control_panel, game_panels)
    manager.update()