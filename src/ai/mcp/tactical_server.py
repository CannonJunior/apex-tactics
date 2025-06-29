"""
Tactical MCP Server

MCP server providing tactical analysis and decision-making tools for AI agents.
Implements basic tools required for Phase 1 foundation.
"""

import json
import time
from typing import Dict, Any, Optional, List

try:
    from fastmcp import FastMCP
except ImportError:
    # Graceful fallback if FastMCP is not available
    print("Warning: FastMCP not available. MCP server will be disabled.")
    FastMCP = None

from core.ecs.world import World
from core.ecs.entity import Entity
from core.math.vector import Vector3, Vector2Int
from core.utils.logging import Logger
from .tactical_ai_tools import TacticalAITools

class TacticalMCPServer:
    """
    MCP server for tactical AI operations.
    
    Provides tools for battlefield analysis, unit evaluation,
    and tactical decision making for AI agents.
    """
    
    def __init__(self, world: World, port: int = 8765):
        self.world = world
        self.port = port
        self.mcp_server = None
        self.running = False
        
        # Initialize advanced AI tools
        self.ai_tools = TacticalAITools(world)
        
        if FastMCP is not None:
            self.mcp_server = FastMCP("TacticalRPG_AI_Server")
            self._register_tools()
            self._register_resources()
        else:
            Logger.warning("FastMCP not available - MCP server disabled")
    
    def _register_tools(self):
        """Register MCP tools for tactical operations"""
        if self.mcp_server is None:
            return
        
        @self.mcp_server.tool
        def analyze_tactical_situation(unit_id: str) -> Dict[str, Any]:
            """
            Comprehensive battlefield analysis for AI decision-making.
            
            Args:
                unit_id: ID of unit to analyze situation for
                
            Returns:
                Tactical analysis including position value, threats, opportunities
            """
            try:
                entity = self.world.get_entity(unit_id)
                if not entity:
                    return {
                        "success": False,
                        "error": f"Unit {unit_id} not found"
                    }
                
                # Basic analysis - will be expanded as systems develop
                from core.ecs.component import Transform
                transform = entity.get_component(Transform)
                
                analysis = {
                    "success": True,
                    "unit_id": unit_id,
                    "position": transform.position.to_dict() if transform else None,
                    "timestamp": time.time(),
                    "analysis": {
                        "position_value": self._calculate_position_value(entity),
                        "threat_assessment": self._analyze_threats(entity),
                        "action_opportunities": self._evaluate_opportunities(entity),
                        "resource_status": self._get_resource_status(entity)
                    }
                }
                
                return analysis
                
            except Exception as e:
                Logger.error(f"Error in analyze_tactical_situation: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp_server.tool
        def execute_complex_action(unit_id: str, action_type: str, 
                                  parameters: Dict[str, Any]) -> Dict[str, Any]:
            """
            Execute tactical actions with full validation and feedback.
            
            Args:
                unit_id: ID of unit performing action
                action_type: Type of action to execute
                parameters: Action-specific parameters
                
            Returns:
                Execution result with success status and details
            """
            try:
                entity = self.world.get_entity(unit_id)
                if not entity:
                    return {
                        "success": False,
                        "error": f"Unit {unit_id} not found"
                    }
                
                # Basic action execution - will be expanded with combat system
                result = {
                    "success": True,
                    "unit_id": unit_id,
                    "action_type": action_type,
                    "parameters": parameters,
                    "timestamp": time.time(),
                    "result": "Action queued for execution"  # Placeholder
                }
                
                Logger.info(f"Action executed: {action_type} for unit {unit_id}")
                return result
                
            except Exception as e:
                Logger.error(f"Error in execute_complex_action: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        # Advanced AI tools
        @self.mcp_server.tool
        def analyze_battlefield_comprehensive(grid_width: int = 8, grid_height: int = 8) -> Dict[str, Any]:
            """
            Perform comprehensive battlefield analysis using advanced AI.
            
            Args:
                grid_width: Width of tactical grid
                grid_height: Height of tactical grid
                
            Returns:
                Comprehensive tactical analysis with recommendations
            """
            try:
                # Get all units from world
                all_units = list(self.world.get_all_entities())
                
                # Perform analysis using AI tools
                analysis = self.ai_tools.analyze_battlefield(all_units, (grid_width, grid_height))
                
                return {
                    "success": True,
                    "analysis": {
                        "unit_count": analysis.unit_count,
                        "average_power": analysis.average_power,
                        "formation_strength": analysis.formation_strength,
                        "terrain_advantage": analysis.terrain_advantage,
                        "recommended_action": analysis.recommended_action,
                        "confidence": analysis.confidence,
                        "threat_assessment": analysis.threat_assessment
                    },
                    "timestamp": time.time()
                }
                
            except Exception as e:
                Logger.error(f"Error in analyze_battlefield_comprehensive: {e}")
                return {"success": False, "error": str(e)}
        
        @self.mcp_server.tool
        def evaluate_unit_detailed(unit_id: str) -> Dict[str, Any]:
            """
            Detailed unit evaluation using advanced AI analysis.
            
            Args:
                unit_id: ID of unit to evaluate
                
            Returns:
                Detailed unit evaluation with tactical recommendations
            """
            try:
                entity = self.world.get_entity(unit_id)
                if not entity:
                    return {"success": False, "error": f"Unit {unit_id} not found"}
                
                all_units = list(self.world.get_all_entities())
                evaluation = self.ai_tools.evaluate_unit(entity, all_units)
                
                return {
                    "success": True,
                    "evaluation": {
                        "unit_id": evaluation.unit_id,
                        "combat_effectiveness": evaluation.combat_effectiveness,
                        "positioning_score": evaluation.positioning_score,
                        "threat_level": evaluation.threat_level,
                        "tactical_value": evaluation.tactical_value,
                        "recommended_role": evaluation.recommended_role
                    },
                    "timestamp": time.time()
                }
                
            except Exception as e:
                Logger.error(f"Error in evaluate_unit_detailed: {e}")
                return {"success": False, "error": str(e)}
        
        @self.mcp_server.tool
        def find_optimal_position_ai(unit_id: str, grid_width: int = 8, grid_height: int = 8) -> Dict[str, Any]:
            """
            Find optimal position for unit using AI tactical analysis.
            
            Args:
                unit_id: ID of unit to position
                grid_width: Width of tactical grid
                grid_height: Height of tactical grid
                
            Returns:
                Optimal position recommendation
            """
            try:
                entity = self.world.get_entity(unit_id)
                if not entity:
                    return {"success": False, "error": f"Unit {unit_id} not found"}
                
                all_units = list(self.world.get_all_entities())
                optimal_pos = self.ai_tools.find_optimal_position(entity, all_units, (grid_width, grid_height))
                
                if optimal_pos:
                    return {
                        "success": True,
                        "optimal_position": {
                            "x": optimal_pos.x,
                            "y": optimal_pos.y
                        },
                        "unit_id": unit_id,
                        "timestamp": time.time()
                    }
                else:
                    return {
                        "success": False,
                        "error": "No optimal position found",
                        "unit_id": unit_id
                    }
                
            except Exception as e:
                Logger.error(f"Error in find_optimal_position_ai: {e}")
                return {"success": False, "error": str(e)}
        
        @self.mcp_server.tool
        def select_optimal_target_ai(attacker_id: str) -> Dict[str, Any]:
            """
            Select optimal target using AI analysis.
            
            Args:
                attacker_id: ID of attacking unit
                
            Returns:
                Optimal target recommendation
            """
            try:
                attacker = self.world.get_entity(attacker_id)
                if not attacker:
                    return {"success": False, "error": f"Attacker {attacker_id} not found"}
                
                # Get potential targets (simplified - in full implementation would filter by team)
                all_units = list(self.world.get_all_entities())
                potential_targets = [unit for unit in all_units if unit.id != attacker_id]
                
                optimal_target = self.ai_tools.select_optimal_target(attacker, potential_targets)
                
                if optimal_target:
                    return {
                        "success": True,
                        "optimal_target": {
                            "unit_id": optimal_target.id
                        },
                        "attacker_id": attacker_id,
                        "timestamp": time.time()
                    }
                else:
                    return {
                        "success": False,
                        "error": "No valid target found",
                        "attacker_id": attacker_id
                    }
                
            except Exception as e:
                Logger.error(f"Error in select_optimal_target_ai: {e}")
                return {"success": False, "error": str(e)}
        
        @self.mcp_server.tool
        def plan_tactical_sequence_ai(turns: int = 3) -> Dict[str, Any]:
            """
            Plan multi-turn tactical sequence using AI.
            
            Args:
                turns: Number of turns to plan ahead
                
            Returns:
                Multi-turn tactical plan
            """
            try:
                all_units = list(self.world.get_all_entities())
                tactical_plan = self.ai_tools.plan_tactical_sequence(all_units, turns)
                
                return {
                    "success": True,
                    "tactical_plan": tactical_plan,
                    "turns_planned": turns,
                    "units_count": len(all_units),
                    "timestamp": time.time()
                }
                
            except Exception as e:
                Logger.error(f"Error in plan_tactical_sequence_ai: {e}")
                return {"success": False, "error": str(e)}
        
        @self.mcp_server.tool
        def evaluate_position_value(position_x: float, position_y: float, 
                                   position_z: float, unit_id: str = None) -> Dict[str, Any]:
            """
            Calculate tactical value of a battlefield position.
            
            Args:
                position_x: X coordinate of position
                position_y: Y coordinate of position  
                position_z: Z coordinate of position
                unit_id: Optional unit ID for context-specific evaluation
                
            Returns:
                Position evaluation with tactical metrics
            """
            try:
                position = Vector3(position_x, position_y, position_z)
                
                evaluation = {
                    "success": True,
                    "position": position.to_dict(),
                    "unit_id": unit_id,
                    "timestamp": time.time(),
                    "evaluation": {
                        "cover_value": self._calculate_cover_value(position),
                        "visibility": self._calculate_visibility(position),
                        "mobility": self._calculate_mobility_value(position),
                        "strategic_importance": self._calculate_strategic_value(position),
                        "overall_score": 0.5  # Placeholder calculation
                    }
                }
                
                return evaluation
                
            except Exception as e:
                Logger.error(f"Error in evaluate_position_value: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.mcp_server.tool
        def predict_battle_outcome(scenario_data: str) -> Dict[str, Any]:
            """
            Predict likely battle outcomes based on current state.
            
            Args:
                scenario_data: JSON string containing battle scenario
                
            Returns:
                Prediction analysis with probability estimates
            """
            try:
                scenario = json.loads(scenario_data)
                
                prediction = {
                    "success": True,
                    "scenario": scenario,
                    "timestamp": time.time(),
                    "prediction": {
                        "victory_probability": 0.5,  # Placeholder
                        "estimated_duration": 300,   # 5 minutes placeholder
                        "key_factors": [
                            "Unit positioning",
                            "Equipment advantages", 
                            "Tactical terrain"
                        ],
                        "recommended_strategy": "Maintain defensive positions"
                    }
                }
                
                return prediction
                
            except Exception as e:
                Logger.error(f"Error in predict_battle_outcome: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
    
    def _register_resources(self):
        """Register MCP resources for game state access"""
        if self.mcp_server is None:
            return
        
        @self.mcp_server.resource("tactical_state")
        def get_tactical_state() -> str:
            """Get current tactical battle state"""
            try:
                all_entities = self.world.get_all_entities()
                
                state = {
                    "timestamp": time.time(),
                    "entity_count": len(all_entities),
                    "world_stats": self.world.get_statistics(),
                    "units": []
                }
                
                # Add unit data (limited for now until more components exist)
                for entity in all_entities[:10]:  # Limit to first 10 for performance
                    from core.ecs.component import Transform
                    transform = entity.get_component(Transform)
                    
                    unit_data = {
                        "id": entity.id,
                        "active": entity.active,
                        "position": transform.position.to_dict() if transform else None,
                        "components": list(comp_type.__name__ for comp_type in entity.get_component_types())
                    }
                    state["units"].append(unit_data)
                
                return json.dumps(state)
                
            except Exception as e:
                Logger.error(f"Error getting tactical state: {e}")
                return json.dumps({"error": str(e)})
        
        @self.mcp_server.resource("unit_capabilities")
        def get_unit_capabilities() -> str:
            """Get available actions and abilities for units"""
            try:
                capabilities = {
                    "timestamp": time.time(),
                    "available_actions": [
                        "move",
                        "attack", 
                        "defend",
                        "wait"
                    ],
                    "ability_categories": [
                        "combat",
                        "movement",
                        "support"
                    ]
                }
                
                return json.dumps(capabilities)
                
            except Exception as e:
                Logger.error(f"Error getting unit capabilities: {e}")
                return json.dumps({"error": str(e)})
    
    def start(self):
        """Start the MCP server"""
        if self.mcp_server is None:
            Logger.warning("Cannot start MCP server - FastMCP not available")
            return
        
        try:
            # Note: In a real implementation, you would start the server
            # For now, we just mark it as running
            self.running = True
            Logger.info(f"Tactical MCP server started (simulated)")
            
        except Exception as e:
            Logger.error(f"Failed to start MCP server: {e}")
            raise
    
    def stop(self):
        """Stop the MCP server"""
        if self.running:
            self.running = False
            Logger.info("Tactical MCP server stopped")
    
    # Helper methods for tactical analysis
    
    def _calculate_position_value(self, entity: Entity) -> float:
        """Calculate tactical value of entity's position"""
        # Placeholder implementation
        return 0.5
    
    def _analyze_threats(self, entity: Entity) -> Dict[str, Any]:
        """Analyze threats to entity"""
        return {
            "immediate_threats": 0,
            "potential_threats": 0,
            "threat_level": "low"
        }
    
    def _evaluate_opportunities(self, entity: Entity) -> List[str]:
        """Evaluate tactical opportunities for entity"""
        return [
            "maintain_position",
            "advance_cautiously"
        ]
    
    def _get_resource_status(self, entity: Entity) -> Dict[str, Any]:
        """Get resource status for entity"""
        return {
            "hp": 100,  # Placeholder
            "mp": 50,   # Placeholder
            "rage": 0,  # Placeholder
            "kwan": 25  # Placeholder
        }
    
    def _calculate_cover_value(self, position: Vector3) -> float:
        """Calculate cover value at position"""
        return 0.3  # Placeholder
    
    def _calculate_visibility(self, position: Vector3) -> float:
        """Calculate visibility from position"""
        return 0.7  # Placeholder
    
    def _calculate_mobility_value(self, position: Vector3) -> float:
        """Calculate mobility value at position"""
        return 0.6  # Placeholder
    
    def _calculate_strategic_value(self, position: Vector3) -> float:
        """Calculate strategic importance of position"""
        return 0.4  # Placeholder