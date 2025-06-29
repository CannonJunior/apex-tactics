"""
Portable UI System

Multi-engine UI framework supporting Ursina, Unity, Godot, and other engines.
Provides abstraction layer for cross-platform UI development.
"""

# Import portable UI core
from .core import *
from .screens import *

# Import legacy UI components
try:
    from .camera_controller import CameraController
    from .visual.grid_visualizer import GridVisualizer
    from .interface.inventory_interface import InventoryInterface
    from .interface.combat_interface import CombatInterface
    
    # Import Ursina-dependent visual components separately
    try:
        from ursina import Entity
        from .visual.tile_highlighter import TileHighlighter
        from .visual.combat_animator import CombatAnimator
        VISUAL_COMPONENTS_AVAILABLE = True
    except ImportError:
        VISUAL_COMPONENTS_AVAILABLE = False
    
    LEGACY_UI_AVAILABLE = True
except ImportError:
    LEGACY_UI_AVAILABLE = False
    VISUAL_COMPONENTS_AVAILABLE = False

# Conditionally import engine-specific implementations
try:
    from .ursina import *
    URSINA_UI_AVAILABLE = True
except ImportError:
    URSINA_UI_AVAILABLE = False

__all__ = [
    # Core abstractions
    'UIColor', 'UIVector2', 'UIRect', 'UIAnchor', 'UILayoutMode',
    'IUIElement', 'IUIButton', 'IUIPanel', 'IUIText', 'IUIScreen', 'IUIManager',
    'UIEvent', 'UIEventBus', 'UITheme', 'UIState', 'ui_state',
    
    # Screen implementations
    'GameSettings', 'StartScreen', 'SettingsScreen', 'MainMenuManager',
    
    # Engine availability flags
    'URSINA_UI_AVAILABLE', 'LEGACY_UI_AVAILABLE'
]

# Add legacy components if available
if LEGACY_UI_AVAILABLE:
    __all__.extend([
        'CameraController', 'GridVisualizer', 
        'InventoryInterface', 'CombatInterface'
    ])
    
    # Add visual components if available
    if VISUAL_COMPONENTS_AVAILABLE:
        __all__.extend([
            'TileHighlighter', 'CombatAnimator'
        ])

# Add Ursina components if available
if URSINA_UI_AVAILABLE:
    __all__.extend([
        'UrsinaUIButton', 'UrsinaUIPanel', 'UrsinaUIText', 
        'UrsinaUIScreen', 'UrsinaUIManager'
    ])