"""
Integration Layer

Provides adapters and bridges between the refactored modular architecture
and the original monolithic tactical RPG controller for seamless integration.
"""

from .ursina_adapter import UrsinaIntegrationAdapter
from .controller_bridge import ControllerBridge
from .legacy_compatibility import LegacyCompatibilityLayer

__all__ = [
    'UrsinaIntegrationAdapter',
    'ControllerBridge', 
    'LegacyCompatibilityLayer'
]