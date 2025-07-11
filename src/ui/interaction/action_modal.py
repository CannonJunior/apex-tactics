"""
Action Modal System

Modal dialog system for unit actions, confirmations, and interactive choices.
Based on patterns from the apex-tactics implementation.
"""

from typing import List, Dict, Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass

try:
    from ursina import Entity, Text, Button, color, destroy, camera
    from ursina.prefabs.button import Button as UrsinaButton
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from core.ecs.entity import Entity as GameEntity


class ModalType(Enum):
    """Types of modal dialogs"""
    UNIT_ACTIONS = "unit_actions"
    MOVEMENT_CONFIRMATION = "movement_confirmation"
    ATTACK_CONFIRMATION = "attack_confirmation"
    ABILITY_SELECTION = "ability_selection"
    ITEM_SELECTION = "item_selection"
    CONFIRMATION = "confirmation"


@dataclass
class ActionOption:
    """Represents an action option in a modal"""
    text: str
    callback: Callable
    enabled: bool = True
    tooltip: Optional[str] = None
    icon: Optional[str] = None


class ActionModal:
    """
    Modal dialog system for tactical game interactions.
    
    Provides popup dialogs for unit actions, confirmations, and choices
    with proper visual styling and interaction handling.
    """
    
    def __init__(self, modal_type: ModalType, title: str, 
                 actions: List[ActionOption], target_entity: Optional[GameEntity] = None):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for ActionModal")
        
        # Load master UI configuration
        from src.core.ui.ui_config_manager import get_ui_config_manager
        self.ui_config = get_ui_config_manager()
        
        self.modal_type = modal_type
        self.title = title
        self.actions = actions
        self.target_entity = target_entity
        
        # Modal state
        self.is_visible = False
        self.modal_entity = None
        self.background_entity = None
        self.action_buttons = []
        
        # Styling configuration from master UI config
        modal_config = self.ui_config.get('ui_interaction.action_modal', {})
        self.modal_width = modal_config.get('modal_width', 0.4)
        self.modal_height = modal_config.get('modal_height', 0.6)
        self.button_height = modal_config.get('button_height', 0.08)
        self.button_spacing = modal_config.get('button_spacing', 0.02)
        
        # Colors from master UI config
        self.colors = {
            'background': self.ui_config.get_color('ui_interaction.action_modal.colors.background', '#555555'),
            'modal_bg': self.ui_config.get_color('ui_interaction.action_modal.colors.modal_bg', '#A9A9A9'),
            'modal_border': self.ui_config.get_color('ui_interaction.action_modal.colors.modal_border', '#FFFFFF'),
            'button_normal': self.ui_config.get_color('ui_interaction.action_modal.colors.button_normal', '#87CEEB'),
            'button_hover': self.ui_config.get_color('ui_interaction.action_modal.colors.button_hover', '#0000FF'),
            'button_disabled': self.ui_config.get_color('ui_interaction.action_modal.colors.button_disabled', '#808080'),
            'text': self.ui_config.get_color('ui_interaction.action_modal.colors.text', '#FFFFFF'),
            'title': self.ui_config.get_color('ui_interaction.action_modal.colors.title', '#FFFF00')
        }
        
        # Create modal
        self._create_modal()
    
    def _create_modal(self):
        """Create the modal UI elements using master UI config."""
        # Get entity configuration from master UI config
        entity_config = self.ui_config.get('ui_interaction.action_modal.entities', {})
        background_model = entity_config.get('background_model', 'cube')
        modal_model = entity_config.get('modal_model', 'cube')
        background_scale = entity_config.get('background_scale', {'x': 2, 'y': 1, 'z': 2})
        modal_thickness = entity_config.get('modal_thickness', 0.01)
        background_z_offset = entity_config.get('background_z_offset', -0.1)
        
        # Create semi-transparent background
        self.background_entity = Entity(
            model=background_model,
            color=self.colors['background'],
            scale=(background_scale['x'], background_scale['y'], background_scale['z']),
            position=(0, 0, background_z_offset),
            enabled=False
        )
        
        # Create main modal panel
        self.modal_entity = Entity(
            model=modal_model,
            color=self.colors['modal_bg'],
            scale=(self.modal_width, self.modal_height, modal_thickness),
            position=(0, 0, 0),
            enabled=False
        )
        
        # Create title text using master UI config
        title_config = self.ui_config.get('ui_interaction.action_modal.title', {})
        title_y_offset = title_config.get('y_offset', 0.1)
        title_z_offset = title_config.get('z_offset', 0.01)
        title_scale = title_config.get('scale', 1.5)
        title_origin = title_config.get('origin', [0, 0])
        
        self.title_text = Text(
            self.title,
            parent=self.modal_entity,
            position=(0, self.modal_height/2 - title_y_offset, title_z_offset),
            scale=title_scale,
            color=self.colors['title'],
            origin=tuple(title_origin)
        )
        
        # Create action buttons
        self._create_action_buttons()
        
        # Position modal relative to camera
        self._position_modal()
    
    def _create_action_buttons(self):
        """Create buttons for each action option"""
        button_start_y = self.modal_height/2 - 0.2
        
        for i, action in enumerate(self.actions):
            button_y = button_start_y - (i * (self.button_height + self.button_spacing))
            
            # Create button
            button = Button(
                text=action.text,
                color=self.colors['button_normal'] if action.enabled else self.colors['button_disabled'],
                scale=(self.modal_width - 0.1, self.button_height),
                position=(0, button_y, 0.01),
                parent=self.modal_entity,
                enabled=action.enabled
            )
            
            # Set up button callback
            if action.enabled:
                button.on_click = self._create_action_callback(action)
                button.on_mouse_enter = lambda b=button: setattr(b, 'color', self.colors['button_hover'])
                button.on_mouse_exit = lambda b=button: setattr(b, 'color', self.colors['button_normal'])
            
            self.action_buttons.append(button)
        
        # Add cancel button using master UI config
        cancel_config = self.ui_config.get('ui_interaction.action_modal.cancel_button', {})
        cancel_spacing = cancel_config.get('spacing', 0.05)
        cancel_text = cancel_config.get('text', 'Cancel')
        cancel_color = self.ui_config.get_color('ui_interaction.action_modal.cancel_button.color', '#FF0000')
        cancel_hover_color = self.ui_config.get_color('ui_interaction.action_modal.cancel_button.hover_color', '#A9A9A9')
        button_width_offset = cancel_config.get('width_offset', 0.1)
        button_z_offset = cancel_config.get('z_offset', 0.01)
        
        cancel_button_y = button_start_y - (len(self.actions) * (self.button_height + self.button_spacing)) - cancel_spacing
        
        cancel_button = Button(
            text=cancel_text,
            color=cancel_color,
            scale=(self.modal_width - button_width_offset, self.button_height),
            position=(0, cancel_button_y, button_z_offset),
            parent=self.modal_entity
        )
        cancel_button.on_click = self.close
        cancel_button.on_mouse_enter = lambda: setattr(cancel_button, 'color', cancel_hover_color)
        cancel_button.on_mouse_exit = lambda: setattr(cancel_button, 'color', cancel_color)
        
        self.action_buttons.append(cancel_button)
    
    def _create_action_callback(self, action: ActionOption) -> Callable:
        """Create a callback function for an action button"""
        def callback():
            try:
                # Execute the action callback
                if action.callback:
                    action.callback(self.target_entity if self.target_entity else None)
            except Exception as e:
                print(f"Error executing action '{action.text}': {e}")
            finally:
                # Always close the modal after action
                self.close()
        
        return callback
    
    def _position_modal(self):
        """Position the modal relative to the camera using master UI config."""
        if camera:
            # Get positioning configuration from master UI config
            position_config = self.ui_config.get('ui_interaction.action_modal.positioning', {})
            modal_distance = position_config.get('modal_distance', 2.0)
            background_offset = position_config.get('background_offset', 0.1)
            face_camera = position_config.get('face_camera', True)
            look_at_axis = position_config.get('look_at_axis', 'forward')
            
            # Position modal in front of camera
            self.modal_entity.position = camera.position + camera.forward * modal_distance
            self.background_entity.position = camera.position + camera.forward * (modal_distance - background_offset)
            
            # Make modal face the camera if configured
            if face_camera:
                self.modal_entity.look_at(camera.position, axis=look_at_axis)
    
    def show(self):
        """Show the modal dialog"""
        if self.modal_entity and self.background_entity:
            self.background_entity.enabled = True
            self.modal_entity.enabled = True
            self.is_visible = True
            
            # Refresh positioning
            self._position_modal()
    
    def close(self):
        """Close and destroy the modal dialog"""
        self.is_visible = False
        
        if self.modal_entity:
            self.modal_entity.enabled = False
        
        if self.background_entity:
            self.background_entity.enabled = False
        
        # Clean up after a short delay to allow animation
        self.destroy()
    
    def destroy(self):
        """Completely destroy the modal and clean up resources"""
        try:
            if self.modal_entity:
                destroy(self.modal_entity)
                self.modal_entity = None
            
            if self.background_entity:
                destroy(self.background_entity)
                self.background_entity = None
            
            self.action_buttons.clear()
            
        except Exception as e:
            print(f"Error destroying modal: {e}")
    
    def update_position(self):
        """Update modal position (call during camera movement)"""
        if self.is_visible:
            self._position_modal()


class ActionModalManager:
    """
    Manages multiple action modals and prevents overlapping.
    """
    
    def __init__(self):
        self.active_modals: List[ActionModal] = []
        self.modal_history: List[ModalType] = []
    
    def show_unit_actions_modal(self, unit: GameEntity, available_actions: List[str],
                              action_callbacks: Dict[str, Callable]) -> ActionModal:
        """Show a modal with available unit actions"""
        # Create action options
        actions = []
        for action_name in available_actions:
            callback = action_callbacks.get(action_name)
            if callback:
                actions.append(ActionOption(
                    text=action_name.replace('_', ' ').title(),
                    callback=callback,
                    enabled=True
                ))
        
        modal = ActionModal(
            modal_type=ModalType.UNIT_ACTIONS,
            title=f"Unit Actions",
            actions=actions,
            target_entity=unit
        )
        
        return self._show_modal(modal)
    
    def show_confirmation_modal(self, title: str, message: str, 
                              confirm_callback: Callable, 
                              cancel_callback: Optional[Callable] = None) -> ActionModal:
        """Show a confirmation dialog"""
        actions = [
            ActionOption(text="Confirm", callback=confirm_callback),
        ]
        
        if cancel_callback:
            actions.append(ActionOption(text="Cancel", callback=cancel_callback))
        
        modal = ActionModal(
            modal_type=ModalType.CONFIRMATION,
            title=title,
            actions=actions
        )
        
        return self._show_modal(modal)
    
    def show_movement_confirmation_modal(self, path: List, confirm_callback: Callable) -> ActionModal:
        """Show movement confirmation modal"""
        actions = [
            ActionOption(text=f"Move ({len(path)} tiles)", callback=confirm_callback),
        ]
        
        modal = ActionModal(
            modal_type=ModalType.MOVEMENT_CONFIRMATION,
            title="Confirm Movement",
            actions=actions
        )
        
        return self._show_modal(modal)
    
    def _show_modal(self, modal: ActionModal) -> ActionModal:
        """Internal method to show a modal and manage the stack"""
        # Close any existing modals of the same type
        self.close_modals_of_type(modal.modal_type)
        
        # Add to active modals
        self.active_modals.append(modal)
        self.modal_history.append(modal.modal_type)
        
        # Show the modal
        modal.show()
        
        return modal
    
    def close_all_modals(self):
        """Close all active modals"""
        for modal in self.active_modals[:]:  # Copy list to avoid modification during iteration
            modal.close()
        
        self.active_modals.clear()
        self.modal_history.clear()
    
    def close_modals_of_type(self, modal_type: ModalType):
        """Close all modals of a specific type"""
        for modal in self.active_modals[:]:
            if modal.modal_type == modal_type:
                modal.close()
                self.active_modals.remove(modal)
    
    def has_active_modals(self) -> bool:
        """Check if there are any active modals"""
        return len(self.active_modals) > 0
    
    def update(self):
        """Update all active modals (call in main update loop)"""
        for modal in self.active_modals[:]:
            if not modal.is_visible:
                self.active_modals.remove(modal)
            else:
                modal.update_position()