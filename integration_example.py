
# Example: Integrating Refactored System with Original Controller

from ursina import *
from integration.controller_bridge import create_controller_bridge
from game.config.feature_flags import FeatureFlags

# Enable new features
FeatureFlags.USE_ACTION_MANAGER = True
FeatureFlags.USE_NEW_QUEUE_UI = True

app = Ursina()

# Create original controller (your existing code)
from game.controllers.tactical_rpg_controller import TacticalRPG
original_game = TacticalRPG()

# Create bridge to integrate new systems
bridge = create_controller_bridge(original_game)

# Now you can use both old and new features:

# Old way (still works)
if original_game.active_unit:
    original_game.handle_attack(target_pos)

# New way (enhanced features)
bridge.queue_action('unit_id', 'fireball', [{'x': 5, 'y': 5}])
queue_status = bridge.action_manager.get_queue_status()

# AI agents can now control units
from ai.ai_integration_manager import AIIntegrationManager
ai_manager = AIIntegrationManager(bridge.action_manager)
ai_manager.initialize()

# UI shows action queues and predictions
from ui.ui_integration import create_integrated_ui
ui_system = create_integrated_ui(bridge.action_manager)

def input(key):
    # Handle input through bridge (backwards compatible)
    if not bridge.original_controller().handle_input(key):
        # Handle new features
        if key == 'q':
            ui_system.show_action_preview()

app.run()
