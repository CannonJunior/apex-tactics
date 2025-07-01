"""
Game Panel Manager

Centralized management for all game UI panels with keyboard shortcuts.
Coordinates panel visibility and provides unified interface for panel interactions.
"""

from typing import Optional, Dict, Any
from .character_panel import CharacterPanel
from .inventory_panel import InventoryPanel
from .talent_panel import TalentPanel
from .party_panel import PartyPanel
from .upgrade_panel import UpgradePanel


class GamePanelManager:
    """
    Enhanced panel manager specifically for Apex Tactics game panels.
    
    Manages game panels:
    - Character Panel ('c' key)
    - Inventory Panel ('i' key)
    - Talent Panel ('t' key)
    - Party Panel ('p' key)
    - Upgrade Panel ('u' key)
    """
    
    def __init__(self, game_reference: Optional[Any] = None):
        """
        Initialize game panel manager with all panels.
        
        Args:
            game_reference: Reference to main game object
        """
        self.game_reference = game_reference
        self.panels: Dict[str, Any] = {}
        self.key_bindings: Dict[str, str] = {}
        self.active_panel: Optional[str] = None
        
        # Initialize all panels
        self._create_panels()
        
        # Register panels with keyboard shortcuts
        self._register_panels()
        
        print(f"✅ Game Panel Manager initialized with {len(self.panels)} panels")
    
    def _create_panels(self):
        """Create all game panels."""
        try:
            self.character_panel = CharacterPanel(self.game_reference)
            print("✅ Character panel created successfully")
            
        except Exception as e:
            print(f"❌ Error creating character panel: {e}")
            self.character_panel = None
        
        try:
            self.inventory_panel = InventoryPanel(self.game_reference)
            print("✅ Inventory panel created successfully")
            
        except Exception as e:
            print(f"❌ Error creating inventory panel: {e}")
            self.inventory_panel = None
        
        try:
            self.talent_panel = TalentPanel(self.game_reference)
            print("✅ Talent panel created successfully")
            
        except Exception as e:
            print(f"❌ Error creating talent panel: {e}")
            self.talent_panel = None
        
        try:
            self.party_panel = PartyPanel(self.game_reference)
            print("✅ Party panel created successfully")
            
        except Exception as e:
            print(f"❌ Error creating party panel: {e}")
            self.party_panel = None
        
        try:
            self.upgrade_panel = UpgradePanel(self.game_reference)
            print("✅ Upgrade panel created successfully")
            
        except Exception as e:
            print(f"❌ Error creating upgrade panel: {e}")
            self.upgrade_panel = None
    
    def _register_panels(self):
        """Register panels with their keyboard shortcuts."""
        if self.character_panel:
            self.panels["character"] = self.character_panel
            self.key_bindings["c"] = "character"
        
        if self.inventory_panel:
            self.panels["inventory"] = self.inventory_panel
            self.key_bindings["i"] = "inventory"
        
        if self.talent_panel:
            self.panels["talent"] = self.talent_panel
            self.key_bindings["t"] = "talent"
        
        if self.party_panel:
            self.panels["party"] = self.party_panel
            self.key_bindings["p"] = "party"
        
        if self.upgrade_panel:
            self.panels["upgrade"] = self.upgrade_panel
            self.key_bindings["u"] = "upgrade"
    
    def update_character_data(self, character):
        """
        Update character-related panels with character data.
        
        Args:
            character: Character/unit object
        """
        # Update character panel
        if self.character_panel:
            self.character_panel.set_character(character)
    
    def show_panel(self, name: str):
        """
        Show specific panel (hides others if exclusive).
        
        Args:
            name: Panel name to show
        """
        if name not in self.panels:
            return
        
        # Hide current active panel
        if self.active_panel and self.active_panel != name:
            self.panels[self.active_panel].hide()
        
        # Show requested panel
        self.panels[name].show()
        self.active_panel = name
    
    def hide_panel(self, name: str):
        """
        Hide specific panel.
        
        Args:
            name: Panel name to hide
        """
        if name in self.panels:
            self.panels[name].hide()
            if self.active_panel == name:
                self.active_panel = None
    
    def toggle_panel(self, name: str):
        """
        Toggle specific panel visibility.
        
        Args:
            name: Panel name to toggle
        """
        if name not in self.panels:
            return
            
        if self.panels[name].is_visible():
            self.hide_panel(name)
        else:
            self.show_panel(name)
    
    def handle_key_input(self, key: str) -> bool:
        """
        Handle keyboard input for panel toggles.
        
        Args:
            key: Pressed key
            
        Returns:
            True if key was handled, False otherwise
        """
        if key in self.key_bindings:
            panel_name = self.key_bindings[key]
            self.toggle_panel(panel_name)
            return True
        return False
    
    def hide_all_panels(self):
        """Hide all panels."""
        for panel in self.panels.values():
            if panel:
                panel.hide()
        self.active_panel = None
    
    def get_panel_info(self) -> str:
        """
        Get information about available panels and their shortcuts.
        
        Returns:
            Formatted string with panel information
        """
        info_lines = [
            "Available UI Panels:",
            "  [C] Character - Stats and information",
            "  [I] Inventory - Party items and equipment",
            "  [T] Talent - Ability trees and progression",
            "  [P] Party - Team composition and management",
            "  [U] Upgrade - Item tier progression system",
            "",
            "Press the corresponding key to toggle each panel."
        ]
        return "\n".join(info_lines)
    
    def handle_game_input(self, key: str) -> bool:
        """
        Handle keyboard input for game panels.
        
        Args:
            key: Pressed key
            
        Returns:
            True if key was handled by panels, False otherwise
        """
        # Handle the key input
        handled = self.handle_key_input(key)
        
        if handled:
            # Print panel status for debugging
            if key in ['c', 'i', 't', 'p', 'u']:
                panel_name = self.key_bindings.get(key, "unknown")
                if panel_name in self.panels:
                    is_visible = self.panels[panel_name].is_visible()
                    status = "shown" if is_visible else "hidden"
                    print(f"Panel '{panel_name}' {status}")
        
        return handled
    
    def cleanup(self):
        """Clean up all panels and resources."""
        print("🧹 Cleaning up game panels...")
        
        # Clean up individual panels
        for panel in self.panels.values():
            if panel and hasattr(panel, 'cleanup'):
                try:
                    panel.cleanup()
                except Exception as e:
                    print(f"⚠️ Error cleaning up panel: {e}")
        
        self.panels.clear()
        self.key_bindings.clear()
        self.active_panel = None
        
        print("✅ Game panel cleanup complete")


def create_game_panels(game_reference: Optional[Any] = None) -> GamePanelManager:
    """
    Factory function to create game panel manager.
    
    Args:
        game_reference: Reference to main game object
        
    Returns:
        Configured GamePanelManager instance
    """
    try:
        panel_manager = GamePanelManager(game_reference)
        print(f"🎮 Game panels initialized successfully")
        print(panel_manager.get_panel_info())
        return panel_manager
        
    except Exception as e:
        print(f"❌ Failed to create game panels: {e}")
        # Return minimal manager
        return GamePanelManager()
