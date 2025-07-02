"""
Client UI Bridge

Bridges the gap between WebSocket client and Ursina UI components.
Handles UI updates, panel management, and visual synchronization.
"""

import logging
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .websocket_game_client import WebSocketGameClient

logger = logging.getLogger(__name__)


class ClientUIBridge:
    """
    Bridge between WebSocket client and Ursina UI system.
    
    Responsibilities:
    - Translate server events to UI updates
    - Manage panel states and visibility
    - Handle visual effects and animations
    - Coordinate camera and interaction systems
    """
    
    def __init__(self, client_app, ws_client: 'WebSocketGameClient'):
        """
        Initialize UI bridge.
        
        Args:
            client_app: Main client application instance
            ws_client: WebSocket client instance
        """
        self.client_app = client_app
        self.ws_client = ws_client
        
        # UI state tracking
        self.current_unit_selection = None
        self.active_panels = set()
        self.notification_queue = []
        
        # Visual state
        self.highlighted_tiles = []
        self.active_animations = []
        
        logger.info("Client UI Bridge initialized")
    
    def update_battlefield_from_state(self, game_state: Dict[str, Any]):
        """
        Update battlefield visualization from server game state.
        
        Args:
            game_state: Complete game state from server
        """
        try:
            battlefield = game_state.get('battlefield', {})
            units = battlefield.get('units', [])
            
            # Clear existing battlefield
            self.client_app._clear_battlefield()
            
            # Recreate battlefield from server state
            battlefield_size = battlefield.get('size', (10, 10))
            self._create_grid_tiles(battlefield_size)
            
            # Place units
            for unit_data in units:
                self._create_unit_from_server_data(unit_data)
            
            logger.info(f"Battlefield updated: {len(units)} units")
            
        except Exception as e:
            logger.error(f"Error updating battlefield: {e}")
    
    def _create_grid_tiles(self, size: tuple):
        """Create interactive grid tiles"""
        width, height = size
        
        try:
            from ursina import Entity, color
            
            for x in range(width):
                for y in range(height):
                    tile = Entity(
                        model='cube',
                        color=color.dark_gray,
                        scale=(0.95, 0.1, 0.95),
                        position=(x + 0.5, 0, y + 0.5)
                    )
                    tile.x_coord = x
                    tile.y_coord = y
                    tile.on_click = lambda t=tile: self.client_app._handle_tile_click(t.x_coord, t.y_coord)
                    self.client_app.grid_tiles.append(tile)
                    
        except ImportError:
            logger.warning("Ursina not available for grid tile creation")
    
    def _create_unit_from_server_data(self, unit_data: Dict[str, Any]):
        """Create unit entity from server data"""
        try:
            from ursina import Entity, color, Text
            
            x = unit_data.get('x', 0)
            y = unit_data.get('y', 0)
            name = unit_data.get('name', 'Unit')
            team = unit_data.get('team', 'neutral')
            unit_type = unit_data.get('type', 'warrior')
            
            # Determine unit color based on team
            if team == 'player':
                unit_color = color.blue
            elif team == 'enemy':
                unit_color = color.red
            else:
                unit_color = color.gray
            
            # Create unit visual
            unit_entity = Entity(
                model='cube',
                color=unit_color,
                scale=(0.8, 1.5, 0.8),
                position=(x + 0.5, 1.0, y + 0.5)
            )
            
            # Store unit data
            unit_entity.unit_data = unit_data
            unit_entity.x_coord = x
            unit_entity.y_coord = y
            
            # Add name label
            unit_label = Text(
                text=name,
                parent=unit_entity,
                position=(0, 2, 0),
                scale=10,
                color=color.white,
                billboard=True
            )
            
            # Add health indicator if available
            if 'hp' in unit_data and 'max_hp' in unit_data:
                hp_ratio = unit_data['hp'] / unit_data['max_hp']
                health_color = color.green if hp_ratio > 0.5 else color.yellow if hp_ratio > 0.25 else color.red
                
                health_bar = Entity(
                    model='cube',
                    color=health_color,
                    scale=(0.8 * hp_ratio, 0.1, 0.1),
                    position=(0, 2.5, 0),
                    parent=unit_entity
                )
            
            self.client_app.unit_entities.append(unit_entity)
            
        except ImportError:
            logger.warning("Ursina not available for unit creation")
        except Exception as e:
            logger.error(f"Error creating unit entity: {e}")
    
    def update_unit_selection(self, selected_unit_id: Optional[str]):
        """Update visual unit selection"""
        try:
            from ursina import color
            
            # Clear previous selection
            for unit_entity in self.client_app.unit_entities:
                if hasattr(unit_entity, 'selection_indicator'):
                    unit_entity.selection_indicator.enabled = False
            
            # Highlight selected unit
            if selected_unit_id:
                for unit_entity in self.client_app.unit_entities:
                    if unit_entity.unit_data.get('id') == selected_unit_id:
                        # Create selection indicator
                        if not hasattr(unit_entity, 'selection_indicator'):
                            from ursina import Entity
                            unit_entity.selection_indicator = Entity(
                                model='cube',
                                color=color.yellow,
                                scale=(1.0, 0.1, 1.0),
                                position=(0, -0.8, 0),
                                parent=unit_entity
                            )
                        else:
                            unit_entity.selection_indicator.enabled = True
                        
                        self.current_unit_selection = selected_unit_id
                        break
            
        except ImportError:
            logger.warning("Ursina not available for selection update")
        except Exception as e:
            logger.error(f"Error updating unit selection: {e}")
    
    def highlight_tiles(self, tiles: List[Dict[str, Any]], highlight_type: str, duration: Optional[float] = None):
        """
        Highlight specific tiles with different colors.
        
        Args:
            tiles: List of tile coordinates and properties
            highlight_type: Type of highlight (movement, attack, effect)
            duration: How long to show highlight (None = permanent)
        """
        try:
            from ursina import Entity, color, invoke, destroy
            
            # Clear existing highlights if new type
            if highlight_type in ['movement', 'attack']:
                self._clear_tile_highlights()
            
            # Color mapping for different highlight types
            color_map = {
                'movement': color.green,
                'attack': color.red,
                'effect': color.yellow,
                'selection': color.blue,
                'path': color.cyan
            }
            
            highlight_color = color_map.get(highlight_type, color.white)
            
            for tile_data in tiles:
                x = tile_data.get('x', 0)
                y = tile_data.get('y', 0)
                
                highlight = Entity(
                    model='cube',
                    color=highlight_color,
                    scale=(0.9, 0.2, 0.9),
                    position=(x + 0.5, 0.1, y + 0.5),
                    alpha=0.7
                )
                
                self.client_app.highlight_entities.append(highlight)
                self.highlighted_tiles.append({
                    'entity': highlight,
                    'type': highlight_type,
                    'coords': (x, y)
                })
                
                # Auto-remove after duration
                if duration:
                    invoke(destroy, highlight, delay=duration)
            
        except ImportError:
            logger.warning("Ursina not available for tile highlighting")
        except Exception as e:
            logger.error(f"Error highlighting tiles: {e}")
    
    def _clear_tile_highlights(self, highlight_type: Optional[str] = None):
        """Clear tile highlights of specific type or all"""
        try:
            from ursina import destroy
            
            for highlight_data in self.highlighted_tiles[:]:
                if highlight_type is None or highlight_data['type'] == highlight_type:
                    destroy(highlight_data['entity'])
                    self.highlighted_tiles.remove(highlight_data)
            
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Error clearing highlights: {e}")
    
    def show_action_animation(self, action_type: str, source_pos: tuple, target_pos: tuple):
        """
        Show visual animation for game actions.
        
        Args:
            action_type: Type of action (attack, spell, movement)
            source_pos: Starting position (x, y)
            target_pos: Target position (x, y)
        """
        try:
            from ursina import Entity, color, invoke, destroy
            
            if action_type == 'attack':
                # Create attack effect at target
                effect = Entity(
                    model='sphere',
                    color=color.red,
                    scale=0.3,
                    position=(target_pos[0] + 0.5, 1.5, target_pos[1] + 0.5)
                )
                
                # Animate effect
                effect.animate_scale(1.2, duration=0.3)
                effect.animate_color(color.yellow, duration=0.3)
                invoke(destroy, effect, delay=0.5)
                
            elif action_type == 'spell':
                # Create magical effect
                effect = Entity(
                    model='sphere',
                    color=color.blue,
                    scale=0.4,
                    position=(target_pos[0] + 0.5, 2.0, target_pos[1] + 0.5)
                )
                
                effect.animate_scale(1.5, duration=0.5)
                effect.animate_color(color.cyan, duration=0.5)
                invoke(destroy, effect, delay=0.8)
                
            elif action_type == 'movement':
                # Create movement trail
                trail = Entity(
                    model='cube',
                    color=color.green,
                    scale=(0.5, 0.1, 0.5),
                    position=(source_pos[0] + 0.5, 0.2, source_pos[1] + 0.5)
                )
                
                # Animate to target
                trail.animate_position((target_pos[0] + 0.5, 0.2, target_pos[1] + 0.5), duration=0.5)
                invoke(destroy, trail, delay=0.7)
            
        except ImportError:
            logger.warning("Ursina not available for animations")
        except Exception as e:
            logger.error(f"Error showing action animation: {e}")
    
    def update_panel_from_game_state(self, panel_name: str, game_state: Dict[str, Any]):
        """
        Update specific UI panel with game state data.
        
        Args:
            panel_name: Name of panel to update
            game_state: Current game state
        """
        try:
            if panel_name == 'control':
                self._update_control_panel(game_state)
            elif panel_name == 'character':
                self._update_character_panel(game_state)
            elif panel_name == 'inventory':
                self._update_inventory_panel(game_state)
            elif panel_name == 'party':
                self._update_party_panel(game_state)
            
        except Exception as e:
            logger.error(f"Error updating panel {panel_name}: {e}")
    
    def _update_control_panel(self, game_state: Dict[str, Any]):
        """Update main control panel"""
        current_turn = game_state.get('current_turn', {})
        current_unit_id = current_turn.get('current_unit')
        
        if current_unit_id and hasattr(self.client_app, 'control_panel'):
            # Find unit data
            battlefield = game_state.get('battlefield', {})
            for unit in battlefield.get('units', []):
                if unit.get('id') == current_unit_id:
                    # Update control panel with unit info
                    if hasattr(self.client_app.control_panel, 'update_unit_info'):
                        self.client_app.control_panel.update_unit_info(unit)
                    break
    
    def _update_character_panel(self, game_state: Dict[str, Any]):
        """Update character panel"""
        # Implementation for character panel updates
        pass
    
    def _update_inventory_panel(self, game_state: Dict[str, Any]):
        """Update inventory panel"""
        # Implementation for inventory panel updates
        pass
    
    def _update_party_panel(self, game_state: Dict[str, Any]):
        """Update party panel"""
        # Implementation for party panel updates
        pass
    
    def show_notification(self, notification: Dict[str, Any]):
        """
        Show game notification.
        
        Args:
            notification: Notification data from server
        """
        title = notification.get('title', 'Notification')
        message = notification.get('message', '')
        notification_type = notification.get('type', 'info')
        
        logger.info(f"Notification [{notification_type}] {title}: {message}")
        
        # Add to notification queue for UI display
        self.notification_queue.append(notification)
        
        # Limit queue size
        if len(self.notification_queue) > 10:
            self.notification_queue.pop(0)
    
    def process_ui_updates(self, ui_data: Dict[str, Any]):
        """
        Process UI updates from server.
        
        Args:
            ui_data: UI data from server
        """
        # Handle notifications
        if 'notifications' in ui_data:
            for notification in ui_data['notifications']:
                self.show_notification(notification)
        
        # Handle visual effects
        if 'visual_effects' in ui_data:
            for effect in ui_data['visual_effects']:
                self._process_visual_effect(effect)
        
        # Handle UI state updates
        if 'ui_state' in ui_data:
            self._process_ui_state_updates(ui_data['ui_state'])
    
    def _process_visual_effect(self, effect: Dict[str, Any]):
        """Process visual effect from server"""
        effect_type = effect.get('type', 'unknown')
        
        if effect_type == 'highlight_tiles':
            tiles = effect.get('tiles', [])
            highlight_type = effect.get('highlight_type', 'selection')
            duration = effect.get('duration')
            self.highlight_tiles(tiles, highlight_type, duration)
        
        elif effect_type == 'action_animation':
            action_type = effect.get('action_type', 'unknown')
            source_pos = effect.get('source_pos', (0, 0))
            target_pos = effect.get('target_pos', (0, 0))
            self.show_action_animation(action_type, source_pos, target_pos)
    
    def _process_ui_state_updates(self, ui_state: Dict[str, Any]):
        """Process UI state updates"""
        # Handle unit selection
        if 'selected_unit' in ui_state:
            self.update_unit_selection(ui_state['selected_unit'])
        
        # Handle mode changes
        if 'current_mode' in ui_state:
            self.client_app.current_mode = ui_state['current_mode']
        
        # Handle panel visibility
        if 'panel_states' in ui_state:
            self._update_panel_visibility(ui_state['panel_states'])
    
    def _update_panel_visibility(self, panel_states: Dict[str, bool]):
        """Update panel visibility based on server state"""
        for panel_name, visible in panel_states.items():
            panel = getattr(self.client_app, f"{panel_name}_panel", None)
            if panel and hasattr(panel, 'set_visible'):
                panel.set_visible(visible)
    
    def get_ui_state_for_server(self) -> Dict[str, Any]:
        """
        Get current UI state to send to server.
        
        Returns:
            Dict with current UI state
        """
        return {
            'current_mode': self.client_app.current_mode,
            'selected_unit': self.current_unit_selection,
            'panel_states': {
                'talent': getattr(self.client_app.talent_panel, 'visible', False),
                'inventory': getattr(self.client_app.inventory_panel, 'visible', False),
                'party': getattr(self.client_app.party_panel, 'visible', False),
                'upgrade': getattr(self.client_app.upgrade_panel, 'visible', False),
                'character': getattr(self.client_app.character_panel, 'visible', False),
            }
        }
    
    def cleanup(self):
        """Clean up UI bridge resources"""
        self._clear_tile_highlights()
        self.notification_queue.clear()
        self.active_animations.clear()
        logger.info("Client UI Bridge cleaned up")