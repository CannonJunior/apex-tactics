"""
Adaptive Scaling System

Real-time performance monitoring and difficulty adjustment.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time
import statistics
from .difficulty_manager import DifficultyManager, AIDifficulty


@dataclass
class PerformanceMetrics:
    """Real-time performance metrics for adaptive scaling"""
    actions_per_minute: float
    average_decision_time: float
    tactical_accuracy: float     # How often player makes optimal moves
    reaction_speed: float        # Speed of response to threats
    resource_efficiency: float   # How well player manages resources
    positioning_skill: float     # Quality of unit positioning
    target_selection_skill: float # Quality of target selection


class AdaptiveScaling:
    """
    Real-time adaptive difficulty scaling system.
    
    Monitors player performance during battles and makes micro-adjustments
    to AI behavior to maintain optimal challenge level.
    """
    
    def __init__(self, difficulty_manager: DifficultyManager):
        self.difficulty_manager = difficulty_manager
        
        # Real-time performance tracking
        self.current_metrics = PerformanceMetrics(
            actions_per_minute=0.0,
            average_decision_time=0.0,
            tactical_accuracy=0.5,
            reaction_speed=0.5,
            resource_efficiency=0.5,
            positioning_skill=0.5,
            target_selection_skill=0.5
        )
        
        # Tracking data
        self.action_timestamps: List[float] = []
        self.decision_times: List[float] = []
        self.tactical_decisions: List[Tuple[bool, float]] = []  # (was_optimal, confidence)
        self.reaction_times: List[float] = []
        
        # Adaptive parameters
        self.adaptation_sensitivity = 0.05  # How quickly to adapt (0-1)
        self.performance_baseline = 0.5     # Expected performance level
        self.adjustment_magnitude = 0.1     # How much to adjust AI behavior
        
        # Real-time adjustments
        self.current_ai_adjustments = {
            'accuracy_boost': 0.0,
            'reaction_delay': 0.0,
            'aggression_modifier': 0.0,
            'mistake_frequency': 0.0
        }
    
    def record_player_action(self, action_type: str, decision_time: float, 
                           was_optimal: bool = None, confidence: float = 1.0):
        """
        Record player action for real-time analysis.
        
        Args:
            action_type: Type of action performed
            decision_time: Time taken to make decision
            was_optimal: Whether the action was tactically optimal
            confidence: Confidence in optimality assessment (0-1)
        """
        current_time = time.time()
        
        # Record action timing
        self.action_timestamps.append(current_time)
        self.decision_times.append(decision_time)
        
        # Record tactical decision quality
        if was_optimal is not None:
            self.tactical_decisions.append((was_optimal, confidence))
        
        # Update metrics and adjust AI behavior
        self._update_real_time_metrics()
        self._apply_adaptive_adjustments()
    
    def record_reaction_time(self, threat_detected_time: float, response_time: float):
        """
        Record player reaction time to threats.
        
        Args:
            threat_detected_time: When threat became apparent
            response_time: When player responded
        """
        reaction_time = response_time - threat_detected_time
        self.reaction_times.append(max(0.0, reaction_time))
        
        self._update_real_time_metrics()
        self._apply_adaptive_adjustments()
    
    def _update_real_time_metrics(self):
        """Update current performance metrics"""
        current_time = time.time()
        
        # Calculate actions per minute
        recent_actions = [t for t in self.action_timestamps if current_time - t <= 60.0]
        self.current_metrics.actions_per_minute = len(recent_actions)
        
        # Calculate average decision time
        if self.decision_times:
            recent_decisions = self.decision_times[-10:]  # Last 10 decisions
            self.current_metrics.average_decision_time = statistics.mean(recent_decisions)
        
        # Calculate tactical accuracy
        if self.tactical_decisions:
            recent_tactical = self.tactical_decisions[-15:]  # Last 15 decisions
            weighted_accuracy = sum(
                (1.0 if optimal else 0.0) * confidence 
                for optimal, confidence in recent_tactical
            ) / len(recent_tactical)
            self.current_metrics.tactical_accuracy = weighted_accuracy
        
        # Calculate reaction speed score
        if self.reaction_times:
            recent_reactions = self.reaction_times[-10:]
            avg_reaction = statistics.mean(recent_reactions)
            # Convert to 0-1 score (faster = higher score)
            self.current_metrics.reaction_speed = max(0.0, 1.0 - (avg_reaction / 5.0))
    
    def _apply_adaptive_adjustments(self):
        """Apply real-time adjustments to AI behavior"""
        # Calculate overall performance level
        performance_level = self._calculate_overall_performance()
        
        # Determine adjustment direction
        performance_delta = performance_level - self.performance_baseline
        
        # Apply adjustments based on performance
        if performance_delta > 0.2:  # Player performing well
            self._increase_ai_challenge(performance_delta)
        elif performance_delta < -0.2:  # Player struggling
            self._decrease_ai_challenge(abs(performance_delta))
        else:
            self._maintain_current_challenge()
    
    def _calculate_overall_performance(self) -> float:
        """Calculate overall player performance score (0-1)"""
        metrics = self.current_metrics
        
        # Weight different performance aspects
        performance_score = (
            metrics.tactical_accuracy * 0.3 +
            metrics.reaction_speed * 0.2 +
            min(metrics.actions_per_minute / 20.0, 1.0) * 0.15 +  # Normalize APM
            max(0.0, 1.0 - metrics.average_decision_time / 10.0) * 0.15 +  # Faster decisions = better
            metrics.resource_efficiency * 0.1 +
            metrics.positioning_skill * 0.05 +
            metrics.target_selection_skill * 0.05
        )
        
        return max(0.0, min(1.0, performance_score))
    
    def _increase_ai_challenge(self, performance_delta: float):
        """Increase AI challenge level"""
        adjustment_factor = min(performance_delta * self.adaptation_sensitivity, self.adjustment_magnitude)
        
        # Boost AI capabilities
        self.current_ai_adjustments['accuracy_boost'] = min(0.2, 
            self.current_ai_adjustments['accuracy_boost'] + adjustment_factor)
        
        # Reduce AI reaction delay
        self.current_ai_adjustments['reaction_delay'] = max(-1.0,
            self.current_ai_adjustments['reaction_delay'] - adjustment_factor)
        
        # Increase AI aggression
        self.current_ai_adjustments['aggression_modifier'] = min(0.3,
            self.current_ai_adjustments['aggression_modifier'] + adjustment_factor)
        
        # Reduce AI mistake frequency
        self.current_ai_adjustments['mistake_frequency'] = max(-0.2,
            self.current_ai_adjustments['mistake_frequency'] - adjustment_factor * 0.5)
    
    def _decrease_ai_challenge(self, performance_delta: float):
        """Decrease AI challenge level"""
        adjustment_factor = min(performance_delta * self.adaptation_sensitivity, self.adjustment_magnitude)
        
        # Reduce AI capabilities
        self.current_ai_adjustments['accuracy_boost'] = max(-0.2,
            self.current_ai_adjustments['accuracy_boost'] - adjustment_factor)
        
        # Increase AI reaction delay
        self.current_ai_adjustments['reaction_delay'] = min(1.0,
            self.current_ai_adjustments['reaction_delay'] + adjustment_factor)
        
        # Decrease AI aggression
        self.current_ai_adjustments['aggression_modifier'] = max(-0.3,
            self.current_ai_adjustments['aggression_modifier'] - adjustment_factor)
        
        # Increase AI mistake frequency
        self.current_ai_adjustments['mistake_frequency'] = min(0.3,
            self.current_ai_adjustments['mistake_frequency'] + adjustment_factor * 0.5)
    
    def _maintain_current_challenge(self):
        """Gradually return adjustments to baseline"""
        decay_rate = 0.02  # How quickly adjustments decay
        
        for key in self.current_ai_adjustments:
            current_value = self.current_ai_adjustments[key]
            if abs(current_value) > 0.01:
                # Move towards zero
                self.current_ai_adjustments[key] = current_value * (1.0 - decay_rate)
    
    def get_adjusted_ai_modifier(self, modifier_type: str) -> float:
        """
        Get AI modifier with real-time adjustments applied.
        
        Args:
            modifier_type: Type of modifier to get
            
        Returns:
            Adjusted modifier value
        """
        base_modifier = self.difficulty_manager.get_ai_modifier(modifier_type)
        
        # Apply real-time adjustments
        if modifier_type == 'accuracy':
            return base_modifier + self.current_ai_adjustments['accuracy_boost']
        elif modifier_type == 'reaction_time':
            return base_modifier + self.current_ai_adjustments['reaction_delay']
        elif modifier_type == 'aggression':
            return base_modifier + self.current_ai_adjustments['aggression_modifier']
        elif modifier_type == 'mistake_chance':
            return base_modifier + self.current_ai_adjustments['mistake_frequency']
        else:
            return base_modifier
    
    def should_ai_make_adjusted_mistake(self) -> bool:
        """Check if AI should make mistake with real-time adjustment"""
        base_chance = self.difficulty_manager.get_ai_modifier('mistake_chance')
        adjusted_chance = base_chance + self.current_ai_adjustments['mistake_frequency']
        
        import random
        return random.random() < max(0.0, min(1.0, adjusted_chance))
    
    def get_performance_feedback(self) -> Dict:
        """Get performance feedback for player"""
        overall_performance = self._calculate_overall_performance()
        
        feedback = {
            'overall_score': overall_performance,
            'performance_level': self._get_performance_level_description(overall_performance),
            'strengths': self._identify_strengths(),
            'areas_for_improvement': self._identify_weaknesses(),
            'current_metrics': {
                'tactical_accuracy': self.current_metrics.tactical_accuracy,
                'reaction_speed': self.current_metrics.reaction_speed,
                'actions_per_minute': self.current_metrics.actions_per_minute,
                'average_decision_time': self.current_metrics.average_decision_time
            },
            'ai_adjustments_active': any(abs(v) > 0.01 for v in self.current_ai_adjustments.values())
        }
        
        return feedback
    
    def _get_performance_level_description(self, score: float) -> str:
        """Get description of performance level"""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.65:
            return "Good"
        elif score >= 0.5:
            return "Average"
        elif score >= 0.35:
            return "Below Average"
        else:
            return "Needs Improvement"
    
    def _identify_strengths(self) -> List[str]:
        """Identify player's tactical strengths"""
        strengths = []
        metrics = self.current_metrics
        
        if metrics.tactical_accuracy > 0.7:
            strengths.append("Tactical Decision Making")
        if metrics.reaction_speed > 0.7:
            strengths.append("Quick Reactions")
        if metrics.actions_per_minute > 15:
            strengths.append("Action Economy")
        if metrics.average_decision_time < 3.0:
            strengths.append("Decisive Planning")
        
        return strengths
    
    def _identify_weaknesses(self) -> List[str]:
        """Identify areas where player could improve"""
        weaknesses = []
        metrics = self.current_metrics
        
        if metrics.tactical_accuracy < 0.4:
            weaknesses.append("Tactical Decision Making")
        if metrics.reaction_speed < 0.4:
            weaknesses.append("Threat Response")
        if metrics.actions_per_minute < 8:
            weaknesses.append("Action Efficiency")
        if metrics.average_decision_time > 8.0:
            weaknesses.append("Decision Speed")
        
        return weaknesses
    
    def reset_battle_metrics(self):
        """Reset metrics for new battle"""
        self.action_timestamps.clear()
        self.decision_times.clear()
        self.tactical_decisions.clear()
        self.reaction_times.clear()
        
        # Reset real-time adjustments gradually
        for key in self.current_ai_adjustments:
            self.current_ai_adjustments[key] *= 0.5
    
    def get_adaptive_status(self) -> Dict:
        """Get comprehensive adaptive scaling status"""
        return {
            'current_performance': self._calculate_overall_performance(),
            'performance_metrics': {
                'tactical_accuracy': self.current_metrics.tactical_accuracy,
                'reaction_speed': self.current_metrics.reaction_speed,
                'actions_per_minute': self.current_metrics.actions_per_minute,
                'decision_time': self.current_metrics.average_decision_time
            },
            'active_adjustments': self.current_ai_adjustments.copy(),
            'adaptation_active': any(abs(v) > 0.01 for v in self.current_ai_adjustments.values()),
            'data_points': {
                'actions_recorded': len(self.action_timestamps),
                'decisions_analyzed': len(self.tactical_decisions),
                'reactions_measured': len(self.reaction_times)
            }
        }