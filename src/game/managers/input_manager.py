"""
Input Manager

Handles input processing with priority system extracted from monolithic controller.
Manages keyboard/mouse input routing with modal override capabilities.

Priority System:
1. Modal input (highest priority)
2. ESC key for mode cancellation  
3. Panel toggles (r, t keys)
4. Hotkey activation (1-8 keys)
5. Camera controls (lowest priority)
"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum

from game.interfaces.game_interfaces import IInputManager, InputEvent, IGameStateManager


class InputPriority(Enum):
    """Input handling priority levels."""
    MODAL = 1      # Highest - Modal dialogs
    MODE = 2       # Mode cancellation (ESC)
    PANEL = 3      # Panel toggles  
    HOTKEY = 4     # Ability hotkeys
    CAMERA = 5     # Lowest - Camera controls


class ModalInfo:
    """Information about registered modals."""
    
    def __init__(self, modal_id: str, priority: int, active: bool = False):
        self.modal_id = modal_id
        self.priority = priority
        self.active = active


class InputManager(IInputManager):
    """
    Manages input processing with priority system.
    
    Extracted from monolithic TacticalRPG controller to handle
    complex input routing and modal override behavior.
    """
    
    def __init__(self, game_state: IGameStateManager):
        """Initialize input manager."""
        self.game_state = game_state
        
        # Modal management
        self.registered_modals: Dict[str, ModalInfo] = {}
        self.active_modals: List[str] = []  # Ordered by priority
        
        # Input mode management
        self.input_mode = "normal"
        
        # Callback registrations
        self.hotkey_callbacks: Dict[str, Callable] = {}
        self.panel_toggle_callbacks: Dict[str, Callable] = {}
        self.mode_callbacks: Dict[str, Callable] = {}
        self.camera_callback: Optional[Callable] = None
        
        # Input state tracking
        self.last_input_time = 0
        self.input_blocked = False
        
        print("✅ InputManager initialized")
    
    def handle_input(self, event: InputEvent) -> bool:
        """
        Handle input event with priority system.
        
        Args:
            event: Input event to process
            
        Returns:
            True if input was handled
        """
        if self.input_blocked:
            return True
        
        key = event.key
        if not key:
            return False
        
        # Priority 1: Modal input (highest priority)
        if self._handle_modal_input(key):
            event.handled = True
            return True
        
        # Priority 2: ESC key for mode cancellation
        if key == 'escape' and self._handle_escape_input():
            event.handled = True
            return True
        
        # Priority 3: Panel toggles
        if self._handle_panel_toggles(key):
            event.handled = True
            return True
        
        # Priority 4: Hotkey activation
        if self._handle_hotkey_input(key):
            event.handled = True
            return True
        
        # Priority 5: Camera controls (lowest priority)
        if self._handle_camera_input(key):
            event.handled = True
            return True
        
        return False
    
    def _handle_modal_input(self, key: str) -> bool:
        """Handle input for active modals."""
        if not self.active_modals:
            return False
        
        # Process highest priority modal first
        active_modal_id = self.active_modals[0]
        modal_info = self.registered_modals.get(active_modal_id)
        
        if not modal_info or not modal_info.active:
            return False
        
        # Standard modal input handling
        if key == 'enter':
            self._confirm_modal(active_modal_id)
            return True
        elif key == 'escape':
            self._cancel_modal(active_modal_id)
            return True
        
        return False
    
    def _handle_escape_input(self) -> bool:
        """Handle ESC key for mode cancellation."""
        current_mode = self.game_state.get_current_mode()
        
        if current_mode == "move":
            self._trigger_mode_callback("cancel_movement")
            return True
        elif current_mode == "attack":
            self._trigger_mode_callback("cancel_attack")
            return True
        elif current_mode == "magic":
            self._trigger_mode_callback("cancel_magic")
            return True
        
        return False
    
    def _handle_panel_toggles(self, key: str) -> bool:
        """Handle panel toggle keys."""
        panel_map = {
            'r': 'control_panel',
            't': 'talent_panel',
            'i': 'inventory_panel',
            'c': 'character_panel',
            'p': 'party_panel',
            'u': 'upgrade_panel'
        }
        
        if key in panel_map:
            panel_name = panel_map[key]
            callback = self.panel_toggle_callbacks.get(panel_name)
            if callback:
                try:
                    callback()
                    print(f"🖼️ Toggled {panel_name}")
                    return True
                except Exception as e:
                    print(f"⚠️ Panel toggle error for {panel_name}: {e}")
        
        return False
    
    def _handle_hotkey_input(self, key: str) -> bool:
        """Handle hotkey activation."""
        if key in ['1', '2', '3', '4', '5', '6', '7', '8']:
            slot_index = int(key) - 1
            callback = self.hotkey_callbacks.get(f"slot_{slot_index}")
            if callback:
                try:
                    callback(slot_index)
                    print(f"🔥 Activated hotkey slot {slot_index + 1}")
                    return True
                except Exception as e:
                    print(f"⚠️ Hotkey activation error for slot {slot_index}: {e}")
        
        return False
    
    def _handle_camera_input(self, key: str) -> bool:
        """Handle camera controls."""
        if self.camera_callback:
            try:
                return self.camera_callback(key)
            except Exception as e:
                print(f"⚠️ Camera input error: {e}")
        
        return False
    
    def register_modal(self, modal_id: str, priority: int):
        """Register a modal for input handling."""
        self.registered_modals[modal_id] = ModalInfo(modal_id, priority)
        print(f"📋 Registered modal: {modal_id} (priority {priority})")
    
    def unregister_modal(self, modal_id: str):
        """Unregister a modal."""
        if modal_id in self.registered_modals:
            self._deactivate_modal(modal_id)
            del self.registered_modals[modal_id]
            print(f"📋 Unregistered modal: {modal_id}")
    
    def activate_modal(self, modal_id: str):
        """Activate a modal for input handling."""
        if modal_id not in self.registered_modals:
            print(f"⚠️ Cannot activate unregistered modal: {modal_id}")
            return
        
        modal_info = self.registered_modals[modal_id]
        modal_info.active = True
        
        # Insert in priority order (highest priority first)
        if modal_id not in self.active_modals:
            inserted = False
            for i, active_id in enumerate(self.active_modals):
                active_info = self.registered_modals[active_id]
                if modal_info.priority < active_info.priority:
                    self.active_modals.insert(i, modal_id)
                    inserted = True
                    break
            
            if not inserted:
                self.active_modals.append(modal_id)
        
        print(f"🎭 Activated modal: {modal_id}")
    
    def _deactivate_modal(self, modal_id: str):
        """Deactivate a modal."""
        if modal_id in self.registered_modals:
            self.registered_modals[modal_id].active = False
        
        if modal_id in self.active_modals:
            self.active_modals.remove(modal_id)
        
        print(f"🎭 Deactivated modal: {modal_id}")
    
    def _confirm_modal(self, modal_id: str):
        """Handle modal confirmation."""
        callback = self.mode_callbacks.get(f"confirm_{modal_id}")
        if callback:
            try:
                callback()
            except Exception as e:
                print(f"⚠️ Modal confirm error for {modal_id}: {e}")
        
        self._deactivate_modal(modal_id)
    
    def _cancel_modal(self, modal_id: str):
        """Handle modal cancellation."""
        callback = self.mode_callbacks.get(f"cancel_{modal_id}")
        if callback:
            try:
                callback()
            except Exception as e:
                print(f"⚠️ Modal cancel error for {modal_id}: {e}")
        
        self._deactivate_modal(modal_id)
    
    def _trigger_mode_callback(self, mode_action: str):
        """Trigger a mode-related callback."""
        callback = self.mode_callbacks.get(mode_action)
        if callback:
            try:
                callback()
            except Exception as e:
                print(f"⚠️ Mode callback error for {mode_action}: {e}")
    
    def set_input_mode(self, mode: str):
        """Set the input processing mode."""
        self.input_mode = mode
        print(f"🎮 Input mode set: {mode}")
    
    def block_input(self, block: bool):
        """Block or unblock input processing."""
        self.input_blocked = block
        print(f"🚫 Input {'blocked' if block else 'unblocked'}")
    
    # Callback Registration Methods
    
    def register_hotkey_callback(self, slot_index: int, callback: Callable):
        """Register callback for hotkey slot."""
        self.hotkey_callbacks[f"slot_{slot_index}"] = callback
    
    def register_panel_toggle_callback(self, panel_name: str, callback: Callable):
        """Register callback for panel toggle."""
        self.panel_toggle_callbacks[panel_name] = callback
    
    def register_mode_callback(self, mode_action: str, callback: Callable):
        """Register callback for mode actions."""
        self.mode_callbacks[mode_action] = callback
    
    def register_camera_callback(self, callback: Callable):
        """Register callback for camera input."""
        self.camera_callback = callback
    
    # State Query Methods
    
    def is_modal_active(self) -> bool:
        """Check if any modal is currently active."""
        return len(self.active_modals) > 0
    
    def get_active_modal(self) -> Optional[str]:
        """Get the highest priority active modal."""
        return self.active_modals[0] if self.active_modals else None
    
    def get_input_state(self) -> Dict[str, Any]:
        """Get comprehensive input state information."""
        return {
            "input_mode": self.input_mode,
            "input_blocked": self.input_blocked,
            "active_modals": self.active_modals.copy(),
            "registered_modals": len(self.registered_modals),
            "hotkey_slots": len(self.hotkey_callbacks),
            "panel_toggles": len(self.panel_toggle_callbacks)
        }
    
    def shutdown(self):
        """Clean shutdown of input manager."""
        self.active_modals.clear()
        self.registered_modals.clear()
        self.hotkey_callbacks.clear()
        self.panel_toggle_callbacks.clear()
        self.mode_callbacks.clear()
        self.camera_callback = None
        
        print("✅ InputManager shutdown complete")