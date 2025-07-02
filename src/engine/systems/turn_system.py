"""
Turn System

Manages turn-based gameplay, turn order, action phases,
and turn progression for tactical RPG mechanics.
"""

import asyncio
from typing import Dict, Any, List, Optional, Set, Type
from datetime import datetime, timedelta

import structlog

from ...core.ecs import System, EntityID, ECSManager, BaseComponent, Entity
from ...core.events import EventBus, GameEvent, EventType
from ..components.stats_component import StatsComponent
from ..components.position_component import PositionComponent
from ..components.team_component import TeamComponent
from ..components.status_effects_component import StatusEffectsComponent

logger = structlog.get_logger()


class TurnSystem(System):
    """System for managing turn-based gameplay"""
    
    def __init__(self, ecs: ECSManager, event_bus: EventBus):
        super().__init__()
        self.ecs = ecs
        self.event_bus = event_bus
        self.execution_order = 10  # Early in update cycle
        
        # Turn state per session
        self.session_turns: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.default_turn_time = 30.0
        self.action_points_per_turn = 2
        
        logger.info("Turn system initialized")
    
    def get_required_components(self) -> Set[Type[BaseComponent]]:
        """Return required components for this system"""
        return {StatsComponent, PositionComponent, TeamComponent}
    
    def update(self, delta_time: float, entities: List[Entity]):
        """Update turn system for all entities"""
        # This is the required abstract method signature
        # The actual turn logic is handled separately by session-specific methods
        pass
    
    async def update_for_session(self, session_id: str, delta_time: float):
        """Update turn system for a specific session"""
        if session_id not in self.session_turns:
            return
        
        turn_data = self.session_turns[session_id]
        
        # Check turn timer
        if turn_data.get("turn_active", False):
            await self._check_turn_timer(session_id, delta_time)
        
        # Process turn phases
        await self._process_turn_phases(session_id)
        
        # Reset unit states at turn start
        await self._reset_unit_turn_states(session_id)
    
    async def initialize_for_session(self, session_id: str, players: List[str], 
                                   turn_config: Optional[Dict[str, Any]] = None):
        """Initialize turn system for a session"""
        config = turn_config or {}
        
        turn_data = {
            "players": players,
            "turn_order": players.copy(),
            "current_turn": 0,
            "current_player_index": 0,
            "current_player": players[0] if players else None,
            "turn_active": False,
            "turn_start_time": None,
            "turn_time_limit": config.get("turn_time_limit", self.default_turn_time),
            "actions_remaining": self.action_points_per_turn,
            "turn_phase": "start",
            "units_acted": set(),
            "simultaneous_turns": config.get("simultaneous_turns", False)
        }
        
        self.session_turns[session_id] = turn_data
        
        logger.info("Turn system initialized for session", 
                   session_id=session_id, 
                   players=players)
    
    async def start_turn(self, session_id: str) -> bool:
        """Start a new turn"""
        if session_id not in self.session_turns:
            return False
        
        turn_data = self.session_turns[session_id]
        
        # Increment turn counter
        turn_data["current_turn"] += 1
        turn_data["turn_active"] = True
        turn_data["turn_start_time"] = datetime.now()
        turn_data["turn_phase"] = "start"
        turn_data["actions_remaining"] = self.action_points_per_turn
        turn_data["units_acted"].clear()
        
        # Reset all unit states for new turn
        await self._reset_all_units_for_turn(session_id)
        
        # Emit turn start event
        await self.event_bus.emit(GameEvent(
            type=EventType.TURN_START,
            session_id=session_id,
            data={
                "turn_number": turn_data["current_turn"],
                "current_player": turn_data["current_player"],
                "time_limit": turn_data["turn_time_limit"]
            }
        ))
        
        logger.info("Turn started", 
                   session_id=session_id, 
                   turn=turn_data["current_turn"],
                   player=turn_data["current_player"])
        
        return True
    
    async def end_turn(self, session_id: str, player_id: str) -> bool:
        """End current turn"""
        if session_id not in self.session_turns:
            return False
        
        turn_data = self.session_turns[session_id]
        
        # Validate turn ending
        if not turn_data["turn_active"]:
            return False
        
        if turn_data["current_player"] != player_id:
            return False
        
        # Process end of turn effects
        await self._process_end_of_turn_effects(session_id)
        
        # Emit turn end event
        await self.event_bus.emit(GameEvent(
            type=EventType.TURN_END,
            session_id=session_id,
            data={
                "turn_number": turn_data["current_turn"],
                "player": player_id,
                "actions_taken": turn_data["actions_remaining"] != self.action_points_per_turn
            }
        ))
        
        # Advance to next player
        if not turn_data["simultaneous_turns"]:
            await self._advance_turn(session_id)
        else:
            await self._handle_simultaneous_turn_end(session_id, player_id)
        
        logger.info("Turn ended", 
                   session_id=session_id, 
                   player=player_id)
        
        return True
    
    async def _advance_turn(self, session_id: str):
        """Advance to next player in turn order"""
        turn_data = self.session_turns[session_id]
        
        # Move to next player
        turn_data["current_player_index"] = (turn_data["current_player_index"] + 1) % len(turn_data["turn_order"])
        turn_data["current_player"] = turn_data["turn_order"][turn_data["current_player_index"]]
        
        # If back to first player, start new turn
        if turn_data["current_player_index"] == 0:
            await self.start_turn(session_id)
        else:
            # Continue with next player in same turn
            turn_data["turn_start_time"] = datetime.now()
            turn_data["actions_remaining"] = self.action_points_per_turn
            turn_data["units_acted"].clear()
            
            # Reset movement for current player's units
            await self._reset_player_units_for_turn(session_id, turn_data["current_player"])
    
    async def _handle_simultaneous_turn_end(self, session_id: str, player_id: str):
        """Handle end of turn in simultaneous mode"""
        turn_data = self.session_turns[session_id]
        
        # Mark player as finished
        if "players_finished" not in turn_data:
            turn_data["players_finished"] = set()
        
        turn_data["players_finished"].add(player_id)
        
        # Check if all players finished
        if len(turn_data["players_finished"]) >= len(turn_data["players"]):
            # All players finished, start new turn
            turn_data["players_finished"].clear()
            await self.start_turn(session_id)
    
    async def _reset_all_units_for_turn(self, session_id: str):
        """Reset all units for new turn"""
        entities_with_position = self.get_entities_with_components(session_id, PositionComponent)
        
        for entity_id in entities_with_position:
            await self._reset_unit_for_turn(session_id, entity_id)
    
    async def _reset_player_units_for_turn(self, session_id: str, player_id: str):
        """Reset units for specific player's turn"""
        entities_with_team = self.get_entities_with_components(session_id, TeamComponent)
        
        for entity_id in entities_with_team:
            team_component = self.ecs.get_component(entity_id, TeamComponent)
            if team_component and team_component.team == player_id:
                await self._reset_unit_for_turn(session_id, entity_id)
    
    async def _reset_unit_for_turn(self, session_id: str, entity_id: EntityID):
        """Reset individual unit for turn"""
        # Reset movement
        position_component = self.ecs.get_component(entity_id, PositionComponent)
        if position_component:
            position_component.reset_movement()
        
        # Process status effects
        status_component = self.ecs.get_component(entity_id, StatusEffectsComponent)
        if status_component:
            expired_effects = status_component.update_effects(1.0)  # 1 turn duration
            
            # Log expired effects
            if expired_effects:
                logger.debug("Status effects expired", 
                           entity_id=str(entity_id), 
                           effects=expired_effects)
    
    async def _process_end_of_turn_effects(self, session_id: str):
        """Process effects that trigger at end of turn"""
        entities_with_status = self.get_entities_with_components(session_id, StatusEffectsComponent)
        
        for entity_id in entities_with_status:
            stats_component = self.ecs.get_component(entity_id, StatsComponent)
            status_component = self.ecs.get_component(entity_id, StatusEffectsComponent)
            
            if stats_component and status_component:
                # Process damage over time effects
                await self._process_dot_effects(entity_id, stats_component, status_component)
                
                # Process healing over time effects
                await self._process_hot_effects(entity_id, stats_component, status_component)
                
                # Regenerate MP
                await self._regenerate_mp(entity_id, stats_component)
    
    async def _process_dot_effects(self, entity_id: EntityID, stats: StatsComponent, 
                                  status: StatusEffectsComponent):
        """Process damage over time effects"""
        dot_effects = ["poison", "burn", "bleed"]
        
        for effect in dot_effects:
            if status.has_effect(effect):
                intensity = status.get_effect_intensity(effect)
                
                if effect == "poison":
                    damage = stats.max_hp * 0.05 * intensity  # 5% max HP per turn
                elif effect == "burn":
                    damage = stats.max_hp * 0.08 * intensity  # 8% max HP per turn
                elif effect == "bleed":
                    damage = stats.max_hp * 0.03 * intensity  # 3% max HP per turn
                else:
                    damage = 0
                
                if damage > 0:
                    stats.take_damage(int(damage))
                    
                    logger.debug("DOT damage applied", 
                               entity_id=str(entity_id), 
                               effect=effect, 
                               damage=damage)
                    
                    # Check for death
                    if not stats.alive:
                        await self.event_bus.emit(GameEvent(
                            type=EventType.UNIT_DIED,
                            session_id=str(entity_id).split('_')[0],  # Extract session from entity ID
                            data={"unit_id": str(entity_id), "cause": effect}
                        ))
    
    async def _process_hot_effects(self, entity_id: EntityID, stats: StatsComponent, 
                                  status: StatusEffectsComponent):
        """Process healing over time effects"""
        hot_effects = ["regeneration", "blessed"]
        
        for effect in hot_effects:
            if status.has_effect(effect):
                intensity = status.get_effect_intensity(effect)
                
                if effect == "regeneration":
                    healing = stats.max_hp * 0.1 * intensity  # 10% max HP per turn
                elif effect == "blessed":
                    healing = stats.max_hp * 0.05 * intensity  # 5% max HP per turn
                else:
                    healing = 0
                
                if healing > 0:
                    actual_healing = stats.heal(int(healing))
                    
                    if actual_healing > 0:
                        logger.debug("HOT healing applied", 
                                   entity_id=str(entity_id), 
                                   effect=effect, 
                                   healing=actual_healing)
    
    async def _regenerate_mp(self, entity_id: EntityID, stats: StatsComponent):
        """Regenerate MP at end of turn"""
        if stats.current_mp < stats.max_mp:
            # Regenerate 20% of max MP per turn, minimum 1
            regen_amount = max(1, int(stats.max_mp * 0.2))
            actual_regen = stats.restore_mp(regen_amount)
            
            if actual_regen > 0:
                logger.debug("MP regenerated", 
                           entity_id=str(entity_id), 
                           amount=actual_regen)
    
    async def _check_turn_timer(self, session_id: str, delta_time: float):
        """Check if turn timer has expired"""
        turn_data = self.session_turns[session_id]
        
        if not turn_data["turn_start_time"]:
            return
        
        elapsed = (datetime.now() - turn_data["turn_start_time"]).total_seconds()
        
        if elapsed >= turn_data["turn_time_limit"]:
            # Force end turn
            current_player = turn_data["current_player"]
            logger.warning("Turn timer expired, forcing end turn", 
                         session_id=session_id, 
                         player=current_player)
            
            await self.end_turn(session_id, current_player)
    
    async def _process_turn_phases(self, session_id: str):
        """Process different turn phases"""
        turn_data = self.session_turns[session_id]
        
        if turn_data["turn_phase"] == "start":
            # Transition to movement phase
            turn_data["turn_phase"] = "movement"
        
        elif turn_data["turn_phase"] == "movement":
            # Check if movement phase should end
            # (This would be triggered by game logic)
            pass
        
        elif turn_data["turn_phase"] == "action":
            # Check if action phase should end
            pass
    
    async def _reset_unit_turn_states(self, session_id: str):
        """Reset unit states for turn processing"""
        if session_id not in self.session_turns:
            return
        
        turn_data = self.session_turns[session_id]
        
        # Only reset at start of new turn
        if turn_data["turn_phase"] != "start":
            return
        
        entities_with_stats = self.get_entities_with_components(session_id, StatsComponent)
        
        for entity_id in entities_with_stats:
            stats_component = self.ecs.get_component(entity_id, StatsComponent)
            position_component = self.ecs.get_component(entity_id, PositionComponent)
            
            # Reset action flags
            if position_component:
                position_component.has_moved = False
                position_component.can_move = True
    
    async def can_unit_act(self, session_id: str, entity_id: EntityID) -> bool:
        """Check if unit can act this turn"""
        if session_id not in self.session_turns:
            return False
        
        turn_data = self.session_turns[session_id]
        
        # Check if unit already acted
        if str(entity_id) in turn_data["units_acted"]:
            return False
        
        # Check unit status
        stats_component = self.ecs.get_component(entity_id, StatsComponent)
        if not stats_component or not stats_component.can_act():
            return False
        
        status_component = self.ecs.get_component(entity_id, StatusEffectsComponent)
        if status_component and not status_component.can_act():
            return False
        
        return True
    
    async def mark_unit_acted(self, session_id: str, entity_id: EntityID):
        """Mark unit as having acted this turn"""
        if session_id in self.session_turns:
            self.session_turns[session_id]["units_acted"].add(str(entity_id))
    
    async def consume_action_point(self, session_id: str) -> bool:
        """Consume an action point"""
        if session_id not in self.session_turns:
            return False
        
        turn_data = self.session_turns[session_id]
        
        if turn_data["actions_remaining"] > 0:
            turn_data["actions_remaining"] -= 1
            return True
        
        return False
    
    async def get_current_player(self, session_id: str) -> Optional[str]:
        """Get current player for session"""
        if session_id in self.session_turns:
            return self.session_turns[session_id]["current_player"]
        return None
    
    async def get_turn_info(self, session_id: str) -> Dict[str, Any]:
        """Get current turn information"""
        if session_id not in self.session_turns:
            return {}
        
        turn_data = self.session_turns[session_id]
        
        time_remaining = 0.0
        if turn_data["turn_start_time"]:
            elapsed = (datetime.now() - turn_data["turn_start_time"]).total_seconds()
            time_remaining = max(0, turn_data["turn_time_limit"] - elapsed)
        
        return {
            "turn_number": turn_data["current_turn"],
            "current_player": turn_data["current_player"],
            "turn_phase": turn_data["turn_phase"],
            "actions_remaining": turn_data["actions_remaining"],
            "time_remaining": time_remaining,
            "turn_active": turn_data["turn_active"],
            "units_acted": len(turn_data["units_acted"])
        }
    
    async def skip_turn(self, session_id: str, player_id: str) -> bool:
        """Skip current turn"""
        return await self.end_turn(session_id, player_id)
    
    def cleanup_session(self, session_id: str):
        """Clean up session data"""
        if session_id in self.session_turns:
            del self.session_turns[session_id]
            logger.info("Turn system session cleaned up", session_id=session_id)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get turn system statistics"""
        return {
            "active_sessions": len(self.session_turns),
            "total_turns": sum(data["current_turn"] for data in self.session_turns.values()),
            "average_turn_time": self.default_turn_time,
            "action_points_per_turn": self.action_points_per_turn
        }