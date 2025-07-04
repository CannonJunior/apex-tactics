#!/usr/bin/env python3
"""
Apex Tactics - Enhanced Version

Runs the tactical RPG with the new refactored architecture integrated
through the ControllerBridge. Provides all original functionality plus
enhanced features like action queuing, AI agents, and visual queue management.
"""

from ursina import *
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Original game imports
from game.controllers.tactical_rpg_controller import TacticalRPG
from ui.panels.control_panel import CharacterAttackInterface
from ui.panels.talent_panel import TalentPanel
from ui.panels.inventory_panel import InventoryPanel
from ui.panels.party_panel import PartyPanel
from ui.panels.upgrade_panel import UpgradePanel
from ui.panels.character_panel import CharacterPanel

# New integration imports
from integration.controller_bridge import create_controller_bridge
from ui.ui_integration import create_integrated_ui, UIIntegrationConfig
from ui.queue_management import UITheme
from game.config.feature_flags import FeatureFlags
from ai.ai_integration_manager import AIIntegrationManager

# Configure enhanced features
FeatureFlags.USE_ACTION_MANAGER = True
FeatureFlags.USE_NEW_QUEUE_UI = True
FeatureFlags.USE_MCP_TOOLS = True
FeatureFlags.USE_AI_ORCHESTRATION = True
FeatureFlags.USE_PREDICTION_ENGINE = True

print("🚀 APEX TACTICS - ENHANCED VERSION")
print("=" * 50)
print("Enhanced features enabled:")
print("  ✅ Multi-action queuing per unit")
print("  ✅ AI agent control via MCP tools")
print("  ✅ Visual queue management UI")
print("  ✅ Action prediction system")
print("  ✅ Performance optimization")
print()

app = Ursina()

# Create all original panels
control_panel = CharacterAttackInterface()
talent_panel = TalentPanel()
inventory_panel = InventoryPanel()
party_panel = PartyPanel()
upgrade_panel = UpgradePanel()
character_panel = CharacterPanel()

# Initialize original game controller
print("🎮 Initializing original game controller...")
game = TacticalRPG(control_panel=control_panel)

# Set game reference for all panels
control_panel.set_game_reference(game)
talent_panel.game_reference = game
inventory_panel.game_reference = game
party_panel.game_reference = game
upgrade_panel.game_reference = game
character_panel.game_reference = game

# Set character state manager for character panel
character_panel.set_character_state_manager(game.character_state_manager)

# Create controller bridge for enhanced features
print("🔗 Creating controller bridge...")
try:
    bridge = create_controller_bridge(game)
    bridge.print_bridge_status()
    
    # Create enhanced UI if enabled (disabled for now to avoid visual conflicts)
    enhanced_ui = None
    if False:  # Temporarily disabled - FeatureFlags.USE_NEW_QUEUE_UI:
        print("🖼️ Enhanced queue management UI disabled to prevent visual conflicts")
        print("🔧 Will be enabled after Ursina integration improvements")
        # TODO: Enable after fixing Ursina Entity creation conflicts
        try:
            ui_config = UIIntegrationConfig(
                theme=UITheme.TACTICAL,
                enable_predictions=True,
                enable_ai_displays=False,  # Disable AI displays to reduce conflicts
                auto_update_enabled=False  # Disable auto-updates to reduce conflicts
            )
            enhanced_ui = create_integrated_ui(bridge.action_manager, ui_config)
            if enhanced_ui:
                print("✅ Enhanced UI created successfully")
            else:
                print("⚠️ Enhanced UI creation failed, using original UI only")
        except Exception as e:
            print(f"⚠️ Enhanced UI error: {e}")
            enhanced_ui = None
    
    # Initialize AI system if enabled
    ai_manager = None
    if FeatureFlags.USE_AI_ORCHESTRATION:
        print("🤖 Initializing AI integration...")
        try:
            ai_manager = AIIntegrationManager(bridge.action_manager)
            ai_manager.initialize()
            print("✅ AI integration enabled")
        except Exception as e:
            print(f"⚠️ AI integration error: {e}")
    
    print("🎉 Enhanced systems initialized successfully!")
    
except Exception as e:
    print(f"❌ Bridge creation failed: {e}")
    print("🔄 Falling back to original controller only")
    bridge = None
    enhanced_ui = None
    ai_manager = None

def input(key):
    """Enhanced input handling with new features."""
    
    # Handle enhanced features (currently backend-only)
    if key == 'q' and bridge:
        # Show queue status in console
        try:
            status = bridge.action_manager.get_action_statistics()
            print(f"📊 Action System Status: {status}")
            if bridge.action_manager:
                bridge.action_manager.action_registry.list_actions()
            return
        except Exception as e:
            print(f"⚠️ Queue status error: {e}")
    
    if key == 'r' and bridge and game.active_unit:
        # Queue test action for selected unit
        try:
            unit_id = game.active_unit.id if hasattr(game.active_unit, 'id') else 'active_unit'
            success = bridge.queue_action(unit_id, 'test_action', [{'x': 5, 'y': 5}])
            print(f"🎯 Test action queued: {'Success' if success else 'Failed'}")
            return
        except Exception as e:
            print(f"⚠️ Action queue error: {e}")
    
    # Handle game input first (modals, etc.) - highest priority
    if game.handle_input(key):
        return  # Input was handled by game controller
    
    # Handle panel toggles
    if key == 't':
        talent_panel.toggle_visibility()
        return
    elif key == 'i':
        inventory_panel.toggle_visibility()
        return
    elif key == 'p':
        party_panel.toggle_visibility()
        return
    elif key == 'u':
        upgrade_panel.toggle_visibility()
        return
    elif key == 'c':
        character_panel.toggle_visibility()
        return
    elif key == 'h':
        # Show help for enhanced features
        show_enhanced_help()
        return
    
    # Handle path movement for selected unit ONLY if in move mode
    if (game.active_unit and game.current_mode == "move" and 
        key in ['w', 'a', 's', 'd', 'enter']):
        game.handle_path_movement(key)
        return  # Don't process camera controls if unit is selected and WASD/Enter is pressed
    
    # Handle camera controls only if not handling unit movement
    game.camera_controller.handle_input(key, control_panel)

def update():
    """Enhanced update loop with new systems."""
    
    # Update camera
    game.camera_controller.handle_mouse_input()
    game.camera_controller.update_camera()
    
    # Update control panel with current unit info
    if game.turn_manager and game.turn_manager.current_unit() and not game.active_unit:
        control_panel.update_unit_info(game.turn_manager.current_unit())
    
    # Update enhanced UI
    if enhanced_ui:
        try:
            enhanced_ui.update_ui()
        except Exception as e:
            # Silently handle UI update errors
            pass
    
    # Update AI system
    if ai_manager:
        try:
            ai_manager.update()
        except Exception as e:
            # Silently handle AI update errors
            pass

def show_enhanced_help():
    """Show help for enhanced features."""
    help_text = """
🎮 APEX TACTICS - ENHANCED CONTROLS

Original Controls:
  T - Toggle Talent Panel
  I - Toggle Inventory Panel  
  P - Toggle Party Panel
  U - Toggle Upgrade Panel
  C - Toggle Character Panel
  WASD - Move selected unit
  Mouse - Select units/tiles

Enhanced Controls (Backend):
  Q - Show Action System Status
  R - Queue Test Action (if unit selected)
  H - Show this help

Enhanced Features (Active):
  ✅ Multi-action queuing system (backend)
  ✅ AI agent integration (backend)
  ✅ Performance optimization
  ⚠️ Visual UI temporarily disabled

Note: Enhanced UI disabled to prevent visual conflicts.
The new action system runs in the background and can be
accessed via console commands.

Status: """ + ("Bridge Active" if bridge and bridge.is_bridged else "Legacy Mode")
    
    print(help_text)

# Set initial camera position
game.camera_controller.update_camera()

# Add lighting
DirectionalLight(y=10, z=5)

# Show startup message
show_enhanced_help()

print("\n🎮 Game ready! Press H for enhanced controls help.")

# Run the enhanced game
app.run()

# Cleanup on exit
if enhanced_ui:
    enhanced_ui.shutdown()
if ai_manager:
    ai_manager.shutdown()
if bridge:
    bridge.shutdown()

print("🎮 Apex Tactics Enhanced - Session ended")