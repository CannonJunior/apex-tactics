"""
Character Panel Implementation

Displays character stats, equipment slots, and paper doll visualization.
Toggleable with 'c' key, shows selected unit's complete information.
"""

from typing import Optional, Dict, Any, List

try:
    from ursina import Text, Button, color
    from ursina.prefabs.window_panel import WindowPanel
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


class CharacterPanel:
    """
    Character information panel showing stats and character details.
    
    Features:
    - Character name, class, and level
    - Core attribute stats (STR, FOR, FIN, WIS, WON, WOR)
    - Attack and defense values
    - Equipment summary
    """
    
    def __init__(self, game_reference: Optional[Any] = None):
        """Initialize character panel."""
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for CharacterPanel")
        
        self.game_reference = game_reference
        self.current_character = None
        
        # Create text elements
        self._create_text_elements()
        
        # Create main panel
        self._create_main_panel()
        
        # Position panel
        self._position_panel()
    
    def _create_text_elements(self):
        """Create all text display elements."""
        self.character_name_text = Text('No Character Selected')
        self.character_class_text = Text('Class: Unknown')
        self.character_level_text = Text('Level: --')
        
        # Core stats
        self.strength_text = Text('STR: --')
        self.fortitude_text = Text('FOR: --')
        self.finesse_text = Text('FIN: --')
        self.wisdom_text = Text('WIS: --')
        self.wonder_text = Text('WON: --')
        self.worthy_text = Text('WOR: --')
        
        # Combat stats
        self.physical_attack_text = Text('Physical ATK: --')
        self.magical_attack_text = Text('Magical ATK: --')
        self.spiritual_attack_text = Text('Spiritual ATK: --')
        self.physical_defense_text = Text('Physical DEF: --')
        self.magical_defense_text = Text('Magical DEF: --')
        self.spiritual_defense_text = Text('Spiritual DEF: --')
    
    def _create_main_panel(self):
        """Create the main window panel with all content."""
        self.panel = WindowPanel(
            title='Character Information',
            content=(
                self.character_name_text,
                self.character_class_text,
                self.character_level_text,
                Text('--- ATTRIBUTES ---'),
                self.strength_text,
                self.fortitude_text,
                self.finesse_text,
                self.wisdom_text,
                self.wonder_text,
                self.worthy_text,
                Text('--- COMBAT ---'),
                self.physical_attack_text,
                self.magical_attack_text,
                self.spiritual_attack_text,
                self.physical_defense_text,
                self.magical_defense_text,
                self.spiritual_defense_text
            ),
            popup=False
        )
        # Start hidden
        self.panel.enabled = False
    
    def _position_panel(self):
        """Position the panel on the right side of the screen."""
        self.panel.x = 0.5
        self.panel.y = 0.0
        self.panel.layout()
    
    def set_character(self, character):
        """
        Set the character to display.
        
        Args:
            character: Character object to display, or None to clear
        """
        self.current_character = character
        self.update_display()
    
    def update_display(self):
        """Update all display elements with current character data."""
        if not self.current_character:
            self._clear_display()
            return
        
        char = self.current_character
        
        # Update character info
        self.character_name_text.text = f"Name: {getattr(char, 'name', 'Unknown')}"
        self.character_class_text.text = f"Class: {self._calculate_character_class(char)}"
        self.character_level_text.text = f"Level: {getattr(char, 'level', 1)}"
        
        # Update stats
        self._update_stats_display(char)
    
    def _update_stats_display(self, character):
        """Update stats section with character data."""
        # Core attributes
        if hasattr(character, 'stats') and hasattr(character.stats, 'attributes'):
            attrs = character.stats.attributes
            self.strength_text.text = f"STR: {attrs.strength}"
            self.fortitude_text.text = f"FOR: {attrs.fortitude}"
            self.finesse_text.text = f"FIN: {attrs.finesse}"
            self.wisdom_text.text = f"WIS: {attrs.wisdom}"
            self.wonder_text.text = f"WON: {attrs.wonder}"
            self.worthy_text.text = f"WOR: {attrs.worthy}"
        else:
            # Fallback for legacy character objects
            self.strength_text.text = f"STR: {getattr(character, 'strength', 10)}"
            self.fortitude_text.text = f"FOR: {getattr(character, 'fortitude', 10)}"
            self.finesse_text.text = f"FIN: {getattr(character, 'finesse', 10)}"
            self.wisdom_text.text = f"WIS: {getattr(character, 'wisdom', 10)}"
            self.wonder_text.text = f"WON: {getattr(character, 'wonder', 10)}"
            self.worthy_text.text = f"WOR: {getattr(character, 'worthy', 10)}"
        
        # Combat stats
        self.physical_attack_text.text = f"Physical ATK: {getattr(character, 'physical_attack', 0)}"
        self.magical_attack_text.text = f"Magical ATK: {getattr(character, 'magical_attack', 0)}"
        self.spiritual_attack_text.text = f"Spiritual ATK: {getattr(character, 'spiritual_attack', 0)}"
        
        self.physical_defense_text.text = f"Physical DEF: {getattr(character, 'physical_defense', 0)}"
        self.magical_defense_text.text = f"Magical DEF: {getattr(character, 'magical_defense', 0)}"
        self.spiritual_defense_text.text = f"Spiritual DEF: {getattr(character, 'spiritual_defense', 0)}"
    
    def _calculate_character_class(self, character) -> str:
        """Calculate character class based on stats and abilities."""
        # Simplified class calculation
        if not hasattr(character, 'stats') or not hasattr(character.stats, 'attributes'):
            return "Warrior"  # Default
        
        attrs = character.stats.attributes
        
        # Find highest stat
        stat_values = {
            'strength': attrs.strength,
            'finesse': attrs.finesse,
            'wisdom': attrs.wisdom,
            'wonder': attrs.wonder,
            'worthy': attrs.worthy,
            'fortitude': attrs.fortitude
        }
        
        highest_stat = max(stat_values, key=stat_values.get)
        
        # Map stats to classes
        class_mapping = {
            'strength': 'Warrior',
            'finesse': 'Rogue',
            'wisdom': 'Mage',
            'wonder': 'Sorcerer',
            'worthy': 'Paladin',
            'fortitude': 'Guardian'
        }
        
        return class_mapping.get(highest_stat, 'Adventurer')
    
    def _clear_display(self):
        """Clear all character information."""
        self.character_name_text.text = "Name: No Character Selected"
        self.character_class_text.text = "Class: Unknown"
        self.character_level_text.text = "Level: --"
        
        # Clear stats
        for text_element in [self.strength_text, self.fortitude_text, self.finesse_text,
                           self.wisdom_text, self.wonder_text, self.worthy_text,
                           self.physical_attack_text, self.magical_attack_text, self.spiritual_attack_text,
                           self.physical_defense_text, self.magical_defense_text, self.spiritual_defense_text]:
            if hasattr(text_element, 'text'):
                original_label = text_element.text.split(':')[0]
                text_element.text = f"{original_label}: --"
    
    def toggle_visibility(self):
        """Toggle the visibility of the character panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = not self.panel.enabled
            status = "shown" if self.panel.enabled else "hidden"
            print(f"Character panel {status}")
    
    def show(self):
        """Show the character panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = True
    
    def hide(self):
        """Hide the character panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = False
    
    def is_visible(self) -> bool:
        """Check if the character panel is currently visible."""
        if hasattr(self, 'panel') and self.panel:
            return self.panel.enabled
        return False
    
    def update_content(self, data: Dict[str, Any]):
        """
        Update panel content with new data.
        
        Args:
            data: Dictionary with 'character' key containing character data
        """
        if 'character' in data:
            self.set_character(data['character'])
    
    def set_game_reference(self, game: Any):
        """
        Set reference to the main game object.
        
        Args:
            game: Main game object
        """
        self.game_reference = game
    
    def cleanup(self):
        """Clean up panel resources."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = False