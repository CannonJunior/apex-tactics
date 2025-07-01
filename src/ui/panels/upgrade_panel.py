"""
Upgrade Panel Implementation

Displays item upgrade system for improving equipment through tier progression.
From Base → Enhanced → Enchanted → Superpowered → Metapowered.
Toggleable with 'u' key.
"""

from typing import Optional, Dict, Any, List

try:
    from ursina import Text, Button, color
    from ursina.prefabs.window_panel import WindowPanel
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


class UpgradePanel:
    """
    Item upgrade panel for improving equipment tiers.
    
    Features:
    - Item tier progression (Base to Metapowered)
    - Upgrade material requirements
    - Character selection for item destruction/recovery
    - Risk assessment for sentient item destruction
    """
    
    def __init__(self, game_reference: Optional[Any] = None):
        """Initialize upgrade panel."""
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for UpgradePanel")
        
        self.game_reference = game_reference
        self.selected_item = None
        self.selected_character = None
        self.upgrade_materials: List[Dict[str, Any]] = []
        self.tier_progression = ["BASE", "ENHANCED", "ENCHANTED", "SUPERPOWERED", "METAPOWERED"]
        
        # Create text elements
        self._create_text_elements()
        
        # Create main panel
        self._create_main_panel()
        
        # Position panel
        self._position_panel()
        
        # Load sample upgrade data
        self._load_sample_data()
        self._update_display()
    
    def _create_text_elements(self):
        """Create all text display elements."""
        self.upgrade_title_text = Text('Item Upgrade System')
        self.selected_item_text = Text('Selected Item: None')
        self.current_tier_text = Text('Current Tier: --')
        self.next_tier_text = Text('Next Tier: --')
        self.upgrade_cost_text = Text('Upgrade Cost: --')
        
        # Available upgrade items
        self.upgradeable_items_text = Text('Upgradeable Items:')
        self.item_list_texts = []
        for i in range(8):
            item_text = Text(f'Item {i+1}: Empty')
            self.item_list_texts.append(item_text)
        
        # Materials section
        self.materials_title_text = Text('Upgrade Materials:')
        self.material_texts = []
        for i in range(6):
            material_text = Text(f'Material {i+1}: Empty')
            self.material_texts.append(material_text)
        
        # Character selection for destruction
        self.destruction_title_text = Text('Item Destruction & Recovery:')
        self.selected_character_text = Text('Selected Character: None')
        self.destruction_warning_text = Text('Warning: Sentient items may fight back!')
        
        # Controls
        self.controls_text = Text('Controls: ↑↓ Select Item | Enter Upgrade | D Destroy | C Select Character')
    
    def _create_main_panel(self):
        """Create the main window panel with all content."""
        content_list = [
            self.upgrade_title_text,
            Text('--- SELECTED ITEM ---'),
            self.selected_item_text,
            self.current_tier_text,
            self.next_tier_text,
            self.upgrade_cost_text,
            Text('--- UPGRADEABLE ITEMS ---'),
            self.upgradeable_items_text,
        ]
        
        # Add item list
        content_list.extend(self.item_list_texts)
        
        # Add materials section
        content_list.extend([
            Text('--- UPGRADE MATERIALS ---'),
            self.materials_title_text,
        ])
        content_list.extend(self.material_texts)
        
        # Add destruction section
        content_list.extend([
            Text('--- DESTRUCTION & RECOVERY ---'),
            self.destruction_title_text,
            self.selected_character_text,
            self.destruction_warning_text,
            Text('--- CONTROLS ---'),
            self.controls_text
        ])
        
        self.panel = WindowPanel(
            title='Item Upgrade System',
            content=tuple(content_list),
            popup=False
        )
        # Start hidden
        self.panel.enabled = False
    
    def _position_panel(self):
        """Position the panel on the center-right of the screen."""
        self.panel.x = 0.1
        self.panel.y = 0.0
        self.panel.layout()
    
    def _load_sample_data(self):
        """Load sample upgrade data for testing."""
        # Sample upgradeable items
        self.upgradeable_items = [
            {
                "name": "Iron Sword",
                "tier": "BASE",
                "type": "Weapon",
                "is_sentient": False,
                "upgrade_materials": ["Iron Ore", "Coal"],
                "upgrade_cost": 100
            },
            {
                "name": "Steel Axe",
                "tier": "ENHANCED",
                "type": "Weapon",
                "is_sentient": False,
                "upgrade_materials": ["Magic Crystal", "Enchanted Steel"],
                "upgrade_cost": 250
            },
            {
                "name": "Flame Blade",
                "tier": "ENCHANTED",
                "type": "Weapon",
                "is_sentient": True,
                "upgrade_materials": ["Phoenix Feather", "Elemental Core"],
                "upgrade_cost": 500
            },
            {
                "name": "Leather Armor",
                "tier": "BASE",
                "type": "Armor",
                "is_sentient": False,
                "upgrade_materials": ["Tough Hide", "Thread"],
                "upgrade_cost": 75
            },
            {
                "name": "Chain Mail",
                "tier": "ENHANCED",
                "type": "Armor",
                "is_sentient": False,
                "upgrade_materials": ["Mithril Links", "Reinforcement Runes"],
                "upgrade_cost": 200
            },
            {
                "name": "Dragon Scale Armor",
                "tier": "ENCHANTED",
                "type": "Armor",
                "is_sentient": True,
                "upgrade_materials": ["Ancient Dragon Scale", "Cosmic Essence"],
                "upgrade_cost": 750
            }
        ]
        
        # Sample upgrade materials inventory
        self.upgrade_materials = [
            {"name": "Iron Ore", "quantity": 15, "tier": "BASE"},
            {"name": "Coal", "quantity": 20, "tier": "BASE"},
            {"name": "Magic Crystal", "quantity": 8, "tier": "ENHANCED"},
            {"name": "Enchanted Steel", "quantity": 5, "tier": "ENHANCED"},
            {"name": "Phoenix Feather", "quantity": 2, "tier": "ENCHANTED"},
            {"name": "Elemental Core", "quantity": 1, "tier": "ENCHANTED"},
            {"name": "Tough Hide", "quantity": 12, "tier": "BASE"},
            {"name": "Thread", "quantity": 25, "tier": "BASE"},
            {"name": "Mithril Links", "quantity": 6, "tier": "ENHANCED"},
            {"name": "Reinforcement Runes", "quantity": 4, "tier": "ENHANCED"},
            {"name": "Ancient Dragon Scale", "quantity": 1, "tier": "ENCHANTED"},
            {"name": "Cosmic Essence", "quantity": 1, "tier": "SUPERPOWERED"}
        ]
        
        # Sample characters for destruction tasks
        self.available_characters = [
            {"name": "Hero", "level": 5, "destruction_skill": 75},
            {"name": "Sage", "level": 4, "destruction_skill": 45},
            {"name": "Rogue", "level": 3, "destruction_skill": 85},
            {"name": "Cleric", "level": 4, "destruction_skill": 30}
        ]
        
        # Default selections
        if self.upgradeable_items:
            self.selected_item = self.upgradeable_items[0]
        if self.available_characters:
            self.selected_character = self.available_characters[0]
    
    def _update_display(self):
        """Update all display elements with current data."""
        # Update selected item info
        if self.selected_item:
            self.selected_item_text.text = f'Selected Item: {self.selected_item["name"]}'
            self.current_tier_text.text = f'Current Tier: {self.selected_item["tier"]}'
            
            # Calculate next tier
            current_tier_index = self.tier_progression.index(self.selected_item["tier"])
            if current_tier_index < len(self.tier_progression) - 1:
                next_tier = self.tier_progression[current_tier_index + 1]
                self.next_tier_text.text = f'Next Tier: {next_tier}'
                self.upgrade_cost_text.text = f'Upgrade Cost: {self.selected_item["upgrade_cost"]} gold'
            else:
                self.next_tier_text.text = 'Next Tier: MAX TIER'
                self.upgrade_cost_text.text = 'Upgrade Cost: Cannot upgrade further'
        else:
            self.selected_item_text.text = 'Selected Item: None'
            self.current_tier_text.text = 'Current Tier: --'
            self.next_tier_text.text = 'Next Tier: --'
            self.upgrade_cost_text.text = 'Upgrade Cost: --'
        
        # Update upgradeable items list
        for i, item_text in enumerate(self.item_list_texts):
            if i < len(self.upgradeable_items):
                item = self.upgradeable_items[i]
                selected_indicator = "► " if item == self.selected_item else "  "
                sentient_indicator = " [SENTIENT]" if item["is_sentient"] else ""
                item_text.text = f'{selected_indicator}{item["name"]} ({item["tier"]}){sentient_indicator}'
            else:
                item_text.text = f'Item {i+1}: Empty'
        
        # Update materials list
        for i, material_text in enumerate(self.material_texts):
            if i < len(self.upgrade_materials):
                material = self.upgrade_materials[i]
                material_text.text = f'{material["name"]} x{material["quantity"]} ({material["tier"]})'
            else:
                material_text.text = f'Material {i+1}: Empty'
        
        # Update character selection
        if self.selected_character:
            destruction_skill = self.selected_character["destruction_skill"]
            skill_rating = "Expert" if destruction_skill >= 80 else "Good" if destruction_skill >= 60 else "Average" if destruction_skill >= 40 else "Poor"
            self.selected_character_text.text = f'Selected Character: {self.selected_character["name"]} (Skill: {skill_rating})'
        else:
            self.selected_character_text.text = 'Selected Character: None'
    
    def select_item(self, direction: str):
        """Select different item for upgrade."""
        if not self.upgradeable_items:
            return
        
        current_index = self.upgradeable_items.index(self.selected_item) if self.selected_item else 0
        
        if direction == "up":
            new_index = (current_index - 1) % len(self.upgradeable_items)
        elif direction == "down":
            new_index = (current_index + 1) % len(self.upgradeable_items)
        else:
            return
        
        self.selected_item = self.upgradeable_items[new_index]
        self._update_display()
    
    def select_character(self, direction: str):
        """Select different character for destruction tasks."""
        if not self.available_characters:
            return
        
        current_index = self.available_characters.index(self.selected_character) if self.selected_character else 0
        
        if direction == "next":
            new_index = (current_index + 1) % len(self.available_characters)
        elif direction == "previous":
            new_index = (current_index - 1) % len(self.available_characters)
        else:
            return
        
        self.selected_character = self.available_characters[new_index]
        self._update_display()
    
    def attempt_upgrade(self) -> bool:
        """
        Attempt to upgrade the selected item.
        
        Returns:
            True if upgrade was successful
        """
        if not self.selected_item:
            print("No item selected for upgrade!")
            return False
        
        current_tier_index = self.tier_progression.index(self.selected_item["tier"])
        if current_tier_index >= len(self.tier_progression) - 1:
            print(f"{self.selected_item['name']} is already at maximum tier!")
            return False
        
        # Check if player has required materials
        required_materials = self.selected_item["upgrade_materials"]
        available_materials = {mat["name"]: mat["quantity"] for mat in self.upgrade_materials}
        
        for material in required_materials:
            if material not in available_materials or available_materials[material] < 1:
                print(f"Insufficient materials: Need {material}")
                return False
        
        # Consume materials and upgrade item
        for material in required_materials:
            for mat in self.upgrade_materials:
                if mat["name"] == material:
                    mat["quantity"] -= 1
                    break
        
        # Upgrade the item
        next_tier = self.tier_progression[current_tier_index + 1]
        self.selected_item["tier"] = next_tier
        self.selected_item["upgrade_cost"] = int(self.selected_item["upgrade_cost"] * 2.5)  # Increase cost for next upgrade
        
        # Update required materials for next tier
        if next_tier == "ENHANCED":
            self.selected_item["upgrade_materials"] = ["Magic Crystal", "Reinforcement Runes"]
        elif next_tier == "ENCHANTED":
            self.selected_item["upgrade_materials"] = ["Phoenix Feather", "Elemental Core"]
        elif next_tier == "SUPERPOWERED":
            self.selected_item["upgrade_materials"] = ["Cosmic Essence", "Divine Fragment"]
        elif next_tier == "METAPOWERED":
            self.selected_item["upgrade_materials"] = ["Reality Shard", "Omnipotent Catalyst"]
        
        self._update_display()
        print(f"{self.selected_item['name']} successfully upgraded to {next_tier} tier!")
        return True
    
    def attempt_destruction(self) -> bool:
        """
        Attempt to destroy selected item and recover upgrade materials.
        
        Returns:
            True if destruction was successful
        """
        if not self.selected_item or not self.selected_character:
            print("Need both item and character selected for destruction!")
            return False
        
        # Check if item is sentient
        if self.selected_item["is_sentient"]:
            print(f"Warning: {self.selected_item['name']} is sentient and may resist!")
            
            # Calculate success chance based on character skill
            destruction_skill = self.selected_character["destruction_skill"]
            success_chance = min(destruction_skill, 85)  # Max 85% chance for sentient items
            
            print(f"{self.selected_character['name']} has {success_chance}% chance of success")
            
            # Simulate destruction attempt (in real game, this would be more complex)
            import random
            if random.randint(1, 100) > success_chance:
                print(f"{self.selected_item['name']} fights back! Starting combat...")
                # In a real implementation, this would trigger a 1v1 battle
                return False
        
        # Successful destruction - recover some materials
        print(f"{self.selected_item['name']} successfully destroyed!")
        
        # Add recovered materials back to inventory
        recovered_materials = self.selected_item["upgrade_materials"]
        for material_name in recovered_materials:
            # Find material in inventory and add some back
            for mat in self.upgrade_materials:
                if mat["name"] == material_name:
                    recovered_amount = 1 if not self.selected_item["is_sentient"] else 2
                    mat["quantity"] += recovered_amount
                    print(f"Recovered {recovered_amount}x {material_name}")
                    break
        
        # Remove item from upgradeable items
        self.upgradeable_items.remove(self.selected_item)
        
        # Select new item if available
        if self.upgradeable_items:
            self.selected_item = self.upgradeable_items[0]
        else:
            self.selected_item = None
        
        self._update_display()
        return True
    
    def get_upgrade_requirements(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get upgrade requirements for an item.
        
        Args:
            item: Item dictionary
            
        Returns:
            Dictionary with upgrade requirements
        """
        if not item:
            return {}
        
        current_tier_index = self.tier_progression.index(item["tier"])
        if current_tier_index >= len(self.tier_progression) - 1:
            return {"can_upgrade": False, "reason": "Max tier reached"}
        
        next_tier = self.tier_progression[current_tier_index + 1]
        required_materials = item["upgrade_materials"]
        available_materials = {mat["name"]: mat["quantity"] for mat in self.upgrade_materials}
        
        missing_materials = []
        for material in required_materials:
            if material not in available_materials or available_materials[material] < 1:
                missing_materials.append(material)
        
        return {
            "can_upgrade": len(missing_materials) == 0,
            "next_tier": next_tier,
            "required_materials": required_materials,
            "missing_materials": missing_materials,
            "cost": item["upgrade_cost"]
        }
    
    def add_upgrade_material(self, material_name: str, quantity: int = 1):
        """Add upgrade material to inventory."""
        for mat in self.upgrade_materials:
            if mat["name"] == material_name:
                mat["quantity"] += quantity
                self._update_display()
                return
        
        # Add new material if not found
        self.upgrade_materials.append({
            "name": material_name,
            "quantity": quantity,
            "tier": "BASE"  # Default tier
        })
        self._update_display()
    
    def toggle_visibility(self):
        """Toggle the visibility of the upgrade panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = not self.panel.enabled
            status = "shown" if self.panel.enabled else "hidden"
            print(f"Upgrade panel {status}")
    
    def show(self):
        """Show the upgrade panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = True
    
    def hide(self):
        """Hide the upgrade panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = False
    
    def is_visible(self) -> bool:
        """Check if the upgrade panel is currently visible."""
        if hasattr(self, 'panel') and self.panel:
            return self.panel.enabled
        return False
    
    def update_content(self, data: Dict[str, Any]):
        """
        Update panel content with new data.
        
        Args:
            data: Dictionary with upgrade system data
        """
        if 'upgradeable_items' in data:
            self.upgradeable_items = data['upgradeable_items']
            if self.upgradeable_items and not self.selected_item:
                self.selected_item = self.upgradeable_items[0]
        
        if 'upgrade_materials' in data:
            self.upgrade_materials = data['upgrade_materials']
        
        if 'available_characters' in data:
            self.available_characters = data['available_characters']
            if self.available_characters and not self.selected_character:
                self.selected_character = self.available_characters[0]
        
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