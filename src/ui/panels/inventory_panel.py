"""
Interactive Inventory Panel Implementation

Displays party inventory with drag-and-drop functionality for item management.
Features interactive item slots, equipped item tracking, and item categorization.
Toggleable with 'i' key.
"""

from typing import Optional, Dict, Any, List
import random

try:
    from ursina import Entity, Text, Button, color, camera, Draggable, Tooltip, destroy, held_keys, Vec3
    from ursina.prefabs.window_panel import WindowPanel
    from ursina.models.procedural.quad import Quad
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

# Import UI style manager for colors
try:
    from ...ui.core.ui_style_manager import get_ui_style_manager
    UI_STYLES_AVAILABLE = True
except ImportError:
    UI_STYLES_AVAILABLE = False

# Import asset management system
try:
    from ...core.assets.data_manager import get_data_manager, create_sample_inventory
    from ...core.assets.asset_loader import load_texture
    ASSETS_AVAILABLE = True
except ImportError:
    ASSETS_AVAILABLE = False
    print("⚠️ Asset system not available, using fallback data")


class InventoryItem(Draggable):
    """Interactive inventory item that can be dragged and dropped."""
    
    def __init__(self, item_data: Dict[str, Any], inventory_parent, **kwargs):
        self.item_data = item_data
        self.inventory_parent = inventory_parent
        self.is_equipped = item_data.get('equipped_by') is not None
        
        # Load item texture and color
        item_texture = self._load_item_texture()
        item_color = self._get_item_color()
        
        # Create draggable item
        super().__init__(
            parent=inventory_parent,
            model='quad',
            texture=item_texture,
            color=item_color,
            origin=(-.5, .5),
            z=-.1,
            **kwargs
        )
        
        # Create equipped highlight border if item is equipped
        self.equipped_border = None
        if self.is_equipped:
            self._create_equipped_border()
        
        # Create tooltip
        item_name = item_data.get('name', 'Unknown Item')
        tier = item_data.get('tier', 'BASE')
        equipped_info = f" (Equipped by {item_data['equipped_by']})" if self.is_equipped else ""
        quantity_info = f" x{item_data['quantity']}" if item_data.get('quantity', 1) > 1 else ""
        
        tooltip_text = f"{item_name} [{tier}]{quantity_info}{equipped_info}"
        self.tooltip = Tooltip(tooltip_text)
        self.tooltip.background.color = color.hsv(0, 0, 0, .8)
        
        # Store original position for drag operations
        self.org_pos = None
    
    def _load_item_texture(self):
        """Load the appropriate texture for this item."""
        if not ASSETS_AVAILABLE:
            return 'white_cube'  # Fallback texture
        
        # Try to load item-specific texture
        icon_path = self.item_data.get('icon', '')
        if icon_path:
            texture = load_texture(icon_path, fallback='white_cube')
            return texture
        
        # Fallback based on item type
        type_textures = {
            'Weapons': 'items/weapons/default_weapon.png',
            'Armor': 'items/armor/default_armor.png',
            'Accessories': 'items/accessories/default_accessory.png',
            'Consumables': 'items/consumables/default_potion.png',
            'Materials': 'items/materials/default_material.png'
        }
        
        item_type = self.item_data.get('type', 'Materials')
        fallback_path = type_textures.get(item_type, 'white_cube')
        
        return load_texture(fallback_path, fallback='white_cube')
    
    def _get_item_color(self):
        """Get the appropriate color for this item based on its type."""
        if not UI_STYLES_AVAILABLE:
            return color.white  # Fallback color
        
        style_manager = get_ui_style_manager()
        item_type = self.item_data.get('type', 'Materials')
        
        return style_manager.get_item_type_color(item_type)
    
    def _create_equipped_border(self):
        """Create a highlight border for equipped items."""
        if not UI_STYLES_AVAILABLE:
            return
        
        style_manager = get_ui_style_manager()
        border_color = style_manager.get_equipped_highlight_color()
        border_width = style_manager.get_equipped_highlight_width()
        
        # Create border as a larger entity behind the item
        self.equipped_border = Entity(
            parent=self,
            model='quad',
            color=border_color,
            scale=(1 + border_width * 2, 1 + border_width * 2),
            z=0.01,  # Behind the item
            origin=(-.5, .5)
        )
    
    def _remove_equipped_border(self):
        """Remove the equipped border."""
        if self.equipped_border:
            destroy(self.equipped_border)
            self.equipped_border = None
    
    def set_equipped_status(self, is_equipped: bool):
        """Update the equipped status and visual representation."""
        self.is_equipped = is_equipped
        
        if is_equipped and not self.equipped_border:
            self._create_equipped_border()
        elif not is_equipped and self.equipped_border:
            self._remove_equipped_border()
    
    def destroy(self):
        """Override destroy to clean up equipped border."""
        self._remove_equipped_border()
        super().destroy()
    
    def drag(self):
        """Called when item starts being dragged."""
        self.org_pos = (self.x, self.y)
        self.z -= .01  # Move item forward visually
        
        # Move equipped border with the item
        if self.equipped_border:
            self.equipped_border.z -= .01
        
        # Disable camera movement during drag
        self._set_camera_drag_state(True, "inventory item")
        
        print(f"Dragging {self.item_data['name']}")
    
    def drop(self):
        """Called when item is dropped."""
        self.x = round(self.x, 3)
        self.y = round(self.y, 3)
        self.z += .01  # Move item back
        
        # Move equipped border back with the item
        if self.equipped_border:
            self.equipped_border.z += .01
        
        # Re-enable camera movement after drag
        self._set_camera_drag_state(False, "inventory item")
        
        # Get inventory dimensions
        inv_width = self.inventory_parent.width
        inv_height = self.inventory_parent.height
        
        # Calculate grid position
        grid_x = int(self.x * self.inventory_parent.texture_scale[0])
        grid_y = int(self.y * self.inventory_parent.texture_scale[1])
        
        # Check if dropped within inventory bounds
        if 0 <= grid_x < inv_width and -inv_height < grid_y <= 0:
            # Snap to grid
            self.x = grid_x / self.inventory_parent.texture_scale[0]
            self.y = grid_y / self.inventory_parent.texture_scale[1]
            
            # Check for item swapping
            for child in self.inventory_parent.children:
                if child == self or not isinstance(child, InventoryItem):
                    continue
                if abs(child.x - self.x) < 0.01 and abs(child.y - self.y) < 0.01:
                    print(f'Swapping {self.item_data["name"]} with {child.item_data["name"]}')
                    child.position = self.org_pos
                    break
        else:
            # Return to original position if dropped outside bounds
            print(f"Item {self.item_data['name']} dropped outside inventory bounds")
            self.position = self.org_pos
    
    def _set_camera_drag_state(self, is_dragging: bool, source: str):
        """Set camera drag state through game reference."""
        try:
            # Path: InventoryItem → InteractiveInventory → InventoryPanel → game_reference
            
            # Try access through inventory_parent's panel_reference (InventoryPanel)
            if (hasattr(self.inventory_parent, 'panel_reference') and 
                hasattr(self.inventory_parent.panel_reference, 'game_reference') and
                hasattr(self.inventory_parent.panel_reference.game_reference, 'camera_controller')):
                camera_controller = self.inventory_parent.panel_reference.game_reference.camera_controller
                camera_controller.set_ui_dragging(is_dragging, source)
                return
                
            # Try through inventory_parent's game_reference directly
            elif (hasattr(self.inventory_parent, 'game_reference') and
                  hasattr(self.inventory_parent.game_reference, 'camera_controller')):
                camera_controller = self.inventory_parent.game_reference.camera_controller
                camera_controller.set_ui_dragging(is_dragging, source)
                return
                
            # Try through inventory_parent's parent (fallback for any other hierarchy)
            elif (hasattr(self.inventory_parent, 'parent') and 
                  hasattr(self.inventory_parent.parent, 'game_reference') and
                  hasattr(self.inventory_parent.parent.game_reference, 'camera_controller')):
                camera_controller = self.inventory_parent.parent.game_reference.camera_controller
                camera_controller.set_ui_dragging(is_dragging, source)
                return
                
            print(f"⚠️ Could not access camera controller for {source} drag state")
            print(f"   inventory_parent type: {type(self.inventory_parent)}")
            print(f"   panel_reference exists: {hasattr(self.inventory_parent, 'panel_reference')}")
            
        except Exception as e:
            print(f"⚠️ Error setting camera drag state: {e}")
            import traceback
            traceback.print_exc()


class InteractiveInventory(Entity):
    """Interactive inventory grid with drag-and-drop functionality."""
    
    def __init__(self, width=6, height=8, **kwargs):
        super().__init__(
            parent=camera.ui,
            model=Quad(radius=.015),
            texture='white_cube',
            texture_scale=(width, height),
            scale=(width*.08, height*.08),
            origin=(-.5, .5),
            position=(-.2, .2),
            color=color.hsv(0, 0, .1, .9),
            **kwargs
        )
        
        self.width = width
        self.height = height
        self.items: List[Dict[str, Any]] = []
    
    def find_free_spot(self):
        """Find the first available spot in the inventory grid using a simple counter approach."""
        # Count how many items we currently have
        current_item_count = len([c for c in self.children if isinstance(c, InventoryItem)])
        
        # Convert count to grid position (row-major order)
        if current_item_count >= self.width * self.height:
            return None  # Inventory full
        
        # Calculate grid position based on item count
        # Row-major order: items fill left to right, then top to bottom
        x = current_item_count % self.width
        y = current_item_count // self.width
        
        return x, y
    
    def add_item(self, item_data: Dict[str, Any], x=None, y=None):
        """Add an item to the inventory."""
        # Check if inventory is full
        current_items = len([c for c in self.children if isinstance(c, InventoryItem)])
        if current_items >= self.width * self.height:
            print('Inventory full!')
            return False
        
        # Find position for the item
        if x is None or y is None:
            free_spot = self.find_free_spot()
            if free_spot is None:
                print('No free spots available!')
                return False
            x, y = free_spot
        
        # Convert grid coordinates to normalized position within the inventory
        # Grid (0,0) is top-left, so y needs to be negated
        normalized_x = x / self.width
        normalized_y = -y / self.height
        
        # Create inventory item with proper scaling
        item = InventoryItem(
            item_data=item_data,
            inventory_parent=self,
            scale_x=1/self.width,
            scale_y=1/self.height,
            x=normalized_x,
            y=normalized_y,
        )
        
        self.items.append(item_data)
        print(f"Added {item_data['name']} to inventory at ({x}, {y})")
        return True
    
    def remove_item(self, item_name: str):
        """Remove an item from the inventory."""
        for child in self.children.copy():
            if isinstance(child, InventoryItem) and child.item_data['name'] == item_name:
                self.items = [item for item in self.items if item['name'] != item_name]
                destroy(child)
                print(f"Removed {item_name} from inventory")
                return True
        return False
    
    def get_items_by_type(self, item_type: str):
        """Get all items of a specific type."""
        if item_type == "All":
            return self.items
        return [item for item in self.items if item.get('type') == item_type]


class InventoryPanel:
    """
    Interactive inventory management panel with drag-and-drop functionality.
    
    Features:
    - Interactive drag-and-drop item management
    - Tabbed interface by item type
    - Visual feedback for equipped items
    - Item tooltips with detailed information
    - Grid-based inventory layout
    """
    
    def __init__(self, game_reference: Optional[Any] = None):
        """Initialize interactive inventory panel."""
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for InventoryPanel")
        
        self.game_reference = game_reference
        self.current_tab = "All"
        self._is_visible = False
        
        # Create interactive inventory
        self.interactive_inventory = None
        self.tab_buttons = []
        self.info_panel = None
        
        # Load sample data
        self._load_sample_data()
        
        # Create UI elements (but don't show them yet)
        self._create_ui_elements()
    
    def _create_ui_elements(self):
        """Create the UI elements for the inventory panel."""
        # Create interactive inventory grid
        self.interactive_inventory = InteractiveInventory(width=6, height=8)
        self.interactive_inventory.enabled = False
        
        # Set panel reference for camera controller access (not using Ursina parent)
        self.interactive_inventory.panel_reference = self
        
        # Create info panel for inventory stats
        self._create_info_panel()
        
        # Create tab buttons
        self._create_tab_buttons()
        
        # Create action buttons
        self._create_action_buttons()
        
        # Populate inventory with sample items
        self._populate_sample_items()
    
    def _create_info_panel(self):
        """Create information panel showing inventory stats."""
        info_text = [
            "Interactive Inventory",
            "Drag items to rearrange",
            "Equipped items have highlight border",
            f"Tab: {self.current_tab}",
            f"Items: {len(self.sample_items)}"
        ]
        
        self.info_panel = WindowPanel(
            title='Inventory Info',
            content=tuple(Text(line) for line in info_text),
            popup=False
        )
        self.info_panel.scale = (0.3, 0.4)
        self.info_panel.position = (0.3, 0.2)
        self.info_panel.enabled = False
    
    def _create_tab_buttons(self):
        """Create tab buttons for filtering items."""
        tabs = ["All", "Weapons", "Armor", "Accessories", "Consumables", "Materials"]
        
        for i, tab in enumerate(tabs):
            btn = Button(
                text=tab,
                color=color.azure if tab == self.current_tab else color.dark_gray,
                scale=(0.08, 0.03),
                position=(-0.4 + i * 0.09, 0.45),
                parent=camera.ui,
                on_click=lambda t=tab: self.switch_tab(t)
            )
            btn.enabled = False
            self.tab_buttons.append(btn)
    
    def _create_action_buttons(self):
        """Create action buttons for inventory management."""
        # Position buttons adjacent to the info panel (info panel is at 0.3, 0.2)
        # Add random item button
        self.add_item_btn = Button(
            text='Add Item',
            color=color.lime.tint(-.25),
            scale=(0.08, 0.04),
            position=(0.3, 0.0),  # Below the info panel
            parent=camera.ui,
            tooltip=Tooltip('Add random item'),
            on_click=self._add_random_item
        )
        self.add_item_btn.enabled = False
        
        # Sort items button
        self.sort_btn = Button(
            text='Sort',
            color=color.orange.tint(-.25),
            scale=(0.08, 0.04),
            position=(0.4, 0.0),  # Next to the Add Item button
            parent=camera.ui,
            tooltip=Tooltip('Sort items by type'),
            on_click=self._sort_items
        )
        self.sort_btn.enabled = False
    
    def _load_sample_data(self):
        """Load sample inventory data from asset files."""
        if ASSETS_AVAILABLE:
            try:
                # Load items from asset management system
                self.sample_items = create_sample_inventory()
                print(f"✅ Loaded {len(self.sample_items)} items from asset files")
            except Exception as e:
                print(f"⚠️ Failed to load from assets: {e}, using fallback data")
                self._load_fallback_data()
        else:
            print("⚠️ Asset system not available, using fallback data")
            self._load_fallback_data()
    
    def _load_fallback_data(self):
        """Load fallback sample data when asset system is unavailable."""
        self.sample_items = [
            {"name": "Iron Sword", "type": "Weapons", "tier": "BASE", "equipped_by": "Hero", "quantity": 1},
            {"name": "Steel Axe", "type": "Weapons", "tier": "ENHANCED", "equipped_by": None, "quantity": 1},
            {"name": "Magic Bow", "type": "Weapons", "tier": "ENCHANTED", "equipped_by": None, "quantity": 1},
            {"name": "Leather Armor", "type": "Armor", "tier": "BASE", "equipped_by": "Hero", "quantity": 1},
            {"name": "Chain Mail", "type": "Armor", "tier": "ENHANCED", "equipped_by": None, "quantity": 1},
            {"name": "Power Ring", "type": "Accessories", "tier": "ENHANCED", "equipped_by": "Mage", "quantity": 1},
            {"name": "Health Potion", "type": "Consumables", "tier": "BASE", "equipped_by": None, "quantity": 5},
            {"name": "Mana Potion", "type": "Consumables", "tier": "BASE", "equipped_by": None, "quantity": 3},
            {"name": "Iron Ore", "type": "Materials", "tier": "BASE", "equipped_by": None, "quantity": 10},
            {"name": "Magic Crystal", "type": "Materials", "tier": "ENHANCED", "equipped_by": None, "quantity": 2},
            {"name": "Dragon Scale", "type": "Materials", "tier": "ENCHANTED", "equipped_by": None, "quantity": 1},
        ]
    
    def _populate_sample_items(self):
        """Populate the interactive inventory with sample items."""
        for item in self.sample_items:
            self.interactive_inventory.add_item(item)
    
    def _add_random_item(self):
        """Add a random item to the inventory."""
        random_items = [
            {"name": "Random Sword", "type": "Weapons", "tier": "BASE", "equipped_by": None, "quantity": 1},
            {"name": "Random Shield", "type": "Armor", "tier": "BASE", "equipped_by": None, "quantity": 1},
            {"name": "Random Gem", "type": "Accessories", "tier": "ENHANCED", "equipped_by": None, "quantity": 1},
            {"name": "Random Potion", "type": "Consumables", "tier": "BASE", "equipped_by": None, "quantity": 1},
        ]
        
        item = random.choice(random_items)
        item["name"] = f"{item['name']} {random.randint(1, 999)}"
        
        if self.interactive_inventory.add_item(item):
            self.sample_items.append(item)
            self._update_info_panel()
    
    def _sort_items(self):
        """Sort items in the inventory by type."""
        # Clear current items completely
        children_to_destroy = []
        for child in self.interactive_inventory.children:
            if isinstance(child, InventoryItem):
                children_to_destroy.append(child)
        
        # Destroy all inventory items
        for child in children_to_destroy:
            destroy(child)
        
        # Clear the children list manually to ensure it's empty
        self.interactive_inventory.children = [child for child in self.interactive_inventory.children 
                                             if not isinstance(child, InventoryItem)]
        
        # Re-add items sorted by type
        sorted_items = sorted(self.sample_items, key=lambda x: (x['type'], x['name']))
        self.interactive_inventory.items = []
        
        for item in sorted_items:
            self.interactive_inventory.add_item(item)
        
        print("Items sorted by type")
    
    def switch_tab(self, tab_name: str):
        """Switch to different item type tab."""
        self.current_tab = tab_name
        
        # Update tab button colors
        for i, btn in enumerate(self.tab_buttons):
            tabs = ["All", "Weapons", "Armor", "Accessories", "Consumables", "Materials"]
            btn.color = color.azure if tabs[i] == tab_name else color.dark_gray
        
        # Filter and display items (simplified - in full implementation would hide/show items)
        filtered_items = self.interactive_inventory.get_items_by_type(tab_name)
        print(f"Switched to {tab_name} tab. Showing {len(filtered_items)} items.")
        
        self._update_info_panel()
    
    def _update_info_panel(self):
        """Update the information panel with current stats."""
        if self.info_panel:
            destroy(self.info_panel)
        
        filtered_items = self.interactive_inventory.get_items_by_type(self.current_tab)
        equipped_count = len([item for item in filtered_items if item.get('equipped_by')])
        
        info_text = [
            "Interactive Inventory",
            "Drag items to rearrange",
            "Equipped items shown in gray",
            f"Tab: {self.current_tab}",
            f"Items: {len(filtered_items)}",
            f"Equipped: {equipped_count}"
        ]
        
        self.info_panel = WindowPanel(
            title='Inventory Info',
            content=tuple(Text(line) for line in info_text),
            popup=False
        )
        self.info_panel.scale = (0.3, 0.4)
        self.info_panel.position = (0.3, 0.2)
        self.info_panel.enabled = self._is_visible
    
    def toggle_visibility(self):
        """Toggle the visibility of the inventory panel."""
        self._is_visible = not self._is_visible
        
        # Toggle all UI elements
        if self.interactive_inventory:
            self.interactive_inventory.enabled = self._is_visible
        
        if self.info_panel:
            self.info_panel.enabled = self._is_visible
        
        for btn in self.tab_buttons:
            btn.enabled = self._is_visible
        
        if hasattr(self, 'add_item_btn'):
            self.add_item_btn.enabled = self._is_visible
        if hasattr(self, 'sort_btn'):
            self.sort_btn.enabled = self._is_visible
        
        status = "shown" if self._is_visible else "hidden"
        print(f"Interactive inventory panel {status}")
    
    def show(self):
        """Show the inventory panel."""
        if not self._is_visible:
            self.toggle_visibility()
    
    def hide(self):
        """Hide the inventory panel."""
        if self._is_visible:
            self.toggle_visibility()
    
    def is_visible(self) -> bool:
        """Check if the inventory panel is currently visible."""
        return self._is_visible
    
    def update_content(self, data: Dict[str, Any]):
        """
        Update panel content with new data.
        
        Args:
            data: Dictionary with inventory data
        """
        if 'inventory' in data:
            self.sample_items = data['inventory']
            # Refresh inventory display
            if self.interactive_inventory:
                # Clear and repopulate
                for child in self.interactive_inventory.children.copy():
                    if isinstance(child, InventoryItem):
                        destroy(child)
                self.interactive_inventory.items = []
                self._populate_sample_items()
            self._update_info_panel()
    
    def set_game_reference(self, game: Any):
        """
        Set reference to the main game object.
        
        Args:
            game: Main game object
        """
        self.game_reference = game
    
    def cleanup(self):
        """Clean up panel resources."""
        if self.interactive_inventory:
            destroy(self.interactive_inventory)
        if self.info_panel:
            destroy(self.info_panel)
        for btn in self.tab_buttons:
            destroy(btn)
        if hasattr(self, 'add_item_btn'):
            destroy(self.add_item_btn)
        if hasattr(self, 'sort_btn'):
            destroy(self.sort_btn)