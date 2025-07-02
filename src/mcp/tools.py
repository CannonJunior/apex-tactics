"""
MCP Tools for Apex Tactics

FastMCP tool implementations for AI agents to interact with the game.
"""

from typing import Dict, Any, Optional, List
import asyncio
import json

from fastmcp.tools import Tool
import structlog

from .models import (
    MoveActionParams, AttackActionParams, SpellActionParams, 
    ItemActionParams, ToolResult
)
from .game_client import GameEngineClient

logger = structlog.get_logger()


class MoveUnitTool(Tool):
    """Tool for moving units on the battlefield"""
    
    def __init__(self, game_client: GameEngineClient):
        self.game_client = game_client
        super().__init__(
            name="move_unit",
            description="Move a unit to a new position on the battlefield",
            parameters_schema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Game session identifier"
                    },
                    "unit_id": {
                        "type": "string", 
                        "description": "ID of the unit to move"
                    },
                    "target_x": {
                        "type": "integer",
                        "description": "Target X coordinate (0-9 for standard grid)"
                    },
                    "target_y": {
                        "type": "integer", 
                        "description": "Target Y coordinate (0-9 for standard grid)"
                    }
                },
                "required": ["session_id", "unit_id", "target_x", "target_y"]
            }
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the move unit action"""
        try:
            params = MoveActionParams(**kwargs)
            result = await self.game_client.move_unit(params)
            
            logger.info("Move unit tool executed", 
                       session_id=params.session_id, 
                       unit_id=params.unit_id,
                       target=(params.target_x, params.target_y),
                       success=result.success)
            
            return {
                "success": result.success,
                "message": result.message,
                "action_type": "move",
                "unit_id": params.unit_id,
                "new_position": [params.target_x, params.target_y]
            }
            
        except Exception as e:
            logger.error("Move unit tool failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action_type": "move"
            }


class AttackUnitTool(Tool):
    """Tool for attacking other units"""
    
    def __init__(self, game_client: GameEngineClient):
        self.game_client = game_client
        super().__init__(
            name="attack_unit",
            description="Attack another unit with physical, magical, or spiritual damage",
            parameters_schema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Game session identifier"
                    },
                    "attacker_id": {
                        "type": "string",
                        "description": "ID of the attacking unit"
                    },
                    "target_id": {
                        "type": "string", 
                        "description": "ID of the target unit"
                    },
                    "attack_type": {
                        "type": "string",
                        "enum": ["physical", "magical", "spiritual"],
                        "description": "Type of attack to perform",
                        "default": "physical"
                    }
                },
                "required": ["session_id", "attacker_id", "target_id"]
            }
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the attack action"""
        try:
            # Set default attack type if not provided
            if "attack_type" not in kwargs:
                kwargs["attack_type"] = "physical"
                
            params = AttackActionParams(**kwargs)
            result = await self.game_client.attack_unit(params)
            
            logger.info("Attack unit tool executed",
                       session_id=params.session_id,
                       attacker_id=params.attacker_id,
                       target_id=params.target_id,
                       attack_type=params.attack_type,
                       success=result.success)
            
            return {
                "success": result.success,
                "message": result.message,
                "action_type": "attack",
                "attacker_id": params.attacker_id,
                "target_id": params.target_id,
                "attack_type": params.attack_type
            }
            
        except Exception as e:
            logger.error("Attack unit tool failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action_type": "attack"
            }


class GetGameStateTool(Tool):
    """Tool for getting current game state"""
    
    def __init__(self, game_client: GameEngineClient):
        self.game_client = game_client
        super().__init__(
            name="get_game_state",
            description="Get the current state of the game including all units and battlefield information",
            parameters_schema={
                "type": "object", 
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Game session identifier"
                    }
                },
                "required": ["session_id"]
            }
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get current game state"""
        try:
            session_id = kwargs["session_id"]
            game_state = await self.game_client.get_game_state(session_id)
            
            logger.info("Get game state tool executed", session_id=session_id)
            
            return {
                "success": True,
                "game_state": game_state,
                "action_type": "get_state"
            }
            
        except Exception as e:
            logger.error("Get game state tool failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action_type": "get_state"
            }


class AnalyzeBattlefieldTool(Tool):
    """Tool for analyzing battlefield conditions"""
    
    def __init__(self, game_client: GameEngineClient):
        self.game_client = game_client
        super().__init__(
            name="analyze_battlefield",
            description="Analyze the current battlefield state and provide tactical recommendations",
            parameters_schema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Game session identifier"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["tactical", "strategic", "threat"],
                        "description": "Type of analysis to perform",
                        "default": "tactical"
                    },
                    "focus_unit_id": {
                        "type": "string",
                        "description": "Optional unit ID to focus analysis on"
                    }
                },
                "required": ["session_id"]
            }
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Analyze battlefield conditions"""
        try:
            session_id = kwargs["session_id"]
            analysis_type = kwargs.get("analysis_type", "tactical")
            
            analysis = await self.game_client.analyze_battlefield(session_id, analysis_type)
            
            logger.info("Battlefield analysis tool executed",
                       session_id=session_id,
                       analysis_type=analysis_type)
            
            return {
                "success": True,
                "analysis": analysis,
                "action_type": "analyze",
                "analysis_type": analysis_type
            }
            
        except Exception as e:
            logger.error("Battlefield analysis tool failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action_type": "analyze"
            }


class GetAvailableActionsTool(Tool):
    """Tool for getting available actions for a unit"""
    
    def __init__(self, game_client: GameEngineClient):
        self.game_client = game_client
        super().__init__(
            name="get_available_actions",
            description="Get all available actions for a specific unit",
            parameters_schema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Game session identifier"
                    },
                    "unit_id": {
                        "type": "string",
                        "description": "ID of the unit to check actions for"
                    }
                },
                "required": ["session_id", "unit_id"]
            }
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get available actions for a unit"""
        try:
            session_id = kwargs["session_id"]
            unit_id = kwargs["unit_id"]
            
            actions = await self.game_client.get_available_actions(session_id, unit_id)
            
            logger.info("Get available actions tool executed",
                       session_id=session_id,
                       unit_id=unit_id)
            
            return {
                "success": True,
                "available_actions": actions,
                "action_type": "get_actions",
                "unit_id": unit_id
            }
            
        except Exception as e:
            logger.error("Get available actions tool failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action_type": "get_actions"
            }


class EndTurnTool(Tool):
    """Tool for ending the current unit's turn"""
    
    def __init__(self, game_client: GameEngineClient):
        self.game_client = game_client
        super().__init__(
            name="end_turn",
            description="End the current unit's turn and advance to the next unit",
            parameters_schema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Game session identifier"
                    }
                },
                "required": ["session_id"]
            }
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """End the current turn"""
        try:
            session_id = kwargs["session_id"]
            result = await self.game_client.end_turn(session_id)
            
            logger.info("End turn tool executed",
                       session_id=session_id,
                       success=result.success)
            
            return {
                "success": result.success,
                "message": result.message,
                "action_type": "end_turn"
            }
            
        except Exception as e:
            logger.error("End turn tool failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action_type": "end_turn"
            }


class CastSpellTool(Tool):
    """Tool for casting spells"""
    
    def __init__(self, game_client: GameEngineClient):
        self.game_client = game_client
        super().__init__(
            name="cast_spell",
            description="Cast a magical spell at a target location",
            parameters_schema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Game session identifier"
                    },
                    "caster_id": {
                        "type": "string",
                        "description": "ID of the unit casting the spell"
                    },
                    "spell_name": {
                        "type": "string",
                        "description": "Name of the spell to cast"
                    },
                    "target_x": {
                        "type": "integer",
                        "description": "Target X coordinate"
                    },
                    "target_y": {
                        "type": "integer",
                        "description": "Target Y coordinate"
                    }
                },
                "required": ["session_id", "caster_id", "spell_name", "target_x", "target_y"]
            }
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Cast a spell"""
        try:
            params = SpellActionParams(**kwargs)
            result = await self.game_client.cast_spell(params)
            
            logger.info("Cast spell tool executed",
                       session_id=params.session_id,
                       caster_id=params.caster_id,
                       spell_name=params.spell_name,
                       success=result.success)
            
            return {
                "success": result.success,
                "message": result.message,
                "action_type": "spell",
                "caster_id": params.caster_id,
                "spell_name": params.spell_name,
                "target": [params.target_x, params.target_y]
            }
            
        except Exception as e:
            logger.error("Cast spell tool failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action_type": "spell"
            }


class UseItemTool(Tool):
    """Tool for using items from inventory"""
    
    def __init__(self, game_client: GameEngineClient):
        self.game_client = game_client
        super().__init__(
            name="use_item",
            description="Use an item from a unit's inventory",
            parameters_schema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Game session identifier"
                    },
                    "unit_id": {
                        "type": "string",
                        "description": "ID of the unit using the item"
                    },
                    "item_id": {
                        "type": "string",
                        "description": "ID of the item to use"
                    },
                    "target_id": {
                        "type": "string",
                        "description": "Optional target unit ID for items that affect other units"
                    }
                },
                "required": ["session_id", "unit_id", "item_id"]
            }
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Use an item"""
        try:
            params = ItemActionParams(**kwargs)
            result = await self.game_client.use_item(params)
            
            logger.info("Use item tool executed",
                       session_id=params.session_id,
                       unit_id=params.unit_id,
                       item_id=params.item_id,
                       success=result.success)
            
            return {
                "success": result.success,
                "message": result.message,
                "action_type": "item",
                "unit_id": params.unit_id,
                "item_id": params.item_id,
                "target_id": params.target_id
            }
            
        except Exception as e:
            logger.error("Use item tool failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action_type": "item"
            }


class GetUnitDetailsTool(Tool):
    """Tool for getting detailed information about a specific unit"""
    
    def __init__(self, game_client: GameEngineClient):
        self.game_client = game_client
        super().__init__(
            name="get_unit_details",
            description="Get detailed information about a specific unit including stats, equipment, and abilities",
            parameters_schema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Game session identifier"
                    },
                    "unit_id": {
                        "type": "string",
                        "description": "ID of the unit to examine"
                    }
                },
                "required": ["session_id", "unit_id"]
            }
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Get detailed unit information"""
        try:
            session_id = kwargs["session_id"]
            unit_id = kwargs["unit_id"]
            
            # Get game state and find the unit
            game_state = await self.game_client.get_game_state(session_id)
            
            unit = None
            for u in game_state.get("units", []):
                if u["id"] == unit_id:
                    unit = u
                    break
            
            if not unit:
                return {
                    "success": False,
                    "error": f"Unit {unit_id} not found",
                    "action_type": "get_unit_details"
                }
            
            # Get available actions for this unit
            actions = await self.game_client.get_available_actions(session_id, unit_id)
            
            logger.info("Get unit details tool executed",
                       session_id=session_id,
                       unit_id=unit_id)
            
            return {
                "success": True,
                "unit_details": unit,
                "available_actions": actions,
                "action_type": "get_unit_details"
            }
            
        except Exception as e:
            logger.error("Get unit details tool failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action_type": "get_unit_details"
            }


class CalculateDistanceTool(Tool):
    """Tool for calculating distances and ranges on the battlefield"""
    
    def __init__(self, game_client: GameEngineClient):
        self.game_client = game_client
        super().__init__(
            name="calculate_distance",
            description="Calculate distance between two points or units on the battlefield",
            parameters_schema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Game session identifier"
                    },
                    "from_unit_id": {
                        "type": "string",
                        "description": "ID of the source unit (optional if using coordinates)"
                    },
                    "to_unit_id": {
                        "type": "string",
                        "description": "ID of the target unit (optional if using coordinates)"
                    },
                    "from_x": {
                        "type": "integer",
                        "description": "Source X coordinate (optional if using unit ID)"
                    },
                    "from_y": {
                        "type": "integer",
                        "description": "Source Y coordinate (optional if using unit ID)"
                    },
                    "to_x": {
                        "type": "integer",
                        "description": "Target X coordinate (optional if using unit ID)"
                    },
                    "to_y": {
                        "type": "integer",
                        "description": "Target Y coordinate (optional if using unit ID)"
                    }
                },
                "required": ["session_id"]
            }
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Calculate distance between points or units"""
        try:
            session_id = kwargs["session_id"]
            
            # Determine source and target coordinates
            if "from_unit_id" in kwargs:
                game_state = await self.game_client.get_game_state(session_id)
                from_unit = next((u for u in game_state.get("units", []) if u["id"] == kwargs["from_unit_id"]), None)
                if not from_unit:
                    return {"success": False, "error": f"Source unit {kwargs['from_unit_id']} not found"}
                from_x, from_y = from_unit["position"]
            else:
                from_x, from_y = kwargs.get("from_x", 0), kwargs.get("from_y", 0)
            
            if "to_unit_id" in kwargs:
                game_state = await self.game_client.get_game_state(session_id)
                to_unit = next((u for u in game_state.get("units", []) if u["id"] == kwargs["to_unit_id"]), None)
                if not to_unit:
                    return {"success": False, "error": f"Target unit {kwargs['to_unit_id']} not found"}
                to_x, to_y = to_unit["position"]
            else:
                to_x, to_y = kwargs.get("to_x", 0), kwargs.get("to_y", 0)
            
            # Calculate Manhattan distance (typical for grid-based tactical games)
            manhattan_distance = abs(to_x - from_x) + abs(to_y - from_y)
            
            # Calculate Euclidean distance
            euclidean_distance = ((to_x - from_x) ** 2 + (to_y - from_y) ** 2) ** 0.5
            
            logger.info("Calculate distance tool executed",
                       session_id=session_id,
                       from_pos=(from_x, from_y),
                       to_pos=(to_x, to_y))
            
            return {
                "success": True,
                "from_position": [from_x, from_y],
                "to_position": [to_x, to_y],
                "manhattan_distance": manhattan_distance,
                "euclidean_distance": round(euclidean_distance, 2),
                "action_type": "calculate_distance"
            }
            
        except Exception as e:
            logger.error("Calculate distance tool failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action_type": "calculate_distance"
            }