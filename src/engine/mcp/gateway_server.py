"""
MCP Gateway Server

FastMCP server that provides MCP tools for interacting with the game engine,
allowing external agents to analyze game state and execute actions.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

import structlog
from fastmcp import FastMCP

from ...core.ecs import EntityID
from ..game_engine import GameEngine
from ..battlefield import BattlefieldManager
from ..components.stats_component import StatsComponent
from ..components.position_component import PositionComponent
from ..components.team_component import TeamComponent
from ..components.equipment_component import EquipmentComponent
from ..components.status_effects_component import StatusEffectsComponent

logger = structlog.get_logger()


class GameEngineMCPGateway:
    """MCP Gateway for game engine interaction"""
    
    def __init__(self, game_engine: GameEngine, port: int = 8004):
        self.game_engine = game_engine
        self.port = port
        
        # Create FastMCP server
        self.mcp = FastMCP("Apex Tactics Game Engine Gateway")
        
        # Register all MCP tools
        self._register_tools()
        
        logger.info("MCP Gateway initialized", port=port)
    
    def _register_tools(self):
        """Register all MCP tools"""
        
        @self.mcp.tool()
        async def get_game_sessions() -> List[Dict[str, Any]]:
            """Get list of all active game sessions
            
            Returns:
                List of active game sessions with basic information
            """
            sessions = []
            for session_id, session in self.game_engine.active_sessions.items():
                sessions.append({
                    "session_id": session_id,
                    "player_ids": session.player_ids,
                    "current_phase": session.current_phase.value,
                    "turn_number": session.turn_number,
                    "start_time": session.start_time.isoformat(),
                    "config": session.config.__dict__
                })
            
            return sessions
        
        @self.mcp.tool()
        async def get_session_state(session_id: str) -> Dict[str, Any]:
            """Get detailed state for a specific game session
            
            Args:
                session_id: ID of the game session
                
            Returns:
                Comprehensive game state information
            """
            if session_id not in self.game_engine.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            game_state = await self.game_engine.get_session_state(session_id)
            return game_state or {}
        
        @self.mcp.tool()
        async def get_battlefield_state(session_id: str) -> Dict[str, Any]:
            """Get battlefield information for a session
            
            Args:
                session_id: ID of the game session
                
            Returns:
                Battlefield grid, units, and terrain information
            """
            if session_id not in self.game_engine.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            battlefield_state = await self.game_engine.battlefield.get_state(session_id)
            return battlefield_state or {}
        
        @self.mcp.tool()
        async def get_all_units(session_id: str) -> List[Dict[str, Any]]:
            """Get information about all units in a session
            
            Args:
                session_id: ID of the game session
                
            Returns:
                List of all units with their complete data
            """
            if session_id not in self.game_engine.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            units = []
            entities_with_position = self.game_engine.ecs.get_entities_with_components([PositionComponent])
            
            for entity_id in entities_with_position:
                unit_data = await self._get_unit_data(entity_id)
                if unit_data:
                    units.append(unit_data)
            
            return units
        
        @self.mcp.tool()
        async def get_unit_details(session_id: str, unit_id: str) -> Dict[str, Any]:
            """Get detailed information about a specific unit
            
            Args:
                session_id: ID of the game session
                unit_id: ID of the unit
                
            Returns:
                Comprehensive unit information including stats, equipment, status effects
            """
            if session_id not in self.game_engine.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            entity_id = EntityID(unit_id)
            unit_data = await self._get_unit_data(entity_id)
            
            if not unit_data:
                raise ValueError(f"Unit {unit_id} not found")
            
            return unit_data
        
        @self.mcp.tool()
        async def get_available_actions(session_id: str, unit_id: str) -> List[Dict[str, Any]]:
            """Get available actions for a specific unit
            
            Args:
                session_id: ID of the game session
                unit_id: ID of the unit
                
            Returns:
                List of available actions with their parameters
            """
            if session_id not in self.game_engine.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            entity_id = EntityID(unit_id)
            
            # Get unit components
            position = self.game_engine.ecs.get_component(entity_id, PositionComponent)
            stats = self.game_engine.ecs.get_component(entity_id, StatsComponent)
            status_effects = self.game_engine.ecs.get_component(entity_id, StatusEffectsComponent)
            team = self.game_engine.ecs.get_component(entity_id, TeamComponent)
            
            if not position or not stats or not team:
                raise ValueError(f"Unit {unit_id} missing required components")
            
            actions = []
            
            # Check if unit can act
            can_act = stats.alive
            if status_effects:
                can_act = can_act and status_effects.can_act()
            
            if not can_act:
                return [{"type": "wait", "reason": "Unit cannot act due to status effects or death"}]
            
            # Movement actions
            if position.can_move and not position.has_moved:
                movement_positions = await self._get_movement_positions(session_id, entity_id)
                actions.append({
                    "type": "move",
                    "available_positions": movement_positions,
                    "description": "Move to a new position"
                })
            
            # Attack actions
            attack_targets = await self._get_attack_targets(session_id, entity_id)
            if attack_targets:
                actions.append({
                    "type": "attack",
                    "available_targets": attack_targets,
                    "description": "Attack an enemy unit"
                })
            
            # Wait action (always available)
            actions.append({
                "type": "wait",
                "description": "End turn without taking action"
            })
            
            return actions
        
        @self.mcp.tool()
        async def execute_unit_action(session_id: str, player_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
            """Execute an action for a unit
            
            Args:
                session_id: ID of the game session
                player_id: ID of the player executing the action
                action: Action to execute with all required parameters
                
            Returns:
                Result of the action execution
            """
            if session_id not in self.game_engine.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            try:
                success = await self.game_engine.execute_player_action(session_id, player_id, action)
                return {
                    "success": success,
                    "action": action,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "success": False,
                    "action": action,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.mcp.tool()
        async def get_turn_info(session_id: str) -> Dict[str, Any]:
            """Get current turn information for a session
            
            Args:
                session_id: ID of the game session
                
            Returns:
                Current turn number, active player, time remaining, etc.
            """
            if session_id not in self.game_engine.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            turn_info = await self.game_engine.turn_system.get_turn_info(session_id)
            return turn_info
        
        @self.mcp.tool()
        async def analyze_tactical_situation(session_id: str, team: str = None) -> Dict[str, Any]:
            """Analyze the current tactical situation for a team or overall
            
            Args:
                session_id: ID of the game session
                team: Optional team to analyze (if None, analyzes all teams)
                
            Returns:
                Tactical analysis including unit counts, positions, threats
            """
            if session_id not in self.game_engine.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            analysis = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "teams": {},
                "battlefield": {},
                "threats": [],
                "opportunities": []
            }
            
            # Get all units
            units = await self.get_all_units(session_id)
            
            # Analyze by team
            teams = {}
            for unit in units:
                unit_team = unit.get("team", "neutral")
                if unit_team not in teams:
                    teams[unit_team] = {
                        "total_units": 0,
                        "alive_units": 0,
                        "total_hp": 0,
                        "max_hp": 0,
                        "average_position": {"x": 0, "y": 0},
                        "units": []
                    }
                
                team_data = teams[unit_team]
                team_data["total_units"] += 1
                team_data["units"].append(unit)
                
                if unit.get("stats", {}).get("alive", False):
                    team_data["alive_units"] += 1
                    team_data["total_hp"] += unit.get("stats", {}).get("hp", {}).get("current", 0)
                    team_data["max_hp"] += unit.get("stats", {}).get("hp", {}).get("max", 0)
                    
                    # Calculate average position
                    pos = unit.get("position", {})
                    team_data["average_position"]["x"] += pos.get("x", 0)
                    team_data["average_position"]["y"] += pos.get("y", 0)
            
            # Finalize average positions
            for team_name, team_data in teams.items():
                if team_data["alive_units"] > 0:
                    team_data["average_position"]["x"] /= team_data["alive_units"]
                    team_data["average_position"]["y"] /= team_data["alive_units"]
                    team_data["hp_percentage"] = team_data["total_hp"] / team_data["max_hp"] if team_data["max_hp"] > 0 else 0
            
            analysis["teams"] = teams
            
            # Battlefield analysis
            battlefield_state = await self.get_battlefield_state(session_id)
            analysis["battlefield"] = {
                "size": battlefield_state.get("size", [10, 10]),
                "occupied_tiles": len([u for u in units if u.get("stats", {}).get("alive", False)])
            }
            
            # Simple threat analysis
            for unit in units:
                if not unit.get("stats", {}).get("alive", False):
                    continue
                
                unit_team = unit.get("team", "neutral")
                unit_pos = unit.get("position", {})
                
                # Find nearby enemies
                nearby_enemies = []
                for other_unit in units:
                    if (other_unit.get("team", "neutral") != unit_team and 
                        other_unit.get("stats", {}).get("alive", False)):
                        
                        other_pos = other_unit.get("position", {})
                        distance = abs(unit_pos.get("x", 0) - other_pos.get("x", 0)) + abs(unit_pos.get("y", 0) - other_pos.get("y", 0))
                        
                        if distance <= 3:  # Within 3 tiles
                            nearby_enemies.append({
                                "unit_id": other_unit.get("unit_id"),
                                "distance": distance,
                                "team": other_unit.get("team")
                            })
                
                if nearby_enemies:
                    analysis["threats"].append({
                        "unit_id": unit.get("unit_id"),
                        "team": unit_team,
                        "position": unit_pos,
                        "nearby_enemies": nearby_enemies
                    })
            
            # Filter by team if specified
            if team:
                if team not in analysis["teams"]:
                    raise ValueError(f"Team {team} not found in session")
                
                analysis["teams"] = {team: analysis["teams"][team]}
                analysis["threats"] = [t for t in analysis["threats"] if t["team"] == team]
            
            return analysis
        
        @self.mcp.tool()
        async def get_game_statistics(session_id: str) -> Dict[str, Any]:
            """Get comprehensive game statistics for a session
            
            Args:
                session_id: ID of the game session
                
            Returns:
                Game performance and state statistics
            """
            if session_id not in self.game_engine.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            # Get engine performance stats
            performance_stats = self.game_engine.get_performance_stats()
            
            # Get UI statistics
            ui_stats = {
                "ui_manager": self.game_engine.ui_manager.get_ui_stats(),
                "visual_effects": self.game_engine.visual_effects.get_stats(),
                "notifications": self.game_engine.notifications.get_stats()
            }
            
            # Get AI statistics
            ai_stats = self.game_engine.ai_integration.get_ai_stats()
            
            # Get turn system stats
            turn_stats = self.game_engine.turn_system.get_system_stats()
            
            return {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "performance": performance_stats,
                "ui_stats": ui_stats,
                "ai_stats": ai_stats,
                "turn_stats": turn_stats
            }
        
        @self.mcp.tool()
        async def send_notification(session_id: str, type: str, title: str, message: str, 
                                  player_id: str = None) -> Dict[str, Any]:
            """Send a notification to players in a session
            
            Args:
                session_id: ID of the game session
                type: Type of notification (info, success, warning, error, combat, turn, achievement)
                title: Notification title
                message: Notification message
                player_id: Optional specific player to notify (None for all players)
                
            Returns:
                Result of notification sending
            """
            if session_id not in self.game_engine.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            success = await self.game_engine.send_notification(session_id, type, title, message, player_id)
            
            return {
                "success": success,
                "session_id": session_id,
                "type": type,
                "title": title,
                "message": message,
                "player_id": player_id,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.mcp.tool()
        async def highlight_tiles(session_id: str, tiles: List[Dict[str, Any]], 
                                highlight_type: str = "selection", duration: float = None) -> Dict[str, Any]:
            """Highlight tiles on the battlefield for visual feedback
            
            Args:
                session_id: ID of the game session
                tiles: List of tile coordinates to highlight [{"x": int, "y": int}]
                highlight_type: Type of highlight (movement, attack_range, effect_area, danger_zone, selection, invalid, path)
                duration: Optional duration in seconds (None for permanent until cleared)
                
            Returns:
                Result of highlighting operation
            """
            if session_id not in self.game_engine.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            success = await self.game_engine.highlight_tiles(session_id, tiles, highlight_type, duration)
            
            return {
                "success": success,
                "session_id": session_id,
                "tiles_highlighted": len(tiles),
                "highlight_type": highlight_type,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.mcp.tool()
        async def create_test_session(battlefield_size: List[int] = [10, 10], 
                                    player_count: int = 2) -> Dict[str, Any]:
            """Create a test game session for demonstration or testing
            
            Args:
                battlefield_size: Size of the battlefield [width, height]
                player_count: Number of players to create
                
            Returns:
                Information about the created test session
            """
            import uuid
            
            session_id = f"test_{uuid.uuid4().hex[:8]}"
            player_ids = [f"player_{i+1}" for i in range(player_count)]
            
            from ..game_engine import GameConfig, GameMode
            
            config = GameConfig(
                mode=GameMode.TUTORIAL,
                battlefield_size=tuple(battlefield_size),
                max_turns=50,
                turn_time_limit=60.0,
                ai_difficulty="normal"
            )
            
            try:
                session = await self.game_engine.create_session(session_id, player_ids, config)
                await self.game_engine.start_game(session_id)
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "player_ids": player_ids,
                    "battlefield_size": battlefield_size,
                    "config": config.__dict__,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
    
    async def _get_unit_data(self, entity_id: EntityID) -> Optional[Dict[str, Any]]:
        """Get comprehensive data for a unit"""
        stats = self.game_engine.ecs.get_component(entity_id, StatsComponent)
        position = self.game_engine.ecs.get_component(entity_id, PositionComponent)
        team = self.game_engine.ecs.get_component(entity_id, TeamComponent)
        equipment = self.game_engine.ecs.get_component(entity_id, EquipmentComponent)
        status_effects = self.game_engine.ecs.get_component(entity_id, StatusEffectsComponent)
        
        if not position or not stats:
            return None
        
        unit_data = {
            "unit_id": str(entity_id),
            "position": {
                "x": position.x,
                "y": position.y,
                "z": position.z
            },
            "team": team.team if team else "neutral",
            "is_ai": team.is_ai if team else False,
            "movement": {
                "can_move": position.can_move,
                "has_moved": position.has_moved,
                "movement_speed": getattr(position, 'movement_speed', 3)
            },
            "stats": {
                "hp": {
                    "current": stats.current_hp,
                    "max": stats.max_hp
                },
                "mp": {
                    "current": stats.current_mp,
                    "max": stats.max_mp
                },
                "attributes": stats.attributes,
                "alive": stats.alive
            }
        }
        
        # Add equipment data
        if equipment:
            equipment.calculate_bonuses()
            unit_data["equipment"] = {
                "attack_bonus": equipment.total_attack_bonus,
                "defense_bonus": equipment.total_defense_bonus,
                "accuracy_bonus": equipment.total_accuracy_bonus,
                "critical_bonus": equipment.total_critical_bonus,
                "active_abilities": equipment.active_abilities,
                "status_immunities": equipment.status_immunities
            }
        
        # Add status effects
        if status_effects:
            unit_data["status_effects"] = status_effects.get_effect_summary()
        
        return unit_data
    
    async def _get_movement_positions(self, session_id: str, entity_id: EntityID) -> List[Dict[str, Any]]:
        """Get valid movement positions for a unit"""
        position = self.game_engine.ecs.get_component(entity_id, PositionComponent)
        if not position:
            return []
        
        movement_speed = getattr(position, 'movement_speed', 3)
        valid_positions = []
        
        # Simple movement calculation (would be more sophisticated in practice)
        for dx in range(-movement_speed, movement_speed + 1):
            for dy in range(-movement_speed, movement_speed + 1):
                if abs(dx) + abs(dy) <= movement_speed and (dx != 0 or dy != 0):
                    target_x = position.x + dx
                    target_y = position.y + dy
                    
                    # Basic validation (would check for obstacles, etc.)
                    if target_x >= 0 and target_y >= 0 and target_x < 10 and target_y < 10:
                        valid_positions.append({
                            "x": target_x,
                            "y": target_y,
                            "distance": abs(dx) + abs(dy)
                        })
        
        return valid_positions
    
    async def _get_attack_targets(self, session_id: str, entity_id: EntityID) -> List[Dict[str, Any]]:
        """Get valid attack targets for a unit"""
        position = self.game_engine.ecs.get_component(entity_id, PositionComponent)
        team = self.game_engine.ecs.get_component(entity_id, TeamComponent)
        
        if not position or not team:
            return []
        
        attack_range = 1  # Default attack range
        targets = []
        
        # Find all enemy units within range
        entities_with_position = self.game_engine.ecs.get_entities_with_components([PositionComponent, TeamComponent])
        
        for target_entity_id in entities_with_position:
            if target_entity_id == entity_id:
                continue
            
            target_position = self.game_engine.ecs.get_component(target_entity_id, PositionComponent)
            target_team = self.game_engine.ecs.get_component(target_entity_id, TeamComponent)
            target_stats = self.game_engine.ecs.get_component(target_entity_id, StatsComponent)
            
            if not target_position or not target_team or not target_stats:
                continue
            
            # Check if target is enemy and alive
            if target_team.team != team.team and target_stats.alive:
                distance = abs(target_position.x - position.x) + abs(target_position.y - position.y)
                if distance <= attack_range:
                    targets.append({
                        "unit_id": str(target_entity_id),
                        "position": {
                            "x": target_position.x,
                            "y": target_position.y
                        },
                        "distance": distance,
                        "team": target_team.team,
                        "hp": {
                            "current": target_stats.current_hp,
                            "max": target_stats.max_hp
                        }
                    })
        
        return targets
    
    async def start_server(self):
        """Start the MCP server"""
        logger.info("Starting MCP Gateway server", port=self.port)
        await self.mcp.run(transport="stdio")
    
    async def run_server_http(self):
        """Run MCP server over HTTP for testing"""
        import uvicorn
        
        # Create a simple HTTP wrapper for testing
        from fastapi import FastAPI
        
        app = FastAPI(title="Apex Tactics MCP Gateway", version="1.0.0")
        
        @app.get("/tools")
        async def list_tools():
            """List available MCP tools"""
            return {
                "tools": [
                    {
                        "name": "get_game_sessions",
                        "description": "Get list of all active game sessions"
                    },
                    {
                        "name": "get_session_state",
                        "description": "Get detailed state for a specific game session"
                    },
                    {
                        "name": "get_battlefield_state", 
                        "description": "Get battlefield information for a session"
                    },
                    {
                        "name": "get_all_units",
                        "description": "Get information about all units in a session"
                    },
                    {
                        "name": "get_unit_details",
                        "description": "Get detailed information about a specific unit"
                    },
                    {
                        "name": "get_available_actions",
                        "description": "Get available actions for a specific unit"
                    },
                    {
                        "name": "execute_unit_action",
                        "description": "Execute an action for a unit"
                    },
                    {
                        "name": "get_turn_info",
                        "description": "Get current turn information for a session"
                    },
                    {
                        "name": "analyze_tactical_situation",
                        "description": "Analyze the current tactical situation"
                    },
                    {
                        "name": "get_game_statistics",
                        "description": "Get comprehensive game statistics"
                    },
                    {
                        "name": "send_notification",
                        "description": "Send a notification to players"
                    },
                    {
                        "name": "highlight_tiles",
                        "description": "Highlight tiles on the battlefield"
                    },
                    {
                        "name": "create_test_session",
                        "description": "Create a test game session"
                    }
                ]
            }
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "active_sessions": len(self.game_engine.active_sessions)
            }
        
        logger.info("Starting MCP Gateway HTTP server", port=self.port)
        uvicorn.run(app, host="0.0.0.0", port=self.port)


# Entry point for running the MCP server standalone
if __name__ == "__main__":
    import sys
    import os
    
    # Add src to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))
    
    from src.engine.game_engine import GameEngine, GameConfig
    
    async def main():
        # Create game engine
        config = GameConfig()
        engine = GameEngine(config)
        
        # Create and start MCP gateway
        gateway = GameEngineMCPGateway(engine, port=8004)
        
        if len(sys.argv) > 1 and sys.argv[1] == "--http":
            # Run HTTP server for testing
            await gateway.run_server_http()
        else:
            # Run standard MCP server
            await gateway.start_server()
    
    asyncio.run(main())