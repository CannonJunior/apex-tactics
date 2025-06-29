"""
UI Interaction Module

Enhanced user interaction systems for tactical games including:
- Interactive tile system with click detection
- Action modal dialogs 
- Comprehensive interaction management
- Visual feedback systems

Based on patterns from apex-tactics implementation.
"""

from .interactive_tile import InteractiveTile, TileState
from .action_modal import ActionModal, ActionModalManager, ActionOption, ModalType
from .interaction_manager import InteractionManager, InteractionMode

__all__ = [
    'InteractiveTile',
    'TileState', 
    'ActionModal',
    'ActionModalManager',
    'ActionOption',
    'ModalType',
    'InteractionManager',
    'InteractionMode'
]