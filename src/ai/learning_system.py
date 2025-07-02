"""
AI Learning System

Implements machine learning capabilities for AI improvement based on
game outcomes, pattern recognition, and opponent adaptation.
"""

import json
import math
import time
import pickle
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

import structlog
from pydantic import BaseModel
import numpy as np

from .models import BattlefieldState, AIDecisionRequest, GameAction
from .personalities import AIPersonality, PersonalityType

logger = structlog.get_logger()


class LearningType(str, Enum):
    """Types of learning algorithms"""
    REINFORCEMENT = "reinforcement"
    PATTERN_MATCHING = "pattern_matching" 
    OPPONENT_MODELING = "opponent_modeling"
    TACTICAL_EVOLUTION = "tactical_evolution"


class OutcomeType(str, Enum):
    """Types of action outcomes"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass
class LearningExample:
    """Single learning example from game experience"""
    situation_id: str
    battlefield_state: Dict[str, Any]
    action_taken: Dict[str, Any]
    outcome: OutcomeType
    reward: float
    timestamp: datetime
    metadata: Dict[str, Any]


class TacticalPattern(BaseModel):
    """Recognized tactical pattern"""
    pattern_id: str
    pattern_type: str
    situation_features: Dict[str, Any]
    successful_responses: List[Dict[str, Any]]
    failure_responses: List[Dict[str, Any]]
    success_rate: float
    confidence: float
    usage_count: int
    last_updated: datetime


class OpponentModel(BaseModel):
    """Model of opponent behavior"""
    opponent_id: str
    behavioral_traits: Dict[str, float]
    preferred_actions: Dict[str, float]
    weaknesses: List[str]
    strengths: List[str]
    predictability: float
    adaptation_rate: float
    games_observed: int
    last_encounter: Optional[datetime] = None


class LearningMetrics(BaseModel):
    """Metrics for learning system performance"""
    total_examples: int
    patterns_learned: int
    opponents_modeled: int
    average_improvement: float
    learning_rate: float
    confidence_score: float
    adaptation_count: int


class ReinforcementLearner:
    """Q-Learning based reinforcement learning for tactical decisions"""
    
    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.9, 
                 exploration_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.state_visits: Dict[str, int] = defaultdict(int)
        self.action_history: deque = deque(maxlen=1000)
        
    def get_state_key(self, battlefield_state: Dict[str, Any], unit_id: str) -> str:
        """Generate a state key for Q-learning"""
        # Simplify state representation for learning
        current_unit = None
        enemies = []
        allies = []
        
        for unit in battlefield_state.get("units", []):
            if unit["id"] == unit_id:
                current_unit = unit
            elif unit["alive"]:
                if unit.get("team") != current_unit.get("team") if current_unit else None:
                    enemies.append(unit)
                else:
                    allies.append(unit)
        
        if not current_unit:
            return "invalid_state"
        
        # Create state features
        features = {
            "hp_ratio": round(current_unit["hp"] / max(current_unit["max_hp"], 1), 2),
            "enemy_count": len(enemies),
            "ally_count": len(allies),
            "nearest_enemy_distance": self._get_nearest_enemy_distance(current_unit, enemies),
            "position_type": self._classify_position(current_unit, battlefield_state),
            "turn_phase": self._classify_turn_phase(battlefield_state)
        }
        
        # Create state key from features
        return f"hp{features['hp_ratio']}_e{features['enemy_count']}_a{features['ally_count']}_d{features['nearest_enemy_distance']}_p{features['position_type']}_t{features['turn_phase']}"
    
    def _get_nearest_enemy_distance(self, current_unit: Dict[str, Any], enemies: List[Dict[str, Any]]) -> int:
        """Get distance to nearest enemy"""
        if not enemies:
            return 10  # Large distance if no enemies
        
        current_pos = current_unit["position"]
        min_distance = float('inf')
        
        for enemy in enemies:
            enemy_pos = enemy["position"]
            distance = abs(current_pos[0] - enemy_pos[0]) + abs(current_pos[1] - enemy_pos[1])
            min_distance = min(min_distance, distance)
        
        return min(int(min_distance), 10)  # Cap at 10 for state space
    
    def _classify_position(self, unit: Dict[str, Any], battlefield_state: Dict[str, Any]) -> str:
        """Classify unit position (center, edge, corner)"""
        pos = unit["position"]
        grid_size = battlefield_state.get("grid_size", [10, 10])
        
        center_x, center_y = grid_size[0] // 2, grid_size[1] // 2
        distance_from_center = abs(pos[0] - center_x) + abs(pos[1] - center_y)
        
        if distance_from_center <= 2:
            return "center"
        elif pos[0] == 0 or pos[0] == grid_size[0]-1 or pos[1] == 0 or pos[1] == grid_size[1]-1:
            return "edge"
        else:
            return "middle"
    
    def _classify_turn_phase(self, battlefield_state: Dict[str, Any]) -> str:
        """Classify game phase (early, mid, late)"""
        turn_number = battlefield_state.get("turn_number", 1)
        total_units = len(battlefield_state.get("units", []))
        alive_units = len([u for u in battlefield_state.get("units", []) if u.get("alive", True)])
        
        casualty_rate = 1.0 - (alive_units / max(total_units, 1))
        
        if turn_number <= 3:
            return "early"
        elif casualty_rate > 0.5:
            return "late"
        else:
            return "mid"
    
    def choose_action(self, state_key: str, available_actions: List[str]) -> str:
        """Choose action using epsilon-greedy policy"""
        self.state_visits[state_key] += 1
        
        # Exploration vs exploitation
        if np.random.random() < self.exploration_rate:
            return np.random.choice(available_actions)
        
        # Choose best action based on Q-values
        q_values = {action: self.q_table[state_key][action] for action in available_actions}
        return max(q_values, key=q_values.get) if q_values else np.random.choice(available_actions)
    
    def update_q_value(self, state_key: str, action: str, reward: float, next_state_key: str, 
                      next_available_actions: List[str]):
        """Update Q-value using Q-learning formula"""
        # Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
        
        current_q = self.q_table[state_key][action]
        
        if next_available_actions:
            max_next_q = max(self.q_table[next_state_key][a] for a in next_available_actions)
        else:
            max_next_q = 0
        
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state_key][action] = new_q
        
        # Record action in history
        self.action_history.append({
            "state": state_key,
            "action": action,
            "reward": reward,
            "q_value": new_q,
            "timestamp": datetime.now()
        })
        
        logger.debug("Q-learning update",
                    state=state_key,
                    action=action,
                    reward=reward,
                    old_q=current_q,
                    new_q=new_q)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            "states_explored": len(self.q_table),
            "total_state_visits": sum(self.state_visits.values()),
            "exploration_rate": self.exploration_rate,
            "learning_rate": self.learning_rate,
            "recent_actions": len(self.action_history)
        }


class PatternRecognizer:
    """Recognizes and learns tactical patterns from gameplay"""
    
    def __init__(self, pattern_threshold: float = 0.7):
        self.pattern_threshold = pattern_threshold
        self.patterns: Dict[str, TacticalPattern] = {}
        self.situation_database: List[Dict[str, Any]] = []
        self.feature_importance: Dict[str, float] = {}
        
    def analyze_situation(self, battlefield_state: Dict[str, Any], unit_id: str) -> Dict[str, Any]:
        """Extract features from battlefield situation"""
        current_unit = next((u for u in battlefield_state.get("units", []) if u["id"] == unit_id), None)
        if not current_unit:
            return {}
        
        enemies = [u for u in battlefield_state.get("units", []) 
                  if u.get("team") != current_unit.get("team") and u.get("alive", True)]
        allies = [u for u in battlefield_state.get("units", []) 
                 if u.get("team") == current_unit.get("team") and u.get("alive", True) and u["id"] != unit_id]
        
        features = {
            # Unit state features
            "unit_hp_ratio": current_unit["hp"] / max(current_unit["max_hp"], 1),
            "unit_mp_ratio": current_unit.get("mp", 0) / max(current_unit.get("max_mp", 1), 1),
            "unit_position": current_unit["position"],
            
            # Tactical situation features
            "enemy_count": len(enemies),
            "ally_count": len(allies),
            "numerical_advantage": len(allies) - len(enemies),
            "average_enemy_hp": np.mean([e["hp"] / max(e["max_hp"], 1) for e in enemies]) if enemies else 1.0,
            "average_ally_hp": np.mean([a["hp"] / max(a["max_hp"], 1) for a in allies]) if allies else 1.0,
            
            # Positioning features
            "isolation_score": self._calculate_isolation(current_unit, allies),
            "threat_pressure": self._calculate_threat_pressure(current_unit, enemies),
            "flanking_opportunities": self._count_flanking_opportunities(current_unit, enemies),
            "escape_routes": self._count_escape_routes(current_unit, enemies, battlefield_state),
            
            # Strategic features
            "turn_number": battlefield_state.get("turn_number", 1),
            "battle_phase": self._determine_battle_phase(battlefield_state),
            "objective_control": self._assess_objective_control(battlefield_state, current_unit)
        }
        
        return features
    
    def _calculate_isolation(self, unit: Dict[str, Any], allies: List[Dict[str, Any]]) -> float:
        """Calculate how isolated a unit is from allies"""
        if not allies:
            return 1.0
        
        unit_pos = unit["position"]
        distances = [abs(unit_pos[0] - ally["position"][0]) + abs(unit_pos[1] - ally["position"][1]) 
                    for ally in allies]
        
        avg_distance = np.mean(distances)
        return min(avg_distance / 5.0, 1.0)  # Normalize to 0-1
    
    def _calculate_threat_pressure(self, unit: Dict[str, Any], enemies: List[Dict[str, Any]]) -> float:
        """Calculate incoming threat pressure"""
        if not enemies:
            return 0.0
        
        unit_pos = unit["position"]
        threat_score = 0.0
        
        for enemy in enemies:
            enemy_pos = enemy["position"]
            distance = abs(unit_pos[0] - enemy_pos[0]) + abs(unit_pos[1] - enemy_pos[1])
            
            # Closer enemies contribute more threat
            if distance <= 3:
                enemy_power = (enemy.get("physical_attack", 10) + enemy.get("magical_attack", 10))
                threat_contribution = enemy_power / max(distance, 1)
                threat_score += threat_contribution
        
        return min(threat_score / 50.0, 1.0)  # Normalize
    
    def _count_flanking_opportunities(self, unit: Dict[str, Any], enemies: List[Dict[str, Any]]) -> int:
        """Count potential flanking opportunities"""
        unit_pos = unit["position"]
        opportunities = 0
        
        for enemy in enemies:
            enemy_pos = enemy["position"]
            distance = abs(unit_pos[0] - enemy_pos[0]) + abs(unit_pos[1] - enemy_pos[1])
            
            # Can flank if within movement range and enemy has limited escape
            if distance <= 4:  # Within potential movement + attack range
                opportunities += 1
        
        return opportunities
    
    def _count_escape_routes(self, unit: Dict[str, Any], enemies: List[Dict[str, Any]], 
                           battlefield_state: Dict[str, Any]) -> int:
        """Count available escape routes"""
        unit_pos = unit["position"]
        grid_size = battlefield_state.get("grid_size", [10, 10])
        escape_routes = 0
        
        # Check adjacent positions
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            new_x, new_y = unit_pos[0] + dx, unit_pos[1] + dy
            
            # Check if position is valid and not too close to enemies
            if 0 <= new_x < grid_size[0] and 0 <= new_y < grid_size[1]:
                min_enemy_distance = float('inf')
                for enemy in enemies:
                    enemy_pos = enemy["position"]
                    dist = abs(new_x - enemy_pos[0]) + abs(new_y - enemy_pos[1])
                    min_enemy_distance = min(min_enemy_distance, dist)
                
                if min_enemy_distance > 2:  # Safe distance
                    escape_routes += 1
        
        return escape_routes
    
    def _determine_battle_phase(self, battlefield_state: Dict[str, Any]) -> str:
        """Determine current battle phase"""
        units = battlefield_state.get("units", [])
        alive_units = [u for u in units if u.get("alive", True)]
        turn_number = battlefield_state.get("turn_number", 1)
        
        casualty_rate = 1.0 - (len(alive_units) / max(len(units), 1))
        
        if turn_number <= 2:
            return "opening"
        elif casualty_rate > 0.6:
            return "endgame"
        elif casualty_rate > 0.3:
            return "late_midgame"
        else:
            return "early_midgame"
    
    def _assess_objective_control(self, battlefield_state: Dict[str, Any], unit: Dict[str, Any]) -> float:
        """Assess control of battlefield objectives"""
        # Simplified: control of center area
        center_x, center_y = 5, 5  # Assuming 10x10 grid
        unit_pos = unit["position"]
        
        distance_from_center = abs(unit_pos[0] - center_x) + abs(unit_pos[1] - center_y)
        return 1.0 - (distance_from_center / 10.0)  # Normalized
    
    def record_pattern(self, situation_features: Dict[str, Any], action_taken: Dict[str, Any], 
                      outcome: OutcomeType, reward: float):
        """Record a pattern from gameplay"""
        pattern_id = self._generate_pattern_id(situation_features)
        
        if pattern_id not in self.patterns:
            self.patterns[pattern_id] = TacticalPattern(
                pattern_id=pattern_id,
                pattern_type=self._classify_pattern_type(situation_features),
                situation_features=situation_features,
                successful_responses=[],
                failure_responses=[],
                success_rate=0.0,
                confidence=0.0,
                usage_count=0,
                last_updated=datetime.now()
            )
        
        pattern = self.patterns[pattern_id]
        pattern.usage_count += 1
        pattern.last_updated = datetime.now()
        
        response_data = {
            "action": action_taken,
            "reward": reward,
            "timestamp": datetime.now()
        }
        
        if outcome == OutcomeType.SUCCESS:
            pattern.successful_responses.append(response_data)
        else:
            pattern.failure_responses.append(response_data)
        
        # Update success rate
        total_responses = len(pattern.successful_responses) + len(pattern.failure_responses)
        pattern.success_rate = len(pattern.successful_responses) / max(total_responses, 1)
        
        # Update confidence based on sample size and consistency
        pattern.confidence = min(1.0, total_responses / 10.0) * pattern.success_rate
        
        logger.debug("Pattern recorded",
                    pattern_id=pattern_id,
                    success_rate=pattern.success_rate,
                    confidence=pattern.confidence)
    
    def _generate_pattern_id(self, features: Dict[str, Any]) -> str:
        """Generate unique pattern ID from features"""
        # Discretize continuous features for pattern matching
        discretized = {
            "hp": "high" if features.get("unit_hp_ratio", 1) > 0.7 else "medium" if features.get("unit_hp_ratio", 1) > 0.3 else "low",
            "enemies": "many" if features.get("enemy_count", 0) > 2 else "few",
            "advantage": "positive" if features.get("numerical_advantage", 0) > 0 else "negative" if features.get("numerical_advantage", 0) < 0 else "even",
            "threat": "high" if features.get("threat_pressure", 0) > 0.7 else "low",
            "phase": features.get("battle_phase", "unknown")
        }
        
        return f"{discretized['hp']}_{discretized['enemies']}_{discretized['advantage']}_{discretized['threat']}_{discretized['phase']}"
    
    def _classify_pattern_type(self, features: Dict[str, Any]) -> str:
        """Classify the type of tactical pattern"""
        threat = features.get("threat_pressure", 0)
        flanking = features.get("flanking_opportunities", 0)
        isolation = features.get("isolation_score", 0)
        
        if threat > 0.7:
            return "high_threat"
        elif flanking > 1:
            return "flanking_opportunity"
        elif isolation > 0.8:
            return "isolated_unit"
        else:
            return "standard_tactical"
    
    def find_matching_patterns(self, situation_features: Dict[str, Any]) -> List[TacticalPattern]:
        """Find patterns that match the current situation"""
        pattern_id = self._generate_pattern_id(situation_features)
        
        matching_patterns = []
        
        # Exact match
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            if pattern.confidence > self.pattern_threshold:
                matching_patterns.append(pattern)
        
        # Similar patterns (relaxed matching)
        for pattern in self.patterns.values():
            if pattern.pattern_id != pattern_id and pattern.confidence > self.pattern_threshold:
                similarity = self._calculate_pattern_similarity(situation_features, pattern.situation_features)
                if similarity > 0.8:
                    matching_patterns.append(pattern)
        
        return sorted(matching_patterns, key=lambda p: p.confidence, reverse=True)
    
    def _calculate_pattern_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """Calculate similarity between two feature sets"""
        # Simplified similarity calculation
        similar_keys = 0
        total_keys = 0
        
        for key in features1:
            if key in features2:
                total_keys += 1
                val1, val2 = features1[key], features2[key]
                
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    if abs(val1 - val2) < 0.2:  # Within 20% for numeric values
                        similar_keys += 1
                elif val1 == val2:  # Exact match for categorical
                    similar_keys += 1
        
        return similar_keys / max(total_keys, 1)
    
    def get_pattern_recommendation(self, situation_features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get action recommendation based on learned patterns"""
        matching_patterns = self.find_matching_patterns(situation_features)
        
        if not matching_patterns:
            return None
        
        best_pattern = matching_patterns[0]
        
        if best_pattern.successful_responses:
            # Choose the most successful response
            best_response = max(best_pattern.successful_responses, key=lambda r: r["reward"])
            
            return {
                "recommended_action": best_response["action"],
                "confidence": best_pattern.confidence,
                "pattern_type": best_pattern.pattern_type,
                "success_rate": best_pattern.success_rate,
                "reasoning": f"Pattern-based recommendation from {best_pattern.usage_count} examples"
            }
        
        return None


class OpponentModeler:
    """Models opponent behavior and adapts strategies accordingly"""
    
    def __init__(self):
        self.opponent_models: Dict[str, OpponentModel] = {}
        self.interaction_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
    def observe_opponent_action(self, opponent_id: str, action: Dict[str, Any], 
                              situation: Dict[str, Any], outcome: Dict[str, Any]):
        """Observe and record opponent action"""
        if opponent_id not in self.opponent_models:
            self.opponent_models[opponent_id] = OpponentModel(
                opponent_id=opponent_id,
                behavioral_traits={},
                preferred_actions={},
                weaknesses=[],
                strengths=[],
                predictability=0.5,
                adaptation_rate=0.1,
                games_observed=0
            )
        
        model = self.opponent_models[opponent_id]
        model.last_encounter = datetime.now()
        
        # Record interaction
        interaction = {
            "action": action,
            "situation": situation,
            "outcome": outcome,
            "timestamp": datetime.now()
        }
        self.interaction_history[opponent_id].append(interaction)
        
        # Update behavioral analysis
        self._update_behavioral_traits(opponent_id, action, situation)
        self._update_preferred_actions(opponent_id, action)
        self._analyze_predictability(opponent_id)
        
        logger.debug("Opponent action observed",
                    opponent_id=opponent_id,
                    action_type=action.get("action_type", "unknown"))
    
    def _update_behavioral_traits(self, opponent_id: str, action: Dict[str, Any], 
                                 situation: Dict[str, Any]):
        """Update behavioral trait analysis"""
        model = self.opponent_models[opponent_id]
        
        # Analyze aggression
        if action.get("action_type") == "attack":
            current_aggression = model.behavioral_traits.get("aggression", 0.5)
            model.behavioral_traits["aggression"] = min(1.0, current_aggression + 0.1)
        elif action.get("action_type") == "move":
            # Analyze movement pattern for aggression/defensiveness
            current_aggression = model.behavioral_traits.get("aggression", 0.5)
            model.behavioral_traits["aggression"] = max(0.0, current_aggression - 0.05)
        
        # Analyze risk tolerance
        hp_ratio = situation.get("unit_hp_ratio", 1.0)
        if action.get("action_type") == "attack" and hp_ratio < 0.3:
            # Attacking with low health indicates high risk tolerance
            current_risk = model.behavioral_traits.get("risk_tolerance", 0.5)
            model.behavioral_traits["risk_tolerance"] = min(1.0, current_risk + 0.2)
        
        # Analyze patience
        if action.get("action_type") == "end_turn":
            current_patience = model.behavioral_traits.get("patience", 0.5)
            model.behavioral_traits["patience"] = min(1.0, current_patience + 0.1)
    
    def _update_preferred_actions(self, opponent_id: str, action: Dict[str, Any]):
        """Update preferred action analysis"""
        model = self.opponent_models[opponent_id]
        action_type = action.get("action_type", "unknown")
        
        current_count = model.preferred_actions.get(action_type, 0)
        model.preferred_actions[action_type] = current_count + 1
        
        # Normalize to percentages
        total_actions = sum(model.preferred_actions.values())
        for act_type in model.preferred_actions:
            model.preferred_actions[act_type] = model.preferred_actions[act_type] / total_actions
    
    def _analyze_predictability(self, opponent_id: str):
        """Analyze how predictable the opponent is"""
        interactions = self.interaction_history[opponent_id]
        if len(interactions) < 5:
            return
        
        # Analyze action patterns
        recent_actions = [i["action"].get("action_type") for i in interactions[-10:]]
        action_frequency = {}
        for action in recent_actions:
            action_frequency[action] = action_frequency.get(action, 0) + 1
        
        # Calculate entropy as measure of unpredictability
        total = len(recent_actions)
        entropy = 0
        for count in action_frequency.values():
            prob = count / total
            if prob > 0:
                entropy -= prob * math.log2(prob)
        
        # Convert entropy to predictability (lower entropy = higher predictability)
        max_entropy = math.log2(len(set(recent_actions))) if recent_actions else 1
        predictability = 1.0 - (entropy / max_entropy)
        
        model = self.opponent_models[opponent_id]
        model.predictability = predictability
    
    def predict_opponent_action(self, opponent_id: str, situation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Predict opponent's likely action based on model"""
        if opponent_id not in self.opponent_models:
            return None
        
        model = self.opponent_models[opponent_id]
        
        # Use behavioral traits and preferred actions to predict
        aggression = model.behavioral_traits.get("aggression", 0.5)
        risk_tolerance = model.behavioral_traits.get("risk_tolerance", 0.5)
        
        hp_ratio = situation.get("unit_hp_ratio", 1.0)
        enemy_count = situation.get("enemy_count", 0)
        
        prediction_scores = {}
        
        # Score attack actions
        if enemy_count > 0:
            attack_preference = model.preferred_actions.get("attack", 0.2)
            attack_score = aggression * attack_preference
            
            # Adjust based on situation
            if hp_ratio > 0.7:
                attack_score *= 1.5
            elif hp_ratio < 0.3:
                attack_score *= risk_tolerance
            
            prediction_scores["attack"] = attack_score
        
        # Score move actions
        move_preference = model.preferred_actions.get("move", 0.3)
        move_score = move_preference
        
        if hp_ratio < 0.4:
            move_score *= 2.0  # More likely to move when low health
        
        prediction_scores["move"] = move_score
        
        # Score defensive actions
        defensive_score = (1.0 - aggression) * (1.0 - risk_tolerance)
        prediction_scores["end_turn"] = defensive_score
        
        if not prediction_scores:
            return None
        
        # Choose most likely action
        predicted_action = max(prediction_scores, key=prediction_scores.get)
        confidence = model.predictability * prediction_scores[predicted_action]
        
        return {
            "predicted_action": predicted_action,
            "confidence": confidence,
            "reasoning": f"Based on {len(self.interaction_history[opponent_id])} observations",
            "behavioral_profile": model.behavioral_traits
        }
    
    def get_counter_strategy(self, opponent_id: str) -> Optional[Dict[str, Any]]:
        """Get recommended counter-strategy for opponent"""
        if opponent_id not in self.opponent_models:
            return None
        
        model = self.opponent_models[opponent_id]
        
        aggression = model.behavioral_traits.get("aggression", 0.5)
        risk_tolerance = model.behavioral_traits.get("risk_tolerance", 0.5)
        predictability = model.predictability
        
        # Generate counter-strategy
        if aggression > 0.7:
            strategy = "defensive_counter"
            tactics = ["Use defensive positioning", "Wait for overextension", "Counter-attack when safe"]
        elif aggression < 0.3:
            strategy = "aggressive_pressure"
            tactics = ["Apply constant pressure", "Force difficult decisions", "Control initiative"]
        elif predictability > 0.8:
            strategy = "pattern_breaking"
            tactics = ["Use unexpected moves", "Vary attack patterns", "Break routine positioning"]
        else:
            strategy = "adaptive_response"
            tactics = ["Mirror opponent adaptations", "Maintain flexible positioning", "React to opportunities"]
        
        return {
            "strategy": strategy,
            "tactics": tactics,
            "confidence": min(1.0, len(self.interaction_history[opponent_id]) / 20.0),
            "opponent_profile": {
                "aggression": aggression,
                "risk_tolerance": risk_tolerance,
                "predictability": predictability
            }
        }


class LearningSystem:
    """Main learning system that coordinates all learning components"""
    
    def __init__(self, personality: AIPersonality):
        self.personality = personality
        self.reinforcement_learner = ReinforcementLearner()
        self.pattern_recognizer = PatternRecognizer()
        self.opponent_modeler = OpponentModeler()
        self.learning_examples: List[LearningExample] = []
        self.metrics = LearningMetrics(
            total_examples=0,
            patterns_learned=0,
            opponents_modeled=0,
            average_improvement=0.0,
            learning_rate=0.1,
            confidence_score=0.5,
            adaptation_count=0
        )
        
    async def learn_from_experience(self, decision_data: Dict[str, Any], outcome_data: Dict[str, Any]):
        """Learn from a completed decision and its outcome"""
        # Create learning example
        example = LearningExample(
            situation_id=decision_data.get("situation_id", f"situation_{time.time()}"),
            battlefield_state=decision_data.get("battlefield_state", {}),
            action_taken=decision_data.get("action", {}),
            outcome=OutcomeType(outcome_data.get("outcome_type", "unknown")),
            reward=self._calculate_reward(decision_data, outcome_data),
            timestamp=datetime.now(),
            metadata={
                "personality_type": self.personality.personality_type,
                "decision_confidence": decision_data.get("confidence", 0.5),
                "execution_time": outcome_data.get("execution_time", 0)
            }
        )
        
        self.learning_examples.append(example)
        self.metrics.total_examples += 1
        
        # Update different learning components
        await self._update_reinforcement_learning(example)
        await self._update_pattern_recognition(example)
        await self._update_opponent_modeling(example, decision_data, outcome_data)
        
        # Update personality learning
        await self.personality.learn_from_outcome(decision_data, outcome_data.dict() if hasattr(outcome_data, 'dict') else outcome_data)
        
        # Update metrics
        await self._update_metrics()
        
        logger.info("Learning system updated",
                   total_examples=self.metrics.total_examples,
                   reward=example.reward,
                   outcome=example.outcome)
    
    def _calculate_reward(self, decision_data: Dict[str, Any], outcome_data: Dict[str, Any]) -> float:
        """Calculate reward for reinforcement learning"""
        base_reward = 0.0
        
        # Success/failure reward
        if outcome_data.get("success", False):
            base_reward += 1.0
        else:
            base_reward -= 0.5
        
        # Efficiency bonus
        execution_time = outcome_data.get("execution_time", 1.0)
        if execution_time < 0.5:  # Fast decision
            base_reward += 0.2
        
        # Damage dealt/received adjustments
        damage_dealt = outcome_data.get("damage_dealt", 0)
        damage_received = outcome_data.get("damage_received", 0)
        
        base_reward += damage_dealt * 0.1
        base_reward -= damage_received * 0.15
        
        # Personality-specific rewards
        if self.personality.personality_type == PersonalityType.AGGRESSIVE:
            if decision_data.get("action", {}).get("action_type") == "attack":
                base_reward += 0.3
        elif self.personality.personality_type == PersonalityType.DEFENSIVE:
            if damage_received == 0:  # Avoided damage
                base_reward += 0.4
        
        return max(-2.0, min(2.0, base_reward))  # Clamp between -2 and 2
    
    async def _update_reinforcement_learning(self, example: LearningExample):
        """Update Q-learning with new experience"""
        unit_id = example.metadata.get("unit_id", "unknown")
        state_key = self.reinforcement_learner.get_state_key(example.battlefield_state, unit_id)
        action = example.action_taken.get("action_type", "unknown")
        
        # For Q-learning, we'd need the next state, but for simplicity we'll update with current info
        self.reinforcement_learner.update_q_value(
            state_key=state_key,
            action=action,
            reward=example.reward,
            next_state_key=state_key,  # Simplified
            next_available_actions=[action]  # Simplified
        )
    
    async def _update_pattern_recognition(self, example: LearningExample):
        """Update pattern recognition with new experience"""
        if example.battlefield_state:
            situation_features = self.pattern_recognizer.analyze_situation(
                example.battlefield_state, 
                example.metadata.get("unit_id", "unknown")
            )
            
            self.pattern_recognizer.record_pattern(
                situation_features=situation_features,
                action_taken=example.action_taken,
                outcome=example.outcome,
                reward=example.reward
            )
            
            self.metrics.patterns_learned = len(self.pattern_recognizer.patterns)
    
    async def _update_opponent_modeling(self, example: LearningExample, 
                                      decision_data: Dict[str, Any], outcome_data: Dict[str, Any]):
        """Update opponent models if opponent actions are available"""
        # This would be called when we observe opponent actions
        # For now, we'll skip this part as we'd need opponent action data
        pass
    
    async def _update_metrics(self):
        """Update learning system metrics"""
        if len(self.learning_examples) > 1:
            recent_rewards = [ex.reward for ex in self.learning_examples[-10:]]
            self.metrics.average_improvement = np.mean(recent_rewards)
        
        # Calculate confidence based on experience and success rate
        if self.learning_examples:
            successful_examples = len([ex for ex in self.learning_examples if ex.outcome == OutcomeType.SUCCESS])
            success_rate = successful_examples / len(self.learning_examples)
            experience_factor = min(1.0, len(self.learning_examples) / 100.0)
            self.metrics.confidence_score = success_rate * experience_factor
    
    async def get_learning_recommendation(self, battlefield_state: Dict[str, Any], 
                                        unit_id: str, available_actions: List[str]) -> Optional[Dict[str, Any]]:
        """Get action recommendation based on learned experience"""
        recommendations = []
        
        # Get reinforcement learning recommendation
        state_key = self.reinforcement_learner.get_state_key(battlefield_state, unit_id)
        if available_actions:
            rl_action = self.reinforcement_learner.choose_action(state_key, available_actions)
            recommendations.append({
                "source": "reinforcement_learning",
                "action": rl_action,
                "confidence": 0.6,
                "reasoning": "Q-learning recommendation"
            })
        
        # Get pattern recognition recommendation
        situation_features = self.pattern_recognizer.analyze_situation(battlefield_state, unit_id)
        pattern_rec = self.pattern_recognizer.get_pattern_recommendation(situation_features)
        if pattern_rec:
            recommendations.append({
                "source": "pattern_recognition",
                "action": pattern_rec["recommended_action"],
                "confidence": pattern_rec["confidence"],
                "reasoning": pattern_rec["reasoning"]
            })
        
        if not recommendations:
            return None
        
        # Choose best recommendation
        best_rec = max(recommendations, key=lambda r: r["confidence"])
        
        return {
            "recommended_action": best_rec["action"],
            "confidence": best_rec["confidence"],
            "source": best_rec["source"],
            "reasoning": best_rec["reasoning"],
            "alternatives": [r for r in recommendations if r != best_rec]
        }
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics"""
        return {
            "metrics": self.metrics.dict(),
            "reinforcement_learning": self.reinforcement_learner.get_stats(),
            "pattern_recognition": {
                "patterns_learned": len(self.pattern_recognizer.patterns),
                "high_confidence_patterns": len([p for p in self.pattern_recognizer.patterns.values() if p.confidence > 0.8])
            },
            "opponent_modeling": {
                "opponents_modeled": len(self.opponent_modeler.opponent_models),
                "total_interactions": sum(len(hist) for hist in self.opponent_modeler.interaction_history.values())
            },
            "personality_learning": self.personality.get_stats()
        }