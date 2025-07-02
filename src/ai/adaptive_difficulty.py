"""
Adaptive Difficulty System

Dynamically adjusts AI difficulty based on player performance, engagement,
and learning patterns to maintain optimal challenge and fun.
"""

import time
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
from dataclasses import dataclass

import structlog
from pydantic import BaseModel
import numpy as np

from .personalities import PersonalityType, PersonalityTraits, AIPersonality
from .models import AIDecisionRequest

logger = structlog.get_logger()


class DifficultyLevel(str, Enum):
    """Difficulty levels"""
    TUTORIAL = "tutorial"
    VERY_EASY = "very_easy"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    VERY_HARD = "very_hard"
    EXPERT = "expert"
    NIGHTMARE = "nightmare"


class PlayerMetric(str, Enum):
    """Player performance metrics"""
    WIN_RATE = "win_rate"
    AVERAGE_GAME_LENGTH = "average_game_length"
    DECISION_SPEED = "decision_speed"
    UNIT_SURVIVAL_RATE = "unit_survival_rate"
    TACTICAL_EFFICIENCY = "tactical_efficiency"
    ENGAGEMENT_LEVEL = "engagement_level"
    FRUSTRATION_INDICATORS = "frustration_indicators"
    LEARNING_PROGRESS = "learning_progress"


@dataclass
class GameSessionData:
    """Data from a single game session"""
    session_id: str
    player_id: str
    start_time: datetime
    end_time: Optional[datetime]
    difficulty_level: DifficultyLevel
    player_won: Optional[bool]
    player_units_lost: int
    ai_units_lost: int
    total_turns: int
    player_decision_times: List[float]
    tactical_mistakes: int
    ragequit: bool
    completion_rate: float
    engagement_score: float


class PlayerProfile(BaseModel):
    """Player skill and behavior profile"""
    player_id: str
    current_difficulty: DifficultyLevel
    skill_level: float  # 0.0 to 1.0
    learning_rate: float  # How quickly they improve
    preferred_pace: str  # "fast", "medium", "slow"
    risk_tolerance: float  # 0.0 to 1.0
    patience_level: float  # 0.0 to 1.0
    competitive_drive: float  # 0.0 to 1.0
    
    # Performance history
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    average_game_length: float = 0.0
    recent_performance: List[float] = []  # Last 10 game performance scores
    
    # Adaptation history
    difficulty_changes: List[Dict[str, Any]] = []
    last_update: Optional[datetime] = None
    
    # Preferences
    prefers_challenge: bool = True
    frustration_tolerance: float = 0.7
    desired_win_rate: float = 0.6


class DifficultyAdjustment(BaseModel):
    """Represents a difficulty adjustment"""
    old_difficulty: DifficultyLevel
    new_difficulty: DifficultyLevel
    reason: str
    confidence: float
    player_metrics: Dict[str, float]
    timestamp: datetime
    temporary: bool = False
    duration: Optional[int] = None  # seconds if temporary


class AdaptiveDifficultySystem:
    """Main adaptive difficulty system"""
    
    def __init__(self):
        self.player_profiles: Dict[str, PlayerProfile] = {}
        self.session_data: Dict[str, GameSessionData] = {}
        self.active_sessions: Dict[str, str] = {}  # session_id -> player_id
        self.adjustment_history: List[DifficultyAdjustment] = []
        
        # Configuration
        self.min_games_for_adjustment = 3
        self.adjustment_sensitivity = 0.3
        self.performance_window = 10  # Number of recent games to consider
        self.engagement_threshold = 0.4
        self.frustration_threshold = 0.8
        
        # Difficulty scaling parameters
        self.difficulty_parameters = self._initialize_difficulty_parameters()
    
    def _initialize_difficulty_parameters(self) -> Dict[DifficultyLevel, Dict[str, float]]:
        """Initialize parameters for each difficulty level"""
        return {
            DifficultyLevel.TUTORIAL: {
                "ai_aggression": 0.1,
                "ai_intelligence": 0.2,
                "ai_reaction_time": 2.0,
                "player_advantage": 0.3,
                "mistake_tolerance": 0.9,
                "hint_frequency": 0.8
            },
            DifficultyLevel.VERY_EASY: {
                "ai_aggression": 0.2,
                "ai_intelligence": 0.3,
                "ai_reaction_time": 1.5,
                "player_advantage": 0.2,
                "mistake_tolerance": 0.7,
                "hint_frequency": 0.5
            },
            DifficultyLevel.EASY: {
                "ai_aggression": 0.3,
                "ai_intelligence": 0.4,
                "ai_reaction_time": 1.0,
                "player_advantage": 0.1,
                "mistake_tolerance": 0.5,
                "hint_frequency": 0.3
            },
            DifficultyLevel.NORMAL: {
                "ai_aggression": 0.5,
                "ai_intelligence": 0.6,
                "ai_reaction_time": 0.8,
                "player_advantage": 0.0,
                "mistake_tolerance": 0.3,
                "hint_frequency": 0.1
            },
            DifficultyLevel.HARD: {
                "ai_aggression": 0.7,
                "ai_intelligence": 0.8,
                "ai_reaction_time": 0.5,
                "player_advantage": -0.1,
                "mistake_tolerance": 0.1,
                "hint_frequency": 0.0
            },
            DifficultyLevel.VERY_HARD: {
                "ai_aggression": 0.8,
                "ai_intelligence": 0.9,
                "ai_reaction_time": 0.3,
                "player_advantage": -0.2,
                "mistake_tolerance": 0.0,
                "hint_frequency": 0.0
            },
            DifficultyLevel.EXPERT: {
                "ai_aggression": 0.9,
                "ai_intelligence": 0.95,
                "ai_reaction_time": 0.2,
                "player_advantage": -0.3,
                "mistake_tolerance": 0.0,
                "hint_frequency": 0.0
            },
            DifficultyLevel.NIGHTMARE: {
                "ai_aggression": 1.0,
                "ai_intelligence": 1.0,
                "ai_reaction_time": 0.1,
                "player_advantage": -0.4,
                "mistake_tolerance": 0.0,
                "hint_frequency": 0.0
            }
        }
    
    def get_player_profile(self, player_id: str) -> PlayerProfile:
        """Get or create player profile"""
        if player_id not in self.player_profiles:
            self.player_profiles[player_id] = PlayerProfile(
                player_id=player_id,
                current_difficulty=DifficultyLevel.NORMAL,
                skill_level=0.5,
                learning_rate=0.1,
                preferred_pace="medium",
                risk_tolerance=0.5,
                patience_level=0.5,
                competitive_drive=0.5
            )
        
        return self.player_profiles[player_id]
    
    def start_session(self, session_id: str, player_id: str, requested_difficulty: Optional[DifficultyLevel] = None) -> DifficultyLevel:
        """Start a new game session"""
        profile = self.get_player_profile(player_id)
        
        # Determine starting difficulty
        if requested_difficulty:
            # Player explicitly requested a difficulty
            difficulty = requested_difficulty
        else:
            # Use adaptive difficulty
            difficulty = self._calculate_adaptive_difficulty(profile)
        
        # Create session data
        self.session_data[session_id] = GameSessionData(
            session_id=session_id,
            player_id=player_id,
            start_time=datetime.now(),
            end_time=None,
            difficulty_level=difficulty,
            player_won=None,
            player_units_lost=0,
            ai_units_lost=0,
            total_turns=0,
            player_decision_times=[],
            tactical_mistakes=0,
            ragequit=False,
            completion_rate=0.0,
            engagement_score=0.5
        )
        
        self.active_sessions[session_id] = player_id
        
        logger.info("Session started",
                   session_id=session_id,
                   player_id=player_id,
                   difficulty=difficulty,
                   player_skill=profile.skill_level)
        
        return difficulty
    
    def _calculate_adaptive_difficulty(self, profile: PlayerProfile) -> DifficultyLevel:
        """Calculate appropriate difficulty for player"""
        if profile.total_games < self.min_games_for_adjustment:
            return profile.current_difficulty
        
        # Calculate performance indicators
        win_rate = profile.wins / max(profile.total_games, 1)
        recent_performance = np.mean(profile.recent_performance) if profile.recent_performance else 0.5
        
        # Target metrics based on player preferences
        target_win_rate = profile.desired_win_rate
        target_performance = 0.6  # Slightly above average
        
        # Calculate adjustment need
        win_rate_diff = win_rate - target_win_rate
        performance_diff = recent_performance - target_performance
        
        # Determine if adjustment is needed
        adjustment_score = (win_rate_diff + performance_diff) / 2
        
        current_level = list(DifficultyLevel).index(profile.current_difficulty)
        
        if adjustment_score > 0.15 and profile.prefers_challenge:
            # Player performing too well, increase difficulty
            new_level = min(len(DifficultyLevel) - 1, current_level + 1)
        elif adjustment_score < -0.15:
            # Player struggling, decrease difficulty
            new_level = max(0, current_level - 1)
        else:
            # No change needed
            new_level = current_level
        
        return list(DifficultyLevel)[new_level]
    
    def record_player_action(self, session_id: str, action_data: Dict[str, Any]):
        """Record player action for analysis"""
        if session_id not in self.session_data:
            return
        
        session = self.session_data[session_id]
        
        # Record decision time
        decision_time = action_data.get("decision_time", 1.0)
        session.player_decision_times.append(decision_time)
        
        # Analyze for tactical mistakes
        if action_data.get("was_mistake", False):
            session.tactical_mistakes += 1
        
        # Update engagement metrics
        engagement_indicators = action_data.get("engagement_indicators", {})
        session.engagement_score = self._calculate_engagement_score(engagement_indicators)
    
    def _calculate_engagement_score(self, indicators: Dict[str, Any]) -> float:
        """Calculate player engagement score"""
        score = 0.5  # Base score
        
        # Time between actions (faster = more engaged)
        action_speed = indicators.get("action_speed", 1.0)
        if action_speed < 0.5:
            score += 0.2
        elif action_speed > 2.0:
            score -= 0.2
        
        # Mouse/keyboard activity
        input_activity = indicators.get("input_activity", 0.5)
        score += (input_activity - 0.5) * 0.3
        
        # Menu interactions (lots of pausing = less engaged)
        menu_time_ratio = indicators.get("menu_time_ratio", 0.1)
        score -= menu_time_ratio * 0.4
        
        # Decision changes (indicates thinking/engagement)
        decision_changes = indicators.get("decision_changes", 0)
        score += min(0.2, decision_changes * 0.05)
        
        return max(0.0, min(1.0, score))
    
    def record_game_event(self, session_id: str, event: Dict[str, Any]):
        """Record significant game events"""
        if session_id not in self.session_data:
            return
        
        session = self.session_data[session_id]
        event_type = event.get("type")
        
        if event_type == "unit_killed":
            if event.get("player_unit", False):
                session.player_units_lost += 1
            else:
                session.ai_units_lost += 1
        
        elif event_type == "turn_completed":
            session.total_turns += 1
        
        elif event_type == "player_quit":
            session.ragequit = True
            session.completion_rate = event.get("progress", 0.0)
        
        elif event_type == "game_paused":
            # Extended pauses might indicate frustration
            pause_duration = event.get("duration", 0)
            if pause_duration > 30:  # 30 seconds
                session.engagement_score = max(0.0, session.engagement_score - 0.1)
    
    def end_session(self, session_id: str, outcome: Dict[str, Any]) -> Optional[DifficultyAdjustment]:
        """End a game session and potentially adjust difficulty"""
        if session_id not in self.session_data:
            return None
        
        session = self.session_data[session_id]
        session.end_time = datetime.now()
        session.player_won = outcome.get("player_won", False)
        session.completion_rate = outcome.get("completion_rate", 1.0)
        
        player_id = session.player_id
        profile = self.get_player_profile(player_id)
        
        # Update player profile
        self._update_player_profile(profile, session)
        
        # Check if difficulty adjustment is needed
        adjustment = self._evaluate_difficulty_adjustment(profile, session)
        
        # Clean up
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        return adjustment
    
    def _update_player_profile(self, profile: PlayerProfile, session: GameSessionData):
        """Update player profile based on session data"""
        profile.total_games += 1
        
        if session.player_won:
            profile.wins += 1
        else:
            profile.losses += 1
        
        # Calculate session performance score
        performance_score = self._calculate_session_performance(session)
        profile.recent_performance.append(performance_score)
        
        # Keep only recent performance data
        if len(profile.recent_performance) > self.performance_window:
            profile.recent_performance = profile.recent_performance[-self.performance_window:]
        
        # Update average game length
        if session.end_time:
            game_duration = (session.end_time - session.start_time).total_seconds() / 60.0  # minutes
            if profile.total_games == 1:
                profile.average_game_length = game_duration
            else:
                profile.average_game_length = (profile.average_game_length * (profile.total_games - 1) + game_duration) / profile.total_games
        
        # Update skill level estimate
        self._update_skill_estimate(profile, session)
        
        profile.last_update = datetime.now()
    
    def _calculate_session_performance(self, session: GameSessionData) -> float:
        """Calculate overall performance score for a session"""
        score = 0.5  # Base score
        
        # Win/loss
        if session.player_won:
            score += 0.3
        else:
            score -= 0.2
        
        # Unit preservation
        if session.player_units_lost + session.ai_units_lost > 0:
            preservation_ratio = session.ai_units_lost / (session.player_units_lost + session.ai_units_lost)
            score += (preservation_ratio - 0.5) * 0.2
        
        # Tactical efficiency (fewer mistakes = better)
        if session.total_turns > 0:
            mistake_ratio = session.tactical_mistakes / session.total_turns
            score -= mistake_ratio * 0.3
        
        # Decision speed (consistent moderate speed is good)
        if session.player_decision_times:
            avg_decision_time = np.mean(session.player_decision_times)
            ideal_time = 2.0  # 2 seconds
            time_penalty = abs(avg_decision_time - ideal_time) / ideal_time
            score -= min(0.2, time_penalty * 0.1)
        
        # Completion rate
        score += (session.completion_rate - 0.5) * 0.2
        
        # Engagement
        score += (session.engagement_score - 0.5) * 0.1
        
        return max(0.0, min(1.0, score))
    
    def _update_skill_estimate(self, profile: PlayerProfile, session: GameSessionData):
        """Update player skill level estimate"""
        # Performance against difficulty
        difficulty_index = list(DifficultyLevel).index(session.difficulty_level)
        expected_difficulty = difficulty_index / (len(DifficultyLevel) - 1)
        
        session_performance = self._calculate_session_performance(session)
        
        # If player performed well against higher difficulty, increase skill estimate
        if session_performance > 0.6 and expected_difficulty > profile.skill_level:
            skill_adjustment = 0.05
        elif session_performance < 0.4 and expected_difficulty < profile.skill_level:
            skill_adjustment = -0.05
        else:
            # Gradual adjustment towards equilibrium
            skill_adjustment = (session_performance - 0.5) * profile.learning_rate * 0.1
        
        profile.skill_level = max(0.0, min(1.0, profile.skill_level + skill_adjustment))
    
    def _evaluate_difficulty_adjustment(self, profile: PlayerProfile, session: GameSessionData) -> Optional[DifficultyAdjustment]:
        """Evaluate if difficulty should be adjusted"""
        if profile.total_games < self.min_games_for_adjustment:
            return None
        
        # Calculate recent performance metrics
        recent_performance = np.mean(profile.recent_performance[-5:]) if len(profile.recent_performance) >= 3 else None
        win_rate = profile.wins / profile.total_games
        
        if recent_performance is None:
            return None
        
        # Determine if adjustment is needed
        current_difficulty_index = list(DifficultyLevel).index(profile.current_difficulty)
        suggested_difficulty_index = current_difficulty_index
        adjustment_reason = ""
        confidence = 0.5
        
        # Check for consistent high performance
        if recent_performance > 0.75 and win_rate > 0.8:
            if current_difficulty_index < len(DifficultyLevel) - 1:
                suggested_difficulty_index += 1
                adjustment_reason = "Player consistently performing above expectations"
                confidence = min(1.0, recent_performance)
        
        # Check for consistent poor performance
        elif recent_performance < 0.35 and win_rate < 0.3:
            if current_difficulty_index > 0:
                suggested_difficulty_index -= 1
                adjustment_reason = "Player struggling with current difficulty"
                confidence = 1.0 - recent_performance
        
        # Check for ragequit or low engagement
        elif session.ragequit or session.engagement_score < self.engagement_threshold:
            if current_difficulty_index > 0:
                suggested_difficulty_index -= 1
                adjustment_reason = "Player showing signs of frustration"
                confidence = 0.8
        
        # Check for boredom (high performance but low engagement)
        elif recent_performance > 0.65 and session.engagement_score < 0.5:
            if current_difficulty_index < len(DifficultyLevel) - 1:
                suggested_difficulty_index += 1
                adjustment_reason = "Player appears bored with current difficulty"
                confidence = 0.6
        
        if suggested_difficulty_index != current_difficulty_index:
            old_difficulty = profile.current_difficulty
            new_difficulty = list(DifficultyLevel)[suggested_difficulty_index]
            
            adjustment = DifficultyAdjustment(
                old_difficulty=old_difficulty,
                new_difficulty=new_difficulty,
                reason=adjustment_reason,
                confidence=confidence,
                player_metrics={
                    "recent_performance": recent_performance,
                    "win_rate": win_rate,
                    "engagement": session.engagement_score,
                    "skill_level": profile.skill_level
                },
                timestamp=datetime.now()
            )
            
            # Apply the adjustment
            profile.current_difficulty = new_difficulty
            profile.difficulty_changes.append(adjustment.dict())
            self.adjustment_history.append(adjustment)
            
            logger.info("Difficulty adjusted",
                       player_id=profile.player_id,
                       old_difficulty=old_difficulty,
                       new_difficulty=new_difficulty,
                       reason=adjustment_reason,
                       confidence=confidence)
            
            return adjustment
        
        return None
    
    def get_ai_parameters(self, session_id: str) -> Dict[str, float]:
        """Get AI parameters for current difficulty"""
        if session_id not in self.session_data:
            return self.difficulty_parameters[DifficultyLevel.NORMAL]
        
        session = self.session_data[session_id]
        base_params = self.difficulty_parameters[session.difficulty_level]
        
        # Apply dynamic adjustments based on current session
        adjusted_params = base_params.copy()
        
        # If player is struggling this session, slightly reduce difficulty
        if session.player_units_lost > session.ai_units_lost * 2:
            adjusted_params["ai_aggression"] *= 0.9
            adjusted_params["mistake_tolerance"] *= 1.1
        
        # If player is dominating this session, slightly increase difficulty
        elif session.ai_units_lost > session.player_units_lost * 2:
            adjusted_params["ai_aggression"] *= 1.1
            adjusted_params["ai_intelligence"] *= 1.05
        
        return adjusted_params
    
    def create_adaptive_personality(self, session_id: str, base_personality_type: PersonalityType) -> Tuple[PersonalityType, PersonalityTraits]:
        """Create AI personality adapted to current difficulty"""
        ai_params = self.get_ai_parameters(session_id)
        
        # Adjust personality traits based on difficulty parameters
        base_traits = PersonalityTraits()
        
        adjusted_traits = PersonalityTraits(
            aggression=ai_params["ai_aggression"],
            risk_tolerance=ai_params["ai_aggression"] * 0.8,
            patience=1.0 - ai_params["ai_aggression"] * 0.7,
            teamwork=ai_params["ai_intelligence"],
            adaptability=ai_params["ai_intelligence"],
            planning_horizon=ai_params["ai_intelligence"],
            resource_management=ai_params["ai_intelligence"] * 0.9,
            target_prioritization="damage" if ai_params["ai_aggression"] > 0.7 else "balanced"
        )
        
        # Modify personality type based on difficulty
        if ai_params["ai_aggression"] > 0.8:
            adapted_type = PersonalityType.AGGRESSIVE
        elif ai_params["ai_intelligence"] > 0.8:
            adapted_type = PersonalityType.TACTICAL
        elif ai_params["ai_aggression"] < 0.3:
            adapted_type = PersonalityType.DEFENSIVE
        else:
            adapted_type = base_personality_type
        
        return adapted_type, adjusted_traits
    
    def get_hint_probability(self, session_id: str) -> float:
        """Get probability of showing hints to player"""
        ai_params = self.get_ai_parameters(session_id)
        return ai_params.get("hint_frequency", 0.0)
    
    def should_provide_assistance(self, session_id: str, player_action: Dict[str, Any]) -> bool:
        """Determine if AI should provide assistance to struggling player"""
        if session_id not in self.session_data:
            return False
        
        session = self.session_data[session_id]
        ai_params = self.get_ai_parameters(session_id)
        
        # Check if player is making obvious mistakes
        if player_action.get("is_obvious_mistake", False):
            return ai_params["mistake_tolerance"] > 0.5
        
        # Check if player is taking too long
        decision_time = player_action.get("decision_time", 0)
        if decision_time > 10:  # 10 seconds
            return ai_params["hint_frequency"] > 0.3
        
        # Check session performance
        if (session.player_units_lost > session.ai_units_lost * 1.5 and 
            session.total_turns > 5):
            return ai_params["mistake_tolerance"] > 0.4
        
        return False
    
    def get_dynamic_ai_request(self, base_request: AIDecisionRequest, session_id: str) -> AIDecisionRequest:
        """Modify AI decision request based on adaptive difficulty"""
        ai_params = self.get_ai_parameters(session_id)
        
        # Adjust constraints based on difficulty
        constraints = base_request.constraints or {}
        
        # Add difficulty-based constraints
        constraints.update({
            "max_thinking_time": ai_params["ai_reaction_time"],
            "aggression_bias": ai_params["ai_aggression"],
            "intelligence_level": ai_params["ai_intelligence"],
            "mistake_allowance": ai_params["mistake_tolerance"]
        })
        
        # Modify difficulty level
        if ai_params["ai_intelligence"] > 0.8:
            difficulty = "expert"
        elif ai_params["ai_intelligence"] > 0.6:
            difficulty = "hard"
        elif ai_params["ai_intelligence"] > 0.4:
            difficulty = "normal"
        else:
            difficulty = "easy"
        
        return AIDecisionRequest(
            session_id=base_request.session_id,
            unit_id=base_request.unit_id,
            difficulty_level=difficulty,
            time_limit=ai_params["ai_reaction_time"],
            constraints=constraints
        )
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get adaptive difficulty system statistics"""
        total_players = len(self.player_profiles)
        active_sessions = len(self.active_sessions)
        total_adjustments = len(self.adjustment_history)
        
        # Difficulty distribution
        difficulty_dist = {}
        for profile in self.player_profiles.values():
            difficulty = profile.current_difficulty
            difficulty_dist[difficulty] = difficulty_dist.get(difficulty, 0) + 1
        
        # Recent adjustment rate
        recent_adjustments = len([
            adj for adj in self.adjustment_history
            if adj.timestamp > datetime.now() - timedelta(hours=24)
        ])
        
        return {
            "total_players": total_players,
            "active_sessions": active_sessions,
            "total_adjustments": total_adjustments,
            "recent_adjustments_24h": recent_adjustments,
            "difficulty_distribution": difficulty_dist,
            "average_skill_level": np.mean([p.skill_level for p in self.player_profiles.values()]) if self.player_profiles else 0.0,
            "average_games_per_player": np.mean([p.total_games for p in self.player_profiles.values()]) if self.player_profiles else 0.0
        }
    
    def export_player_data(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Export player data for analysis"""
        if player_id not in self.player_profiles:
            return None
        
        profile = self.player_profiles[player_id]
        
        return {
            "profile": profile.dict(),
            "difficulty_history": profile.difficulty_changes,
            "recent_sessions": [
                session.__dict__ for session in self.session_data.values()
                if session.player_id == player_id and session.end_time
            ][-10:]  # Last 10 sessions
        }
    
    def import_player_data(self, player_data: Dict[str, Any]) -> bool:
        """Import player data from external source"""
        try:
            profile_data = player_data["profile"]
            player_id = profile_data["player_id"]
            
            self.player_profiles[player_id] = PlayerProfile(**profile_data)
            
            logger.info("Player data imported", player_id=player_id)
            return True
            
        except Exception as e:
            logger.error("Failed to import player data", error=str(e))
            return False