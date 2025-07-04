"""
MCP Tools for AI Agent Integration

Provides standardized tool interfaces for LLM-powered AI agents to control units
and make tactical decisions. Each tool corresponds to a specific game action
that AI agents can perform.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import json

from game.managers.action_manager import ActionManager
from game.actions.action_system import ActionType
from game.queue.action_queue import ActionPriority
from game.config.feature_flags import FeatureFlags


@dataclass
class ToolResult:
    """Standardized result format for MCP tools."""
    success: bool
    data: Any = None
    error_message: str = ""
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms
        }


class MCPToolError(Exception):
    """Exception for MCP tool failures."""
    pass


class GameStateTool:
    """Tool for AI agents to query current game state."""
    
    def __init__(self, action_manager: ActionManager):
        self.action_manager = action_manager
        self.game_controller = action_manager.game_controller
    
    def get_battlefield_state(self) -> ToolResult:
        """
        Get complete battlefield state for AI decision making.
        
        Returns:
            ToolResult with battlefield data including units, positions, and status
        """
        try:
            units_data = []
            
            # Get all units
            for unit_id, unit in self.game_controller.units.items():
                unit_data = {
                    'id': unit_id,
                    'name': getattr(unit, 'name', unit_id),
                    'hp': getattr(unit, 'hp', 0),
                    'max_hp': getattr(unit, 'max_hp', 0),
                    'mp': getattr(unit, 'mp', 0),
                    'max_mp': getattr(unit, 'max_mp', 0),
                    'ap': getattr(unit, 'ap', 0),
                    'max_ap': getattr(unit, 'max_ap', 0),
                    'position': {
                        'x': getattr(unit, 'x', 0),
                        'y': getattr(unit, 'y', 0)
                    },
                    'alive': getattr(unit, 'alive', True),
                    'team': 'player' if unit_id in [u.id for u in self.game_controller.player_units] else 'enemy'
                }
                units_data.append(unit_data)
            
            battlefield_data = {
                'units': units_data,
                'turn': getattr(self.game_controller, 'current_turn', 0),
                'battle_state': getattr(self.game_controller, 'battle_state', 'active'),
                'grid_size': {'width': 10, 'height': 10}  # Default grid size
            }
            
            return ToolResult(success=True, data=battlefield_data)
            
        except Exception as e:
            return ToolResult(success=False, error_message=f"Failed to get battlefield state: {e}")
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get current game state for AI analysis."""
        try:
            state = {
                'units': [],
                'battlefield': {
                    'width': getattr(getattr(self.game_controller, 'grid', None), 'width', 10),
                    'height': getattr(getattr(self.game_controller, 'grid', None), 'height', 10)
                },
                'turn': getattr(self.game_controller, 'current_turn', 0),
                'battle_state': getattr(self.game_controller, 'battle_state', 'active')
            }
            
            # Add units
            units = getattr(self.game_controller, 'units', {})
            if isinstance(units, dict):
                for unit_id, unit in units.items():
                    state['units'].append({
                        'id': unit_id,
                        'name': getattr(unit, 'name', unit_id),
                        'x': getattr(unit, 'x', 0),
                        'y': getattr(unit, 'y', 0),
                        'hp': getattr(unit, 'hp', 100),
                        'team': getattr(unit, 'team', 'unknown')
                    })
            
            return state
            
        except Exception as e:
            return {'error': f"Failed to get game state: {e}"}
    
    def get_unit_details(self, unit_id: str) -> ToolResult:
        """
        Get detailed information about a specific unit.
        
        Args:
            unit_id: ID of unit to query
            
        Returns:
            ToolResult with detailed unit information
        """
        try:
            unit = self.game_controller.units.get(unit_id)
            if not unit:
                return ToolResult(success=False, error_message=f"Unit {unit_id} not found")
            
            # Get available actions for this unit
            available_actions = self.action_manager.get_available_actions_for_unit(unit_id)
            
            # Get queued actions
            queued_actions = self.action_manager.get_unit_queue_preview(unit_id)
            
            unit_details = {
                'id': unit_id,
                'name': getattr(unit, 'name', unit_id),
                'stats': {
                    'hp': getattr(unit, 'hp', 0),
                    'max_hp': getattr(unit, 'max_hp', 0),
                    'mp': getattr(unit, 'mp', 0),
                    'max_mp': getattr(unit, 'max_mp', 0),
                    'ap': getattr(unit, 'ap', 0),
                    'max_ap': getattr(unit, 'max_ap', 0),
                    'initiative': getattr(unit, 'initiative', 50),
                    'physical_defense': getattr(unit, 'physical_defense', 0),
                    'magical_defense': getattr(unit, 'magical_defense', 0),
                    'spiritual_defense': getattr(unit, 'spiritual_defense', 0)
                },
                'position': {
                    'x': getattr(unit, 'x', 0),
                    'y': getattr(unit, 'y', 0)
                },
                'status': {
                    'alive': getattr(unit, 'alive', True),
                    'cooldowns': getattr(unit, 'action_cooldowns', {})
                },
                'available_actions': available_actions,
                'queued_actions': queued_actions
            }
            
            return ToolResult(success=True, data=unit_details)
            
        except Exception as e:
            return ToolResult(success=False, error_message=f"Failed to get unit details: {e}")


class ActionExecutionTool:
    """Tool for AI agents to execute unit actions."""
    
    def __init__(self, action_manager: ActionManager):
        self.action_manager = action_manager
    
    def queue_unit_action(self, unit_id: str, action_id: str, target_positions: List[Dict[str, int]], 
                         priority: str = "NORMAL", prediction: str = "") -> ToolResult:
        """
        Queue an action for a unit.
        
        Args:
            unit_id: ID of unit to perform action
            action_id: ID of action to perform
            target_positions: List of target positions [{x: int, y: int}]
            priority: Action priority ("HIGH", "NORMAL", "LOW")
            prediction: AI's prediction about action outcome for bonus points
            
        Returns:
            ToolResult indicating success/failure
        """
        try:
            # Convert priority string to enum
            priority_map = {
                "HIGH": ActionPriority.HIGH,
                "NORMAL": ActionPriority.NORMAL,
                "LOW": ActionPriority.LOW,
                "IMMEDIATE": ActionPriority.IMMEDIATE,
                "CLEANUP": ActionPriority.CLEANUP
            }
            
            action_priority = priority_map.get(priority.upper(), ActionPriority.NORMAL)
            
            # Convert positions to target objects (simplified for now)
            targets = []
            for pos in target_positions:
                # In a real implementation, this would resolve positions to actual targets
                targets.append(pos)
            
            # Queue the action
            success = self.action_manager.queue_action(
                unit_id=unit_id,
                action_id=action_id,
                targets=targets,
                priority=action_priority,
                player_prediction=prediction
            )
            
            if success:
                return ToolResult(success=True, data={
                    'action_queued': True,
                    'unit_id': unit_id,
                    'action_id': action_id,
                    'targets': len(targets),
                    'priority': priority
                })
            else:
                return ToolResult(success=False, error_message="Failed to queue action")
                
        except Exception as e:
            return ToolResult(success=False, error_message=f"Action execution failed: {e}")
    
    def execute_immediate_action(self, unit_id: str, action_id: str, 
                                target_positions: List[Dict[str, int]]) -> ToolResult:
        """
        Execute an action immediately without queuing.
        
        Args:
            unit_id: ID of unit to perform action
            action_id: ID of action to perform
            target_positions: List of target positions
            
        Returns:
            ToolResult with execution results
        """
        try:
            # Convert positions to targets (simplified)
            targets = target_positions
            
            # Execute immediately
            result = self.action_manager.execute_action_immediately(unit_id, action_id, targets)
            
            return ToolResult(success=result['success'], data=result)
            
        except Exception as e:
            return ToolResult(success=False, error_message=f"Immediate action failed: {e}")
    
    def cancel_unit_action(self, unit_id: str, action_index: int) -> ToolResult:
        """
        Cancel a queued action for a unit.
        
        Args:
            unit_id: ID of unit
            action_index: Index of action to cancel
            
        Returns:
            ToolResult indicating success/failure
        """
        try:
            success = self.action_manager.remove_unit_action(unit_id, action_index)
            
            return ToolResult(success=success, data={
                'action_cancelled': success,
                'unit_id': unit_id,
                'action_index': action_index
            })
            
        except Exception as e:
            return ToolResult(success=False, error_message=f"Action cancellation failed: {e}")


class TacticalAnalysisTool:
    """Tool for AI agents to perform tactical analysis."""
    
    def __init__(self, action_manager: ActionManager):
        self.action_manager = action_manager
        self.game_controller = action_manager.game_controller
    
    def analyze_action_outcomes(self, unit_id: str, action_id: str, 
                              target_positions: List[Dict[str, int]]) -> ToolResult:
        """
        Analyze potential outcomes of an action without executing it.
        
        Args:
            unit_id: ID of unit that would perform action
            action_id: ID of action to analyze
            target_positions: Potential target positions
            
        Returns:
            ToolResult with analysis data
        """
        try:
            # Get action preview
            targets = target_positions  # Simplified
            preview = self.action_manager.get_action_preview(unit_id, action_id, targets)
            
            if 'error' in preview:
                return ToolResult(success=False, error_message=preview['error'])
            
            # Add tactical analysis
            analysis = {
                'action_preview': preview,
                'resource_costs': preview.get('costs', {}),
                'estimated_effects': preview.get('effect_previews', []),
                'tactical_assessment': self._assess_action_value(unit_id, action_id, targets)
            }
            
            return ToolResult(success=True, data=analysis)
            
        except Exception as e:
            return ToolResult(success=False, error_message=f"Analysis failed: {e}")
    
    def get_timeline_preview(self) -> ToolResult:
        """
        Get preview of action execution timeline for tactical planning.
        
        Returns:
            ToolResult with timeline data
        """
        try:
            # Get unit stats for timeline calculation
            unit_stats = {}
            for unit_id, unit in self.game_controller.units.items():
                unit_stats[unit_id] = {
                    'initiative': getattr(unit, 'initiative', 50)
                }
            
            timeline = self.action_manager.get_action_queue_preview(unit_stats)
            
            return ToolResult(success=True, data={
                'timeline': timeline,
                'total_actions': len(timeline)
            })
            
        except Exception as e:
            return ToolResult(success=False, error_message=f"Timeline preview failed: {e}")
    
    def calculate_threat_assessment(self, unit_id: str) -> ToolResult:
        """
        Calculate threat level for a specific unit.
        
        Args:
            unit_id: ID of unit to assess
            
        Returns:
            ToolResult with threat assessment
        """
        try:
            unit = self.game_controller.units.get(unit_id)
            if not unit:
                return ToolResult(success=False, error_message=f"Unit {unit_id} not found")
            
            # Calculate basic threat metrics
            hp_percentage = getattr(unit, 'hp', 0) / max(getattr(unit, 'max_hp', 1), 1)
            mp_percentage = getattr(unit, 'mp', 0) / max(getattr(unit, 'max_mp', 1), 1)
            
            # Count available offensive actions
            available_actions = self.action_manager.get_available_actions_for_unit(unit_id)
            offensive_actions = [a for a in available_actions if a['type'] in ['Attack', 'Magic']]
            
            threat_level = len(offensive_actions) * hp_percentage * (1 + mp_percentage)
            
            assessment = {
                'unit_id': unit_id,
                'threat_level': threat_level,
                'hp_percentage': hp_percentage,
                'mp_percentage': mp_percentage,
                'offensive_actions_available': len(offensive_actions),
                'threat_category': 'HIGH' if threat_level > 2 else 'MEDIUM' if threat_level > 1 else 'LOW'
            }
            
            return ToolResult(success=True, data=assessment)
            
        except Exception as e:
            return ToolResult(success=False, error_message=f"Threat assessment failed: {e}")
    
    def _assess_action_value(self, unit_id: str, action_id: str, targets: List[Any]) -> Dict[str, Any]:
        """Internal method to assess tactical value of an action."""
        # Simplified tactical assessment
        action = self.action_manager.action_registry.get(action_id)
        if not action:
            return {'value': 0, 'reason': 'Action not found'}
        
        # Basic assessment based on action type and targets
        base_value = 1.0
        
        if action.type == ActionType.ATTACK:
            base_value = 1.5
        elif action.type == ActionType.MAGIC:
            base_value = 2.0
        elif action.type == ActionType.SPIRIT:
            base_value = 1.8
        
        # Modify based on number of targets
        target_modifier = len(targets) * 0.5
        
        total_value = base_value + target_modifier
        
        return {
            'tactical_value': total_value,
            'base_value': base_value,
            'target_modifier': target_modifier,
            'recommendation': 'EXECUTE' if total_value > 1.5 else 'CONSIDER' if total_value > 1.0 else 'AVOID'
        }


class MCPToolRegistry:
    """Registry for managing all MCP tools available to AI agents."""
    
    def __init__(self, action_manager: ActionManager):
        self.action_manager = action_manager
        
        # Initialize tools
        self.game_state_tool = GameStateTool(action_manager)
        self.action_tool = ActionExecutionTool(action_manager)
        self.analysis_tool = TacticalAnalysisTool(action_manager)
        
        # Tool registry for easy access
        self.tools = {
            'get_battlefield_state': self.game_state_tool.get_battlefield_state,
            'get_unit_details': self.game_state_tool.get_unit_details,
            'queue_unit_action': self.action_tool.queue_unit_action,
            'execute_immediate_action': self.action_tool.execute_immediate_action,
            'cancel_unit_action': self.action_tool.cancel_unit_action,
            'analyze_action_outcomes': self.analysis_tool.analyze_action_outcomes,
            'get_timeline_preview': self.analysis_tool.get_timeline_preview,
            'calculate_threat_assessment': self.analysis_tool.calculate_threat_assessment
        }
    
    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name with arguments.
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Arguments for the tool
            
        Returns:
            ToolResult from tool execution
        """
        if not FeatureFlags.USE_MCP_TOOLS:
            return ToolResult(success=False, error_message="MCP tools disabled by feature flags")
        
        tool_function = self.tools.get(tool_name)
        if not tool_function:
            return ToolResult(success=False, error_message=f"Unknown tool: {tool_name}")
        
        try:
            import time
            start_time = time.time()
            
            result = tool_function(**kwargs)
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            result.execution_time_ms = execution_time
            
            return result
            
        except Exception as e:
            return ToolResult(success=False, error_message=f"Tool execution failed: {e}")
    
    def list_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())
    
    def get_tool_documentation(self, tool_name: str) -> Optional[str]:
        """Get documentation for a specific tool."""
        tool_docs = {
            'get_battlefield_state': 'Get complete battlefield state including all units and positions',
            'get_unit_details': 'Get detailed information about a specific unit',
            'queue_unit_action': 'Queue an action for a unit to execute during turn resolution',
            'execute_immediate_action': 'Execute an action immediately without queuing',
            'cancel_unit_action': 'Cancel a previously queued action',
            'analyze_action_outcomes': 'Analyze potential outcomes of an action without executing',
            'get_timeline_preview': 'Get preview of action execution timeline',
            'calculate_threat_assessment': 'Calculate threat level of a unit'
        }
        
        return tool_docs.get(tool_name)