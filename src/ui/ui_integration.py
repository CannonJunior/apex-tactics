"""
UI Integration with ActionManager

Integrates the Queue Management UI with the existing ActionManager and game systems.
Provides event-driven updates, user interaction handling, and seamless data flow.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
import time

from .queue_management import QueueManagementUIManager, UIConfig, UITheme
from .action_prediction import ActionPredictionEngine, PredictionDisplayWidget
from game.managers.action_manager import ActionManager
from game.config.feature_flags import FeatureFlags
from ai.ai_integration_manager import AIIntegrationManager


@dataclass
class UIIntegrationConfig:
    """Configuration for UI integration."""
    auto_update_enabled: bool = True
    update_interval: float = 0.5
    enable_predictions: bool = True
    enable_ai_displays: bool = True
    enable_drag_drop: bool = True
    theme: UITheme = UITheme.TACTICAL


class ActionManagerUIBridge:
    """
    Bridge between ActionManager and Queue Management UI.
    
    Responsibilities:
    - Event handling and UI updates
    - User interaction processing
    - Data synchronization
    - Performance optimization
    """
    
    def __init__(self, action_manager: ActionManager, config: UIIntegrationConfig):
        self.action_manager = action_manager
        self.config = config
        self.game_controller = action_manager.game_controller
        
        # UI components
        self.queue_ui_manager: Optional[QueueManagementUIManager] = None
        self.prediction_engine: Optional[ActionPredictionEngine] = None
        self.prediction_widget: Optional[PredictionDisplayWidget] = None
        
        # AI integration
        self.ai_manager: Optional[AIIntegrationManager] = None
        
        # State tracking
        self.is_initialized = False
        self.last_ui_update = 0.0
        self.cached_queue_state = {}
        
        # Event subscriptions
        self.event_subscriptions = []
        
        # User interaction callbacks
        self.interaction_callbacks: Dict[str, Callable] = {}
        
        print("🔗 ActionManager UI Bridge created")
    
    def initialize(self, ui_parent=None) -> bool:
        """Initialize the UI integration."""
        if not FeatureFlags.USE_NEW_QUEUE_UI:
            print("🔗 Queue UI disabled by feature flags")
            return False
        
        try:
            # Create UI configuration
            ui_config = UIConfig(
                theme=self.config.theme,
                enable_animations=True,
                enable_drag_drop=self.config.enable_drag_drop,
                enable_previews=self.config.enable_predictions,
                auto_update_interval=self.config.update_interval,
                show_ai_coordination=self.config.enable_ai_displays
            )
            
            # Initialize UI components
            self.queue_ui_manager = QueueManagementUIManager(self.action_manager, ui_config)
            success = self.queue_ui_manager.initialize_ui(ui_parent)
            
            if not success:
                return False
            
            # Initialize prediction system
            if self.config.enable_predictions:
                self.prediction_engine = ActionPredictionEngine(self.action_manager)
                if self.queue_ui_manager.ui_root:
                    self.prediction_widget = PredictionDisplayWidget(
                        self.queue_ui_manager.ui_root, self.prediction_engine
                    )
            
            # Set up event subscriptions
            self._setup_event_subscriptions()
            
            # Set up interaction callbacks
            self._setup_interaction_callbacks()
            
            # Try to get AI manager if available
            self._setup_ai_integration()
            
            self.is_initialized = True
            print("🔗 UI Integration initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize UI Integration: {e}")
            return False
    
    def _setup_event_subscriptions(self):
        """Set up event subscriptions for UI updates."""
        if not hasattr(self.game_controller, 'event_bus') or not self.game_controller.event_bus:
            print("⚠️ No event bus available for UI integration")
            return
        
        event_bus = self.game_controller.event_bus
        
        # Subscribe to relevant events
        subscriptions = [
            ('action_queued', self._on_action_queued),
            ('action_executed', self._on_action_executed),
            ('action_cancelled', self._on_action_cancelled),
            ('turn_started', self._on_turn_started),
            ('turn_ended', self._on_turn_ended),
            ('unit_selected', self._on_unit_selected),
            ('battle_state_changed', self._on_battle_state_changed)
        ]
        
        for event_type, handler in subscriptions:
            try:
                subscription = event_bus.subscribe(event_type, handler)
                self.event_subscriptions.append(subscription)
                print(f"🔗 Subscribed to {event_type}")
            except Exception as e:
                print(f"⚠️ Failed to subscribe to {event_type}: {e}")
    
    def _setup_interaction_callbacks(self):
        """Set up user interaction callbacks."""
        self.interaction_callbacks = {
            'queue_action': self._handle_queue_action,
            'remove_action': self._handle_remove_action,
            'reorder_actions': self._handle_reorder_actions,
            'preview_action': self._handle_preview_action,
            'select_unit': self._handle_select_unit,
            'change_theme': self._handle_change_theme
        }
        print("🔗 Interaction callbacks configured")
    
    def _setup_ai_integration(self):
        """Set up AI integration if available."""
        try:
            # Check if AI integration manager is available
            if hasattr(self.action_manager, 'ai_integration_manager'):
                self.ai_manager = self.action_manager.ai_integration_manager
                print("🔗 AI integration detected")
            else:
                print("🔗 No AI integration available")
        except Exception as e:
            print(f"⚠️ Error setting up AI integration: {e}")
    
    def update_ui(self, force_update: bool = False):
        """Update UI with current game state."""
        if not self.is_initialized or not self.config.auto_update_enabled:
            return
        
        current_time = time.time()
        if not force_update and current_time - self.last_ui_update < self.config.update_interval:
            return
        
        try:
            # Update queue management UI
            if self.queue_ui_manager:
                self.queue_ui_manager.update_ui(force_update)
            
            # Update predictions if a unit is selected
            self._update_predictions()
            
            self.last_ui_update = current_time
            
        except Exception as e:
            print(f"❌ Error updating UI: {e}")
    
    def _update_predictions(self):
        """Update action predictions display."""
        if not self.prediction_engine or not self.prediction_widget:
            return
        
        # For now, hide predictions when no specific action is being previewed
        # In a full implementation, this would show predictions for selected actions
        self.prediction_widget.hide_predictions()
    
    def create_unit_panel(self, unit_id: str) -> bool:
        """Create a unit action panel."""
        if not self.queue_ui_manager:
            return False
        
        success = self.queue_ui_manager.create_unit_panel(unit_id)
        if success:
            print(f"🔗 Created unit panel for {unit_id}")
        return success
    
    def show_action_preview(self, action_id: str, caster_id: str, target_ids: List[str]):
        """Show preview of action effects."""
        if not self.prediction_engine or not self.prediction_widget:
            return
        
        try:
            predictions = self.prediction_engine.predict_action_outcome(
                action_id, caster_id, target_ids
            )
            self.prediction_widget.show_predictions(predictions)
            print(f"🔗 Showing preview for {action_id}")
        except Exception as e:
            print(f"❌ Error showing action preview: {e}")
    
    def hide_action_preview(self):
        """Hide action preview."""
        if self.prediction_widget:
            self.prediction_widget.hide_predictions()
    
    # Event handlers
    def _on_action_queued(self, event):
        """Handle action queued event."""
        print(f"🔗 Action queued: {event.data}")
        self.update_ui(force_update=True)
    
    def _on_action_executed(self, event):
        """Handle action executed event."""
        print(f"🔗 Action executed: {event.data}")
        self.update_ui(force_update=True)
    
    def _on_action_cancelled(self, event):
        """Handle action cancelled event."""
        print(f"🔗 Action cancelled: {event.data}")
        self.update_ui(force_update=True)
    
    def _on_turn_started(self, event):
        """Handle turn started event."""
        print(f"🔗 Turn started: {event.data}")
        self.update_ui(force_update=True)
        
        # Clear prediction cache for new turn
        if self.prediction_engine:
            self.prediction_engine.clear_cache()
    
    def _on_turn_ended(self, event):
        """Handle turn ended event."""
        print(f"🔗 Turn ended: {event.data}")
        self.update_ui(force_update=True)
    
    def _on_unit_selected(self, event):
        """Handle unit selection event."""
        unit_id = event.data.get('unit_id') if event.data else None
        if unit_id:
            print(f"🔗 Unit selected: {unit_id}")
            self.create_unit_panel(unit_id)
    
    def _on_battle_state_changed(self, event):
        """Handle battle state change event."""
        print(f"🔗 Battle state changed: {event.data}")
        self.update_ui(force_update=True)
    
    # Interaction handlers
    def _handle_queue_action(self, unit_id: str, action_id: str, targets: List[str], 
                           priority: str = 'NORMAL') -> bool:
        """Handle queue action request from UI."""
        try:
            # Convert targets to positions (simplified)
            target_positions = [{'x': 0, 'y': 0} for _ in targets]
            
            # Queue action through ActionManager
            from ..game.queue.action_queue import ActionPriority
            priority_map = {
                'HIGH': ActionPriority.HIGH,
                'NORMAL': ActionPriority.NORMAL,
                'LOW': ActionPriority.LOW
            }
            
            success = self.action_manager.queue_action(
                unit_id=unit_id,
                action_id=action_id,
                targets=target_positions,
                priority=priority_map.get(priority, ActionPriority.NORMAL)
            )
            
            if success:
                print(f"🔗 Queued action {action_id} for {unit_id}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error queuing action: {e}")
            return False
    
    def _handle_remove_action(self, unit_id: str, action_index: int) -> bool:
        """Handle remove action request from UI."""
        try:
            success = self.action_manager.remove_unit_action(unit_id, action_index)
            if success:
                print(f"🔗 Removed action {action_index} from {unit_id}")
            return success
        except Exception as e:
            print(f"❌ Error removing action: {e}")
            return False
    
    def _handle_reorder_actions(self, unit_id: str, new_order: List[int]) -> bool:
        """Handle action reordering request from UI."""
        try:
            self.action_manager.reorder_unit_actions(unit_id, new_order)
            print(f"🔗 Reordered actions for {unit_id}: {new_order}")
            return True
        except Exception as e:
            print(f"❌ Error reordering actions: {e}")
            return False
    
    def _handle_preview_action(self, action_id: str, caster_id: str, target_ids: List[str]):
        """Handle action preview request from UI."""
        self.show_action_preview(action_id, caster_id, target_ids)
    
    def _handle_select_unit(self, unit_id: str):
        """Handle unit selection from UI."""
        self.create_unit_panel(unit_id)
        
        # Emit unit selection event
        if hasattr(self.game_controller, 'event_bus') and self.game_controller.event_bus:
            self.game_controller.event_bus.emit('unit_selected', {'unit_id': unit_id})
    
    def _handle_change_theme(self, theme: str):
        """Handle theme change request from UI."""
        try:
            theme_enum = UITheme(theme)
            if self.queue_ui_manager:
                self.queue_ui_manager.set_theme(theme_enum)
            print(f"🔗 Changed UI theme to {theme}")
        except Exception as e:
            print(f"❌ Error changing theme: {e}")
    
    def handle_user_interaction(self, interaction_type: str, **kwargs) -> Any:
        """Handle user interaction from UI."""
        handler = self.interaction_callbacks.get(interaction_type)
        if handler:
            return handler(**kwargs)
        else:
            print(f"⚠️ Unknown interaction type: {interaction_type}")
            return None
    
    def get_ui_status(self) -> Dict[str, Any]:
        """Get current UI integration status."""
        return {
            'initialized': self.is_initialized,
            'auto_update_enabled': self.config.auto_update_enabled,
            'predictions_enabled': self.config.enable_predictions,
            'ai_displays_enabled': self.config.enable_ai_displays,
            'theme': self.config.theme.value,
            'last_update': self.last_ui_update,
            'event_subscriptions': len(self.event_subscriptions),
            'queue_ui_active': self.queue_ui_manager is not None and self.queue_ui_manager.is_active
        }
    
    def shutdown(self):
        """Shutdown UI integration."""
        self.is_initialized = False
        
        # Unsubscribe from events
        if hasattr(self.game_controller, 'event_bus') and self.game_controller.event_bus:
            for subscription in self.event_subscriptions:
                try:
                    self.game_controller.event_bus.unsubscribe(subscription)
                except:
                    pass
        
        # Shutdown UI components
        if self.queue_ui_manager:
            self.queue_ui_manager.shutdown()
        
        if self.prediction_widget:
            self.prediction_widget.destroy()
        
        print("🔗 UI Integration shut down")


def create_integrated_ui(action_manager: ActionManager, 
                        config: Optional[UIIntegrationConfig] = None,
                        ui_parent=None) -> Optional[ActionManagerUIBridge]:
    """
    Create and initialize integrated queue management UI.
    
    Args:
        action_manager: ActionManager instance to integrate with
        config: UI integration configuration
        ui_parent: Parent entity for UI (optional)
        
    Returns:
        ActionManagerUIBridge instance or None if failed
    """
    if not FeatureFlags.USE_NEW_QUEUE_UI:
        print("🔗 Queue UI creation skipped - disabled by feature flags")
        return None
    
    if config is None:
        config = UIIntegrationConfig()
    
    try:
        bridge = ActionManagerUIBridge(action_manager, config)
        success = bridge.initialize(ui_parent)
        
        if success:
            print("🔗 Integrated queue management UI created successfully")
            return bridge
        else:
            print("❌ Failed to create integrated UI")
            return None
            
    except Exception as e:
        print(f"❌ Error creating integrated UI: {e}")
        return None