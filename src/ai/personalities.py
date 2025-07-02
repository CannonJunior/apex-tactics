"""
AI Personality System

Defines different AI personalities with distinct behavioral patterns,
decision-making styles, and tactical preferences.
"""

import random
import json
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from abc import ABC, abstractmethod

import structlog
from pydantic import BaseModel

from .models import (
    AIDecisionRequest, AIDecisionResponse, GameAction,
    BattlefieldState, ThreatAssessment, OpportunityAssessment
)

logger = structlog.get_logger()


class PersonalityType(str, Enum):
    """Different AI personality types"""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    TACTICAL = "tactical"
    BERSERKER = "berserker"
    SUPPORT = "support"
    ADAPTIVE = "adaptive"
    OPPORTUNIST = "opportunist"
    CONSERVATIVE = "conservative"


class PersonalityTraits(BaseModel):
    """Personality trait configuration"""
    aggression: float = 0.5  # 0.0 = very defensive, 1.0 = very aggressive
    risk_tolerance: float = 0.5  # 0.0 = risk-averse, 1.0 = risk-seeking
    patience: float = 0.5  # 0.0 = impatient, 1.0 = very patient
    teamwork: float = 0.5  # 0.0 = individualistic, 1.0 = team-focused
    adaptability: float = 0.5  # 0.0 = rigid, 1.0 = highly adaptive
    planning_horizon: float = 0.5  # 0.0 = short-term, 1.0 = long-term
    resource_management: float = 0.5  # 0.0 = wasteful, 1.0 = conservative
    target_prioritization: str = "balanced"  # "damage", "survival", "objectives", "balanced"


class PersonalityMemory(BaseModel):
    """Memory system for personality learning"""
    successful_tactics: List[Dict[str, Any]] = []
    failed_tactics: List[Dict[str, Any]] = []
    opponent_patterns: Dict[str, List[Dict[str, Any]]] = {}
    situation_outcomes: Dict[str, List[Dict[str, Any]]] = {}
    adaptation_history: List[Dict[str, Any]] = []
    confidence_levels: Dict[str, float] = {}


class AIPersonality(ABC):
    """Base class for AI personalities"""
    
    def __init__(self, personality_type: PersonalityType, traits: PersonalityTraits):
        self.personality_type = personality_type
        self.traits = traits
        self.memory = PersonalityMemory()
        self.decision_count = 0
        self.success_rate = 0.0
        self.adaptation_rate = 0.1
        
    @abstractmethod
    async def evaluate_situation(self, battlefield: BattlefieldState, unit_id: str) -> Dict[str, Any]:
        """Evaluate the current battlefield situation from this personality's perspective"""
        pass
    
    @abstractmethod
    async def choose_action(self, request: AIDecisionRequest, available_actions: List[GameAction], 
                          situation_eval: Dict[str, Any]) -> Tuple[GameAction, float, str]:
        """Choose an action based on personality traits and situation evaluation"""
        pass
    
    async def learn_from_outcome(self, decision: Dict[str, Any], outcome: Dict[str, Any]):
        """Learn from the outcome of a previous decision"""
        self.decision_count += 1
        
        # Update success rate
        success = outcome.get("success", False)
        if self.decision_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            # Running average
            self.success_rate = ((self.success_rate * (self.decision_count - 1)) + 
                               (1.0 if success else 0.0)) / self.decision_count
        
        # Store successful/failed tactics
        tactic_data = {
            "situation": decision.get("situation", {}),
            "action": decision.get("action", {}),
            "outcome": outcome,
            "timestamp": decision.get("timestamp")
        }
        
        if success:
            self.memory.successful_tactics.append(tactic_data)
            # Keep only recent successes (limit memory)
            if len(self.memory.successful_tactics) > 50:
                self.memory.successful_tactics = self.memory.successful_tactics[-50:]
        else:
            self.memory.failed_tactics.append(tactic_data)
            if len(self.memory.failed_tactics) > 30:
                self.memory.failed_tactics = self.memory.failed_tactics[-30:]
        
        # Adaptive trait adjustment based on outcomes
        await self._adapt_traits(decision, outcome)
        
        logger.info("AI personality learned from outcome",
                   personality=self.personality_type,
                   success=success,
                   success_rate=self.success_rate,
                   decision_count=self.decision_count)
    
    async def _adapt_traits(self, decision: Dict[str, Any], outcome: Dict[str, Any]):
        """Adapt personality traits based on experience"""
        if self.traits.adaptability < 0.3:
            return  # Low adaptability personalities don't change much
        
        success = outcome.get("success", False)
        action_type = decision.get("action", {}).get("action_type", "")
        
        # Adjust traits based on action success/failure
        adjustment = self.adaptation_rate * self.traits.adaptability
        
        if action_type == "attack":
            if success:
                self.traits.aggression = min(1.0, self.traits.aggression + adjustment)
            else:
                self.traits.aggression = max(0.0, self.traits.aggression - adjustment)
        
        elif action_type == "move":
            if success:
                self.traits.patience = min(1.0, self.traits.patience + adjustment * 0.5)
            else:
                self.traits.risk_tolerance = max(0.0, self.traits.risk_tolerance - adjustment)
        
        # Adapt risk tolerance based on overall performance
        if self.success_rate > 0.7:
            self.traits.risk_tolerance = min(1.0, self.traits.risk_tolerance + adjustment * 0.3)
        elif self.success_rate < 0.3:
            self.traits.risk_tolerance = max(0.0, self.traits.risk_tolerance - adjustment * 0.5)
    
    def get_personality_prompt_modifier(self) -> str:
        """Get personality-specific prompt modifications for LLM"""
        base_prompt = f"You are an AI with a {self.personality_type.value} personality. "
        
        trait_descriptions = []
        
        if self.traits.aggression > 0.7:
            trait_descriptions.append("You prefer aggressive, offensive tactics")
        elif self.traits.aggression < 0.3:
            trait_descriptions.append("You favor defensive, cautious approaches")
        
        if self.traits.risk_tolerance > 0.7:
            trait_descriptions.append("You're willing to take significant risks for potential rewards")
        elif self.traits.risk_tolerance < 0.3:
            trait_descriptions.append("You avoid risky moves and prefer safe options")
        
        if self.traits.patience > 0.7:
            trait_descriptions.append("You think long-term and are willing to wait for the right moment")
        elif self.traits.patience < 0.3:
            trait_descriptions.append("You prefer quick, decisive actions")
        
        if self.traits.teamwork > 0.7:
            trait_descriptions.append("You coordinate well with allies and consider team synergy")
        elif self.traits.teamwork < 0.3:
            trait_descriptions.append("You focus on individual unit performance over team coordination")
        
        if trait_descriptions:
            base_prompt += " ".join(trait_descriptions) + ". "
        
        return base_prompt + f"Your current success rate is {self.success_rate:.1%}. "
    
    def get_stats(self) -> Dict[str, Any]:
        """Get personality statistics"""
        return {
            "personality_type": self.personality_type,
            "traits": self.traits.dict(),
            "decision_count": self.decision_count,
            "success_rate": self.success_rate,
            "memory_size": {
                "successful_tactics": len(self.memory.successful_tactics),
                "failed_tactics": len(self.memory.failed_tactics),
                "opponent_patterns": len(self.memory.opponent_patterns)
            }
        }


class AggressivePersonality(AIPersonality):
    """Aggressive AI that favors offensive actions and quick strikes"""
    
    def __init__(self):
        traits = PersonalityTraits(
            aggression=0.9,
            risk_tolerance=0.8,
            patience=0.2,
            teamwork=0.4,
            adaptability=0.6,
            planning_horizon=0.3,
            resource_management=0.3,
            target_prioritization="damage"
        )
        super().__init__(PersonalityType.AGGRESSIVE, traits)
    
    async def evaluate_situation(self, battlefield: BattlefieldState, unit_id: str) -> Dict[str, Any]:
        """Evaluate situation with focus on attack opportunities"""
        current_unit = next((u for u in battlefield.units if u.id == unit_id), None)
        if not current_unit:
            return {"error": "Unit not found"}
        
        enemies = [u for u in battlefield.units if u.team != current_unit.team and u.alive]
        
        # Look for vulnerable enemies
        vulnerable_enemies = []
        for enemy in enemies:
            hp_ratio = enemy.hp / enemy.max_hp
            if hp_ratio < 0.5:  # Low health enemies
                distance = current_unit.position.distance_to(enemy.position)
                vulnerable_enemies.append({
                    "unit_id": enemy.id,
                    "hp_ratio": hp_ratio,
                    "distance": distance,
                    "priority": (1.0 - hp_ratio) * (1.0 / max(distance, 1))
                })
        
        # Prioritize close, weak enemies
        vulnerable_enemies.sort(key=lambda x: x["priority"], reverse=True)
        
        return {
            "evaluation_type": "aggressive",
            "vulnerable_enemies": vulnerable_enemies[:3],
            "aggression_modifier": 1.2,
            "recommended_stance": "offensive",
            "priority_action_types": ["attack", "move_to_attack"]
        }
    
    async def choose_action(self, request: AIDecisionRequest, available_actions: List[GameAction], 
                          situation_eval: Dict[str, Any]) -> Tuple[GameAction, float, str]:
        """Choose action with aggressive bias"""
        # Strongly prefer attack actions
        attack_actions = [a for a in available_actions if a.action_type == "attack"]
        move_actions = [a for a in available_actions if a.action_type == "move"]
        
        if attack_actions and random.random() < 0.8:  # 80% chance to attack if possible
            chosen_action = random.choice(attack_actions)
            confidence = 0.85
            reasoning = "Aggressive personality chooses to attack when possible"
            
        elif move_actions:
            # Move towards closest enemy
            chosen_action = random.choice(move_actions)  # Simplified - should calculate best position
            confidence = 0.7
            reasoning = "Moving to better attack position"
            
        else:
            # Fallback to any available action
            chosen_action = random.choice(available_actions)
            confidence = 0.5
            reasoning = "No preferred actions available, choosing fallback"
        
        return chosen_action, confidence, reasoning


class DefensivePersonality(AIPersonality):
    """Defensive AI that prioritizes survival and positioning"""
    
    def __init__(self):
        traits = PersonalityTraits(
            aggression=0.2,
            risk_tolerance=0.3,
            patience=0.8,
            teamwork=0.7,
            adaptability=0.5,
            planning_horizon=0.8,
            resource_management=0.8,
            target_prioritization="survival"
        )
        super().__init__(PersonalityType.DEFENSIVE, traits)
    
    async def evaluate_situation(self, battlefield: BattlefieldState, unit_id: str) -> Dict[str, Any]:
        """Evaluate situation with focus on threats and safety"""
        current_unit = next((u for u in battlefield.units if u.id == unit_id), None)
        if not current_unit:
            return {"error": "Unit not found"}
        
        enemies = [u for u in battlefield.units if u.team != current_unit.team and u.alive]
        allies = [u for u in battlefield.units if u.team == current_unit.team and u.alive and u.id != unit_id]
        
        # Assess immediate threats
        immediate_threats = []
        for enemy in enemies:
            distance = current_unit.position.distance_to(enemy.position)
            enemy_attack_range = enemy.attributes.get("attack_range", 1)
            
            if distance <= enemy_attack_range + 1:  # Within striking distance next turn
                threat_level = (enemy.attributes.get("physical_attack", 10) + 
                              enemy.attributes.get("magical_attack", 10)) / max(current_unit.hp, 1)
                immediate_threats.append({
                    "unit_id": enemy.id,
                    "distance": distance,
                    "threat_level": threat_level
                })
        
        # Find safe positions (near allies, away from enemies)
        safe_positions = []
        for ally in allies:
            ally_distance = current_unit.position.distance_to(ally.position)
            if ally_distance <= 3:  # Close to ally
                avg_enemy_distance = sum(
                    ally.position.distance_to(enemy.position) for enemy in enemies
                ) / max(len(enemies), 1)
                
                safe_positions.append({
                    "ally_id": ally.id,
                    "ally_distance": ally_distance,
                    "avg_enemy_distance": avg_enemy_distance,
                    "safety_score": avg_enemy_distance / max(ally_distance, 1)
                })
        
        return {
            "evaluation_type": "defensive",
            "immediate_threats": sorted(immediate_threats, key=lambda x: x["threat_level"], reverse=True),
            "safe_positions": sorted(safe_positions, key=lambda x: x["safety_score"], reverse=True),
            "current_hp_ratio": current_unit.hp / current_unit.max_hp,
            "recommended_stance": "defensive",
            "priority_action_types": ["move_to_safety", "defensive_position"]
        }
    
    async def choose_action(self, request: AIDecisionRequest, available_actions: List[GameAction], 
                          situation_eval: Dict[str, Any]) -> Tuple[GameAction, float, str]:
        """Choose action with defensive bias"""
        hp_ratio = situation_eval.get("current_hp_ratio", 1.0)
        threats = situation_eval.get("immediate_threats", [])
        
        # If low health or many threats, prioritize survival
        if hp_ratio < 0.4 or len(threats) > 1:
            move_actions = [a for a in available_actions if a.action_type == "move"]
            if move_actions:
                # Move away from threats (simplified logic)
                chosen_action = random.choice(move_actions)
                confidence = 0.8
                reasoning = "Defensive retreat due to low health or multiple threats"
            else:
                chosen_action = next((a for a in available_actions if a.action_type == "end_turn"), 
                                   random.choice(available_actions))
                confidence = 0.6
                reasoning = "Cannot retreat, ending turn defensively"
        
        # Only attack if it's safe and advantageous
        elif hp_ratio > 0.7 and len(threats) == 0:
            attack_actions = [a for a in available_actions if a.action_type == "attack"]
            if attack_actions and random.random() < 0.4:  # 40% chance to attack when safe
                chosen_action = random.choice(attack_actions)
                confidence = 0.7
                reasoning = "Safe opportunity for defensive counter-attack"
            else:
                move_actions = [a for a in available_actions if a.action_type == "move"]
                chosen_action = random.choice(move_actions) if move_actions else random.choice(available_actions)
                confidence = 0.6
                reasoning = "Maintaining defensive position"
        
        else:
            # Cautious action
            chosen_action = random.choice(available_actions)
            confidence = 0.5
            reasoning = "Cautious action in uncertain situation"
        
        return chosen_action, confidence, reasoning


class TacticalPersonality(AIPersonality):
    """Tactical AI that focuses on optimal positioning and combo attacks"""
    
    def __init__(self):
        traits = PersonalityTraits(
            aggression=0.6,
            risk_tolerance=0.5,
            patience=0.7,
            teamwork=0.8,
            adaptability=0.8,
            planning_horizon=0.9,
            resource_management=0.7,
            target_prioritization="balanced"
        )
        super().__init__(PersonalityType.TACTICAL, traits)
    
    async def evaluate_situation(self, battlefield: BattlefieldState, unit_id: str) -> Dict[str, Any]:
        """Evaluate situation with focus on tactical advantages"""
        current_unit = next((u for u in battlefield.units if u.id == unit_id), None)
        if not current_unit:
            return {"error": "Unit not found"}
        
        enemies = [u for u in battlefield.units if u.team != current_unit.team and u.alive]
        allies = [u for u in battlefield.units if u.team == current_unit.team and u.alive and u.id != unit_id]
        
        # Analyze tactical opportunities
        flanking_opportunities = []
        for enemy in enemies:
            # Check if we can flank this enemy
            enemy_pos = enemy.position
            potential_flanking_positions = [
                (enemy_pos.x + 1, enemy_pos.y), (enemy_pos.x - 1, enemy_pos.y),
                (enemy_pos.x, enemy_pos.y + 1), (enemy_pos.x, enemy_pos.y - 1)
            ]
            
            for pos_x, pos_y in potential_flanking_positions:
                if 0 <= pos_x < battlefield.grid_size[0] and 0 <= pos_y < battlefield.grid_size[1]:
                    distance = abs(current_unit.position.x - pos_x) + abs(current_unit.position.y - pos_y)
                    if distance <= current_unit.attributes.get("move_points", 3):
                        flanking_opportunities.append({
                            "enemy_id": enemy.id,
                            "flanking_position": (pos_x, pos_y),
                            "distance": distance,
                            "advantage_score": self._calculate_flanking_advantage(enemy, allies)
                        })
        
        # Analyze combo opportunities with allies
        combo_opportunities = []
        for ally in allies:
            for enemy in enemies:
                ally_distance = ally.position.distance_to(enemy.position)
                current_distance = current_unit.position.distance_to(enemy.position)
                
                if ally_distance <= 2 and current_distance <= 3:  # Both can reach enemy
                    combo_opportunities.append({
                        "ally_id": ally.id,
                        "enemy_id": enemy.id,
                        "combo_potential": self._calculate_combo_potential(current_unit, ally, enemy)
                    })
        
        return {
            "evaluation_type": "tactical",
            "flanking_opportunities": sorted(flanking_opportunities, 
                                           key=lambda x: x["advantage_score"], reverse=True),
            "combo_opportunities": sorted(combo_opportunities,
                                        key=lambda x: x["combo_potential"], reverse=True),
            "battlefield_control": self._analyze_battlefield_control(battlefield, current_unit),
            "recommended_stance": "tactical",
            "priority_action_types": ["tactical_move", "coordinated_attack", "positioning"]
        }
    
    def _calculate_flanking_advantage(self, enemy: Any, allies: List[Any]) -> float:
        """Calculate the tactical advantage of flanking an enemy"""
        # Simplified calculation
        enemy_hp_ratio = enemy.hp / enemy.max_hp
        nearby_allies = len([a for a in allies if a.position.distance_to(enemy.position) <= 3])
        return (1.0 - enemy_hp_ratio) + (nearby_allies * 0.2)
    
    def _calculate_combo_potential(self, current_unit: Any, ally: Any, enemy: Any) -> float:
        """Calculate potential for combo attack"""
        # Simplified calculation based on combined attack power vs enemy defense
        combined_attack = (current_unit.attributes.get("physical_attack", 10) + 
                         ally.attributes.get("physical_attack", 10))
        enemy_defense = enemy.attributes.get("physical_defense", 5)
        return combined_attack / max(enemy_defense, 1)
    
    def _analyze_battlefield_control(self, battlefield: BattlefieldState, current_unit: Any) -> Dict[str, Any]:
        """Analyze overall battlefield control"""
        center_x, center_y = battlefield.grid_size[0] // 2, battlefield.grid_size[1] // 2
        
        allies = [u for u in battlefield.units if u.team == current_unit.team and u.alive]
        enemies = [u for u in battlefield.units if u.team != current_unit.team and u.alive]
        
        ally_center_control = sum(1.0 / max(abs(u.position.x - center_x) + abs(u.position.y - center_y), 1) 
                                for u in allies)
        enemy_center_control = sum(1.0 / max(abs(u.position.x - center_x) + abs(u.position.y - center_y), 1) 
                                 for u in enemies)
        
        return {
            "center_control_ratio": ally_center_control / max(enemy_center_control, 0.1),
            "ally_positioning": "clustered" if self._calculate_unit_spread(allies) < 3 else "spread",
            "enemy_positioning": "clustered" if self._calculate_unit_spread(enemies) < 3 else "spread"
        }
    
    def _calculate_unit_spread(self, units: List[Any]) -> float:
        """Calculate average distance between units"""
        if len(units) < 2:
            return 0.0
        
        total_distance = 0
        pairs = 0
        
        for i, unit1 in enumerate(units):
            for unit2 in units[i+1:]:
                total_distance += unit1.position.distance_to(unit2.position)
                pairs += 1
        
        return total_distance / pairs if pairs > 0 else 0.0
    
    async def choose_action(self, request: AIDecisionRequest, available_actions: List[GameAction], 
                          situation_eval: Dict[str, Any]) -> Tuple[GameAction, float, str]:
        """Choose action with tactical optimization"""
        flanking_ops = situation_eval.get("flanking_opportunities", [])
        combo_ops = situation_eval.get("combo_opportunities", [])
        
        # Prioritize tactical opportunities
        if flanking_ops and flanking_ops[0]["advantage_score"] > 0.7:
            # Execute flanking maneuver
            move_actions = [a for a in available_actions if a.action_type == "move"]
            if move_actions:
                chosen_action = random.choice(move_actions)  # Should select optimal flanking position
                confidence = 0.85
                reasoning = f"Executing flanking maneuver against {flanking_ops[0]['enemy_id']}"
            else:
                chosen_action = random.choice(available_actions)
                confidence = 0.5
                reasoning = "Cannot execute flanking, choosing alternative"
        
        elif combo_ops and combo_ops[0]["combo_potential"] > 1.5:
            # Set up or execute combo attack
            attack_actions = [a for a in available_actions if a.action_type == "attack"]
            if attack_actions:
                chosen_action = random.choice(attack_actions)
                confidence = 0.8
                reasoning = f"Coordinated attack with {combo_ops[0]['ally_id']}"
            else:
                move_actions = [a for a in available_actions if a.action_type == "move"]
                chosen_action = random.choice(move_actions) if move_actions else random.choice(available_actions)
                confidence = 0.7
                reasoning = "Positioning for combo attack"
        
        else:
            # Standard tactical decision
            attack_actions = [a for a in available_actions if a.action_type == "attack"]
            move_actions = [a for a in available_actions if a.action_type == "move"]
            
            if attack_actions and random.random() < 0.6:
                chosen_action = random.choice(attack_actions)
                confidence = 0.7
                reasoning = "Tactical attack opportunity"
            elif move_actions:
                chosen_action = random.choice(move_actions)
                confidence = 0.6
                reasoning = "Tactical positioning"
            else:
                chosen_action = random.choice(available_actions)
                confidence = 0.5
                reasoning = "No clear tactical advantage, maintaining position"
        
        return chosen_action, confidence, reasoning


class AdaptivePersonality(AIPersonality):
    """Adaptive AI that learns and changes tactics based on opponent behavior"""
    
    def __init__(self):
        traits = PersonalityTraits(
            aggression=0.5,
            risk_tolerance=0.5,
            patience=0.6,
            teamwork=0.6,
            adaptability=1.0,  # Maximum adaptability
            planning_horizon=0.7,
            resource_management=0.6,
            target_prioritization="balanced"
        )
        super().__init__(PersonalityType.ADAPTIVE, traits)
        self.opponent_analysis = {}
        self.strategy_effectiveness = {}
        self.current_strategy = "balanced"
    
    async def evaluate_situation(self, battlefield: BattlefieldState, unit_id: str) -> Dict[str, Any]:
        """Evaluate situation with adaptive analysis"""
        current_unit = next((u for u in battlefield.units if u.id == unit_id), None)
        if not current_unit:
            return {"error": "Unit not found"}
        
        # Analyze opponent patterns
        enemies = [u for u in battlefield.units if u.team != current_unit.team and u.alive]
        opponent_pattern = await self._analyze_opponent_patterns(enemies, battlefield)
        
        # Determine counter-strategy
        recommended_strategy = await self._determine_counter_strategy(opponent_pattern)
        
        # Update current strategy if needed
        if recommended_strategy != self.current_strategy:
            await self._adapt_strategy(recommended_strategy)
        
        return {
            "evaluation_type": "adaptive",
            "opponent_pattern": opponent_pattern,
            "current_strategy": self.current_strategy,
            "adaptation_confidence": self._calculate_adaptation_confidence(),
            "recommended_stance": self.current_strategy,
            "priority_action_types": self._get_strategy_actions(self.current_strategy)
        }
    
    async def _analyze_opponent_patterns(self, enemies: List[Any], battlefield: BattlefieldState) -> Dict[str, Any]:
        """Analyze opponent behavioral patterns"""
        if not enemies:
            return {"pattern": "none"}
        
        # Analyze positioning patterns
        enemy_spread = self._calculate_unit_spread(enemies)
        center_x, center_y = battlefield.grid_size[0] // 2, battlefield.grid_size[1] // 2
        
        center_preference = sum(
            1.0 / max(abs(e.position.x - center_x) + abs(e.position.y - center_y), 1)
            for e in enemies
        ) / len(enemies)
        
        # Determine dominant pattern
        if enemy_spread < 2:
            positioning = "clustered"
        elif enemy_spread > 5:
            positioning = "spread"
        else:
            positioning = "balanced"
        
        if center_preference > 0.5:
            preference = "center_control"
        else:
            preference = "perimeter"
        
        return {
            "positioning": positioning,
            "preference": preference,
            "aggression_level": self._estimate_opponent_aggression(enemies),
            "pattern": f"{positioning}_{preference}"
        }
    
    def _estimate_opponent_aggression(self, enemies: List[Any]) -> str:
        """Estimate opponent aggression level based on positioning and health"""
        if not enemies:
            return "unknown"
        
        # Simple heuristic: enemies with low health staying in combat are aggressive
        low_health_active = sum(1 for e in enemies if e.hp / e.max_hp < 0.4)
        high_health_ratio = sum(e.hp / e.max_hp for e in enemies) / len(enemies)
        
        if low_health_active > len(enemies) * 0.3:
            return "high"
        elif high_health_ratio > 0.8:
            return "conservative"
        else:
            return "moderate"
    
    async def _determine_counter_strategy(self, opponent_pattern: Dict[str, Any]) -> str:
        """Determine optimal counter-strategy"""
        pattern = opponent_pattern.get("pattern", "balanced")
        aggression = opponent_pattern.get("aggression_level", "moderate")
        
        # Counter-strategy matrix
        if pattern == "clustered_center":
            return "flanking" if aggression == "high" else "harassment"
        elif pattern == "spread_perimeter":
            return "aggressive" if aggression == "conservative" else "defensive"
        elif pattern == "clustered_perimeter":
            return "center_control"
        else:
            return "balanced"
    
    async def _adapt_strategy(self, new_strategy: str):
        """Adapt traits based on new strategy"""
        logger.info("Adaptive AI changing strategy",
                   old_strategy=self.current_strategy,
                   new_strategy=new_strategy)
        
        self.current_strategy = new_strategy
        
        # Adjust traits based on strategy
        if new_strategy == "aggressive":
            self.traits.aggression = min(1.0, self.traits.aggression + 0.2)
            self.traits.risk_tolerance = min(1.0, self.traits.risk_tolerance + 0.1)
        elif new_strategy == "defensive":
            self.traits.aggression = max(0.0, self.traits.aggression - 0.2)
            self.traits.patience = min(1.0, self.traits.patience + 0.1)
        elif new_strategy == "flanking":
            self.traits.teamwork = min(1.0, self.traits.teamwork + 0.1)
            self.traits.planning_horizon = min(1.0, self.traits.planning_horizon + 0.1)
        # ... add more strategy adaptations
    
    def _calculate_adaptation_confidence(self) -> float:
        """Calculate confidence in current adaptation"""
        if self.decision_count < 5:
            return 0.5  # Low confidence with little data
        
        recent_success_rate = self.success_rate
        strategy_experience = self.strategy_effectiveness.get(self.current_strategy, 0.5)
        
        return (recent_success_rate + strategy_experience) / 2
    
    def _get_strategy_actions(self, strategy: str) -> List[str]:
        """Get priority action types for strategy"""
        strategy_actions = {
            "aggressive": ["attack", "advance"],
            "defensive": ["move_to_safety", "defensive_position"],
            "flanking": ["tactical_move", "coordinated_attack"],
            "harassment": ["hit_and_run", "mobility"],
            "center_control": ["move_to_center", "area_control"],
            "balanced": ["situational", "adaptive"]
        }
        return strategy_actions.get(strategy, ["balanced"])
    
    async def choose_action(self, request: AIDecisionRequest, available_actions: List[GameAction], 
                          situation_eval: Dict[str, Any]) -> Tuple[GameAction, float, str]:
        """Choose action based on current adaptive strategy"""
        strategy = situation_eval.get("current_strategy", "balanced")
        confidence_base = situation_eval.get("adaptation_confidence", 0.5)
        
        # Choose action based on current strategy
        if strategy == "aggressive":
            attack_actions = [a for a in available_actions if a.action_type == "attack"]
            if attack_actions:
                chosen_action = random.choice(attack_actions)
                confidence = confidence_base + 0.2
                reasoning = f"Adaptive strategy: {strategy} - attacking opportunity"
            else:
                move_actions = [a for a in available_actions if a.action_type == "move"]
                chosen_action = random.choice(move_actions) if move_actions else random.choice(available_actions)
                confidence = confidence_base
                reasoning = f"Adaptive strategy: {strategy} - advancing position"
        
        elif strategy == "defensive":
            move_actions = [a for a in available_actions if a.action_type == "move"]
            if move_actions:
                chosen_action = random.choice(move_actions)
                confidence = confidence_base + 0.1
                reasoning = f"Adaptive strategy: {strategy} - defensive positioning"
            else:
                chosen_action = next((a for a in available_actions if a.action_type == "end_turn"), 
                                   random.choice(available_actions))
                confidence = confidence_base
                reasoning = f"Adaptive strategy: {strategy} - holding position"
        
        else:  # Balanced or other strategies
            chosen_action = random.choice(available_actions)
            confidence = confidence_base
            reasoning = f"Adaptive strategy: {strategy} - balanced approach"
        
        return chosen_action, confidence, reasoning


# Personality Factory
class PersonalityFactory:
    """Factory for creating AI personalities"""
    
    @staticmethod
    def create_personality(personality_type: PersonalityType) -> AIPersonality:
        """Create a personality instance of the specified type"""
        personalities = {
            PersonalityType.AGGRESSIVE: AggressivePersonality,
            PersonalityType.DEFENSIVE: DefensivePersonality,
            PersonalityType.TACTICAL: TacticalPersonality,
            PersonalityType.ADAPTIVE: AdaptivePersonality,
        }
        
        personality_class = personalities.get(personality_type)
        if not personality_class:
            # Default to tactical for unsupported types
            logger.warning("Unsupported personality type, defaulting to tactical",
                         requested_type=personality_type)
            personality_class = TacticalPersonality
        
        return personality_class()
    
    @staticmethod
    def create_random_personality() -> AIPersonality:
        """Create a random personality"""
        personality_type = random.choice(list(PersonalityType))
        return PersonalityFactory.create_personality(personality_type)
    
    @staticmethod
    def create_custom_personality(traits: PersonalityTraits) -> AIPersonality:
        """Create a custom personality with specific traits"""
        # Determine closest personality type based on traits
        if traits.aggression > 0.7:
            base_type = PersonalityType.AGGRESSIVE
        elif traits.aggression < 0.3:
            base_type = PersonalityType.DEFENSIVE
        elif traits.adaptability > 0.8:
            base_type = PersonalityType.ADAPTIVE
        else:
            base_type = PersonalityType.TACTICAL
        
        personality = PersonalityFactory.create_personality(base_type)
        personality.traits = traits
        return personality