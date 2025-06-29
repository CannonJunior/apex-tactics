"""
Core UI System Module

Provides portable UI abstractions and interfaces for multi-engine support.
"""

from .ui_abstractions import *

__all__ = [
    'UIColor', 'UIVector2', 'UIRect', 'UIAnchor', 'UILayoutMode',
    'IUIElement', 'IUIButton', 'IUIPanel', 'IUIText', 'IUIScreen', 'IUIManager',
    'UIEvent', 'UIEventBus', 'UITheme', 'UIState', 'ui_state'
]