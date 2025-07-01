"""
Dynamic Difficulty Scaling System

Implements adaptive AI difficulty that responds to player performance.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time
import math


class AIDifficulty(Enum):
    """AI difficulty levels with distinct behavioral characteristics"""
    SCRIPTED = 1     # Basic scripted behavior
    STRATEGIC = 2    # Tactical decision-making
    ADAPTIVE = 3     # Adapts to player behavior
    LEARNING = 4     # Learns from player patterns


@dataclass
class DifficultySettings:
    """Configuration for AI difficulty level"""
    level: AIDifficulty
    reaction_time: float         # AI decision delay (seconds)
    accuracy_modifier: float     # Attack accuracy multiplier
    damage_modifier: float       # Damage dealt multiplier
    health_modifier: float       # AI unit health multiplier
    planning_depth: int          # How many turns ahead AI plans
    mistake_chance: float        # Probability of suboptimal decisions
    aggression_level: float      # How aggressive AI behavior is
    formation_skill: float       # How well AI maintains formations
    target_priority_skill: float # How well AI prioritizes targets


class DifficultyManager:
    """
    Manages dynamic difficulty scaling for AI opponents.
    
    Monitors player performance and adjusts AI difficulty accordingly.
    """
    
    def __init__(self, initial_difficulty: AIDifficulty = AIDifficulty.STRATEGIC):
        self.current_difficulty = initial_difficulty
        self.difficulty_settings = self._create_difficulty_settings()
        
        # Performance tracking
        self.performance_history: List[Dict] = []
        self.recent_battles: List[Dict] = []
        self.adaptation_rate = 0.1  # How quickly difficulty adapts
        
        # Difficulty adjustment parameters
        self.min_difficulty = AIDifficulty.SCRIPTED
        self.max_difficulty = AIDifficulty.LEARNING
        self.performance_window = 5  # Number of battles to consider
        
        # Difficulty transition thresholds
        self.difficulty_up_threshold = 0.7    # Win rate to increase difficulty
        self.difficulty_down_threshold = 0.3  # Win rate to decrease difficulty
    
    def _create_difficulty_settings(self) -> Dict[AIDifficulty, DifficultySettings]:
        """Create difficulty setting configurations"""
        return {
            AIDifficulty.SCRIPTED: DifficultySettings(
                level=AIDifficulty.SCRIPTED,
                reaction_time=2.0,
                accuracy_modifier=0.7,
                damage_modifier=0.8,
                health_modifier=0.9,
                planning_depth=1,
                mistake_chance=0.3,
                aggression_level=0.5,
                formation_skill=0.4,
                target_priority_skill=0.5
            ),
            AIDifficulty.STRATEGIC: DifficultySettings(
                level=AIDifficulty.STRATEGIC,
                reaction_time=1.5,
                accuracy_modifier=0.85,
                damage_modifier=1.0,
                health_modifier=1.0,
                planning_depth=2,
                mistake_chance=0.2,
                aggression_level=0.7,
                formation_skill=0.7,
                target_priority_skill=0.7
            ),
            AIDifficulty.ADAPTIVE: DifficultySettings(
                level=AIDifficulty.ADAPTIVE,
                reaction_time=1.0,
                accuracy_modifier=0.95,
                damage_modifier=1.1,
                health_modifier=1.1,
                planning_depth=3,
                mistake_chance=0.1,
                aggression_level=0.8,
                formation_skill=0.85,
                target_priority_skill=0.85
            ),
            AIDifficulty.LEARNING: DifficultySettings(
                level=AIDifficulty.LEARNING,
                reaction_time=0.5,
                accuracy_modifier=1.0,
                damage_modifier=1.2,
                health_modifier=1.2,
                planning_depth=4,
                mistake_chance=0.05,
                aggression_level=0.9,
                formation_skill=0.95,
                target_priority_skill=0.95
            )
        }
    
    def get_current_settings(self) -> DifficultySettings:
        """Get current difficulty settings"""
        return self.difficulty_settings[self.current_difficulty]
    
    def record_battle_result(self, player_won: bool, battle_duration: float, 
                           player_units_lost: int, ai_units_lost: int,
                           player_mistakes: int = 0, ai_mistakes: int = 0):
        """
        Record battle result for difficulty analysis.
        
        Args:
            player_won: Whether player won the battle
            battle_duration: Duration of battle in seconds
            player_units_lost: Number of player units defeated
            ai_units_lost: Number of AI units defeated
            player_mistakes: Number of tactical mistakes by player
            ai_mistakes: Number of tactical mistakes by AI
        """
        battle_record = {
            'timestamp': time.time(),
            'player_won': player_won,
            'duration': battle_duration,
            'player_units_lost': player_units_lost,
            'ai_units_lost': ai_units_lost,
            'player_mistakes': player_mistakes,
            'ai_mistakes': ai_mistakes,
            'difficulty_level': self.current_difficulty.value,
            'win_margin': self._calculate_win_margin(player_won, player_units_lost, ai_units_lost)
        }
        
        self.recent_battles.append(battle_record)
        
        # Keep only recent battles for analysis
        if len(self.recent_battles) > self.performance_window * 2:
            self.recent_battles = self.recent_battles[-self.performance_window * 2:]
        
        # Update difficulty based on performance
        self._update_difficulty()
    
    def _calculate_win_margin(self, player_won: bool, player_losses: int, ai_losses: int) -> float:
        """Calculate how decisive the victory was (-1.0 to 1.0)"""
        if player_losses + ai_losses == 0:
            return 0.0
        
        # Calculate relative performance
        total_casualties = player_losses + ai_losses
        player_loss_ratio = player_losses / total_casualties
        ai_loss_ratio = ai_losses / total_casualties
        
        # Margin calculation
        if player_won:
            # Player won - positive margin based on how few units they lost
            margin = 1.0 - (player_loss_ratio * 2)  # Scale to 0-1
        else:
            # Player lost - negative margin based on how many units they lost
            margin = -1.0 + (ai_loss_ratio * 2)     # Scale to -1-0
        
        return max(-1.0, min(1.0, margin))
    
    def _update_difficulty(self):
        """Update difficulty based on recent performance"""
        if len(self.recent_battles) < 3:
            return  # Need minimum battles for analysis
        
        # Analyze recent performance
        recent_performance = self._analyze_recent_performance()
        
        # Determine if difficulty should change
        current_level = self.current_difficulty.value
        new_level = current_level
        
        # Check for difficulty increase
        if (recent_performance['win_rate'] > self.difficulty_up_threshold and
            recent_performance['average_margin'] > 0.3 and
            current_level < self.max_difficulty.value):
            new_level = current_level + 1
            print(f"Increasing AI difficulty to level {new_level} (win rate: {recent_performance['win_rate']:.2f})")
        
        # Check for difficulty decrease
        elif (recent_performance['win_rate'] < self.difficulty_down_threshold and
              recent_performance['average_margin'] < -0.3 and
              current_level > self.min_difficulty.value):
            new_level = current_level - 1
            print(f"Decreasing AI difficulty to level {new_level} (win rate: {recent_performance['win_rate']:.2f})")
        
        # Apply difficulty change
        if new_level != current_level:
            self.current_difficulty = AIDifficulty(new_level)
    
    def _analyze_recent_performance(self) -> Dict:
        """Analyze recent battle performance"""
        recent_count = min(self.performance_window, len(self.recent_battles))
        recent_battles = self.recent_battles[-recent_count:]
        
        if not recent_battles:
            return {'win_rate': 0.5, 'average_margin': 0.0, 'battle_count': 0}
        
        wins = sum(1 for battle in recent_battles if battle['player_won'])
        win_rate = wins / len(recent_battles)
        
        average_margin = sum(battle['win_margin'] for battle in recent_battles) / len(recent_battles)
        
        return {
            'win_rate': win_rate,
            'average_margin': average_margin,
            'battle_count': len(recent_battles),
            'recent_trend': self._calculate_performance_trend(recent_battles)
        }
    
    def _calculate_performance_trend(self, battles: List[Dict]) -> str:
        """Calculate if performance is improving, declining, or stable"""
        if len(battles) < 3:
            return 'insufficient_data'
        
        # Compare first half vs second half
        mid_point = len(battles) // 2
        first_half = battles[:mid_point]
        second_half = battles[mid_point:]
        
        first_win_rate = sum(1 for b in first_half if b['player_won']) / len(first_half)
        second_win_rate = sum(1 for b in second_half if b['player_won']) / len(second_half)
        
        difference = second_win_rate - first_win_rate
        
        if difference > 0.2:
            return 'improving'
        elif difference < -0.2:
            return 'declining'
        else:
            return 'stable'
    
    def get_ai_modifier(self, modifier_type: str) -> float:
        """
        Get AI modifier for specific aspect.
        
        Args:
            modifier_type: Type of modifier (accuracy, damage, health, etc.)
            
        Returns:
            Modifier value for current difficulty
        """
        settings = self.get_current_settings()
        
        modifier_map = {
            'accuracy': settings.accuracy_modifier,
            'damage': settings.damage_modifier,
            'health': settings.health_modifier,
            'reaction_time': settings.reaction_time,
            'mistake_chance': settings.mistake_chance,
            'aggression': settings.aggression_level,
            'formation_skill': settings.formation_skill,
            'target_priority': settings.target_priority_skill
        }
        
        return modifier_map.get(modifier_type, 1.0)
    
    def should_ai_make_mistake(self) -> bool:
        """Determine if AI should make a tactical mistake"""
        import random
        settings = self.get_current_settings()
        return random.random() < settings.mistake_chance
    
    def get_ai_planning_depth(self) -> int:
        """Get how many turns ahead AI should plan"""
        return self.get_current_settings().planning_depth
    
    def get_ai_reaction_delay(self) -> float:
        """Get AI reaction time delay"""
        return self.get_current_settings().reaction_time
    
    def force_difficulty_change(self, new_difficulty: AIDifficulty):
        """Manually set difficulty level"""
        old_difficulty = self.current_difficulty
        self.current_difficulty = new_difficulty
        print(f"AI difficulty manually changed from {old_difficulty.name} to {new_difficulty.name}")
    
    def get_difficulty_status(self) -> Dict:
        """Get comprehensive difficulty system status"""
        recent_performance = self._analyze_recent_performance()
        settings = self.get_current_settings()
        
        return {
            'current_difficulty': self.current_difficulty.name,
            'difficulty_value': self.current_difficulty.value,
            'recent_performance': recent_performance,
            'settings': {
                'accuracy_modifier': settings.accuracy_modifier,
                'damage_modifier': settings.damage_modifier,
                'health_modifier': settings.health_modifier,
                'planning_depth': settings.planning_depth,
                'mistake_chance': settings.mistake_chance,
                'aggression_level': settings.aggression_level
            },
            'battle_history_count': len(self.recent_battles),
            'adaptation_active': len(self.recent_battles) >= 3
        }