"""
Game Managers Module

Exports all manager classes for the tactical RPG game system.
Includes state management, UI coordination, and system integration.
"""

# Core managers
try:
    from .ui_manager import UIManager
except ImportError:
    print("⚠️ UIManager not available")

# MCP integration manager (Phase 2 - MCP Integration)
try:
    from .mcp_integration_manager import MCPIntegrationManager
except ImportError:
    print("⚠️ MCPIntegrationManager not available")

# Manager registry and interfaces
try:
    from ..interfaces.game_interfaces import ManagerRegistry, BaseManager
    INTERFACES_AVAILABLE = True
except ImportError:
    INTERFACES_AVAILABLE = False
    print("⚠️ Manager interfaces not available")

# Export available managers
__all__ = []

# Add available managers to exports
if 'UIManager' in locals():
    __all__.append('UIManager')

if 'MCPIntegrationManager' in locals():
    __all__.append('MCPIntegrationManager')

if INTERFACES_AVAILABLE:
    __all__.extend(['ManagerRegistry', 'BaseManager'])

print(f"📦 Game managers module loaded - {len(__all__)} managers available")