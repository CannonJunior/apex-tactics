"""
MCP Gateway Data Models

Pydantic models for MCP gateway request/response handling.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from pydantic import BaseModel, Field


class MCPRequest(BaseModel):
    """MCP tool execution request"""
    tool_name: str
    parameters: Dict[str, Any]
    session_id: str
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class MCPResponse(BaseModel):
    """MCP tool execution response"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    tool_name: str
    session_id: str
    request_id: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolCallResult(BaseModel):
    """Result of a tool call execution"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float


class GameAction(BaseModel):
    """Base class for game actions"""
    action_type: str
    unit_id: str
    session_id: str


class MoveActionParams(BaseModel):
    """Parameters for move action"""
    unit_id: str
    target_x: int
    target_y: int
    session_id: str


class AttackActionParams(BaseModel):
    """Parameters for attack action"""
    attacker_id: str
    target_id: str
    attack_type: str = "physical"
    session_id: str


class SpellActionParams(BaseModel):
    """Parameters for spell casting"""
    caster_id: str
    spell_name: str
    target_x: int
    target_y: int
    session_id: str


class ItemActionParams(BaseModel):
    """Parameters for item usage"""
    unit_id: str
    item_id: str
    target_id: Optional[str] = None
    session_id: str


class AnalysisRequest(BaseModel):
    """Request for battlefield analysis"""
    session_id: str
    analysis_type: str = "tactical"  # tactical, strategic, threat
    focus_unit_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class AnalysisResult(BaseModel):
    """Result of battlefield analysis"""
    session_id: str
    analysis_type: str
    focus_unit_id: Optional[str] = None
    recommendations: List[str]
    data: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)


class TacticalAnalysis(BaseModel):
    """Tactical analysis data"""
    possible_moves: List[Dict[str, Any]]
    potential_targets: List[Dict[str, Any]]
    threat_assessment: Dict[str, Any]
    recommendations: List[str]


class StrategicAnalysis(BaseModel):
    """Strategic analysis data"""
    team_strengths: Dict[str, Any]
    team_weaknesses: Dict[str, Any]
    game_phase: str
    victory_probability: float
    recommendations: List[str]


class ThreatAnalysis(BaseModel):
    """Threat analysis data"""
    immediate_threats: List[Dict[str, Any]]
    potential_threats: List[Dict[str, Any]]
    defensive_options: List[Dict[str, Any]]
    recommendations: List[str]


class UnitCapabilities(BaseModel):
    """Unit capabilities and limitations"""
    unit_id: str
    available_actions: List[str]
    movement_range: int
    attack_range: int
    special_abilities: List[str]
    resource_costs: Dict[str, int]
    cooldowns: Dict[str, int]


class BattlefieldState(BaseModel):
    """Current battlefield state for analysis"""
    grid_size: tuple[int, int]
    units: List[Dict[str, Any]]
    obstacles: List[Dict[str, Any]]
    special_tiles: List[Dict[str, Any]]
    turn_number: int
    current_unit_id: Optional[str] = None


class AIDecisionRequest(BaseModel):
    """Request for AI decision making"""
    session_id: str
    unit_id: str
    difficulty_level: str = "normal"
    time_limit: Optional[float] = None
    constraints: Optional[Dict[str, Any]] = None


class AIDecisionResponse(BaseModel):
    """AI decision response"""
    unit_id: str
    recommended_action: GameAction
    alternative_actions: List[GameAction]
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    analysis_used: List[str]


class ToolDefinition(BaseModel):
    """MCP tool definition"""
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    returns_schema: Optional[Dict[str, Any]] = None
    examples: Optional[List[Dict[str, Any]]] = None


class ServiceHealthCheck(BaseModel):
    """Service health check result"""
    service_name: str
    status: str
    response_time: float
    last_check: datetime
    details: Optional[Dict[str, Any]] = None


class MCPGatewayStats(BaseModel):
    """MCP Gateway service statistics"""
    total_tool_calls: int
    successful_calls: int
    failed_calls: int
    average_response_time: float
    active_sessions: int
    registered_tools: int


class ErrorDetails(BaseModel):
    """Detailed error information"""
    error_type: str
    error_message: str
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ValidationError(BaseModel):
    """Parameter validation error"""
    parameter_name: str
    error_message: str
    expected_type: Optional[str] = None
    received_value: Optional[Any] = None


class ToolExecutionContext(BaseModel):
    """Context for tool execution"""
    session_id: str
    user_id: Optional[str] = None
    tool_name: str
    parameters: Dict[str, Any]
    execution_id: str
    timestamp: datetime = Field(default_factory=datetime.now)


class GameStateSnapshot(BaseModel):
    """Snapshot of game state for tool context"""
    session_id: str
    turn_number: int
    current_unit_id: Optional[str] = None
    units: List[Dict[str, Any]]
    game_phase: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolResult(BaseModel):
    """Generic tool execution result"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None


class BatchToolRequest(BaseModel):
    """Request to execute multiple tools"""
    session_id: str
    tool_calls: List[MCPRequest]
    execution_mode: str = "sequential"  # sequential, parallel
    stop_on_error: bool = True


class BatchToolResponse(BaseModel):
    """Response from batch tool execution"""
    session_id: str
    results: List[MCPResponse]
    total_execution_time: float
    successful_count: int
    failed_count: int


class GameEventNotification(BaseModel):
    """Notification of game events for MCP tools"""
    event_type: str
    session_id: str
    unit_id: Optional[str] = None
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolSubscription(BaseModel):
    """Subscription to game events for tools"""
    tool_name: str
    event_types: List[str]
    session_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class MCPToolMetrics(BaseModel):
    """Metrics for MCP tool performance"""
    tool_name: str
    call_count: int
    success_rate: float
    average_execution_time: float
    last_used: Optional[datetime] = None
    error_count: int
    common_errors: List[str]