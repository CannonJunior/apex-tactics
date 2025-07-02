"""
Panel Adapter

Adapts existing UI panels to work with the WebSocket client instead of direct game reference.
Provides compatibility layer for existing panel code.
"""

import logging
from typing import Any, Optional, Dict, List
import asyncio

logger = logging.getLogger(__name__)


class ClientGameAdapter:
    """
    Adapter that makes the WebSocket client look like the original game object
    to existing UI panels. Provides the same interface but routes commands 
    through WebSocket to the server.
    """
    
    def __init__(self, client_app):
        """
        Initialize adapter with client app reference.
        
        Args:
            client_app: Main ApexTacticsClient instance
        """
        self.client_app = client_app
        self.ws_client = None
        
        # Cached game state for panel queries
        self.cached_game_state = {}
        self.cached_units = []
        self.cached_active_unit = None
        
        logger.info("Client game adapter initialized")
    
    def set_websocket_client(self, ws_client):
        """Set WebSocket client reference"""
        self.ws_client = ws_client
    
    # Properties that panels expect from the original game object
    @property
    def active_unit(self):
        """Get currently active unit"""
        return self.cached_active_unit
    
    @active_unit.setter
    def active_unit(self, unit):
        """Set active unit"""
        self.cached_active_unit = unit
    
    @property
    def units(self):
        """Get all units in game"""
        return self.cached_units
    
    @property
    def current_mode(self):
        """Get current game mode"""
        return getattr(self.client_app, 'current_mode', None)
    
    @current_mode.setter
    def current_mode(self, mode):
        """Set current game mode"""
        self.client_app.current_mode = mode
    
    @property
    def turn_manager(self):
        """Mock turn manager for panel compatibility"""
        return MockTurnManager(self)
    
    # Methods that panels call
    def end_current_turn(self):
        """End current turn via WebSocket"""
        if self.ws_client and self.cached_active_unit:
            action = {
                "type": "end_turn",
                "unit_id": self.cached_active_unit.get("id")
            }
            asyncio.create_task(self._send_action(action))
    
    def handle_action_selection(self, action_name: str, unit):
        """Handle action selection"""
        logger.info(f"Action selected: {action_name} for unit {unit}")
        
        if action_name == "Move":
            self.client_app.current_mode = "move"
        elif action_name == "Attack":
            self.client_app.current_mode = "attack"
        elif action_name == "Magic":
            self.client_app.current_mode = "magic"
        else:
            logger.warning(f"Unknown action: {action_name}")
    
    def select_unit_by_index(self, index: int):
        """Select unit by carousel index"""
        if 0 <= index < len(self.cached_units):
            unit = self.cached_units[index]
            unit_id = unit.get("id")
            if unit_id and self.ws_client:
                asyncio.create_task(self.ws_client.select_unit(
                    self.client_app.session_id,
                    self.client_app.player_id,
                    unit_id
                ))
    
    def update_game_state(self, game_state: Dict[str, Any]):
        """Update cached game state from server"""
        self.cached_game_state = game_state
        
        # Update cached units
        battlefield = game_state.get('battlefield', {})
        self.cached_units = battlefield.get('units', [])
        
        # Update active unit
        current_turn = game_state.get('current_turn', {})
        current_unit_id = current_turn.get('current_unit')
        
        if current_unit_id:
            for unit in self.cached_units:
                if unit.get('id') == current_unit_id:
                    self.cached_active_unit = unit
                    break
    
    async def _send_action(self, action: Dict[str, Any]):
        """Send action to server via WebSocket"""
        if self.ws_client:
            await self.ws_client.send_player_action(
                self.client_app.session_id,
                self.client_app.player_id,
                action
            )
    
    # Camera controller compatibility
    @property
    def camera_controller(self):
        """Mock camera controller"""
        return MockCameraController()
    
    # Grid compatibility
    @property
    def grid(self):
        """Mock grid for panel compatibility"""
        return MockBattleGrid()


class MockTurnManager:
    """Mock turn manager for panel compatibility"""
    
    def __init__(self, adapter):
        self.adapter = adapter
    
    @property
    def units(self):
        """Get all units (property for compatibility)"""
        return self.adapter.cached_units
    
    def current_unit(self):
        """Get current unit"""
        return self.adapter.cached_active_unit
    
    def get_turn_order(self):
        """Get turn order"""
        return self.adapter.cached_units
    
    def get_current_turn_index(self):
        """Get current turn index"""
        if self.adapter.cached_active_unit:
            for i, unit in enumerate(self.adapter.cached_units):
                if unit.get('id') == self.adapter.cached_active_unit.get('id'):
                    return i
        return 0


class MockCameraController:
    """Mock camera controller for panel compatibility"""
    
    def handle_input(self, key, control_panel=None):
        """Handle camera input (no-op for client)"""
        pass
    
    def handle_mouse_input(self):
        """Handle mouse input (no-op for client)"""
        pass
    
    def update_camera(self):
        """Update camera (no-op for client)"""
        pass


class MockBattleGrid:
    """Mock battle grid for panel compatibility"""
    
    def __init__(self):
        self.width = 10
        self.height = 10


class PanelClientBridge:
    """
    Bridge that helps panels communicate with the WebSocket client.
    Extends existing panel functionality to work with remote game state.
    """
    
    def __init__(self, client_app):
        self.client_app = client_app
        self.game_adapter = ClientGameAdapter(client_app)
        
    def setup_panel_references(self):
        """Setup game references for all panels to use the adapter"""
        panels = [
            'control_panel',
            'talent_panel', 
            'inventory_panel',
            'party_panel',
            'upgrade_panel',
            'character_panel'
        ]
        
        for panel_name in panels:
            panel = getattr(self.client_app, panel_name, None)
            if panel:
                self._setup_panel_reference(panel)
    
    def _setup_panel_reference(self, panel):
        """Setup game reference for a single panel"""
        # Set both game_reference and client_reference for compatibility
        panel.game_reference = self.game_adapter
        
        if hasattr(panel, 'set_game_reference'):
            panel.set_game_reference(self.game_adapter)
        
        if hasattr(panel, 'set_client_reference'):
            panel.set_client_reference(self.client_app)
        
        logger.info(f"Setup references for {panel.__class__.__name__}")
    
    def update_panels_from_game_state(self, game_state: Dict[str, Any]):
        """Update all panels with new game state"""
        # Update adapter's cached state
        self.game_adapter.update_game_state(game_state)
        
        # Update individual panels
        panels = [
            ('control_panel', self._update_control_panel),
            ('character_panel', self._update_character_panel),
            ('inventory_panel', self._update_inventory_panel),
            ('party_panel', self._update_party_panel),
        ]
        
        for panel_name, update_func in panels:
            panel = getattr(self.client_app, panel_name, None)
            if panel and hasattr(panel, 'update_content'):
                try:
                    update_func(panel, game_state)
                except Exception as e:
                    logger.error(f"Error updating {panel_name}: {e}")
    
    def _update_control_panel(self, panel, game_state: Dict[str, Any]):
        """Update control panel specifically"""
        if hasattr(panel, 'update_unit_info') and self.game_adapter.cached_active_unit:
            panel.update_unit_info(self.game_adapter.cached_active_unit)
        
        # Update unit carousel if it exists
        if hasattr(panel, 'update_unit_carousel'):
            panel.update_unit_carousel(self.game_adapter.cached_units)
    
    def _update_character_panel(self, panel, game_state: Dict[str, Any]):
        """Update character panel"""
        if self.game_adapter.cached_active_unit:
            panel.update_content({
                'character': self.game_adapter.cached_active_unit,
                'game_state': game_state
            })
    
    def _update_inventory_panel(self, panel, game_state: Dict[str, Any]):
        """Update inventory panel"""
        # Extract inventory data from game state
        player_data = game_state.get('player_data', {})
        inventory = player_data.get('inventory', [])
        
        panel.update_content({
            'inventory': inventory,
            'game_state': game_state
        })
    
    def _update_party_panel(self, panel, game_state: Dict[str, Any]):
        """Update party panel"""
        party_units = [unit for unit in self.game_adapter.cached_units 
                      if unit.get('team') == 'player']
        
        panel.update_content({
            'party': party_units,
            'game_state': game_state
        })
    
    def set_websocket_client(self, ws_client):
        """Set WebSocket client for the adapter"""
        self.game_adapter.set_websocket_client(ws_client)