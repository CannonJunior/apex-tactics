"""
Game State Management

This module provides classes and utilities for managing dynamic game state,
bridging the gap between static asset data and runtime gameplay.
"""

from .character_state_manager import (
    CharacterInstance,
    CharacterStateManager,
    get_character_state_manager
)

__all__ = [
    'CharacterInstance',
    'CharacterStateManager',
    'get_character_state_manager'
]