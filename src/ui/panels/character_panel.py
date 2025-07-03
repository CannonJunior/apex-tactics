"""
Character Panel Implementation

Displays character stats, equipment slots, and paper doll visualization.
Toggleable with 'c' key, shows selected unit's complete information.
"""

from typing import Optional, Dict, Any, List

try:
    from ursina import Text, Button, color, Entity, camera, Tooltip, destroy
    from ursina.prefabs.window_panel import WindowPanel
    from ursina.models.procedural.quad import Quad
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

# Import character state management
try:
    from game.state.character_state_manager import CharacterStateManager, CharacterInstance
    CHARACTER_STATE_AVAILABLE = True
except ImportError:
    CHARACTER_STATE_AVAILABLE = False
    print("Warning: Character state management not available")

# Config manager import removed - hotkey functionality moved to TacticalRPG controller


class CharacterPanel:
    """
    Character information panel showing stats and character details.
    
    Features:
    - Character name, class, and level
    - Core attribute stats (STR, FOR, FIN, WIS, WON, WOR)
    - Attack and defense values
    - Equipment summary
    """
    
    def __init__(self, game_reference: Optional[Any] = None, character_state_manager: Optional[CharacterStateManager] = None):
        """Initialize character panel."""
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for CharacterPanel")
        
        self.game_reference = game_reference
        self.character_state_manager = character_state_manager
        self.current_character = None
        self.current_character_instance: Optional[CharacterInstance] = None
        
        # Note: Hotkey slots moved to TacticalRPG controller for better gameplay integration
        
        # Register as observer for character state changes
        if self.character_state_manager and CHARACTER_STATE_AVAILABLE:
            self.character_state_manager.add_observer(self.on_character_state_changed)
        
        # Create text elements
        self._create_text_elements()
        
        # Create additional text elements for character data
        self._create_character_data_elements()
        
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
    
    def _create_character_data_elements(self):
        """Create text elements for extended character data."""
        # Resources
        self.health_text = Text('HP: --/--')
        self.mana_text = Text('MP: --/--')
        self.experience_text = Text('EXP: --')
        
        # Equipment summary
        self.equipped_weapon_text = Text('Weapon: None')
        self.equipped_armor_text = Text('Armor: None')
        self.equipped_accessory_text = Text('Accessory: None')
        
        # Talents summary
        self.unlocked_talents_text = Text('Talents: --')
        
        # Abilities summary
        self.abilities_text = Text('Abilities: --')
    
    def _create_main_panel(self):
        """Create the main window panel with all content."""
        self.panel = WindowPanel(
            title='Character Information',
            content=(
                self.character_name_text,
                self.character_class_text,
                self.character_level_text,
                Text('--- RESOURCES ---'),
                self.health_text,
                self.mana_text,
                self.experience_text,
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
                self.spiritual_defense_text,
                Text('--- EQUIPMENT ---'),
                self.equipped_weapon_text,
                self.equipped_armor_text,
                self.equipped_accessory_text,
                Text('--- PROGRESSION ---'),
                self.unlocked_talents_text,
                self.abilities_text
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
        
        # Try to get character instance if character has instance ID
        if character and hasattr(character, 'character_instance_id') and self.character_state_manager:
            self.current_character_instance = self.character_state_manager.get_character_instance(
                character.character_instance_id
            )
        else:
            self.current_character_instance = None
        
        self.update_display()
    
    def set_character_instance(self, character_instance: Optional[CharacterInstance]):
        """
        Set the character instance to display directly.
        
        Args:
            character_instance: CharacterInstance to display, or None to clear
        """
        self.current_character_instance = character_instance
        self.current_character = None  # Clear legacy character reference
        self.update_display()
    
    def update_from_active_character(self):
        """Update panel with active character data from character state manager."""
        if self.character_state_manager:
            active_character = self.character_state_manager.get_active_character()
            self.set_character_instance(active_character)
    
    def on_character_state_changed(self, event_type: str, character_id: Optional[str], data: Any):
        """
        Handle character state change events.
        
        Args:
            event_type: Type of event ('character_updated', 'active_character_changed', etc.)
            character_id: ID of affected character
            data: Event data
        """
        if event_type == 'active_character_changed':
            # Active character changed, update display
            self.update_from_active_character()
        elif event_type == 'character_updated':
            # Character data updated, refresh if it's the current character
            if (self.current_character_instance and 
                character_id == self.current_character_instance.instance_id):
                self.update_display()
    
    def update_display(self):
        """Update all display elements with current character data."""
        if self.current_character_instance:
            # Use character instance data (preferred)
            self._update_character_instance_display()
        elif self.current_character:
            # Fall back to legacy character data
            self._update_legacy_character_display()
        else:
            # No character selected
            self._clear_display()
    
    # Hotkey slots functionality moved to TacticalRPG controller
    
    def _update_character_instance_display(self):
        """Update display using CharacterInstance data."""
        char_instance = self.current_character_instance
        
        # Update character info
        self.character_name_text.text = f"Name: {char_instance.get_display_name()}"
        self.character_class_text.text = f"Class: {char_instance.get_character_class()}"
        self.character_level_text.text = f"Level: {char_instance.level}"
        
        # Update resources
        effective_stats = char_instance.get_effective_stats()
        max_hp = effective_stats.get('base_health', 100)
        max_mp = effective_stats.get('base_mp', 10)
        
        self.health_text.text = f"HP: {char_instance.current_hp}/{max_hp}"
        self.mana_text.text = f"MP: {char_instance.current_mp}/{max_mp}"
        self.experience_text.text = f"EXP: {char_instance.experience}"
        
        # Update attributes with effective stats (including equipment bonuses)
        self.strength_text.text = f"STR: {effective_stats.get('strength', 10)}"
        self.fortitude_text.text = f"FOR: {effective_stats.get('fortitude', 10)}"
        self.finesse_text.text = f"FIN: {effective_stats.get('finesse', 10)}"
        self.wisdom_text.text = f"WIS: {effective_stats.get('wisdom', 10)}"
        self.wonder_text.text = f"WON: {effective_stats.get('wonder', 10)}"
        self.worthy_text.text = f"WOR: {effective_stats.get('worthy', 10)}"
        
        # Update combat stats (calculated from effective stats)
        phys_attack = effective_stats.get('strength', 10) + effective_stats.get('finesse', 10)
        mag_attack = effective_stats.get('wisdom', 10) + effective_stats.get('wonder', 10)
        spir_attack = effective_stats.get('faith', 10) + effective_stats.get('spirit', 10)
        
        phys_defense = effective_stats.get('fortitude', 10)
        mag_defense = effective_stats.get('wisdom', 10) 
        spir_defense = effective_stats.get('worthy', 10)
        
        self.physical_attack_text.text = f"Physical ATK: {phys_attack}"
        self.magical_attack_text.text = f"Magical ATK: {mag_attack}"
        self.spiritual_attack_text.text = f"Spiritual ATK: {spir_attack}"
        
        self.physical_defense_text.text = f"Physical DEF: {phys_defense}"
        self.magical_defense_text.text = f"Magical DEF: {mag_defense}"
        self.spiritual_defense_text.text = f"Spiritual DEF: {spir_defense}"
        
        # Update equipment
        equipped_items = char_instance.equipped_items
        weapon = equipped_items.get('weapon', {}).get('item_id', 'None')
        armor = equipped_items.get('body', {}).get('item_id', 'None') 
        accessory = equipped_items.get('accessory', {}).get('item_id', 'None')
        
        self.equipped_weapon_text.text = f"Weapon: {weapon}"
        self.equipped_armor_text.text = f"Armor: {armor}"
        self.equipped_accessory_text.text = f"Accessory: {accessory}"
        
        # Update talents
        unlocked_count = len(char_instance.unlocked_talents)
        total_talents = len(char_instance.template_data.get('talents', {}))
        self.unlocked_talents_text.text = f"Talents: {unlocked_count}/{total_talents}"
        
        # Update abilities
        available_abilities = char_instance.get_available_abilities()
        self.abilities_text.text = f"Abilities: {len(available_abilities)} available"
    
    def _update_legacy_character_display(self):
        """Update display using legacy character data (fallback)."""
        char = self.current_character
        
        # Update character info
        self.character_name_text.text = f"Name: {getattr(char, 'name', 'Unknown')}"
        self.character_class_text.text = f"Class: {self._calculate_character_class(char)}"
        self.character_level_text.text = f"Level: {getattr(char, 'level', 1)}"
        
        # Update resources
        self.health_text.text = f"HP: {getattr(char, 'hp', 0)}/{getattr(char, 'max_hp', 100)}"
        self.mana_text.text = f"MP: {getattr(char, 'mp', 0)}/{getattr(char, 'max_mp', 10)}"
        self.experience_text.text = f"EXP: {getattr(char, 'experience', 0)}"
        
        # Update stats
        self._update_stats_display(char)
        
        # Clear character-specific data (not available in legacy)
        self.equipped_weapon_text.text = "Weapon: Unknown"
        self.equipped_armor_text.text = "Armor: Unknown"
        self.equipped_accessory_text.text = "Accessory: Unknown"
        self.unlocked_talents_text.text = "Talents: Unknown"
        self.abilities_text.text = "Abilities: Unknown"
    
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
        
        # Clear resources
        self.health_text.text = "HP: --/--"
        self.mana_text.text = "MP: --/--"
        self.experience_text.text = "EXP: --"
        
        # Clear stats
        for text_element in [self.strength_text, self.fortitude_text, self.finesse_text,
                           self.wisdom_text, self.wonder_text, self.worthy_text,
                           self.physical_attack_text, self.magical_attack_text, self.spiritual_attack_text,
                           self.physical_defense_text, self.magical_defense_text, self.spiritual_defense_text]:
            if hasattr(text_element, 'text'):
                original_label = text_element.text.split(':')[0]
                text_element.text = f"{original_label}: --"
        
        # Clear character-specific data
        self.equipped_weapon_text.text = "Weapon: --"
        self.equipped_armor_text.text = "Armor: --"
        self.equipped_accessory_text.text = "Accessory: --"
        self.unlocked_talents_text.text = "Talents: --"
        self.abilities_text.text = "Abilities: --"
    
    def toggle_visibility(self):
        """Toggle the visibility of the character panel."""
        if hasattr(self, 'panel') and self.panel:
            is_visible = not self.panel.enabled
            self.panel.enabled = is_visible
            
            # Hotkey slots now managed by TacticalRPG controller
            
            status = "shown" if is_visible else "hidden"
            print(f"Character panel {status}")
    
    def show(self):
        """Show the character panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = True
            
            # Hotkey slots now managed by TacticalRPG controller
    
    def hide(self):
        """Hide the character panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = False
            
            # Hotkey slots now managed by TacticalRPG controller
    
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
    
    def set_character_state_manager(self, character_state_manager: CharacterStateManager):
        """
        Set the character state manager for this panel.
        
        Args:
            character_state_manager: CharacterStateManager instance
        """
        # Remove old observer if exists
        if self.character_state_manager and CHARACTER_STATE_AVAILABLE:
            self.character_state_manager.remove_observer(self.on_character_state_changed)
        
        # Set new manager and register observer
        self.character_state_manager = character_state_manager
        if CHARACTER_STATE_AVAILABLE:
            self.character_state_manager.add_observer(self.on_character_state_changed)
    
    def cleanup(self):
        """Clean up panel resources."""
        # Remove observer registration
        if self.character_state_manager and CHARACTER_STATE_AVAILABLE:
            self.character_state_manager.remove_observer(self.on_character_state_changed)
        
        # Hotkey slots now managed by TacticalRPG controller
        
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = False