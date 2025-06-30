"""
UI Panels Module

Provides all game UI panels for Apex Tactics with engine portability.
Includes character, inventory, talent, party, and upgrade management panels.
"""

from .base_panel import BasePanel, PanelConfig, PanelManager
from .character_panel import CharacterPanel
from .inventory_panel import InventoryPanel
from .talent_panel import TalentPanel
from .party_panel import PartyPanel
from .upgrade_panel import UpgradePanel
from .control_panel import CharacterAttackInterface
from .game_panel_manager import GamePanelManager, create_game_panels

__all__ = [
    # Base classes
    'BasePanel',
    'PanelConfig', 
    'PanelManager',
    
    # Game panels
    'CharacterPanel',
    'InventoryPanel',
    'TalentPanel',
    'PartyPanel',
    'UpgradePanel',
    'CharacterAttackInterface',
    
    # Manager
    'GamePanelManager',
    'create_game_panels'
]