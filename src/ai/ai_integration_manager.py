"""
AI Integration Manager

Integrates the AI agent system with the existing ActionManager and game controller.
Provides the bridge between AI decision making and game action execution.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
import time

from ai.orchestration_agent import OrchestrationAgent
from ai.unit_ai_controller import UnitAIController, AIPersonality, AISkillLevel
from ai.mcp_tools import MCPToolRegistry
from game.managers.action_manager import ActionManager
from game.config.feature_flags import FeatureFlags
from game.queue.action_queue import ActionPriority


@dataclass
class AIUnitConfig:
    """Configuration for AI-controlled units."""
    unit_id: str
    personality: AIPersonality = AIPersonality.BALANCED
    skill_level: AISkillLevel = AISkillLevel.STRATEGIC
    is_leader: bool = False
    coordination_priority: int = 0  # Higher = acts earlier in coordination


class AIIntegrationManager:
    """
    Manages integration between AI agents and the game action system.
    
    Responsibilities:
    - Bridge AI decisions to ActionManager
    - Coordinate AI unit behaviors
    - Provide AI access to game state
    - Manage AI performance and difficulty scaling
    """
    
    def __init__(self, action_manager: ActionManager):
        self.action_manager = action_manager
        self.game_controller = action_manager.game_controller
        
        # AI system components
        self.orchestration_agent = OrchestrationAgent(action_manager)
        self.tool_registry = MCPToolRegistry(action_manager)
        
        # AI unit management
        self.ai_controlled_units: Set[str] = set()
        self.unit_controllers: Dict[str, UnitAIController] = {}
        self.unit_configs: Dict[str, AIUnitConfig] = {}
        
        # AI turn management
        self.ai_turn_active = False
        self.current_ai_decisions: Dict[str, Any] = {}
        
        # Performance tracking
        self.ai_performance = {
            'total_ai_turns': 0,
            'average_turn_time_ms': 0.0,
            'successful_actions': 0,
            'failed_actions': 0,
            'coordination_efficiency': 0.0
        }
        
        # Initialize integration
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self):
        """Set up event subscriptions for AI integration."""
        if hasattr(self.game_controller, 'event_bus') and self.game_controller.event_bus:
            event_bus = self.game_controller.event_bus
            
            # Subscribe to relevant game events
            event_bus.subscribe("turn_started", self._on_turn_started)
            event_bus.subscribe("ai_turn_requested", self._on_ai_turn_requested)
            event_bus.subscribe("action_executed", self._on_action_executed)
            event_bus.subscribe("unit_defeated", self._on_unit_defeated)
    
    def register_ai_unit(self, unit_id: str, config: Optional[AIUnitConfig] = None) -> bool:
        """
        Register a unit for AI control.
        
        Args:
            unit_id: ID of unit to control with AI
            config: AI configuration for the unit
            
        Returns:
            True if registration successful
        """
        if not FeatureFlags.USE_MCP_TOOLS:
            print(f"⚠️ MCP tools disabled - cannot register AI unit {unit_id}")
            return False
        
        # Use default config if none provided
        if config is None:
            config = AIUnitConfig(unit_id=unit_id)
        
        # Verify unit exists
        if unit_id not in self.game_controller.units:
            print(f"❌ Unit {unit_id} not found - cannot register for AI control")
            return False
        
        # Create unit AI controller
        unit_controller = UnitAIController(
            unit_id=unit_id,
            tool_registry=self.tool_registry,
            personality=config.personality,
            skill_level=config.skill_level
        )
        
        # Register with systems
        self.ai_controlled_units.add(unit_id)
        self.unit_controllers[unit_id] = unit_controller
        self.unit_configs[unit_id] = config
        
        # Register with orchestration agent
        self.orchestration_agent.register_unit_controller(unit_id)
        
        print(f"🤖 Registered AI control for {unit_id} ({config.personality.value}, {config.skill_level.value})")
        return True
    
    def unregister_ai_unit(self, unit_id: str):
        """Remove a unit from AI control."""
        if unit_id in self.ai_controlled_units:
            self.ai_controlled_units.remove(unit_id)
            self.unit_controllers.pop(unit_id, None)
            self.unit_configs.pop(unit_id, None)
            print(f"🔄 Removed AI control for {unit_id}")
    
    def execute_ai_turn(self, enemy_unit_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute AI turn for all AI-controlled units.
        
        Args:
            enemy_unit_ids: Specific units to control, or None for all AI units
            
        Returns:
            Results of AI turn execution
        """
        if not FeatureFlags.USE_MCP_TOOLS:
            return {'success': False, 'error': 'MCP tools disabled'}
        
        start_time = time.time()
        
        # Determine which units to control
        if enemy_unit_ids is None:
            controlled_units = list(self.ai_controlled_units)
        else:
            controlled_units = [uid for uid in enemy_unit_ids if uid in self.ai_controlled_units]
        
        if not controlled_units:
            return {'success': True, 'message': 'No AI units to control'}
        
        try:
            self.ai_turn_active = True
            
            # Execute coordinated AI turn
            coordination_result = self.orchestration_agent.execute_ai_turn_sync(controlled_units)
            
            if not coordination_result['success']:
                return coordination_result
            
            # Execute the planned actions
            execution_results = self._execute_ai_planned_actions(coordination_result)
            
            # Update performance metrics
            turn_time = (time.time() - start_time) * 1000
            self._update_ai_performance(turn_time, execution_results)
            
            return {
                'success': True,
                'coordination_result': coordination_result,
                'execution_results': execution_results,
                'turn_time_ms': turn_time,
                'units_controlled': len(controlled_units)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'AI turn execution failed: {e}',
                'turn_time_ms': (time.time() - start_time) * 1000
            }
        finally:
            self.ai_turn_active = False
    
    def _execute_ai_planned_actions(self, coordination_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actions planned by AI coordination."""
        if 'unit_actions' not in coordination_result:
            return {'success': False, 'error': 'No unit actions in coordination result'}
        
        unit_actions = coordination_result['unit_actions']
        execution_results = {}
        
        for unit_id, action_plan in unit_actions.items():
            if 'planned_actions' not in action_plan:
                continue
            
            unit_results = []
            
            for planned_action in action_plan['planned_actions']:
                # Extract action details
                action_id = planned_action.get('action_id')
                target_id = planned_action.get('target_id', 'nearest_enemy')
                priority = planned_action.get('priority', 'NORMAL')
                
                if not action_id:
                    continue
                
                # Convert target_id to position (simplified)
                target_positions = self._resolve_target_positions(target_id, unit_id)
                
                # Queue the action
                success = self._queue_ai_action(unit_id, action_id, target_positions, priority)
                
                unit_results.append({
                    'action_id': action_id,
                    'target': target_id,
                    'queued': success,
                    'reasoning': planned_action.get('reasoning', 'AI decision')
                })
            
            execution_results[unit_id] = unit_results
        
        return execution_results
    
    def _queue_ai_action(self, unit_id: str, action_id: str, 
                        target_positions: List[Dict[str, int]], priority_str: str) -> bool:
        """Queue an AI-planned action through the ActionManager."""
        try:
            # Convert priority string to enum
            priority_map = {
                'HIGH': ActionPriority.HIGH,
                'NORMAL': ActionPriority.NORMAL,
                'LOW': ActionPriority.LOW,
                'IMMEDIATE': ActionPriority.IMMEDIATE
            }
            
            priority = priority_map.get(priority_str.upper(), ActionPriority.NORMAL)
            
            # Use ActionManager to queue the action
            success = self.action_manager.queue_action(
                unit_id=unit_id,
                action_id=action_id,
                targets=target_positions,  # Simplified - in real implementation would resolve to actual targets
                priority=priority,
                player_prediction=f"AI decision for {unit_id}"
            )
            
            if success:
                print(f"🎯 AI queued action: {action_id} for {unit_id}")
            else:
                print(f"❌ AI failed to queue action: {action_id} for {unit_id}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error queuing AI action: {e}")
            return False
    
    def _resolve_target_positions(self, target_id: str, acting_unit_id: str) -> List[Dict[str, int]]:
        """Resolve target ID to actual positions."""
        # Simplified target resolution
        if target_id == 'nearest_enemy':
            # Find nearest player unit
            acting_unit = self.game_controller.units.get(acting_unit_id)
            if not acting_unit:
                return [{'x': 0, 'y': 0}]
            
            player_units = [u for u in self.game_controller.units.values() 
                          if getattr(u, 'id', '') in [pu.id for pu in self.game_controller.player_units]]
            
            if player_units:
                # Return position of first player unit (simplified)
                target_unit = player_units[0]
                return [{'x': getattr(target_unit, 'x', 0), 'y': getattr(target_unit, 'y', 0)}]
        
        elif target_id in self.game_controller.units:
            # Specific unit target
            target_unit = self.game_controller.units[target_id]
            return [{'x': getattr(target_unit, 'x', 0), 'y': getattr(target_unit, 'y', 0)}]
        
        # Default position
        return [{'x': 0, 'y': 0}]
    
    def get_ai_controlled_units(self) -> List[str]:
        """Get list of AI-controlled unit IDs."""
        return list(self.ai_controlled_units)
    
    def get_ai_unit_status(self, unit_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific AI-controlled unit."""
        if unit_id not in self.ai_controlled_units:
            return None
        
        config = self.unit_configs.get(unit_id)
        controller = self.unit_controllers.get(unit_id)
        
        status = {
            'unit_id': unit_id,
            'ai_controlled': True,
            'personality': config.personality.value if config else 'unknown',
            'skill_level': config.skill_level.value if config else 'unknown',
            'is_leader': config.is_leader if config else False
        }
        
        if controller:
            status.update(controller.get_performance_summary())
        
        return status
    
    def get_ai_system_status(self) -> Dict[str, Any]:
        """Get overall AI system status."""
        return {
            'ai_enabled': FeatureFlags.USE_MCP_TOOLS,
            'controlled_units': len(self.ai_controlled_units),
            'unit_controllers': len(self.unit_controllers),
            'ai_turn_active': self.ai_turn_active,
            'orchestration_status': self.orchestration_agent.get_orchestration_status(),
            'performance_metrics': self.ai_performance
        }
    
    def adjust_ai_difficulty(self, difficulty_modifier: float):
        """
        Adjust AI difficulty by modifying skill levels and decision quality.
        
        Args:
            difficulty_modifier: 0.5 = easier, 1.0 = normal, 1.5 = harder
        """
        for unit_id, controller in self.unit_controllers.items():
            # Adjust decision time limits
            if hasattr(controller, 'decision_time_limit'):
                base_time = 100.0  # Base decision time in ms
                controller.decision_time_limit = base_time / difficulty_modifier
            
            # Could adjust other parameters like risk tolerance, tactical awareness, etc.
        
        print(f"🎚️ AI difficulty adjusted: {difficulty_modifier}x")
    
    def _update_ai_performance(self, turn_time_ms: float, execution_results: Dict[str, Any]):
        """Update AI performance metrics."""
        self.ai_performance['total_ai_turns'] += 1
        
        # Update average turn time
        current_avg = self.ai_performance['average_turn_time_ms']
        total_turns = self.ai_performance['total_ai_turns']
        new_avg = ((current_avg * (total_turns - 1)) + turn_time_ms) / total_turns
        self.ai_performance['average_turn_time_ms'] = new_avg
        
        # Count successful/failed actions
        for unit_results in execution_results.values():
            for action_result in unit_results:
                if action_result.get('queued', False):
                    self.ai_performance['successful_actions'] += 1
                else:
                    self.ai_performance['failed_actions'] += 1
    
    # Event handlers
    def _on_turn_started(self, event_data):
        """Handle turn start event."""
        if self.ai_controlled_units:
            print(f"🎮 Turn started - {len(self.ai_controlled_units)} AI units ready")
    
    def _on_ai_turn_requested(self, event_data):
        """Handle AI turn request event."""
        unit_ids = event_data.get('unit_ids', None)
        result = self.execute_ai_turn(unit_ids)
        
        # Emit result event
        if hasattr(self.game_controller, 'event_bus') and self.game_controller.event_bus:
            self.game_controller.event_bus.emit('ai_turn_completed', result)
    
    def _on_action_executed(self, event_data):
        """Handle action execution event."""
        # Update AI unit performance if this was an AI action
        # Implementation would track AI action success rates
        pass
    
    def _on_unit_defeated(self, event_data):
        """Handle unit defeat event."""
        unit_id = event_data.get('unit_id')
        if unit_id in self.ai_controlled_units:
            print(f"💀 AI unit {unit_id} defeated")
            # Could trigger tactical adjustments for remaining AI units
    
    def shutdown(self):
        """Shutdown AI integration system."""
        self.orchestration_agent.shutdown()
        self.ai_controlled_units.clear()
        self.unit_controllers.clear()
        self.unit_configs.clear()
        print("🔄 AI Integration Manager shut down")