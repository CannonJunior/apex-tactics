"""
Game Engine Client

HTTP client for communicating with the Apex Tactics game engine API.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
import structlog

from .models import (
    MoveActionParams, AttackActionParams, SpellActionParams, 
    ItemActionParams, ToolResult
)

logger = structlog.get_logger()


class GameEngineClient:
    """Client for communicating with the game engine API"""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def health_check(self) -> bool:
        """Check if game engine is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error("Game engine health check failed", error=str(e))
            return False
    
    async def get_game_state(self, session_id: str) -> Dict[str, Any]:
        """Get current game state from the game engine"""
        try:
            response = await self.client.get(
                f"{self.base_url}/sessions/{session_id}/state"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("Failed to get game state", 
                        session_id=session_id, status_code=e.response.status_code)
            raise
        except Exception as e:
            logger.error("Game state request failed", 
                        session_id=session_id, error=str(e))
            raise
    
    async def create_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new game session"""
        try:
            params = {"session_id": session_id} if session_id else {}
            response = await self.client.post(f"{self.base_url}/sessions", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Failed to create game session", error=str(e))
            raise
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a game session"""
        try:
            response = await self.client.delete(f"{self.base_url}/sessions/{session_id}")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error("Failed to delete game session", 
                        session_id=session_id, error=str(e))
            return False
    
    async def move_unit(self, params: MoveActionParams) -> ToolResult:
        """Execute a unit move action"""
        try:
            action_data = {
                "unit_id": params.unit_id,
                "target_x": params.target_x,
                "target_y": params.target_y
            }
            
            response = await self.client.post(
                f"{self.base_url}/sessions/{params.session_id}/actions/move",
                json=action_data
            )
            response.raise_for_status()
            result = response.json()
            
            return ToolResult(
                success=result.get("success", False),
                message=result.get("message", ""),
                data=result
            )
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Move action failed: HTTP {e.response.status_code}"
            return ToolResult(
                success=False,
                message=error_msg,
                errors=[error_msg]
            )
        except Exception as e:
            error_msg = f"Move action failed: {str(e)}"
            return ToolResult(
                success=False,
                message=error_msg,
                errors=[error_msg]
            )
    
    async def attack_unit(self, params: AttackActionParams) -> ToolResult:
        """Execute a unit attack action"""
        try:
            action_data = {
                "attacker_id": params.attacker_id,
                "target_id": params.target_id,
                "attack_type": params.attack_type
            }
            
            response = await self.client.post(
                f"{self.base_url}/sessions/{params.session_id}/actions/attack",
                json=action_data
            )
            response.raise_for_status()
            result = response.json()
            
            return ToolResult(
                success=result.get("success", False),
                message=result.get("message", ""),
                data=result
            )
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Attack action failed: HTTP {e.response.status_code}"
            return ToolResult(
                success=False,
                message=error_msg,
                errors=[error_msg]
            )
        except Exception as e:
            error_msg = f"Attack action failed: {str(e)}"
            return ToolResult(
                success=False,
                message=error_msg,
                errors=[error_msg]
            )
    
    async def cast_spell(self, params: SpellActionParams) -> ToolResult:
        """Execute a spell casting action"""
        try:
            action_data = {
                "unit_id": params.caster_id,
                "spell_name": params.spell_name,
                "target_x": params.target_x,
                "target_y": params.target_y
            }
            
            # Note: This endpoint doesn't exist yet in the game engine
            # This is a placeholder for future implementation
            response = await self.client.post(
                f"{self.base_url}/sessions/{params.session_id}/actions/magic",
                json=action_data
            )
            response.raise_for_status()
            result = response.json()
            
            return ToolResult(
                success=result.get("success", False),
                message=result.get("message", ""),
                data=result
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Endpoint not implemented yet
                return ToolResult(
                    success=False,
                    message="Spell casting not yet implemented",
                    errors=["Magic system not yet available"]
                )
            error_msg = f"Spell action failed: HTTP {e.response.status_code}"
            return ToolResult(
                success=False,
                message=error_msg,
                errors=[error_msg]
            )
        except Exception as e:
            error_msg = f"Spell action failed: {str(e)}"
            return ToolResult(
                success=False,
                message=error_msg,
                errors=[error_msg]
            )
    
    async def use_item(self, params: ItemActionParams) -> ToolResult:
        """Execute an item usage action"""
        try:
            action_data = {
                "unit_id": params.unit_id,
                "item_id": params.item_id,
                "target_id": params.target_id
            }
            
            # Note: This endpoint doesn't exist yet in the game engine
            response = await self.client.post(
                f"{self.base_url}/sessions/{params.session_id}/actions/item",
                json=action_data
            )
            response.raise_for_status()
            result = response.json()
            
            return ToolResult(
                success=result.get("success", False),
                message=result.get("message", ""),
                data=result
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Endpoint not implemented yet
                return ToolResult(
                    success=False,
                    message="Item usage not yet implemented",
                    errors=["Inventory system not yet available"]
                )
            error_msg = f"Item action failed: HTTP {e.response.status_code}"
            return ToolResult(
                success=False,
                message=error_msg,
                errors=[error_msg]
            )
        except Exception as e:
            error_msg = f"Item action failed: {str(e)}"
            return ToolResult(
                success=False,
                message=error_msg,
                errors=[error_msg]
            )
    
    async def end_turn(self, session_id: str) -> ToolResult:
        """End the current unit's turn"""
        try:
            response = await self.client.post(
                f"{self.base_url}/sessions/{session_id}/actions/end-turn"
            )
            response.raise_for_status()
            result = response.json()
            
            return ToolResult(
                success=result.get("success", False),
                message=result.get("message", ""),
                data=result
            )
            
        except httpx.HTTPStatusError as e:
            error_msg = f"End turn failed: HTTP {e.response.status_code}"
            return ToolResult(
                success=False,
                message=error_msg,
                errors=[error_msg]
            )
        except Exception as e:
            error_msg = f"End turn failed: {str(e)}"
            return ToolResult(
                success=False,
                message=error_msg,
                errors=[error_msg]
            )
    
    async def get_available_actions(self, session_id: str, unit_id: str) -> Dict[str, Any]:
        """Get available actions for a specific unit"""
        try:
            # Get current game state
            game_state = await self.get_game_state(session_id)
            
            # Find the unit
            unit = None
            for u in game_state.get("units", []):
                if u["id"] == unit_id:
                    unit = u
                    break
            
            if not unit:
                return {"error": "Unit not found"}
            
            # Calculate available actions based on unit state
            actions = []
            
            # Movement is almost always available
            if unit.get("alive", False):
                actions.append({
                    "type": "move",
                    "description": "Move unit to a new position",
                    "range": unit.get("move_points", 3)
                })
            
            # Attack if there are valid targets
            if unit.get("alive", False) and unit.get("ap", 0) > 0:
                actions.append({
                    "type": "attack",
                    "description": "Attack an enemy unit",
                    "range": unit.get("attack_range", 1)
                })
            
            # Magic if unit has MP
            if unit.get("alive", False) and unit.get("mp", 0) >= unit.get("magic_mp_cost", 10):
                actions.append({
                    "type": "magic",
                    "description": f"Cast {unit.get('magic_spell_name', 'spell')}",
                    "range": unit.get("magic_range", 2),
                    "mp_cost": unit.get("magic_mp_cost", 10)
                })
            
            # Always available
            actions.append({
                "type": "end_turn",
                "description": "End this unit's turn"
            })
            
            return {
                "unit_id": unit_id,
                "available_actions": actions,
                "current_stats": {
                    "hp": unit.get("hp", 0),
                    "max_hp": unit.get("max_hp", 0),
                    "mp": unit.get("mp", 0),
                    "max_mp": unit.get("max_mp", 0),
                    "ap": unit.get("ap", 0),
                    "move_points": unit.get("move_points", 0)
                }
            }
            
        except Exception as e:
            logger.error("Failed to get available actions", 
                        session_id=session_id, unit_id=unit_id, error=str(e))
            return {"error": str(e)}
    
    async def analyze_battlefield(self, session_id: str, analysis_type: str = "tactical") -> Dict[str, Any]:
        """Analyze the current battlefield state"""
        try:
            # Get current game state
            game_state = await self.get_game_state(session_id)
            
            # Prepare analysis request
            analysis_request = {
                "type": analysis_type,
                "session_id": session_id
            }
            
            # Use the MCP gateway's analysis endpoint
            # Note: This creates a circular dependency that should be resolved
            # in a production environment by having shared analysis logic
            
            # For now, do basic analysis here
            units = game_state.get("units", [])
            current_unit_index = game_state.get("current_unit_index", 0)
            
            if current_unit_index < len(units):
                current_unit = units[current_unit_index]
                
                # Simple tactical analysis
                allies = [u for u in units if u.get("team") == current_unit.get("team") and u["alive"]]
                enemies = [u for u in units if u.get("team") != current_unit.get("team") and u["alive"]]
                
                analysis = {
                    "session_id": session_id,
                    "analysis_type": analysis_type,
                    "current_unit": current_unit["id"],
                    "team_status": {
                        "allies": len(allies),
                        "enemies": len(enemies)
                    },
                    "battlefield_control": {
                        "center_control": _analyze_center_control(units),
                        "positioning_advantage": _analyze_positioning(allies, enemies)
                    },
                    "recommendations": _generate_basic_recommendations(current_unit, enemies)
                }
                
                return analysis
            else:
                return {"error": "No current unit"}
                
        except Exception as e:
            logger.error("Battlefield analysis failed", 
                        session_id=session_id, error=str(e))
            return {"error": str(e)}


def _analyze_center_control(units: List[Dict[str, Any]]) -> str:
    """Analyze which team controls the center of the battlefield"""
    # Simple center control analysis
    center_x, center_y = 5, 5  # Assuming 10x10 grid
    
    ally_distance = 0
    enemy_distance = 0
    ally_count = 0
    enemy_count = 0
    
    for unit in units:
        if not unit.get("alive"):
            continue
            
        x, y = unit["position"]
        distance = abs(x - center_x) + abs(y - center_y)
        
        if unit.get("team") == "player":
            ally_distance += distance
            ally_count += 1
        else:
            enemy_distance += distance
            enemy_count += 1
    
    if ally_count == 0:
        return "enemy_controlled"
    elif enemy_count == 0:
        return "ally_controlled"
    else:
        avg_ally_distance = ally_distance / ally_count
        avg_enemy_distance = enemy_distance / enemy_count
        
        if avg_ally_distance < avg_enemy_distance:
            return "ally_controlled"
        elif avg_enemy_distance < avg_ally_distance:
            return "enemy_controlled"
        else:
            return "contested"


def _analyze_positioning(allies: List[Dict[str, Any]], enemies: List[Dict[str, Any]]) -> str:
    """Analyze positioning advantage"""
    if not allies or not enemies:
        return "unclear"
    
    # Simple clustering analysis
    ally_spread = _calculate_unit_spread(allies)
    enemy_spread = _calculate_unit_spread(enemies)
    
    if ally_spread < enemy_spread * 0.8:
        return "allies_clustered"
    elif enemy_spread < ally_spread * 0.8:
        return "enemies_clustered"
    else:
        return "balanced"


def _calculate_unit_spread(units: List[Dict[str, Any]]) -> float:
    """Calculate the spread/dispersion of units"""
    if len(units) < 2:
        return 0.0
    
    positions = [unit["position"] for unit in units]
    
    # Calculate average distance between all pairs
    total_distance = 0
    pair_count = 0
    
    for i, pos1 in enumerate(positions):
        for j, pos2 in enumerate(positions[i+1:], i+1):
            distance = abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
            total_distance += distance
            pair_count += 1
    
    return total_distance / pair_count if pair_count > 0 else 0.0


def _generate_basic_recommendations(current_unit: Dict[str, Any], enemies: List[Dict[str, Any]]) -> List[str]:
    """Generate basic tactical recommendations"""
    recommendations = []
    
    if not enemies:
        recommendations.append("No enemies remaining - victory is near!")
        return recommendations
    
    # Find nearest enemy
    current_pos = current_unit["position"]
    nearest_enemy = min(enemies, key=lambda e: abs(e["position"][0] - current_pos[0]) + abs(e["position"][1] - current_pos[1]))
    nearest_distance = abs(nearest_enemy["position"][0] - current_pos[0]) + abs(nearest_enemy["position"][1] - current_pos[1])
    
    attack_range = current_unit.get("attack_range", 1)
    
    if nearest_distance <= attack_range:
        recommendations.append(f"Enemy {nearest_enemy['id']} is in attack range - consider attacking")
    else:
        recommendations.append(f"Move closer to enemy {nearest_enemy['id']} (distance: {nearest_distance})")
    
    # Health recommendations
    hp_ratio = current_unit.get("hp", 100) / current_unit.get("max_hp", 100)
    if hp_ratio < 0.3:
        recommendations.append("Unit has low health - consider defensive positioning")
    elif hp_ratio > 0.8:
        recommendations.append("Unit has good health - can afford aggressive moves")
    
    return recommendations