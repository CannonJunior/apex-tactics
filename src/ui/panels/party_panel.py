"""
Party Panel Implementation

Displays party management with 5 party slots and character carousel.
Shows aggregate party stats and individual character status.
Toggleable with 'p' key.
"""

from typing import Optional, Dict, Any, List

try:
    from ursina import Text, Button, color
    from ursina.prefabs.window_panel import WindowPanel
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


class PartyPanel:
    """
    Party management panel showing party composition and stats.
    
    Features:
    - 5 party slots for unit selection
    - Character carousel with all available units
    - Aggregate party stats (similar to character panel)
    - Individual unit status and power ratings
    """
    
    def __init__(self, game_reference: Optional[Any] = None):
        """Initialize party panel."""
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for PartyPanel")
        
        self.game_reference = game_reference
        self.party_members: List[Optional[Any]] = [None] * 5  # 5 party slots
        self.available_characters: List[Any] = []
        self.carousel_index = 0
        
        # Create text elements
        self._create_text_elements()
        
        # Create main panel
        self._create_main_panel()
        
        # Position panel
        self._position_panel()
        
        # Load sample party data
        self._load_sample_party()
        self._update_display()
    
    def _create_text_elements(self):
        """Create all text display elements."""
        self.party_title_text = Text('Party Management')
        
        # Aggregate party stats
        self.party_physical_attack_text = Text('Party Physical ATK: 0')
        self.party_magical_attack_text = Text('Party Magical ATK: 0')
        self.party_spiritual_attack_text = Text('Party Spiritual ATK: 0')
        self.party_physical_defense_text = Text('Party Physical DEF: 0')
        self.party_magical_defense_text = Text('Party Magical DEF: 0')
        self.party_spiritual_defense_text = Text('Party Spiritual DEF: 0')
        self.party_power_text = Text('Party Power: 0')
        
        # Party slot displays (5 slots)
        self.party_slot_texts = []
        for i in range(5):
            slot_text = Text(f'Slot {i+1}: Empty')
            self.party_slot_texts.append(slot_text)
        
        # Character carousel
        self.carousel_title_text = Text('Available Characters')
        self.carousel_info_text = Text('Character 1 of 0')
        self.current_character_text = Text('No Characters Available')
        self.character_status_text = Text('Status: Unknown')
        self.character_power_text = Text('Power: 0')
        
        # Controls
        self.controls_text = Text('Controls: ← → Navigate | Enter Add/Remove | Space Next Character')
    
    def _create_main_panel(self):
        """Create the main window panel with all content."""
        content_list = [
            self.party_title_text,
            Text('--- PARTY STATS ---'),
            self.party_physical_attack_text,
            self.party_magical_attack_text,
            self.party_spiritual_attack_text,
            self.party_physical_defense_text,
            self.party_magical_defense_text,
            self.party_spiritual_defense_text,
            self.party_power_text,
            Text('--- PARTY SLOTS ---'),
        ]
        
        # Add party slot displays
        content_list.extend(self.party_slot_texts)
        
        # Add character carousel section
        content_list.extend([
            Text('--- CHARACTER CAROUSEL ---'),
            self.carousel_title_text,
            self.carousel_info_text,
            self.current_character_text,
            self.character_status_text,
            self.character_power_text,
            Text('--- CONTROLS ---'),
            self.controls_text
        ])
        
        self.panel = WindowPanel(
            title='Party Management',
            content=tuple(content_list),
            popup=False
        )
        # Start hidden
        self.panel.enabled = False
    
    def _position_panel(self):
        """Position the panel on the left side of the screen."""
        self.panel.x = -0.3
        self.panel.y = 0.0
        self.panel.layout()
    
    def _load_sample_party(self):
        """Load sample party data for testing."""
        # Sample available characters
        self.available_characters = [
            {
                "name": "Hero",
                "class": "Warrior",
                "level": 5,
                "status": "Ready",
                "power": 45,
                "physical_attack": 25,
                "magical_attack": 5,
                "spiritual_attack": 10,
                "physical_defense": 20,
                "magical_defense": 8,
                "spiritual_defense": 12,
                "in_party": True
            },
            {
                "name": "Sage",
                "class": "Mage",
                "level": 4,
                "status": "Ready",
                "power": 38,
                "physical_attack": 8,
                "magical_attack": 30,
                "spiritual_attack": 15,
                "physical_defense": 10,
                "magical_defense": 25,
                "spiritual_defense": 20,
                "in_party": True
            },
            {
                "name": "Scout",
                "class": "Rogue",
                "level": 3,
                "status": "Injured",
                "power": 28,
                "physical_attack": 20,
                "magical_attack": 10,
                "spiritual_attack": 8,
                "physical_defense": 15,
                "magical_defense": 12,
                "spiritual_defense": 10,
                "in_party": False
            },
            {
                "name": "Cleric",
                "class": "Healer",
                "level": 4,
                "status": "Ready",
                "power": 35,
                "physical_attack": 12,
                "magical_attack": 18,
                "spiritual_attack": 28,
                "physical_defense": 12,
                "magical_defense": 20,
                "spiritual_defense": 25,
                "in_party": False
            },
            {
                "name": "Guardian",
                "class": "Tank",
                "level": 5,
                "status": "Resting",
                "power": 42,
                "physical_attack": 18,
                "magical_attack": 5,
                "spiritual_attack": 8,
                "physical_defense": 35,
                "magical_defense": 15,
                "spiritual_defense": 18,
                "in_party": False
            }
        ]
        
        # Set initial party (first 2 characters)
        party_chars = [char for char in self.available_characters if char['in_party']]
        for i, char in enumerate(party_chars[:5]):
            if i < len(self.party_members):
                self.party_members[i] = char
    
    def _update_display(self):
        """Update all display elements with current party data."""
        # Update party aggregate stats
        self._update_party_stats()
        
        # Update party slot displays
        for i, slot_text in enumerate(self.party_slot_texts):
            if i < len(self.party_members) and self.party_members[i]:
                char = self.party_members[i]
                status_icon = "✓" if char['status'] == "Ready" else "⚠" if char['status'] == "Injured" else "○"
                slot_text.text = f"Slot {i+1}: {char['name']} ({char['class']}) {status_icon} Pwr:{char['power']}"
            else:
                slot_text.text = f'Slot {i+1}: Empty'
        
        # Update character carousel
        if self.available_characters:
            self.carousel_info_text.text = f'Character {self.carousel_index + 1} of {len(self.available_characters)}'
            current_char = self.available_characters[self.carousel_index]
            
            party_status = " [IN PARTY]" if current_char['in_party'] else ""
            self.current_character_text.text = f"{current_char['name']} - {current_char['class']} Lv{current_char['level']}{party_status}"
            self.character_status_text.text = f"Status: {current_char['status']}"
            self.character_power_text.text = f"Power: {current_char['power']}"
        else:
            self.carousel_info_text.text = 'Character 0 of 0'
            self.current_character_text.text = 'No Characters Available'
            self.character_status_text.text = 'Status: Unknown'
            self.character_power_text.text = 'Power: 0'
    
    def _update_party_stats(self):
        """Calculate and update aggregate party statistics."""
        total_physical_attack = 0
        total_magical_attack = 0
        total_spiritual_attack = 0
        total_physical_defense = 0
        total_magical_defense = 0
        total_spiritual_defense = 0
        total_power = 0
        
        active_members = [member for member in self.party_members if member]
        
        for member in active_members:
            total_physical_attack += member.get('physical_attack', 0)
            total_magical_attack += member.get('magical_attack', 0)
            total_spiritual_attack += member.get('spiritual_attack', 0)
            total_physical_defense += member.get('physical_defense', 0)
            total_magical_defense += member.get('magical_defense', 0)
            total_spiritual_defense += member.get('spiritual_defense', 0)
            total_power += member.get('power', 0)
        
        # Update display texts
        self.party_physical_attack_text.text = f'Party Physical ATK: {total_physical_attack}'
        self.party_magical_attack_text.text = f'Party Magical ATK: {total_magical_attack}'
        self.party_spiritual_attack_text.text = f'Party Spiritual ATK: {total_spiritual_attack}'
        self.party_physical_defense_text.text = f'Party Physical DEF: {total_physical_defense}'
        self.party_magical_defense_text.text = f'Party Magical DEF: {total_magical_defense}'
        self.party_spiritual_defense_text.text = f'Party Spiritual DEF: {total_spiritual_defense}'
        self.party_power_text.text = f'Party Power: {total_power}'
    
    def navigate_carousel(self, direction: str):
        """Navigate the character carousel."""
        if not self.available_characters:
            return
        
        if direction == "next":
            self.carousel_index = (self.carousel_index + 1) % len(self.available_characters)
        elif direction == "previous":
            self.carousel_index = (self.carousel_index - 1) % len(self.available_characters)
        
        self._update_display()
    
    def add_character_to_party(self, character_index: int = None) -> bool:
        """
        Add character to party from carousel or by index.
        
        Args:
            character_index: Index of character to add (defaults to current carousel)
            
        Returns:
            True if character was added successfully
        """
        if character_index is None:
            character_index = self.carousel_index
        
        if character_index < 0 or character_index >= len(self.available_characters):
            return False
        
        character = self.available_characters[character_index]
        
        # Check if character is already in party
        if character['in_party']:
            print(f"{character['name']} is already in the party!")
            return False
        
        # Find empty party slot
        for i, slot in enumerate(self.party_members):
            if slot is None:
                self.party_members[i] = character
                character['in_party'] = True
                self._update_display()
                print(f"{character['name']} added to party slot {i+1}")
                return True
        
        print("Party is full! Remove a character first.")
        return False
    
    def remove_character_from_party(self, slot_index: int = None) -> bool:
        """
        Remove character from party slot.
        
        Args:
            slot_index: Party slot to clear (defaults to finding current carousel character)
            
        Returns:
            True if character was removed successfully
        """
        if slot_index is not None:
            # Remove by slot index
            if 0 <= slot_index < len(self.party_members) and self.party_members[slot_index]:
                character = self.party_members[slot_index]
                character['in_party'] = False
                self.party_members[slot_index] = None
                self._update_display()
                print(f"{character['name']} removed from party")
                return True
        else:
            # Remove current carousel character if in party
            if self.available_characters:
                current_char = self.available_characters[self.carousel_index]
                if current_char['in_party']:
                    # Find and remove from party
                    for i, member in enumerate(self.party_members):
                        if member and member['name'] == current_char['name']:
                            self.party_members[i] = None
                            current_char['in_party'] = False
                            self._update_display()
                            print(f"{current_char['name']} removed from party")
                            return True
        
        return False
    
    def toggle_character_party_status(self):
        """Toggle current carousel character in/out of party."""
        if not self.available_characters:
            return
        
        current_char = self.available_characters[self.carousel_index]
        
        if current_char['in_party']:
            self.remove_character_from_party()
        else:
            self.add_character_to_party()
    
    def get_party_members(self) -> List[Any]:
        """Get list of current party members (excluding None slots)."""
        return [member for member in self.party_members if member]
    
    def get_party_power(self) -> int:
        """Get total party power rating."""
        return sum(member.get('power', 0) for member in self.party_members if member)
    
    def set_available_characters(self, characters: List[Any]):
        """
        Set the list of available characters.
        
        Args:
            characters: List of character objects
        """
        self.available_characters = characters
        self.carousel_index = 0
        self._update_display()
    
    def toggle_visibility(self):
        """Toggle the visibility of the party panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = not self.panel.enabled
            status = "shown" if self.panel.enabled else "hidden"
            print(f"Party panel {status}")
    
    def show(self):
        """Show the party panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = True
    
    def hide(self):
        """Hide the party panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = False
    
    def is_visible(self) -> bool:
        """Check if the party panel is currently visible."""
        if hasattr(self, 'panel') and self.panel:
            return self.panel.enabled
        return False
    
    def update_content(self, data: Dict[str, Any]):
        """
        Update panel content with new data.
        
        Args:
            data: Dictionary with party and character data
        """
        if 'party' in data:
            # Update party composition
            party_data = data['party']
            for i, member_data in enumerate(party_data):
                if i < len(self.party_members):
                    self.party_members[i] = member_data
        
        if 'available_characters' in data:
            self.set_available_characters(data['available_characters'])
        
        self._update_display()
    
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