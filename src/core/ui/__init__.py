"""
Core UI Module

Provides centralized UI configuration management and utilities.
"""

from .ui_config_manager import (
    UIConfigManager,
    get_ui_config_manager,
    reload_ui_config,
    get_ui_color,
    get_ui_position,
    get_ui_scale,
    get_action_color
)

__all__ = [
    'UIConfigManager',
    'get_ui_config_manager', 
    'reload_ui_config',
    'get_ui_color',
    'get_ui_position', 
    'get_ui_scale',
    'get_action_color'
]