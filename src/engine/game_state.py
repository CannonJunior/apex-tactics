"""
Game State Management

Manages overall game state, turn processing, victory conditions,
and state persistence for tactical RPG gameplay.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import structlog

from ..core.events import EventBus, GameEvent, EventType
from ..core.ecs import EntityID

logger = structlog.get_logger()


class GamePhase(str, Enum):
    """Game phases"""
    SETUP = "setup"
    DEPLOYMENT = "deployment"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ERROR = "error"


class TurnPhase(str, Enum):
    """Turn phases"""
    START = "start"
    MOVEMENT = "movement"
    ACTION = "action"
    END = "end"


class VictoryCondition(str, Enum):
    """Victory conditions"""
    ELIMINATE_ALL = "eliminate_all"
    CAPTURE_OBJECTIVES = "capture_objectives"
    SURVIVE_TURNS = "survive_turns"
    ESCORT_UNIT = "escort_unit"
    DEFEND_POSITION = "defend_position"


@dataclass
class PlayerState:
    """State for a single player"""
    player_id: str
    team: str
    is_active: bool = True
    is_ai: bool = False
    has_acted: bool = False
    turn_time_remaining: float = 30.0
    units_alive: int = 0
    units_total: int = 0
    
    # Victory tracking
    objectives_captured: int = 0
    objectives_required: int = 0
    
    # Resources
    action_points: int = 0
    special_resources: Dict[str, int] = field(default_factory=dict)


@dataclass
class TurnState:
    """Current turn state"""
    turn_number: int = 1
    phase: TurnPhase = TurnPhase.START
    current_player: str = ""
    players_acted: Set[str] = field(default_factory=set)
    turn_start_time: datetime = field(default_factory=datetime.now)
    time_limit: float = 30.0
    
    # Turn actions
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    events_this_turn: List[str] = field(default_factory=list)


@dataclass
class GameConditions:
    """Game victory and loss conditions"""
    victory_conditions: List[VictoryCondition] = field(default_factory=list)
    turn_limit: Optional[int] = None
    time_limit: Optional[float] = None  # In seconds
    
    # Objective locations
    objective_positions: List[tuple] = field(default_factory=list)
    escort_target: Optional[EntityID] = None
    defend_position: Optional[tuple] = None


@dataclass
class GameMetrics:
    """Game performance and analytics metrics"""
    total_turns: int = 0
    total_actions: int = 0
    damage_dealt: float = 0.0
    healing_done: float = 0.0
    units_killed: int = 0
    abilities_used: int = 0
    
    # Timing metrics
    average_turn_time: float = 0.0
    longest_turn: float = 0.0
    total_game_time: float = 0.0
    
    # AI metrics
    ai_decisions: int = 0
    ai_decision_time: float = 0.0


class GameStateManager:
    """Manages overall game state and turn processing"""
    
    def __init__(self):
        # Game sessions
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Default configuration
        self.default_config = {
            "turn_time_limit": 30.0,
            "max_turns": 100,
            "victory_conditions": ["eliminate_all"],
            "simultaneous_turns": False,
            "allow_undo": False
        }
        
        logger.info("Game state manager initialized")
    
    async def initialize_session(self, session_id: str, config: Dict[str, Any]):
        """Initialize game state for a session"""
        # Merge with default config
        session_config = {**self.default_config, **config}
        
        # Create initial game state
        game_state = {
            "session_id": session_id,
            "config": session_config,
            "phase": GamePhase.SETUP,
            "start_time": datetime.now(),
            "last_update": datetime.now(),
            
            # Players and teams
            "players": {},
            "turn_order": [],
            
            # Turn management
            "turn_state": TurnState(),
            
            # Game conditions
            "conditions": GameConditions(
                victory_conditions=[VictoryCondition(vc) for vc in session_config["victory_conditions"]],
                turn_limit=session_config.get("max_turns"),
                time_limit=session_config.get("time_limit")
            ),
            
            # Metrics and history
            "metrics": GameMetrics(),
            "history": [],
            
            # State flags
            "winner": None,
            "game_over": False,
            "paused": False
        }
        
        self.sessions[session_id] = game_state
        
        logger.info("Game session initialized", 
                   session_id=session_id, 
                   config=session_config)
    
    async def add_player(self, session_id: str, player_id: str, team: str, 
                        is_ai: bool = False) -> bool:
        """Add player to game session"""
        if session_id not in self.sessions:
            return False
        
        game_state = self.sessions[session_id]
        
        # Check if already in setup phase
        if game_state["phase"] != GamePhase.SETUP:
            return False
        
        player_state = PlayerState(
            player_id=player_id,
            team=team,
            is_ai=is_ai,
            turn_time_remaining=game_state["config"]["turn_time_limit"]
        )
        
        game_state["players"][player_id] = player_state.__dict__
        
        # Add to turn order if not simultaneous
        if not game_state["config"]["simultaneous_turns"]:
            game_state["turn_order"].append(player_id)
        
        logger.info("Player added to session", 
                   session_id=session_id, 
                   player_id=player_id, 
                   team=team)
        
        return True
    
    async def start_game(self, session_id: str) -> bool:
        """Start the game"""
        if session_id not in self.sessions:
            return False
        
        game_state = self.sessions[session_id]
        
        # Check minimum players
        if len(game_state["players"]) < 1:
            return False
        
        # Set phase to active
        game_state["phase"] = GamePhase.ACTIVE
        game_state["start_time"] = datetime.now()
        
        # Initialize first turn
        if game_state["turn_order"]:
            await self._start_turn(session_id, game_state["turn_order"][0])
        
        logger.info("Game started", session_id=session_id)
        return True
    
    async def _start_turn(self, session_id: str, player_id: str):
        """Start a new turn for a player"""
        game_state = self.sessions[session_id]
        turn_state = game_state["turn_state"]
        
        # Increment turn number if starting new round
        if player_id == game_state["turn_order"][0]:
            turn_state["turn_number"] += 1
        
        # Update turn state
        turn_state["current_player"] = player_id
        turn_state["phase"] = TurnPhase.START
        turn_state["turn_start_time"] = datetime.now().isoformat()
        turn_state["players_acted"].clear()
        turn_state["actions_taken"].clear()
        turn_state["events_this_turn"].clear()
        
        # Reset player action state
        if player_id in game_state["players"]:
            game_state["players"][player_id]["has_acted"] = False
            game_state["players"][player_id]["turn_time_remaining"] = game_state["config"]["turn_time_limit"]
        
        # Update last update time
        game_state["last_update"] = datetime.now()
        
        logger.info("Turn started", 
                   session_id=session_id, 
                   player_id=player_id, 
                   turn_number=turn_state["turn_number"])
    
    async def end_turn(self, session_id: str, player_id: str) -> bool:
        """End current player's turn"""
        if session_id not in self.sessions:
            return False
        
        game_state = self.sessions[session_id]
        turn_state = game_state["turn_state"]
        
        # Validate turn ending
        if turn_state["current_player"] != player_id:
            return False
        
        # Mark player as acted
        turn_state["players_acted"].add(player_id)
        if player_id in game_state["players"]:
            game_state["players"][player_id]["has_acted"] = True
        
        # Calculate turn time
        turn_start = datetime.fromisoformat(turn_state["turn_start_time"])
        turn_duration = (datetime.now() - turn_start).total_seconds()
        
        # Update metrics
        metrics = game_state["metrics"]
        metrics["total_turns"] += 1
        metrics["total_actions"] += len(turn_state["actions_taken"])
        
        if metrics["total_turns"] == 1:
            metrics["average_turn_time"] = turn_duration
        else:
            metrics["average_turn_time"] = (
                (metrics["average_turn_time"] * (metrics["total_turns"] - 1) + turn_duration) 
                / metrics["total_turns"]
            )
        
        metrics["longest_turn"] = max(metrics["longest_turn"], turn_duration)
        
        # Check if all players have acted (for simultaneous turns)
        if game_state["config"]["simultaneous_turns"]:
            all_acted = all(
                game_state["players"][pid]["has_acted"] 
                for pid in game_state["players"]
                if game_state["players"][pid]["is_active"]
            )
            
            if all_acted:
                await self._process_simultaneous_turn_end(session_id)
        else:
            # Move to next player
            await self._advance_to_next_player(session_id)
        
        # Update state
        game_state["last_update"] = datetime.now()
        
        logger.info("Turn ended", 
                   session_id=session_id, 
                   player_id=player_id, 
                   duration=turn_duration)
        
        return True
    
    async def _advance_to_next_player(self, session_id: str):
        """Advance to next player in turn order"""
        game_state = self.sessions[session_id]
        turn_order = game_state["turn_order"]
        current_player = game_state["turn_state"]["current_player"]
        
        # Find current player index
        try:
            current_index = turn_order.index(current_player)
            next_index = (current_index + 1) % len(turn_order)
            next_player = turn_order[next_index]
            
            # Check if next player is still active
            if (next_player in game_state["players"] and 
                game_state["players"][next_player]["is_active"]):
                await self._start_turn(session_id, next_player)
            else:
                # Skip inactive players
                await self._find_next_active_player(session_id, next_index)
                
        except ValueError:
            # Current player not in turn order, start from beginning
            if turn_order:
                await self._start_turn(session_id, turn_order[0])
    
    async def _find_next_active_player(self, session_id: str, start_index: int):
        """Find next active player starting from index"""
        game_state = self.sessions[session_id]
        turn_order = game_state["turn_order"]
        
        for i in range(len(turn_order)):
            index = (start_index + i) % len(turn_order)
            player_id = turn_order[index]
            
            if (player_id in game_state["players"] and 
                game_state["players"][player_id]["is_active"]):
                await self._start_turn(session_id, player_id)
                return
        
        # No active players found - game over
        await self.end_game(session_id, "no_active_players")
    
    async def _process_simultaneous_turn_end(self, session_id: str):
        """Process end of simultaneous turn"""
        game_state = self.sessions[session_id]
        
        # Reset all players for next turn
        for player_data in game_state["players"].values():
            player_data["has_acted"] = False
        
        # Start new simultaneous turn
        turn_state = game_state["turn_state"]
        turn_state["turn_number"] += 1
        turn_state["phase"] = TurnPhase.START
        turn_state["turn_start_time"] = datetime.now().isoformat()
        turn_state["players_acted"].clear()
    
    async def record_action(self, session_id: str, player_id: str, action: Dict[str, Any]):
        """Record a player action"""
        if session_id not in self.sessions:
            return
        
        game_state = self.sessions[session_id]
        turn_state = game_state["turn_state"]
        
        # Add action to turn history
        action_record = {
            "player_id": player_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "turn_number": turn_state["turn_number"]
        }
        
        turn_state["actions_taken"].append(action_record)
        game_state["history"].append(action_record)
        
        # Update metrics
        game_state["metrics"]["total_actions"] += 1
        
        # Update last update time
        game_state["last_update"] = datetime.now()
    
    async def check_victory_conditions(self, session_id: str) -> Optional[str]:
        """Check if any victory conditions are met"""
        if session_id not in self.sessions:
            return None
        
        game_state = self.sessions[session_id]
        conditions = game_state["conditions"]
        
        for condition in conditions["victory_conditions"]:
            winner = await self._evaluate_victory_condition(session_id, condition)
            if winner:
                return winner
        
        # Check loss conditions
        if conditions["turn_limit"] and game_state["turn_state"]["turn_number"] > conditions["turn_limit"]:
            return "draw_turn_limit"
        
        if conditions["time_limit"]:
            elapsed = (datetime.now() - datetime.fromisoformat(str(game_state["start_time"]))).total_seconds()
            if elapsed > conditions["time_limit"]:
                return "draw_time_limit"
        
        return None
    
    async def _evaluate_victory_condition(self, session_id: str, condition: VictoryCondition) -> Optional[str]:
        """Evaluate a specific victory condition"""
        game_state = self.sessions[session_id]
        
        if condition == VictoryCondition.ELIMINATE_ALL:
            # Count active teams
            active_teams = set()
            for player_data in game_state["players"].values():
                if player_data["is_active"] and player_data["units_alive"] > 0:
                    active_teams.add(player_data["team"])
            
            if len(active_teams) <= 1:
                return list(active_teams)[0] if active_teams else "draw"
        
        elif condition == VictoryCondition.CAPTURE_OBJECTIVES:
            # Check objective capture
            for player_data in game_state["players"].values():
                if (player_data["objectives_captured"] >= player_data["objectives_required"] and 
                    player_data["objectives_required"] > 0):
                    return player_data["team"]
        
        elif condition == VictoryCondition.SURVIVE_TURNS:
            # Check if any team survived required turns
            turn_limit = game_state["conditions"]["turn_limit"]
            if turn_limit and game_state["turn_state"]["turn_number"] >= turn_limit:
                # Find team with most units alive
                best_team = None
                most_units = 0
                for player_data in game_state["players"].values():
                    if player_data["units_alive"] > most_units:
                        most_units = player_data["units_alive"]
                        best_team = player_data["team"]
                
                return best_team if most_units > 0 else "draw"
        
        return None
    
    async def end_game(self, session_id: str, reason: str, winner: str = None):
        """End the game"""
        if session_id not in self.sessions:
            return
        
        game_state = self.sessions[session_id]
        
        # Update game state
        game_state["phase"] = GamePhase.ENDED
        game_state["game_over"] = True
        game_state["winner"] = winner
        
        # Calculate final metrics
        end_time = datetime.now()
        start_time = datetime.fromisoformat(str(game_state["start_time"]))
        game_state["metrics"]["total_game_time"] = (end_time - start_time).total_seconds()
        
        # Update last update time
        game_state["last_update"] = end_time
        
        logger.info("Game ended", 
                   session_id=session_id, 
                   reason=reason, 
                   winner=winner,
                   duration=game_state["metrics"]["total_game_time"])
    
    async def pause_game(self, session_id: str) -> bool:
        """Pause the game"""
        if session_id not in self.sessions:
            return False
        
        game_state = self.sessions[session_id]
        
        if game_state["phase"] == GamePhase.ACTIVE:
            game_state["phase"] = GamePhase.PAUSED
            game_state["paused"] = True
            game_state["last_update"] = datetime.now()
            
            logger.info("Game paused", session_id=session_id)
            return True
        
        return False
    
    async def resume_game(self, session_id: str) -> bool:
        """Resume paused game"""
        if session_id not in self.sessions:
            return False
        
        game_state = self.sessions[session_id]
        
        if game_state["phase"] == GamePhase.PAUSED:
            game_state["phase"] = GamePhase.ACTIVE
            game_state["paused"] = False
            game_state["last_update"] = datetime.now()
            
            logger.info("Game resumed", session_id=session_id)
            return True
        
        return False
    
    async def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current game state"""
        if session_id not in self.sessions:
            return None
        
        return self.sessions[session_id].copy()
    
    async def update_player_units(self, session_id: str, player_id: str, 
                                 units_alive: int, units_total: int):
        """Update player unit counts"""
        if session_id not in self.sessions:
            return
        
        game_state = self.sessions[session_id]
        
        if player_id in game_state["players"]:
            game_state["players"][player_id]["units_alive"] = units_alive
            game_state["players"][player_id]["units_total"] = units_total
            
            # Mark player as inactive if no units alive
            if units_alive <= 0:
                game_state["players"][player_id]["is_active"] = False
            
            game_state["last_update"] = datetime.now()
    
    async def set_phase(self, session_id: str, phase: GamePhase):
        """Set game phase"""
        if session_id not in self.sessions:
            return
        
        self.sessions[session_id]["phase"] = phase
        self.sessions[session_id]["last_update"] = datetime.now()
    
    async def update(self, session_id: str):
        """Update game state (called from main game loop)"""
        if session_id not in self.sessions:
            return
        
        game_state = self.sessions[session_id]
        
        # Check for turn timeouts
        if game_state["phase"] == GamePhase.ACTIVE:
            turn_state = game_state["turn_state"]
            current_player = turn_state["current_player"]
            
            if current_player and current_player in game_state["players"]:
                turn_start = datetime.fromisoformat(turn_state["turn_start_time"])
                elapsed = (datetime.now() - turn_start).total_seconds()
                time_limit = game_state["config"]["turn_time_limit"]
                
                if elapsed > time_limit:
                    # Force end turn
                    await self.end_turn(session_id, current_player)
                    logger.warning("Turn ended due to timeout", 
                                 session_id=session_id, 
                                 player_id=current_player)
        
        # Check victory conditions
        winner = await self.check_victory_conditions(session_id)
        if winner and not game_state["game_over"]:
            await self.end_game(session_id, "victory_condition", winner)
    
    async def cleanup_session(self, session_id: str):
        """Clean up session data"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info("Game session cleaned up", session_id=session_id)
    
    def get_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get game state manager statistics"""
        active_sessions = sum(1 for s in self.sessions.values() if s["phase"] == GamePhase.ACTIVE)
        paused_sessions = sum(1 for s in self.sessions.values() if s["phase"] == GamePhase.PAUSED)
        ended_sessions = sum(1 for s in self.sessions.values() if s["phase"] == GamePhase.ENDED)
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": active_sessions,
            "paused_sessions": paused_sessions,
            "ended_sessions": ended_sessions,
            "sessions_by_phase": {
                phase.value: sum(1 for s in self.sessions.values() if s["phase"] == phase)
                for phase in GamePhase
            }
        }