"""
Visual Feedback Systems

Real-time visual feedback components for tactical information display.
"""

from .grid_visualizer import GridVisualizer

# Import Ursina-dependent components only if available
try:
    from ursina import Entity
    from .tile_highlighter import TileHighlighter
    from .combat_animator import CombatAnimator
    from .unit_renderer import UnitEntity
    URSINA_AVAILABLE = True
    
    __all__ = [
        'GridVisualizer',
        'TileHighlighter', 
        'CombatAnimator',
        'UnitEntity'
    ]
except ImportError:
    URSINA_AVAILABLE = False
    
    __all__ = [
        'GridVisualizer'
    ]