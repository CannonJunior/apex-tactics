"""
Modal Manager

Manages modal dialogs and overlays for the tactical RPG game.
Integrates with the existing UI modal system and provides game-specific modal handling.
"""

from typing import Dict, Any, Optional, List, Callable
from enum import Enum

from .base_manager import BaseManager
from game.interfaces.game_interfaces import IModalManager


class ModalType(Enum):
    """Types of modals that can be displayed."""
    ATTACK_CONFIRMATION = "attack_confirmation"
    ABILITY_SELECTION = "ability_selection"
    ITEM_SELECTION = "item_selection"
    BATTLE_RESULTS = "battle_results"
    UNIT_INFO = "unit_info"
    SETTINGS = "settings"
    CONFIRM_ACTION = "confirm_action"
    ERROR_MESSAGE = "error_message"
    VICTORY = "victory"
    DEFEAT = "defeat"


class ModalManager(BaseManager, IModalManager):
    """
    Manages modal dialogs and overlays for the game.
    
    Features:
    - Modal state management
    - Modal stacking and priority
    - Integration with UI modal system
    - Game-specific modal types
    """
    
    def __init__(self, game_controller):
        super().__init__(game_controller)
        
        # Modal state
        self.active_modals: Dict[str, Dict[str, Any]] = {}
        self.modal_stack: List[str] = []
        self.modal_counter = 0
        
        # Modal callbacks
        self.modal_callbacks: Dict[str, Callable] = {}
        
        # Modal configurations
        self.modal_configs: Dict[ModalType, Dict[str, Any]] = {}
        
        # UI integration
        self.ui_modal_manager = None  # Will be set during initialization
        
        print("✅ ModalManager initialized")
    
    def _perform_initialization(self):
        """Initialize modal manager."""
        # Try to integrate with existing UI modal system
        self._setup_ui_integration()
        
        # Register default modal types
        self._register_default_modals()
        
        print("✅ ModalManager initialization complete")
    
    def _setup_ui_integration(self):
        """Set up integration with UI modal system."""
        try:
            # Try to get existing modal manager from UI system
            if hasattr(self.game_controller, 'ui_modal_manager'):
                self.ui_modal_manager = self.game_controller.ui_modal_manager
            elif hasattr(self.game_controller, 'control_panel'):
                # Check if control panel has modal capabilities
                control_panel = self.game_controller.control_panel
                if hasattr(control_panel, 'modal_manager'):
                    self.ui_modal_manager = control_panel.modal_manager
            
            print("✅ UI modal system integration established")
        except Exception as e:
            print(f"⚠️ UI modal integration failed: {e}")
    
    def _register_default_modals(self):
        """Register default modal types and their configurations."""
        default_modals = {
            ModalType.ATTACK_CONFIRMATION: {
                'title': 'Confirm Attack',
                'buttons': ['Attack', 'Cancel'],
                'closable': True
            },
            ModalType.ABILITY_SELECTION: {
                'title': 'Select Ability',
                'buttons': ['Use', 'Cancel'],
                'closable': True
            },
            ModalType.ITEM_SELECTION: {
                'title': 'Select Item',
                'buttons': ['Use', 'Cancel'],
                'closable': True
            },
            ModalType.BATTLE_RESULTS: {
                'title': 'Battle Results',
                'buttons': ['Continue'],
                'closable': False
            },
            ModalType.UNIT_INFO: {
                'title': 'Unit Information',
                'buttons': ['Close'],
                'closable': True
            },
            ModalType.SETTINGS: {
                'title': 'Settings',
                'buttons': ['Apply', 'Cancel'],
                'closable': True
            },
            ModalType.CONFIRM_ACTION: {
                'title': 'Confirm Action',
                'buttons': ['Confirm', 'Cancel'],
                'closable': True
            },
            ModalType.ERROR_MESSAGE: {
                'title': 'Error',
                'buttons': ['OK'],
                'closable': True
            },
            ModalType.VICTORY: {
                'title': 'Victory!',
                'buttons': ['Continue'],
                'closable': False
            },
            ModalType.DEFEAT: {
                'title': 'Defeat',
                'buttons': ['Retry', 'Main Menu'],
                'closable': False
            }
        }
        
        for modal_type, config in default_modals.items():
            self._register_modal_type(modal_type, config)
    
    def _register_modal_type(self, modal_type: ModalType, config: Dict[str, Any]):
        """Register a modal type with its configuration."""
        self.modal_configs[modal_type] = config
    
    def show_modal(self, modal_type: ModalType, context: Dict[str, Any] = None) -> str:
        """
        Show a modal dialog.
        
        Args:
            modal_type: Type of modal to show
            context: Additional context data for the modal
            
        Returns:
            Modal ID for tracking
        """
        if context is None:
            context = {}
        
        # Generate unique modal ID
        modal_id = f"{modal_type.value}_{self.modal_counter}"
        self.modal_counter += 1
        
        # Get modal configuration
        config = self.modal_configs.get(modal_type, {})
        
        # Create modal data
        modal_data = {
            'id': modal_id,
            'type': modal_type,
            'context': context,
            'config': config,
            'active': True,
            'created_at': self._get_current_time()
        }
        
        # Add to active modals
        self.active_modals[modal_id] = modal_data
        self.modal_stack.append(modal_id)
        
        # Show modal in UI system
        self._show_ui_modal(modal_id, modal_type, context, config)
        
        # Emit modal opened event
        if hasattr(self.game_controller, 'event_bus'):
            self.game_controller.event_bus.emit('modal_opened', {
                'modal_id': modal_id,
                'modal_type': modal_type.value,
                'context': context
            })
        
        print(f"📋 Opened modal: {modal_type.value} (ID: {modal_id})")
        return modal_id
    
    def hide_modal(self, modal_id: str) -> bool:
        """
        Hide a modal dialog.
        
        Args:
            modal_id: ID of modal to hide
            
        Returns:
            True if modal was successfully hidden
        """
        if modal_id not in self.active_modals:
            return False
        
        # Remove from active modals
        modal_data = self.active_modals.pop(modal_id)
        
        # Remove from stack
        if modal_id in self.modal_stack:
            self.modal_stack.remove(modal_id)
        
        # Hide modal in UI system
        self._hide_ui_modal(modal_id, modal_data)
        
        # Execute callback if registered
        if modal_id in self.modal_callbacks:
            callback = self.modal_callbacks.pop(modal_id)
            try:
                callback(modal_id, 'closed')
            except Exception as e:
                print(f"⚠️ Modal callback error: {e}")
        
        # Emit modal closed event
        if hasattr(self.game_controller, 'event_bus'):
            self.game_controller.event_bus.emit('modal_closed', {
                'modal_id': modal_id,
                'modal_type': modal_data['type'].value
            })
        
        print(f"📋 Closed modal: {modal_data['type'].value} (ID: {modal_id})")
        return True
    
    def is_modal_active(self, modal_id: Optional[str] = None) -> bool:
        """
        Check if a modal is active.
        
        Args:
            modal_id: Specific modal ID to check, or None to check if any modal is active
            
        Returns:
            True if modal is active
        """
        if modal_id is None:
            return len(self.active_modals) > 0
        
        return modal_id in self.active_modals
    
    def get_active_modal(self) -> Optional[str]:
        """
        Get the currently active modal ID.
        
        Returns:
            Modal ID of topmost modal, or None if no modals are active
        """
        if not self.modal_stack:
            return None
        
        return self.modal_stack[-1]
    
    def get_modal_data(self, modal_id: str) -> Optional[Dict[str, Any]]:
        """Get modal data by ID."""
        return self.active_modals.get(modal_id)
    
    def close_all_modals(self):
        """Close all active modals."""
        modal_ids = list(self.active_modals.keys())
        for modal_id in modal_ids:
            self.hide_modal(modal_id)
    
    def show_attack_confirmation(self, attacker_name: str, target_name: str, callback: Callable = None) -> str:
        """Show attack confirmation modal."""
        context = {
            'attacker_name': attacker_name,
            'target_name': target_name,
            'message': f"Confirm attack: {attacker_name} → {target_name}?"
        }
        
        modal_id = self.show_modal(ModalType.ATTACK_CONFIRMATION, context)
        
        if callback:
            self.modal_callbacks[modal_id] = callback
        
        return modal_id
    
    def show_ability_selection(self, unit_name: str, abilities: List[Dict[str, Any]], callback: Callable = None) -> str:
        """Show ability selection modal."""
        context = {
            'unit_name': unit_name,
            'abilities': abilities,
            'message': f"Select ability for {unit_name}:"
        }
        
        modal_id = self.show_modal(ModalType.ABILITY_SELECTION, context)
        
        if callback:
            self.modal_callbacks[modal_id] = callback
        
        return modal_id
    
    def show_battle_results(self, victory: bool, results: Dict[str, Any], callback: Callable = None) -> str:
        """Show battle results modal."""
        context = {
            'victory': victory,
            'results': results,
            'message': "Victory!" if victory else "Defeat"
        }
        
        modal_type = ModalType.VICTORY if victory else ModalType.DEFEAT
        modal_id = self.show_modal(modal_type, context)
        
        if callback:
            self.modal_callbacks[modal_id] = callback
        
        return modal_id
    
    def show_error_message(self, message: str, callback: Callable = None) -> str:
        """Show error message modal."""
        context = {
            'message': message,
            'error': True
        }
        
        modal_id = self.show_modal(ModalType.ERROR_MESSAGE, context)
        
        if callback:
            self.modal_callbacks[modal_id] = callback
        
        return modal_id
    
    def show_action_selection_modal(self, unit, callback: Callable = None) -> str:
        """Show action selection modal for a unit."""
        # Get available actions for the unit
        actions = getattr(unit, 'action_options', ['Move', 'Attack', 'Magic', 'Wait'])
        
        context = {
            'unit_name': unit.name,
            'actions': actions,
            'message': f"Choose action for {unit.name}:"
        }
        
        # Use ability selection modal type for action selection
        modal_id = self.show_modal(ModalType.ABILITY_SELECTION, context)
        
        # Store callback with unit reference
        if callback:
            def action_callback(action_name):
                callback(action_name, unit)
            self.modal_callbacks[modal_id] = action_callback
        
        return modal_id
    
    def show_error_message(self, message: str, callback: Callable = None) -> str:
        """Show error message modal."""
        context = {
            'message': message,
            'title': 'Error'
        }
        
        modal_id = self.show_modal(ModalType.ERROR_MESSAGE, context)
        
        if callback:
            self.modal_callbacks[modal_id] = callback
        
        return modal_id
    
    def _show_ui_modal(self, modal_id: str, modal_type: ModalType, context: Dict[str, Any], config: Dict[str, Any]):
        """Show modal in the UI system."""
        try:
            if self.ui_modal_manager:
                # Use existing UI modal manager
                self.ui_modal_manager.show_modal(modal_id, modal_type.value, context, config)
            else:
                # Fallback to console output for testing
                print(f"📋 UI Modal: {modal_type.value}")
                print(f"   Context: {context}")
                print(f"   Config: {config}")
        except Exception as e:
            print(f"⚠️ UI modal display error: {e}")
    
    def _hide_ui_modal(self, modal_id: str, modal_data: Dict[str, Any]):
        """Hide modal in the UI system."""
        try:
            if self.ui_modal_manager:
                # Use existing UI modal manager
                self.ui_modal_manager.hide_modal(modal_id)
            else:
                # Fallback to console output for testing
                print(f"📋 UI Modal Closed: {modal_data['type'].value}")
        except Exception as e:
            print(f"⚠️ UI modal hide error: {e}")
    
    def _get_current_time(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def get_modal_stats(self) -> Dict[str, Any]:
        """Get modal system statistics."""
        return {
            'active_modals': len(self.active_modals),
            'modal_stack_depth': len(self.modal_stack),
            'total_modals_created': self.modal_counter,
            'modal_types_registered': len(getattr(self, 'modal_configs', {})),
            'ui_integration_active': self.ui_modal_manager is not None
        }
    
    def shutdown(self):
        """Shutdown modal manager."""
        self.close_all_modals()
        self.modal_callbacks.clear()
        print("✅ ModalManager shutdown complete")