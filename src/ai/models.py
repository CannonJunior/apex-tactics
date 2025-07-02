"""
AI Service Data Models

Pydantic models for AI service request/response handling.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from pydantic import BaseModel, Field


class DifficultyLevel(str, Enum):
    """AI difficulty levels"""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXPERT = "expert"


class AIDecisionRequest(BaseModel):
    """Request for AI to make a tactical decision"""
    session_id: str
    unit_id: str
    difficulty_level: DifficultyLevel = DifficultyLevel.NORMAL
    time_limit: Optional[float] = Field(None, description="Max time in seconds for decision")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Additional constraints")
    
    class Config:
        use_enum_values = True


class GameAction(BaseModel):
    """Base class for game actions"""
    action_type: str
    unit_id: str
    session_id: str


class MoveAction(GameAction):
    """Move action"""
    action_type: str = "move"
    target_x: int
    target_y: int


class AttackAction(GameAction):
    """Attack action"""
    action_type: str = "attack"
    target_id: str
    attack_type: str = "physical"


class SpellAction(GameAction):
    """Spell casting action"""
    action_type: str = "spell"
    spell_name: str
    target_x: int
    target_y: int


class ItemAction(GameAction):
    """Item usage action"""
    action_type: str = "item"
    item_id: str
    target_id: Optional[str] = None


class EndTurnAction(GameAction):
    """End turn action"""
    action_type: str = "end_turn"


class AIDecisionResponse(BaseModel):
    """AI decision response"""
    unit_id: str
    recommended_action: Union[MoveAction, AttackAction, SpellAction, ItemAction, EndTurnAction]
    alternative_actions: List[Union[MoveAction, AttackAction, SpellAction, ItemAction, EndTurnAction]]
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    analysis_used: List[str]
    execution_time: Optional[float] = None


class TacticalAnalysisRequest(BaseModel):
    """Request for tactical analysis"""
    session_id: str
    focus_unit_id: Optional[str] = None
    analysis_depth: str = Field("normal", description="shallow, normal, deep")
    include_predictions: bool = True


class TacticalAnalysisResponse(BaseModel):
    """Tactical analysis response"""
    session_id: str
    focus_unit_id: Optional[str] = None
    threat_assessment: Dict[str, Any]
    opportunity_assessment: Dict[str, Any]
    positioning_analysis: Dict[str, Any]
    recommendations: List[str]
    confidence: float = Field(ge=0.0, le=1.0)


class StrategicAnalysisRequest(BaseModel):
    """Request for strategic analysis"""
    session_id: str
    analysis_scope: str = Field("full", description="unit, team, full")
    future_turns: int = Field(3, description="Number of turns to analyze ahead")


class StrategicAnalysisResponse(BaseModel):
    """Strategic analysis response"""
    session_id: str
    team_evaluation: Dict[str, Any]
    victory_probability: float = Field(ge=0.0, le=1.0)
    strategic_phase: str
    key_objectives: List[str]
    long_term_recommendations: List[str]
    confidence: float = Field(ge=0.0, le=1.0)


class UnitEvaluationRequest(BaseModel):
    """Request for unit evaluation"""
    session_id: str
    unit_id: str
    evaluation_aspects: List[str] = Field(default=["combat", "positioning", "resources"])


class UnitEvaluationResponse(BaseModel):
    """Unit evaluation response"""
    unit_id: str
    combat_effectiveness: float = Field(ge=0.0, le=1.0)
    positional_advantage: float = Field(ge=0.0, le=1.0)
    resource_efficiency: float = Field(ge=0.0, le=1.0)
    survival_probability: float = Field(ge=0.0, le=1.0)
    strategic_value: float = Field(ge=0.0, le=1.0)
    recommendations: List[str]


class AIModelConfig(BaseModel):
    """AI model configuration"""
    tactical_model: Optional[str] = "llama2:7b"
    strategic_model: Optional[str] = "llama2:7b"
    tactical_settings: Optional[Dict[str, Any]] = None
    strategic_settings: Optional[Dict[str, Any]] = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1024, gt=0)


class BattlefieldPosition(BaseModel):
    """Position on the battlefield"""
    x: int
    y: int
    
    def distance_to(self, other: 'BattlefieldPosition') -> int:
        """Calculate Manhattan distance to another position"""
        return abs(self.x - other.x) + abs(self.y - other.y)


class UnitState(BaseModel):
    """Current state of a unit"""
    id: str
    name: str
    position: BattlefieldPosition
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    ap: int
    max_ap: int
    alive: bool
    team: str
    unit_type: str
    attributes: Dict[str, int]
    equipment: Dict[str, Any]
    status_effects: List[str] = []


class BattlefieldState(BaseModel):
    """Complete battlefield state"""
    session_id: str
    turn_number: int
    current_unit_id: Optional[str]
    units: List[UnitState]
    grid_size: tuple[int, int] = (10, 10)
    obstacles: List[BattlefieldPosition] = []
    special_tiles: List[Dict[str, Any]] = []


class ThreatAssessment(BaseModel):
    """Assessment of threats on the battlefield"""
    immediate_threats: List[Dict[str, Any]]
    potential_threats: List[Dict[str, Any]]
    threat_level: float = Field(ge=0.0, le=1.0)
    escape_routes: List[BattlefieldPosition]
    defensive_positions: List[BattlefieldPosition]


class OpportunityAssessment(BaseModel):
    """Assessment of opportunities on the battlefield"""
    attack_opportunities: List[Dict[str, Any]]
    positioning_opportunities: List[Dict[str, Any]]
    resource_opportunities: List[Dict[str, Any]]
    opportunity_score: float = Field(ge=0.0, le=1.0)


class AIPerformanceStats(BaseModel):
    """AI performance statistics"""
    total_decisions: int
    successful_decisions: int
    average_decision_time: float
    confidence_distribution: Dict[str, int]
    action_type_distribution: Dict[str, int]
    difficulty_performance: Dict[str, Dict[str, Any]]


class ModelPerformanceMetrics(BaseModel):
    """Ollama model performance metrics"""
    model_name: str
    total_requests: int
    average_response_time: float
    tokens_per_second: float
    memory_usage: Optional[float] = None
    error_rate: float = Field(ge=0.0, le=1.0)


class ChatMessage(BaseModel):
    """Chat message for AI interaction"""
    role: str = Field(description="system, user, assistant")
    content: str


class ChatRequest(BaseModel):
    """Chat request to AI"""
    messages: List[ChatMessage]
    model: str = "llama2:7b"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(512, gt=0)
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response from AI"""
    message: ChatMessage
    model_used: str
    tokens_used: int
    response_time: float


class DecisionTree(BaseModel):
    """Decision tree for AI reasoning"""
    root_node: Dict[str, Any]
    evaluation_criteria: List[str]
    decision_path: List[str]
    confidence_scores: Dict[str, float]


class StrategicObjective(BaseModel):
    """Strategic objective for AI planning"""
    objective_type: str
    description: str
    priority: float = Field(ge=0.0, le=1.0)
    progress: float = Field(ge=0.0, le=1.0)
    estimated_turns: Optional[int] = None
    required_resources: Optional[Dict[str, Any]] = None


class TacticalPattern(BaseModel):
    """Tactical pattern recognition"""
    pattern_name: str
    pattern_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    applicable_units: List[str]
    recommended_response: str
    historical_success_rate: Optional[float] = None


class AILearningData(BaseModel):
    """Data for AI learning and improvement"""
    session_id: str
    decision_id: str
    game_state: BattlefieldState
    decision_made: GameAction
    outcome: Dict[str, Any]
    success_rating: float = Field(ge=0.0, le=1.0)
    lessons_learned: List[str]


class ModelTrainingRequest(BaseModel):
    """Request for model training/fine-tuning"""
    model_name: str
    training_data: List[AILearningData]
    training_parameters: Dict[str, Any]
    validation_split: float = Field(0.2, ge=0.0, le=0.5)


class AIServiceHealth(BaseModel):
    """AI service health status"""
    service_status: str
    ollama_status: str
    available_models: List[str]
    active_sessions: int
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    last_health_check: datetime = Field(default_factory=datetime.now)