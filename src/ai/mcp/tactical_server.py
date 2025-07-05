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
                        "resource_status": self._get_resource_status(entity),
                        # Phase 5: AI Enhancement - Add talent analysis
                        "talent_analysis": self._analyze_available_talents(entity),
                        "talent_recommendations": self._get_talent_recommendations(entity)
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
        
        # Phase 4: MCP Resource Integration - Talent Resources
        @self.mcp_server.resource("available_talents")
        def get_available_talents() -> str:
            """Get talents available to current active character"""
            try:
                from ...core.assets.data_manager import get_data_manager
                
                data_manager = get_data_manager()
                all_talents = data_manager.get_all_talents()
                
                talents_data = {
                    "timestamp": time.time(),
                    "talent_count": len(all_talents),
                    "talents": []
                }
                
                # Convert talent data to JSON-serializable format
                for talent in all_talents:
                    talent_info = {
                        "id": talent.id,
                        "name": talent.name,
                        "action_type": talent.action_type,
                        "level": talent.level,
                        "tier": talent.tier,
                        "description": talent.description,
                        "cost": talent.cost,
                        "effects": talent.effects,
                        "requirements": talent.requirements
                    }
                    talents_data["talents"].append(talent_info)
                
                return json.dumps(talents_data)
                
            except Exception as e:
                Logger.error(f"Error getting available talents: {e}")
                return json.dumps({"error": str(e)})
        
        @self.mcp_server.resource("talent_details")
        def get_talent_details(talent_id: str = "") -> str:
            """Get detailed information about a specific talent"""
            try:
                if not talent_id:
                    return json.dumps({"error": "talent_id parameter required"})
                
                from ...core.assets.data_manager import get_data_manager
                
                data_manager = get_data_manager()
                all_talents = data_manager.get_all_talents()
                
                # Find the specific talent
                target_talent = None
                for talent in all_talents:
                    if talent.id == talent_id:
                        target_talent = talent
                        break
                
                if not target_talent:
                    return json.dumps({"error": f"Talent '{talent_id}' not found"})
                
                talent_details = {
                    "timestamp": time.time(),
                    "talent": {
                        "id": target_talent.id,
                        "name": target_talent.name,
                        "action_type": target_talent.action_type,
                        "level": target_talent.level,
                        "tier": target_talent.tier,
                        "description": target_talent.description,
                        "cost": target_talent.cost,
                        "effects": target_talent.effects,
                        "requirements": target_talent.requirements
                    },
                    "analysis": {
                        "damage_potential": self._analyze_talent_damage(target_talent),
                        "resource_efficiency": self._analyze_talent_efficiency(target_talent),
                        "tactical_value": self._analyze_talent_tactical_value(target_talent)
                    }
                }
                
                return json.dumps(talent_details)
                
            except Exception as e:
                Logger.error(f"Error getting talent details: {e}")
                return json.dumps({"error": str(e)})
        
        @self.mcp_server.resource("talent_cooldowns")
        def get_talent_cooldowns() -> str:
            """Get current talent cooldown status"""
            try:
                # Placeholder implementation - in full system would track actual cooldowns
                cooldown_data = {
                    "timestamp": time.time(),
                    "cooldown_system": "placeholder",
                    "global_cooldown": 0,
                    "talent_cooldowns": {},
                    "note": "Cooldown tracking system to be implemented with combat system"
                }
                
                return json.dumps(cooldown_data)
                
            except Exception as e:
                Logger.error(f"Error getting talent cooldowns: {e}")
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
    
    # Phase 4: MCP Resource Integration - Talent Analysis Helpers
    
    def _analyze_talent_damage(self, talent) -> float:
        """Analyze talent damage potential."""
        try:
            effects = talent.effects
            base_damage = 0
            
            # Extract damage from various effect types
            if 'base_damage' in effects:
                base_damage += effects['base_damage']
            if 'magical_damage' in effects:
                base_damage += effects['magical_damage']
            if 'physical_damage' in effects:
                base_damage += effects['physical_damage']
            if 'spiritual_damage' in effects:
                base_damage += effects['spiritual_damage']
            
            return float(base_damage)
            
        except Exception as e:
            Logger.error(f"Error analyzing talent damage: {e}")
            return 0.0
    
    def _analyze_talent_efficiency(self, talent) -> float:
        """Analyze talent resource efficiency."""
        try:
            effects = talent.effects
            cost = talent.cost
            
            # Calculate damage per resource cost
            total_damage = self._analyze_talent_damage(talent)
            total_cost = cost.get('mp_cost', 0) + cost.get('ap_cost', 0) + cost.get('rage_cost', 0)
            
            if total_cost > 0:
                efficiency = total_damage / total_cost
            else:
                efficiency = total_damage  # No cost abilities are highly efficient
            
            return min(efficiency, 10.0)  # Cap at 10.0 for reasonable values
            
        except Exception as e:
            Logger.error(f"Error analyzing talent efficiency: {e}")
            return 0.0
    
    def _analyze_talent_tactical_value(self, talent) -> float:
        """Analyze tactical value of talent."""
        try:
            action_type = talent.action_type
            effects = talent.effects
            
            # Base tactical value by action type
            tactical_values = {
                'Attack': 0.7,
                'Magic': 0.8,
                'Spirit': 0.6,
                'Move': 0.5
            }
            
            base_value = tactical_values.get(action_type, 0.5)
            
            # Adjust for special effects
            if 'area_of_effect' in effects and effects['area_of_effect'] > 1:
                base_value += 0.2  # AOE abilities are more tactically valuable
            
            if 'healing_amount' in effects:
                base_value += 0.15  # Healing adds tactical value
            
            if effects.get('range', 1) > 2:
                base_value += 0.1  # Long range adds tactical value
            
            return min(base_value, 1.0)  # Cap at 1.0
            
        except Exception as e:
            Logger.error(f"Error analyzing talent tactical value: {e}")
            return 0.5
    
    # Phase 5: AI Enhancement - Talent Analysis for Battlefield Analysis
    
    def _analyze_available_talents(self, entity: Entity) -> Dict[str, Any]:
        """Analyze available talents for tactical decision making."""
        try:
            # Get available talents from data manager
            from ...core.assets.data_manager import get_data_manager
            data_manager = get_data_manager()
            all_talents = data_manager.get_all_talents()
            
            # Analyze talent categories
            talent_analysis = {
                "total_available": len(all_talents),
                "by_action_type": {},
                "damage_potential": 0,
                "support_capabilities": [],
                "tactical_options": []
            }
            
            # Categorize talents by action type
            for talent in all_talents:
                action_type = talent.action_type
                if action_type not in talent_analysis["by_action_type"]:
                    talent_analysis["by_action_type"][action_type] = []
                
                talent_info = {
                    "id": talent.id,
                    "name": talent.name,
                    "level": talent.level,
                    "damage_potential": self._analyze_talent_damage(talent),
                    "tactical_value": self._analyze_talent_tactical_value(talent)
                }
                talent_analysis["by_action_type"][action_type].append(talent_info)
                
                # Accumulate damage potential
                talent_analysis["damage_potential"] += talent_info["damage_potential"]
                
                # Identify support capabilities
                if 'healing_amount' in talent.effects:
                    talent_analysis["support_capabilities"].append(f"Healing: {talent.name}")
                
                # Add tactical options
                if talent.effects.get('area_of_effect', 1) > 1:
                    talent_analysis["tactical_options"].append(f"AOE: {talent.name}")
            
            return talent_analysis
            
        except Exception as e:
            Logger.error(f"Error analyzing available talents: {e}")
            return {"error": str(e)}
    
    def _get_talent_recommendations(self, entity: Entity) -> List[Dict[str, Any]]:
        """Get AI talent recommendations for current tactical situation."""
        try:
            # Get available talents
            from ...core.assets.data_manager import get_data_manager
            data_manager = get_data_manager()
            all_talents = data_manager.get_all_talents()
            
            recommendations = []
            
            # Analyze each talent for current situation
            for talent in all_talents[:5]:  # Limit to top 5 for performance
                recommendation = {
                    "talent_id": talent.id,
                    "talent_name": talent.name,
                    "confidence": self._calculate_talent_confidence_for_situation(talent, entity),
                    "reasoning": self._generate_talent_reasoning_for_situation(talent, entity),
                    "priority": self._calculate_talent_priority(talent, entity)
                }
                recommendations.append(recommendation)
            
            # Sort by confidence score
            recommendations.sort(key=lambda x: x["confidence"], reverse=True)
            
            return recommendations[:3]  # Return top 3 recommendations
            
        except Exception as e:
            Logger.error(f"Error getting talent recommendations: {e}")
            return [{"error": str(e)}]
    
    def _calculate_talent_confidence_for_situation(self, talent, entity: Entity) -> float:
        """Calculate confidence score for talent in current situation."""
        try:
            base_confidence = 0.5
            
            # Adjust based on talent characteristics
            action_type = talent.action_type
            if action_type == 'Attack':
                base_confidence += 0.2  # Offensive actions generally useful
            elif action_type == 'Magic':
                base_confidence += 0.3  # Magic often versatile
            elif action_type == 'Spirit':
                base_confidence += 0.1  # Support abilities
            
            # Adjust based on damage potential
            damage = self._analyze_talent_damage(talent)
            if damage > 20:
                base_confidence += 0.2
            elif damage > 10:
                base_confidence += 0.1
            
            # Adjust based on resource efficiency
            efficiency = self._analyze_talent_efficiency(talent)
            if efficiency > 1.0:
                base_confidence += 0.1
            
            return min(base_confidence, 1.0)
            
        except Exception as e:
            Logger.error(f"Error calculating talent confidence: {e}")
            return 0.0
    
    def _generate_talent_reasoning_for_situation(self, talent, entity: Entity) -> str:
        """Generate reasoning for talent recommendation."""
        try:
            action_type = talent.action_type
            damage = self._analyze_talent_damage(talent)
            
            if action_type == 'Attack' and damage > 15:
                return f"High damage attack ({damage}) suitable for eliminating threats"
            elif action_type == 'Magic':
                aoe = talent.effects.get('area_of_effect', 1)
                if aoe > 1:
                    return f"Area effect magic can hit multiple targets (AOE: {aoe})"
                else:
                    return "Magical attack provides versatile damage option"
            elif action_type == 'Spirit':
                if 'healing_amount' in talent.effects:
                    healing = talent.effects['healing_amount']
                    return f"Healing ability ({healing}) for sustaining team"
                else:
                    return "Spiritual ability provides tactical support"
            else:
                return f"Standard {action_type.lower()} ability with tactical utility"
                
        except Exception as e:
            Logger.error(f"Error generating talent reasoning: {e}")
            return "Analysis unavailable"
    
    def _calculate_talent_priority(self, talent, entity: Entity) -> str:
        """Calculate priority level for talent."""
        try:
            confidence = self._calculate_talent_confidence_for_situation(talent, entity)
            
            if confidence >= 0.8:
                return "high"
            elif confidence >= 0.6:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            Logger.error(f"Error calculating talent priority: {e}")
            return "unknown"
    
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