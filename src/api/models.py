"""
API Data Models

Pydantic models for API request/response serialization and validation.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum

from pydantic import BaseModel, Field


class UnitType(str, Enum):
    """Unit type enumeration for API"""
    HEROMANCER = "HEROMANCER"
    UBERMENSCH = "UBERMENSCH"
    SOUL_LINKED = "SOUL_LINKED"
    REALM_WALKER = "REALM_WALKER"
    WARGI = "WARGI"
    MAGI = "MAGI"


class AttackType(str, Enum):
    """Attack type enumeration"""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    SPIRITUAL = "spiritual"


class GameEventType(str, Enum):
    """Game event types for WebSocket communication"""
    UNIT_MOVED = "unit_moved"
    UNIT_ATTACKED = "unit_attacked"
    UNIT_DIED = "unit_died"
    TURN_ENDED = "turn_ended"
    GAME_OVER = "game_over"
    UNIT_ADDED = "unit_added"
    UNIT_REMOVED = "unit_removed"


class Position(BaseModel):
    """2D position coordinates"""
    x: int
    y: int


class UnitAttributes(BaseModel):
    """Unit attribute values"""
    strength: int
    fortitude: int
    finesse: int
    wisdom: int
    wonder: int
    worthy: int
    faith: int
    spirit: int
    speed: int


class UnitData(BaseModel):
    """Complete unit data for API responses"""
    id: str
    name: str
    unit_type: str
    position: Tuple[int, int]
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    ap: int
    max_ap: int
    alive: bool
    attributes: UnitAttributes
    equipped_weapon: Optional[str] = None
    equipped_armor: Optional[str] = None
    equipped_accessory: Optional[str] = None


class GameSession(BaseModel):
    """Game session information"""
    session_id: str
    status: str = Field(description="Session status: active, paused, ended")
    player_count: int = Field(description="Number of active players")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GameState(BaseModel):
    """Complete game state"""
    session_id: str
    turn_number: int
    current_unit_index: int
    units: List[UnitData]
    game_over: bool = False
    winner: Optional[str] = None
    grid_size: Tuple[int, int] = (10, 10)


class PlayerAction(BaseModel):
    """Base class for player actions"""
    action_type: str
    unit_id: str
    timestamp: Optional[datetime] = None


class MoveAction(PlayerAction):
    """Move action data"""
    action_type: str = "move"
    target_x: int
    target_y: int


class AttackAction(PlayerAction):
    """Attack action data"""
    action_type: str = "attack"
    target_id: str
    attack_type: AttackType


class MagicAction(PlayerAction):
    """Magic action data"""
    action_type: str = "magic"
    target_x: int
    target_y: int
    spell_name: Optional[str] = None


class InventoryAction(PlayerAction):
    """Inventory action data"""
    action_type: str = "inventory"
    item_id: str
    action: str = Field(description="use, equip, unequip, drop")


class GameEvent(BaseModel):
    """Game event for WebSocket communication"""
    type: GameEventType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class ActionResult(BaseModel):
    """Result of an action execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    additional_info: Optional[Dict[str, Any]] = None


class ConfigStats(BaseModel):
    """Configuration manager statistics"""
    loaded_configs: List[str]
    cache_size: int
    active_modifiers: int
    last_reload: float


class MCPToolCall(BaseModel):
    """MCP tool call data"""
    tool_name: str
    parameters: Dict[str, Any]
    session_id: str
    unit_id: Optional[str] = None


class MCPToolResult(BaseModel):
    """MCP tool execution result"""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: Optional[float] = None


class AIDecision(BaseModel):
    """AI decision data from AI service"""
    unit_id: str
    decision_type: str
    action: PlayerAction
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class BattlefieldInfo(BaseModel):
    """Battlefield state information for AI"""
    grid_size: Tuple[int, int]
    units: List[UnitData]
    turn_number: int
    current_unit: Optional[UnitData] = None
    obstacles: List[Position] = []
    special_tiles: List[Dict[str, Any]] = []


class UnitCreationRequest(BaseModel):
    """Request to create a new unit"""
    name: str
    unit_type: UnitType
    position: Position
    custom_attributes: Optional[UnitAttributes] = None


class EquipmentRequest(BaseModel):
    """Request to equip an item"""
    unit_id: str
    item_id: str
    slot: str = Field(description="weapon, armor, accessory")


class GameConfiguration(BaseModel):
    """Game configuration data"""
    turn_time_limit: Optional[int] = None
    auto_end_turn: bool = False
    fog_of_war: bool = False
    permadeath: bool = False
    difficulty_level: str = "normal"


class SessionSettings(BaseModel):
    """Session-specific settings"""
    max_players: int = 2
    ai_difficulty: str = "normal"
    turn_order: str = "speed"  # speed, alternating, random
    victory_conditions: List[str] = ["eliminate_all"]


# WebSocket message types
class WSMessage(BaseModel):
    """Base WebSocket message"""
    type: str
    data: Optional[Dict[str, Any]] = None


class WSPing(WSMessage):
    """WebSocket ping message"""
    type: str = "ping"


class WSPong(WSMessage):
    """WebSocket pong response"""
    type: str = "pong"


class WSGameState(WSMessage):
    """WebSocket game state message"""
    type: str = "game_state"
    data: GameState


class WSGameEvent(WSMessage):
    """WebSocket game event message"""
    type: str = "game_event"
    data: GameEvent


class WSError(WSMessage):
    """WebSocket error message"""
    type: str = "error"
    data: Dict[str, str]  # error, message


class WSSubscribe(WSMessage):
    """WebSocket subscription message"""
    type: str = "subscribe"
    data: Dict[str, List[str]]  # events: [event_types]


class WSUnsubscribe(WSMessage):
    """WebSocket unsubscription message"""
    type: str = "unsubscribe"
    data: Dict[str, List[str]]  # events: [event_types]