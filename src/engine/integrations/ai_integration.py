"""
AI Integration Manager

Coordinates AI decision making with game engine systems,
managing AI unit control and strategic analysis.
"""

import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum

import structlog

from ...core.ecs import EntityID, ECSManager
from ...core.events import EventBus, GameEvent, EventType
from ..components.stats_component import StatsComponent
from ..components.position_component import PositionComponent
from ..components.team_component import TeamComponent
from ..components.equipment_component import EquipmentComponent
from ..components.status_effects_component import StatusEffectsComponent
from ..battlefield import Battlefield
from ..game_state import GameStateManager
from .ai_websocket import AIWebSocketClient

logger = structlog.get_logger()


class AIControlLevel(str, Enum):
    """AI control levels matching Phase 2 implementation"""
    SCRIPTED = "scripted"      # Basic scripted behavior
    STRATEGIC = "strategic"    # Strategic decision making
    ADAPTIVE = "adaptive"      # Adaptive learning AI
    LEARNING = "learning"      # Advanced learning AI


class AIDecisionType(str, Enum):
    """Types of AI decisions"""
    MOVE = "move"
    ATTACK = "attack"
    ABILITY = "ability"
    DEFEND = "defend"
    WAIT = "wait"
    RETREAT = "retreat"


class AIIntegrationManager:
    """Manages AI integration with game engine"""
    
    def __init__(self, ecs: ECSManager, event_bus: EventBus, 
                 battlefield: Battlefield, game_state: GameStateManager,
                 ai_service_url: str = "ws://localhost:8003/ws"):
        self.ecs = ecs
        self.event_bus = event_bus
        self.battlefield = battlefield
        self.game_state = game_state
        
        # AI WebSocket client
        self.ai_client = AIWebSocketClient(ai_service_url, event_bus)
        
        # AI unit tracking
        self.ai_units: Dict[str, Set[EntityID]] = {}  # session_id -> set of AI unit IDs
        self.unit_control_levels: Dict[EntityID, AIControlLevel] = {}
        self.pending_decisions: Dict[str, Dict[str, Any]] = {}  # request_id -> decision context
        
        # Performance tracking
        self.decision_times: List[float] = []
        self.last_state_update: Dict[str, datetime] = {}
        
        # Event subscriptions
        self._subscribe_to_events()
        
        logger.info("AI Integration Manager initialized")
    
    def _subscribe_to_events(self):
        """Subscribe to relevant game events"""
        self.event_bus.subscribe(EventType.TURN_START, self._on_turn_start)
        self.event_bus.subscribe(EventType.TURN_END, self._on_turn_end)
        self.event_bus.subscribe(EventType.UNIT_SPAWNED, self._on_unit_spawned)
        self.event_bus.subscribe(EventType.UNIT_DIED, self._on_unit_died)
        self.event_bus.subscribe(EventType.AI_DECISION_MADE, self._on_ai_decision_made)
        self.event_bus.subscribe(EventType.GAME_START, self._on_game_start)
        self.event_bus.subscribe(EventType.GAME_END, self._on_game_end)
    
    async def initialize(self) -> bool:
        """Initialize AI integration"""
        success = await self.ai_client.connect()
        if success:
            logger.info("AI integration initialized successfully")
        else:
            logger.error("Failed to initialize AI integration")
        return success
    
    async def shutdown(self):
        """Shutdown AI integration"""
        await self.ai_client.cleanup()
        self.ai_units.clear()
        self.unit_control_levels.clear()
        self.pending_decisions.clear()
        logger.info("AI integration shut down")
    
    async def _on_turn_start(self, event: GameEvent):
        """Handle turn start event"""
        session_id = event.session_id
        current_player = event.data.get("current_player")
        
        if not current_player:
            return
        
        # Check if current player has AI units
        ai_units = await self._get_ai_units_for_player(session_id, current_player)
        
        if ai_units:
            logger.info("Processing AI turn", 
                       session_id=session_id, 
                       player=current_player,
                       unit_count=len(ai_units))
            
            # Send updated game state to AI
            await self._send_game_state_update(session_id)
            
            # Request decisions for all AI units
            await self._request_ai_decisions_for_units(session_id, ai_units)
    
    async def _on_turn_end(self, event: GameEvent):
        """Handle turn end event"""
        session_id = event.session_id
        # Update AI with turn results
        await self._send_game_state_update(session_id)
    
    async def _on_unit_spawned(self, event: GameEvent):
        """Handle unit spawn event"""
        session_id = event.session_id
        unit_id = event.data.get("unit_id")
        
        if unit_id:
            entity_id = EntityID(unit_id)
            
            # Check if this is an AI unit
            team_component = self.ecs.get_component(entity_id, TeamComponent)
            if team_component and team_component.is_ai:
                await self._register_ai_unit(session_id, entity_id, team_component.team)
                
                # Notify AI service
                unit_data = await self._get_unit_data(entity_id)
                await self.ai_client.send_unit_event(session_id, "spawn", unit_data)
    
    async def _on_unit_died(self, event: GameEvent):
        """Handle unit death event"""
        session_id = event.session_id
        unit_id = event.data.get("unit_id")
        
        if unit_id:
            entity_id = EntityID(unit_id)
            await self._unregister_ai_unit(session_id, entity_id)
            
            # Notify AI service
            unit_data = {"unit_id": unit_id, "cause": event.data.get("cause", "unknown")}
            await self.ai_client.send_unit_event(session_id, "death", unit_data)
    
    async def _on_ai_decision_made(self, event: GameEvent):
        """Handle AI decision response"""
        request_id = event.data.get("request_id")
        decision = event.data.get("decision", {})
        confidence = event.data.get("confidence", 0.0)
        
        if request_id not in self.pending_decisions:
            logger.warning("Received decision for unknown request", request_id=request_id)
            return
        
        # Get decision context
        context = self.pending_decisions.pop(request_id)
        session_id = context["session_id"]
        entity_id = context["entity_id"]
        
        # Record decision time
        decision_time = (datetime.now() - context["request_time"]).total_seconds()
        self.decision_times.append(decision_time)
        
        logger.info("Executing AI decision", 
                   entity_id=str(entity_id),
                   decision_type=decision.get("action_type"),
                   confidence=confidence,
                   decision_time=decision_time)
        
        # Execute the AI decision
        await self._execute_ai_decision(session_id, entity_id, decision)
    
    async def _on_game_start(self, event: GameEvent):
        """Handle game start event"""
        session_id = event.session_id
        
        # Send battle start notification to AI
        battle_info = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        await self.ai_client.send_battle_start(session_id, battle_info)
    
    async def _on_game_end(self, event: GameEvent):
        """Handle game end event"""
        session_id = event.session_id
        winner = event.data.get("winner")
        
        # Send battle end notification to AI
        battle_result = {
            "session_id": session_id,
            "winner": winner,
            "timestamp": datetime.now().isoformat()
        }
        await self.ai_client.send_battle_end(session_id, battle_result)
        
        # Clean up session AI units
        if session_id in self.ai_units:
            del self.ai_units[session_id]
    
    async def _get_ai_units_for_player(self, session_id: str, player_id: str) -> List[EntityID]:
        """Get AI units belonging to a specific player"""
        if session_id not in self.ai_units:
            return []
        
        ai_units = []
        for entity_id in self.ai_units[session_id]:
            team_component = self.ecs.get_component(entity_id, TeamComponent)
            if team_component and team_component.team == player_id:
                ai_units.append(entity_id)
        
        return ai_units
    
    async def _register_ai_unit(self, session_id: str, entity_id: EntityID, team: str):
        """Register an AI unit"""
        if session_id not in self.ai_units:
            self.ai_units[session_id] = set()
        
        self.ai_units[session_id].add(entity_id)
        
        # Set default control level based on team or configuration
        self.unit_control_levels[entity_id] = AIControlLevel.STRATEGIC
        
        logger.info("Registered AI unit", 
                   session_id=session_id,
                   entity_id=str(entity_id),
                   team=team)
    
    async def _unregister_ai_unit(self, session_id: str, entity_id: EntityID):
        """Unregister an AI unit"""
        if session_id in self.ai_units:
            self.ai_units[session_id].discard(entity_id)
        
        self.unit_control_levels.pop(entity_id, None)
        
        logger.info("Unregistered AI unit", 
                   session_id=session_id,
                   entity_id=str(entity_id))
    
    async def _send_game_state_update(self, session_id: str):
        """Send current game state to AI service"""
        # Throttle updates to avoid spam
        now = datetime.now()
        if session_id in self.last_state_update:
            elapsed = (now - self.last_state_update[session_id]).total_seconds()
            if elapsed < 1.0:  # Minimum 1 second between updates
                return
        
        self.last_state_update[session_id] = now
        
        # Build game state
        game_state = await self._build_game_state(session_id)
        await self.ai_client.send_game_state_update(session_id, game_state)
    
    async def _build_game_state(self, session_id: str) -> Dict[str, Any]:
        """Build comprehensive game state for AI"""
        # Get battlefield state
        battlefield_state = {
            "grid_size": {"width": self.battlefield.width, "height": self.battlefield.height},
            "terrain": await self._get_terrain_data(session_id),
            "units": await self._get_all_units_data(session_id),
            "obstacles": await self._get_obstacles_data(session_id)
        }
        
        # Get game state
        session_state = await self.game_state.get_state(session_id)
        
        # Get turn information
        turn_info = {}
        if hasattr(self, 'turn_system'):
            turn_info = await self.turn_system.get_turn_info(session_id)
        
        return {
            "session_id": session_id,
            "battlefield": battlefield_state,
            "game_state": session_state,
            "turn_info": turn_info,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_terrain_data(self, session_id: str) -> List[List[str]]:
        """Get terrain data for battlefield"""
        terrain_grid = []
        for y in range(self.battlefield.height):
            row = []
            for x in range(self.battlefield.width):
                tile = self.battlefield.get_tile(x, y)
                row.append(tile.terrain_type.value if tile else "empty")
            terrain_grid.append(row)
        return terrain_grid
    
    async def _get_all_units_data(self, session_id: str) -> List[Dict[str, Any]]:
        """Get data for all units on battlefield"""
        units_data = []
        
        # Get all entities with position component
        entities_with_position = self.ecs.get_entities_with_components([PositionComponent])
        
        for entity_id in entities_with_position:
            unit_data = await self._get_unit_data(entity_id)
            if unit_data:
                units_data.append(unit_data)
        
        return units_data
    
    async def _get_obstacles_data(self, session_id: str) -> List[Dict[str, Any]]:
        """Get obstacle data"""
        # This would be implemented based on obstacle system
        return []
    
    async def _get_unit_data(self, entity_id: EntityID) -> Optional[Dict[str, Any]]:
        """Get comprehensive data for a single unit"""
        # Get all relevant components
        position = self.ecs.get_component(entity_id, PositionComponent)
        stats = self.ecs.get_component(entity_id, StatsComponent)
        team = self.ecs.get_component(entity_id, TeamComponent)
        equipment = self.ecs.get_component(entity_id, EquipmentComponent)
        status_effects = self.ecs.get_component(entity_id, StatusEffectsComponent)
        
        if not position or not stats:
            return None
        
        unit_data = {
            "unit_id": str(entity_id),
            "position": {"x": position.x, "y": position.y, "z": position.z},
            "team": team.team if team else "neutral",
            "is_ai": team.is_ai if team else False,
            "stats": {
                "hp": {"current": stats.current_hp, "max": stats.max_hp},
                "mp": {"current": stats.current_mp, "max": stats.max_mp},
                "attributes": stats.attributes,
                "alive": stats.alive
            },
            "movement": {
                "can_move": position.can_move,
                "has_moved": position.has_moved,
                "movement_speed": position.movement_speed
            }
        }
        
        # Add equipment data if available
        if equipment:
            equipment.calculate_bonuses()
            unit_data["equipment"] = {
                "attack_bonus": equipment.total_attack_bonus,
                "defense_bonus": equipment.total_defense_bonus,
                "abilities": equipment.active_abilities
            }
        
        # Add status effects if available
        if status_effects:
            unit_data["status_effects"] = status_effects.get_effect_summary()
        
        return unit_data
    
    async def _request_ai_decisions_for_units(self, session_id: str, ai_units: List[EntityID]):
        """Request AI decisions for multiple units"""
        game_state = await self._build_game_state(session_id)
        
        for entity_id in ai_units:
            await self._request_ai_decision_for_unit(session_id, entity_id, game_state)
    
    async def _request_ai_decision_for_unit(self, session_id: str, entity_id: EntityID, 
                                          game_state: Dict[str, Any]):
        """Request AI decision for a single unit"""
        # Get available actions for this unit
        available_actions = await self._get_available_actions(session_id, entity_id)
        
        if not available_actions:
            logger.debug("No available actions for AI unit", entity_id=str(entity_id))
            return
        
        # Request decision from AI service
        request_id = await self.ai_client.request_ai_decision(
            session_id, game_state, str(entity_id), available_actions
        )
        
        if request_id:
            # Store decision context
            self.pending_decisions[request_id] = {
                "session_id": session_id,
                "entity_id": entity_id,
                "request_time": datetime.now(),
                "available_actions": available_actions
            }
    
    async def _get_available_actions(self, session_id: str, entity_id: EntityID) -> List[Dict[str, Any]]:
        """Get available actions for a unit"""
        actions = []
        
        position = self.ecs.get_component(entity_id, PositionComponent)
        stats = self.ecs.get_component(entity_id, StatsComponent)
        status_effects = self.ecs.get_component(entity_id, StatusEffectsComponent)
        
        if not position or not stats or not stats.alive:
            return actions
        
        # Check if unit can act
        can_act = True
        if status_effects:
            can_act = status_effects.can_act()
        
        if not can_act:
            actions.append({
                "type": AIDecisionType.WAIT.value,
                "description": "Unit cannot act due to status effects"
            })
            return actions
        
        # Movement actions
        if position.can_move and not position.has_moved:
            move_positions = await self._get_valid_move_positions(session_id, entity_id)
            for pos in move_positions:
                actions.append({
                    "type": AIDecisionType.MOVE.value,
                    "target_position": pos,
                    "description": f"Move to ({pos['x']}, {pos['y']})"
                })
        
        # Attack actions
        attack_targets = await self._get_attack_targets(session_id, entity_id)
        for target in attack_targets:
            actions.append({
                "type": AIDecisionType.ATTACK.value,
                "target_id": target["unit_id"],
                "description": f"Attack {target['unit_id']}"
            })
        
        # Ability actions (placeholder for future implementation)
        # This would check equipment abilities and spell abilities
        
        # Wait action (always available)
        actions.append({
            "type": AIDecisionType.WAIT.value,
            "description": "Wait and end turn"
        })
        
        return actions
    
    async def _get_valid_move_positions(self, session_id: str, entity_id: EntityID) -> List[Dict[str, Any]]:
        """Get valid movement positions for a unit"""
        position = self.ecs.get_component(entity_id, PositionComponent)
        if not position:
            return []
        
        # Get movement range based on movement speed
        movement_range = position.movement_speed
        current_pos = (position.x, position.y)
        
        valid_positions = []
        
        # Check all positions within movement range
        for dx in range(-movement_range, movement_range + 1):
            for dy in range(-movement_range, movement_range + 1):
                target_x = position.x + dx
                target_y = position.y + dy
                
                # Skip current position
                if dx == 0 and dy == 0:
                    continue
                
                # Check if position is valid and reachable
                if await self._is_valid_move_position(session_id, entity_id, target_x, target_y):
                    distance = abs(dx) + abs(dy)  # Manhattan distance
                    if distance <= movement_range:
                        valid_positions.append({
                            "x": target_x,
                            "y": target_y,
                            "distance": distance
                        })
        
        return valid_positions
    
    async def _is_valid_move_position(self, session_id: str, entity_id: EntityID, 
                                    x: int, y: int) -> bool:
        """Check if a position is valid for movement"""
        # Check battlefield bounds
        if not (0 <= x < self.battlefield.width and 0 <= y < self.battlefield.height):
            return False
        
        # Check if tile is passable
        tile = self.battlefield.get_tile(x, y)
        if not tile or not tile.is_passable:
            return False
        
        # Check if position is occupied
        entities_with_position = self.ecs.get_entities_with_components([PositionComponent])
        for other_entity_id in entities_with_position:
            if other_entity_id == entity_id:
                continue
            
            other_position = self.ecs.get_component(other_entity_id, PositionComponent)
            if other_position and other_position.x == x and other_position.y == y:
                return False
        
        return True
    
    async def _get_attack_targets(self, session_id: str, entity_id: EntityID) -> List[Dict[str, Any]]:
        """Get valid attack targets for a unit"""
        position = self.ecs.get_component(entity_id, PositionComponent)
        team = self.ecs.get_component(entity_id, TeamComponent)
        
        if not position or not team:
            return []
        
        attack_range = 1  # Default melee range
        targets = []
        
        # Find all enemy units within attack range
        entities_with_position = self.ecs.get_entities_with_components([PositionComponent, TeamComponent])
        
        for target_entity_id in entities_with_position:
            if target_entity_id == entity_id:
                continue
            
            target_position = self.ecs.get_component(target_entity_id, PositionComponent)
            target_team = self.ecs.get_component(target_entity_id, TeamComponent)
            target_stats = self.ecs.get_component(target_entity_id, StatsComponent)
            
            if not target_position or not target_team or not target_stats:
                continue
            
            # Check if target is enemy and alive
            if target_team.team != team.team and target_stats.alive:
                # Check if target is within attack range
                distance = abs(target_position.x - position.x) + abs(target_position.y - position.y)
                if distance <= attack_range:
                    targets.append({
                        "unit_id": str(target_entity_id),
                        "position": {"x": target_position.x, "y": target_position.y},
                        "distance": distance
                    })
        
        return targets
    
    async def _execute_ai_decision(self, session_id: str, entity_id: EntityID, decision: Dict[str, Any]):
        """Execute an AI decision"""
        action_type = decision.get("action_type")
        
        try:
            if action_type == AIDecisionType.MOVE.value:
                await self._execute_move_action(session_id, entity_id, decision)
            elif action_type == AIDecisionType.ATTACK.value:
                await self._execute_attack_action(session_id, entity_id, decision)
            elif action_type == AIDecisionType.ABILITY.value:
                await self._execute_ability_action(session_id, entity_id, decision)
            elif action_type == AIDecisionType.WAIT.value:
                await self._execute_wait_action(session_id, entity_id, decision)
            else:
                logger.warning("Unknown AI action type", action_type=action_type)
                
        except Exception as e:
            logger.error("Failed to execute AI decision", 
                        entity_id=str(entity_id),
                        action_type=action_type,
                        error=str(e))
    
    async def _execute_move_action(self, session_id: str, entity_id: EntityID, decision: Dict[str, Any]):
        """Execute AI move action"""
        target_pos = decision.get("target_position", {})
        target_x = target_pos.get("x")
        target_y = target_pos.get("y")
        
        if target_x is None or target_y is None:
            logger.warning("Invalid move target position", decision=decision)
            return
        
        # Update position component
        position = self.ecs.get_component(entity_id, PositionComponent)
        if position:
            position.x = target_x
            position.y = target_y
            position.has_moved = True
            
            # Emit movement event
            await self.event_bus.emit(GameEvent(
                type=EventType.UNIT_MOVED,
                session_id=session_id,
                data={
                    "unit_id": str(entity_id),
                    "from_position": {"x": position.x, "y": position.y},
                    "to_position": {"x": target_x, "y": target_y},
                    "ai_controlled": True
                }
            ))
            
            logger.info("AI unit moved", 
                       entity_id=str(entity_id),
                       to_position=f"({target_x}, {target_y})")
    
    async def _execute_attack_action(self, session_id: str, entity_id: EntityID, decision: Dict[str, Any]):
        """Execute AI attack action"""
        target_id = decision.get("target_id")
        if not target_id:
            logger.warning("Invalid attack target", decision=decision)
            return
        
        target_entity_id = EntityID(target_id)
        
        # Emit attack event
        await self.event_bus.emit(GameEvent(
            type=EventType.UNIT_ATTACKED,
            session_id=session_id,
            data={
                "attacker_id": str(entity_id),
                "target_id": target_id,
                "ai_controlled": True
            }
        ))
        
        logger.info("AI unit attacked", 
                   attacker=str(entity_id),
                   target=target_id)
    
    async def _execute_ability_action(self, session_id: str, entity_id: EntityID, decision: Dict[str, Any]):
        """Execute AI ability action"""
        # Placeholder for ability system integration
        logger.info("AI ability action requested", 
                   entity_id=str(entity_id),
                   ability=decision.get("ability_name"))
    
    async def _execute_wait_action(self, session_id: str, entity_id: EntityID, decision: Dict[str, Any]):
        """Execute AI wait action"""
        logger.debug("AI unit waiting", entity_id=str(entity_id))
    
    def set_unit_control_level(self, entity_id: EntityID, control_level: AIControlLevel):
        """Set AI control level for a unit"""
        self.unit_control_levels[entity_id] = control_level
        logger.info("Set AI control level", 
                   entity_id=str(entity_id),
                   level=control_level.value)
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """Get AI integration statistics"""
        avg_decision_time = 0.0
        if self.decision_times:
            avg_decision_time = sum(self.decision_times) / len(self.decision_times)
        
        return {
            "connection_status": self.ai_client.get_connection_status(),
            "active_ai_units": sum(len(units) for units in self.ai_units.values()),
            "pending_decisions": len(self.pending_decisions),
            "average_decision_time": avg_decision_time,
            "total_decisions": len(self.decision_times)
        }