"""
Talent Panel Implementation

Displays talent trees with physical, magical, and spiritual ability trees.
Shows available abilities for assignment in the selected unit.
Toggleable with 't' key.
"""

from typing import Optional, Dict, Any, List

try:
    from ursina import Text, Button, color
    from ursina.prefabs.window_panel import WindowPanel
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


class TalentPanel:
    """
    Talent tree panel showing abilities available for assignment.
    
    Features:
    - 3 tabs for physical, magical, and spiritual talents
    - Tree structure with low level abilities at top
    - Higher level abilities towards bottom
    - Ability assignment and progression tracking
    """
    
    def __init__(self, game_reference: Optional[Any] = None):
        """Initialize talent panel."""
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for TalentPanel")
        
        self.game_reference = game_reference
        self.current_character = None
        self.current_tab = "Physical"
        self.talent_trees: Dict[str, List[Dict[str, Any]]] = {}
        
        # Create text elements
        self._create_text_elements()
        
        # Create main panel
        self._create_main_panel()
        
        # Position panel
        self._position_panel()
        
        # Load sample talent data
        self._load_sample_talents()
        self._update_display()
    
    def _create_text_elements(self):
        """Create all text display elements."""
        self.talent_title_text = Text('Talent Trees')
        self.character_name_text = Text('Character: No Character Selected')
        self.current_tab_text = Text('Current Tab: Physical')
        self.available_points_text = Text('Available Points: 0')
        
        # Talent display lines (showing up to 12 talents)
        self.talent_texts = []
        for i in range(12):
            talent_text = Text(f'Talent {i+1}: Empty')
            self.talent_texts.append(talent_text)
        
        # Tab buttons simulation
        self.tab_info_text = Text('Tabs: Physical | Magical | Spiritual')
    
    def _create_main_panel(self):
        """Create the main window panel with all content."""
        content_list = [
            self.talent_title_text,
            self.character_name_text,
            self.current_tab_text,
            self.available_points_text,
            Text('--- TALENT TREE ---'),
        ]
        
        # Add talent display texts
        content_list.extend(self.talent_texts)
        
        # Add tab information
        content_list.append(Text('--- CONTROLS ---'))
        content_list.append(self.tab_info_text)
        
        self.panel = WindowPanel(
            title='Talent Trees',
            content=tuple(content_list),
            popup=False
        )
        # Start hidden
        self.panel.enabled = False
    
    def _position_panel(self):
        """Position the panel on the right side of the screen."""
        self.panel.x = 0.3
        self.panel.y = 0.0
        self.panel.layout()
    
    def _load_sample_talents(self):
        """Load sample talent data for testing."""
        self.talent_trees = {
            "Physical": [
                {"name": "Basic Strike", "level": 1, "tier": "Novice", "learned": True, "description": "Basic melee attack"},
                {"name": "Power Attack", "level": 2, "tier": "Novice", "learned": True, "description": "Stronger but slower attack"},
                {"name": "Weapon Mastery", "level": 3, "tier": "Adept", "learned": False, "description": "Increased weapon proficiency"},
                {"name": "Berserker Rage", "level": 4, "tier": "Adept", "learned": False, "description": "Temporary damage boost"},
                {"name": "Whirlwind", "level": 5, "tier": "Expert", "learned": False, "description": "Attack all adjacent enemies"},
                {"name": "Legendary Strike", "level": 6, "tier": "Master", "learned": False, "description": "Devastating single attack"},
            ],
            "Magical": [
                {"name": "Magic Missile", "level": 1, "tier": "Novice", "learned": True, "description": "Basic ranged spell"},
                {"name": "Heal", "level": 2, "tier": "Novice", "learned": True, "description": "Restore health points"},
                {"name": "Fireball", "level": 3, "tier": "Adept", "learned": False, "description": "Area damage spell"},
                {"name": "Lightning Bolt", "level": 4, "tier": "Adept", "learned": False, "description": "Chain lightning attack"},
                {"name": "Teleport", "level": 5, "tier": "Expert", "learned": False, "description": "Instant movement"},
                {"name": "Meteor", "level": 6, "tier": "Master", "learned": False, "description": "Massive area devastation"},
            ],
            "Spiritual": [
                {"name": "Inner Peace", "level": 1, "tier": "Novice", "learned": True, "description": "Restore mental energy"},
                {"name": "Blessing", "level": 2, "tier": "Novice", "learned": True, "description": "Temporary stat boost"},
                {"name": "Spirit Shield", "level": 3, "tier": "Adept", "learned": False, "description": "Magical damage protection"},
                {"name": "Commune", "level": 4, "tier": "Adept", "learned": False, "description": "Communicate with spirits"},
                {"name": "Astral Projection", "level": 5, "tier": "Expert", "learned": False, "description": "Scout distant locations"},
                {"name": "Divine Intervention", "level": 6, "tier": "Master", "learned": False, "description": "Ultimate protection"},
            ],
        }
    
    def _update_display(self):
        """Update all display elements with current talent data."""
        # Update character and tab information
        char_name = self.current_character.name if self.current_character else "No Character Selected"
        self.character_name_text.text = f'Character: {char_name}'
        self.current_tab_text.text = f'Current Tab: {self.current_tab}'
        
        # Update available points (sample data)
        available_points = 3 if self.current_character else 0
        self.available_points_text.text = f'Available Points: {available_points}'
        
        # Get current tab talents
        current_talents = self.talent_trees.get(self.current_tab, [])
        
        # Update talent display (show up to 12 talents)
        for i, talent_text in enumerate(self.talent_texts):
            if i < len(current_talents):
                talent = current_talents[i]
                status = "✓" if talent['learned'] else "○"
                talent_text.text = f"{status} Lv{talent['level']} {talent['name']} ({talent['tier']})"
            else:
                talent_text.text = f'Talent {i+1}: Empty'
    
    def switch_tab(self, tab_name: str):
        """Switch to different talent tree tab."""
        valid_tabs = ["Physical", "Magical", "Spiritual"]
        if tab_name in valid_tabs:
            self.current_tab = tab_name
            self._update_display()
    
    def set_character(self, character):
        """
        Set the character to display talents for.
        
        Args:
            character: Character object to display, or None to clear
        """
        self.current_character = character
        self._update_display()
    
    def learn_talent(self, talent_name: str, tab: str = None) -> bool:
        """
        Learn a talent for the current character.
        
        Args:
            talent_name: Name of talent to learn
            tab: Talent tree tab (defaults to current tab)
            
        Returns:
            True if talent was learned successfully
        """
        if not self.current_character:
            return False
        
        tab = tab or self.current_tab
        if tab not in self.talent_trees:
            return False
        
        # Find talent
        for talent in self.talent_trees[tab]:
            if talent['name'] == talent_name and not talent['learned']:
                talent['learned'] = True
                self._update_display()
                print(f"{self.current_character.name} learned {talent_name}!")
                return True
        
        return False
    
    def get_learned_talents(self, tab: str = None) -> List[Dict[str, Any]]:
        """
        Get all learned talents for current character.
        
        Args:
            tab: Specific tab to check (defaults to all tabs)
            
        Returns:
            List of learned talent dictionaries
        """
        if not self.current_character:
            return []
        
        learned = []
        tabs_to_check = [tab] if tab else self.talent_trees.keys()
        
        for tab_name in tabs_to_check:
            if tab_name in self.talent_trees:
                for talent in self.talent_trees[tab_name]:
                    if talent['learned']:
                        learned.append(talent)
        
        return learned
    
    def get_available_talents(self, tab: str = None) -> List[Dict[str, Any]]:
        """
        Get talents available to learn for current character.
        
        Args:
            tab: Specific tab to check (defaults to current tab)
            
        Returns:
            List of available talent dictionaries
        """
        if not self.current_character:
            return []
        
        tab = tab or self.current_tab
        if tab not in self.talent_trees:
            return []
        
        available = []
        for talent in self.talent_trees[tab]:
            if not talent['learned']:
                # Check if prerequisites are met (simplified)
                if talent['level'] <= 3:  # Assume levels 1-3 are always available
                    available.append(talent)
                # Could add more complex prerequisite checking here
        
        return available
    
    def toggle_visibility(self):
        """Toggle the visibility of the talent panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = not self.panel.enabled
            status = "shown" if self.panel.enabled else "hidden"
            print(f"Talent panel {status}")
    
    def show(self):
        """Show the talent panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = True
    
    def hide(self):
        """Hide the talent panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = False
    
    def is_visible(self) -> bool:
        """Check if the talent panel is currently visible."""
        if hasattr(self, 'panel') and self.panel:
            return self.panel.enabled
        return False
    
    def update_content(self, data: Dict[str, Any]):
        """
        Update panel content with new data.
        
        Args:
            data: Dictionary with character and talent data
        """
        if 'character' in data:
            self.set_character(data['character'])
        
        if 'talents' in data:
            self.talent_trees = data['talents']
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