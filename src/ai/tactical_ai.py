"""
Advanced Tactical AI

Implements sophisticated tactical analysis, pattern recognition, and decision-making
using AI personalities and learning systems.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

import structlog
import numpy as np

from .models import (
    AIDecisionRequest, AIDecisionResponse, GameAction, MoveAction, AttackAction,
    TacticalAnalysisRequest, TacticalAnalysisResponse, UnitEvaluationRequest,
    UnitEvaluationResponse, BattlefieldState
)
from .personalities import AIPersonality, PersonalityFactory, PersonalityType
from .learning_system import LearningSystem
from .ollama_client import OllamaClient

logger = structlog.get_logger()


class TacticalPattern:
    """Advanced tactical pattern definitions"""
    
    # Formation patterns
    PHALANX = "phalanx"  # Units in tight formation
    SKIRMISH = "skirmish"  # Spread out harassment
    PINCER = "pincer"  # Two-pronged attack
    FLANKING = "flanking"  # Attack from side/rear
    DEFENSIVE_LINE = "defensive_line"  # Defensive formation
    
    # Movement patterns
    ADVANCE = "advance"  # Moving forward
    RETREAT = "retreat"  # Pulling back
    REPOSITION = "reposition"  # Tactical movement
    ENCIRCLE = "encircle"  # Surrounding enemy
    
    # Attack patterns
    FOCUS_FIRE = "focus_fire"  # Multiple units attacking one target
    ALPHA_STRIKE = "alpha_strike"  # All-out attack
    HIT_AND_RUN = "hit_and_run"  # Quick attack then retreat
    SIEGE = "siege"  # Sustained pressure


class TacticalSituation:
    """Represents a tactical situation analysis"""
    
    def __init__(self, battlefield_state: BattlefieldState, focus_unit_id: str):
        self.battlefield_state = battlefield_state
        self.focus_unit_id = focus_unit_id
        self.analysis_time = datetime.now()
        
        # Analyze battlefield
        self.units = battlefield_state.units
        self.focus_unit = next((u for u in self.units if u.id == focus_unit_id), None)
        self.allies = [u for u in self.units if u.team == self.focus_unit.team and u.alive and u.id != focus_unit_id] if self.focus_unit else []
        self.enemies = [u for u in self.units if u.team != self.focus_unit.team and u.alive] if self.focus_unit else []
        
        # Calculate tactical metrics
        self.threat_map = self._calculate_threat_map()
        self.control_zones = self._calculate_control_zones()
        self.tactical_advantages = self._identify_tactical_advantages()
        self.vulnerabilities = self._identify_vulnerabilities()
        self.formations = self._detect_formations()
        self.momentum = self._calculate_momentum()
    
    def _calculate_threat_map(self) -> Dict[Tuple[int, int], float]:
        """Calculate threat level for each battlefield position"""
        threat_map = {}
        grid_size = self.battlefield_state.grid_size
        
        for x in range(grid_size[0]):
            for y in range(grid_size[1]):
                threat_level = 0.0
                
                for enemy in self.enemies:
                    distance = abs(x - enemy.position.x) + abs(y - enemy.position.y)
                    enemy_threat = (enemy.attributes.get("physical_attack", 10) + 
                                  enemy.attributes.get("magical_attack", 10))
                    
                    # Threat decreases with distance
                    if distance <= enemy.attributes.get("attack_range", 1):
                        threat_level += enemy_threat
                    elif distance <= enemy.attributes.get("move_points", 3) + enemy.attributes.get("attack_range", 1):
                        threat_level += enemy_threat * 0.7  # Potential threat next turn
                    elif distance <= 5:
                        threat_level += enemy_threat * 0.3  # Distant threat
                
                threat_map[(x, y)] = threat_level
        
        return threat_map
    
    def _calculate_control_zones(self) -> Dict[str, List[Tuple[int, int]]]:
        """Calculate zones of control for each team"""
        control_zones = {"ally": [], "enemy": [], "contested": [], "neutral": []}
        grid_size = self.battlefield_state.grid_size
        
        for x in range(grid_size[0]):
            for y in range(grid_size[1]):
                ally_influence = 0.0
                enemy_influence = 0.0
                
                # Calculate ally influence
                for ally in self.allies + ([self.focus_unit] if self.focus_unit else []):
                    distance = abs(x - ally.position.x) + abs(y - ally.position.y)
                    if distance <= 3:  # Influence radius
                        ally_influence += (4 - distance) / 4.0
                
                # Calculate enemy influence
                for enemy in self.enemies:
                    distance = abs(x - enemy.position.x) + abs(y - enemy.position.y)
                    if distance <= 3:
                        enemy_influence += (4 - distance) / 4.0
                
                # Classify zone
                if ally_influence > enemy_influence * 1.5:
                    control_zones["ally"].append((x, y))
                elif enemy_influence > ally_influence * 1.5:
                    control_zones["enemy"].append((x, y))
                elif ally_influence > 0.1 or enemy_influence > 0.1:
                    control_zones["contested"].append((x, y))
                else:
                    control_zones["neutral"].append((x, y))
        
        return control_zones
    
    def _identify_tactical_advantages(self) -> List[Dict[str, Any]]:
        """Identify current tactical advantages"""
        advantages = []
        
        if not self.focus_unit:
            return advantages
        
        # Numerical advantage
        if len(self.allies) > len(self.enemies):
            advantages.append({
                "type": "numerical",
                "description": f"Outnumber enemies {len(self.allies)+1} to {len(self.enemies)}",
                "strength": (len(self.allies) + 1) / max(len(self.enemies), 1)
            })
        
        # Positioning advantages
        center_x, center_y = self.battlefield_state.grid_size[0] // 2, self.battlefield_state.grid_size[1] // 2
        focus_distance_to_center = abs(self.focus_unit.position.x - center_x) + abs(self.focus_unit.position.y - center_y)
        
        avg_enemy_distance_to_center = np.mean([
            abs(enemy.position.x - center_x) + abs(enemy.position.y - center_y)
            for enemy in self.enemies
        ]) if self.enemies else 10
        
        if focus_distance_to_center < avg_enemy_distance_to_center:
            advantages.append({
                "type": "positioning",
                "description": "Better center control",
                "strength": avg_enemy_distance_to_center / max(focus_distance_to_center, 1)
            })
        
        # Health advantages
        ally_avg_hp = np.mean([u.hp / u.max_hp for u in self.allies + [self.focus_unit]])
        enemy_avg_hp = np.mean([u.hp / u.max_hp for u in self.enemies]) if self.enemies else 0
        
        if ally_avg_hp > enemy_avg_hp * 1.2:
            advantages.append({
                "type": "health",
                "description": "Superior health condition",
                "strength": ally_avg_hp / max(enemy_avg_hp, 0.1)
            })
        
        # Flanking opportunities
        flanking_ops = self._find_flanking_opportunities()
        if flanking_ops:
            advantages.append({
                "type": "flanking",
                "description": f"{len(flanking_ops)} flanking opportunities available",
                "strength": len(flanking_ops) / max(len(self.enemies), 1),
                "targets": [op["target_id"] for op in flanking_ops]
            })
        
        return advantages
    
    def _identify_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Identify current vulnerabilities"""
        vulnerabilities = []
        
        if not self.focus_unit:
            return vulnerabilities
        
        # Low health vulnerability
        hp_ratio = self.focus_unit.hp / self.focus_unit.max_hp
        if hp_ratio < 0.3:
            vulnerabilities.append({
                "type": "low_health",
                "description": f"Unit at {hp_ratio:.1%} health",
                "severity": 1.0 - hp_ratio,
                "unit_id": self.focus_unit.id
            })
        
        # Isolation vulnerability
        nearest_ally_distance = float('inf')
        for ally in self.allies:
            distance = abs(self.focus_unit.position.x - ally.position.x) + abs(self.focus_unit.position.y - ally.position.y)
            nearest_ally_distance = min(nearest_ally_distance, distance)
        
        if nearest_ally_distance > 4 and self.allies:
            vulnerabilities.append({
                "type": "isolation",
                "description": f"Isolated from nearest ally by {nearest_ally_distance} spaces",
                "severity": min(1.0, nearest_ally_distance / 6.0),
                "unit_id": self.focus_unit.id
            })
        
        # Surrounded vulnerability
        adjacent_enemies = 0
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            check_x = self.focus_unit.position.x + dx
            check_y = self.focus_unit.position.y + dy
            
            for enemy in self.enemies:
                if enemy.position.x == check_x and enemy.position.y == check_y:
                    adjacent_enemies += 1
        
        if adjacent_enemies > 1:
            vulnerabilities.append({
                "type": "surrounded",
                "description": f"Surrounded by {adjacent_enemies} enemies",
                "severity": min(1.0, adjacent_enemies / 4.0),
                "unit_id": self.focus_unit.id
            })
        
        # Resource depletion
        mp_ratio = self.focus_unit.mp / max(self.focus_unit.max_mp, 1)
        if mp_ratio < 0.2 and self.focus_unit.max_mp > 0:
            vulnerabilities.append({
                "type": "low_resources",
                "description": f"Low MP: {mp_ratio:.1%}",
                "severity": 1.0 - mp_ratio,
                "unit_id": self.focus_unit.id
            })
        
        return vulnerabilities
    
    def _detect_formations(self) -> Dict[str, List[str]]:
        """Detect unit formations"""
        formations = {"ally": [], "enemy": []}
        
        # Detect ally formations
        ally_formation = self._analyze_formation(self.allies + ([self.focus_unit] if self.focus_unit else []))
        formations["ally"] = ally_formation
        
        # Detect enemy formations
        enemy_formation = self._analyze_formation(self.enemies)
        formations["enemy"] = enemy_formation
        
        return formations
    
    def _analyze_formation(self, units: List[Any]) -> List[str]:
        """Analyze formation patterns for a group of units"""
        if len(units) < 2:
            return ["scattered"]
        
        formations = []
        
        # Calculate unit spread
        positions = [(u.position.x, u.position.y) for u in units]
        
        # Check if units are clustered (phalanx-like)
        max_distance = 0
        for i, pos1 in enumerate(positions):
            for pos2 in positions[i+1:]:
                distance = abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
                max_distance = max(max_distance, distance)
        
        if max_distance <= 3:
            formations.append(TacticalPattern.PHALANX)
        elif max_distance > 6:
            formations.append(TacticalPattern.SKIRMISH)
        
        # Check for line formation
        if self._is_line_formation(positions):
            formations.append(TacticalPattern.DEFENSIVE_LINE)
        
        # Check for surrounding formation
        if self._is_surrounding_formation(positions, self.enemies if units == self.allies else self.allies):
            formations.append(TacticalPattern.ENCIRCLE)
        
        return formations if formations else ["standard"]
    
    def _is_line_formation(self, positions: List[Tuple[int, int]]) -> bool:
        """Check if positions form a line"""
        if len(positions) < 3:
            return False
        
        # Check if positions are roughly collinear
        for i in range(len(positions) - 2):
            p1, p2, p3 = positions[i], positions[i+1], positions[i+2]
            
            # Calculate cross product to check collinearity
            cross_product = (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0])
            if abs(cross_product) > 2:  # Allow some tolerance
                return False
        
        return True
    
    def _is_surrounding_formation(self, ally_positions: List[Tuple[int, int]], 
                                 enemy_units: List[Any]) -> bool:
        """Check if allies are surrounding enemies"""
        if len(ally_positions) < 3 or not enemy_units:
            return False
        
        # Find center of enemy positions
        enemy_positions = [(u.position.x, u.position.y) for u in enemy_units]
        enemy_center_x = np.mean([pos[0] for pos in enemy_positions])
        enemy_center_y = np.mean([pos[1] for pos in enemy_positions])
        
        # Check if allies are distributed around enemy center
        angles = []
        for pos in ally_positions:
            angle = np.arctan2(pos[1] - enemy_center_y, pos[0] - enemy_center_x)
            angles.append(angle)
        
        angles.sort()
        
        # Check angle distribution
        angle_gaps = []
        for i in range(len(angles)):
            gap = angles[(i + 1) % len(angles)] - angles[i]
            if gap < 0:
                gap += 2 * np.pi
            angle_gaps.append(gap)
        
        # If no gap is too large, it's a surrounding formation
        max_gap = max(angle_gaps)
        return max_gap < np.pi  # No gap larger than 180 degrees
    
    def _find_flanking_opportunities(self) -> List[Dict[str, Any]]:
        """Find flanking opportunities against enemies"""
        opportunities = []
        
        if not self.focus_unit:
            return opportunities
        
        for enemy in self.enemies:
            # Check if we can move to flank this enemy
            enemy_pos = enemy.position
            
            # Potential flanking positions (behind or to the side)
            flanking_positions = [
                (enemy_pos.x + 1, enemy_pos.y),
                (enemy_pos.x - 1, enemy_pos.y),
                (enemy_pos.x, enemy_pos.y + 1),
                (enemy_pos.x, enemy_pos.y - 1),
                (enemy_pos.x + 1, enemy_pos.y + 1),
                (enemy_pos.x + 1, enemy_pos.y - 1),
                (enemy_pos.x - 1, enemy_pos.y + 1),
                (enemy_pos.x - 1, enemy_pos.y - 1)
            ]
            
            for flank_x, flank_y in flanking_positions:
                # Check if position is valid and reachable
                if (0 <= flank_x < self.battlefield_state.grid_size[0] and 
                    0 <= flank_y < self.battlefield_state.grid_size[1]):
                    
                    distance = abs(self.focus_unit.position.x - flank_x) + abs(self.focus_unit.position.y - flank_y)
                    move_points = self.focus_unit.attributes.get("move_points", 3)
                    
                    if distance <= move_points:
                        # Calculate flanking advantage
                        advantage_score = self._calculate_flanking_advantage(enemy, (flank_x, flank_y))
                        
                        opportunities.append({
                            "target_id": enemy.id,
                            "flanking_position": (flank_x, flank_y),
                            "distance": distance,
                            "advantage_score": advantage_score,
                            "recommended": advantage_score > 0.6
                        })
        
        return sorted(opportunities, key=lambda x: x["advantage_score"], reverse=True)
    
    def _calculate_flanking_advantage(self, enemy: Any, flanking_position: Tuple[int, int]) -> float:
        """Calculate the advantage of a flanking position"""
        advantage = 0.0
        
        # Bonus for attacking from behind/side
        advantage += 0.4
        
        # Bonus based on enemy health (easier to finish off wounded enemies)
        enemy_hp_ratio = enemy.hp / enemy.max_hp
        advantage += (1.0 - enemy_hp_ratio) * 0.3
        
        # Penalty if position is too exposed to other enemies
        threat_level = self.threat_map.get(flanking_position, 0)
        max_acceptable_threat = 20  # Adjust based on game balance
        if threat_level > max_acceptable_threat:
            advantage -= 0.5
        
        # Bonus if allies can support
        support_count = 0
        for ally in self.allies:
            ally_distance = abs(ally.position.x - flanking_position[0]) + abs(ally.position.y - flanking_position[1])
            if ally_distance <= 2:
                support_count += 1
        
        advantage += support_count * 0.1
        
        return max(0.0, min(1.0, advantage))
    
    def _calculate_momentum(self) -> Dict[str, float]:
        """Calculate battlefield momentum for each team"""
        # This would typically track changes over multiple turns
        # For now, we'll calculate based on current state
        
        ally_strength = sum(u.hp / u.max_hp for u in self.allies + ([self.focus_unit] if self.focus_unit else []))
        enemy_strength = sum(u.hp / u.max_hp for u in self.enemies) if self.enemies else 0.1
        
        ally_momentum = ally_strength / (ally_strength + enemy_strength)
        enemy_momentum = 1.0 - ally_momentum
        
        return {
            "ally": ally_momentum,
            "enemy": enemy_momentum,
            "trend": "gaining" if ally_momentum > 0.6 else "losing" if ally_momentum < 0.4 else "stable"
        }


class TacticalAI:
    """Advanced tactical AI with pattern recognition and learning"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
        self.personalities: Dict[str, AIPersonality] = {}
        self.learning_systems: Dict[str, LearningSystem] = {}
        self.decision_cache: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics = {
            "decisions_made": 0,
            "success_rate": 0.0,
            "average_confidence": 0.0,
            "pattern_usage": 0
        }
    
    async def make_decision(self, request: AIDecisionRequest, test_game_state: Optional[Dict[str, Any]] = None) -> AIDecisionResponse:
        """Make a tactical decision for a unit"""
        start_time = time.time()
        
        try:
            # Get or create personality for this unit/session
            personality = await self._get_personality(request.unit_id, request.difficulty_level)
            
            # Get game state
            if test_game_state:
                game_state = test_game_state
            else:
                # In a real implementation, this would fetch from game engine
                game_state = {"units": [], "grid_size": [10, 10], "turn_number": 1}
            
            # Create tactical situation analysis
            battlefield_state = BattlefieldState(
                session_id=request.session_id,
                turn_number=game_state.get("turn_number", 1),
                current_unit_id=request.unit_id,
                units=[],  # Would be populated from game_state
                grid_size=tuple(game_state.get("grid_size", [10, 10]))
            )
            
            tactical_situation = TacticalSituation(battlefield_state, request.unit_id)
            
            # Get available actions (simplified for this implementation)
            available_actions = ["move", "attack", "end_turn"]
            
            # Use personality to evaluate and choose action
            situation_eval = await personality.evaluate_situation(battlefield_state, request.unit_id)
            action, confidence, reasoning = await personality.choose_action(request, [], situation_eval)
            
            # Get learning system recommendation if available
            learning_system = self._get_learning_system(personality)
            learning_rec = await learning_system.get_learning_recommendation(
                game_state, request.unit_id, available_actions
            )
            
            # Combine personality and learning recommendations
            if learning_rec and learning_rec["confidence"] > confidence:
                final_action = learning_rec["recommended_action"]
                final_confidence = learning_rec["confidence"]
                final_reasoning = f"Learning-enhanced: {learning_rec['reasoning']}"
            else:
                final_action = action
                final_confidence = confidence
                final_reasoning = reasoning
            
            # Use LLM for enhanced reasoning if available
            if self.ollama_client:
                try:
                    enhanced_reasoning = await self._get_llm_reasoning(
                        tactical_situation, final_action, personality
                    )
                    final_reasoning = enhanced_reasoning
                except Exception as e:
                    logger.warning("LLM reasoning failed", error=str(e))
            
            # Create response
            response = AIDecisionResponse(
                unit_id=request.unit_id,
                recommended_action=final_action if isinstance(final_action, GameAction) else MoveAction(
                    unit_id=request.unit_id,
                    session_id=request.session_id,
                    target_x=0,
                    target_y=0
                ),
                alternative_actions=[],
                reasoning=final_reasoning,
                confidence=final_confidence,
                analysis_used=["personality", "tactical_situation"],
                execution_time=time.time() - start_time
            )
            
            # Update metrics
            self.performance_metrics["decisions_made"] += 1
            self.performance_metrics["average_confidence"] = (
                (self.performance_metrics["average_confidence"] * (self.performance_metrics["decisions_made"] - 1) + 
                 final_confidence) / self.performance_metrics["decisions_made"]
            )
            
            logger.info("Tactical AI decision made",
                       unit_id=request.unit_id,
                       action_type=response.recommended_action.action_type,
                       confidence=final_confidence,
                       execution_time=response.execution_time)
            
            return response
            
        except Exception as e:
            logger.error("Tactical AI decision failed", unit_id=request.unit_id, error=str(e))
            
            # Fallback response
            return AIDecisionResponse(
                unit_id=request.unit_id,
                recommended_action=MoveAction(
                    unit_id=request.unit_id,
                    session_id=request.session_id,
                    target_x=0,
                    target_y=0
                ),
                alternative_actions=[],
                reasoning="Error occurred, using fallback action",
                confidence=0.1,
                analysis_used=["fallback"],
                execution_time=time.time() - start_time
            )
    
    async def _get_personality(self, unit_id: str, difficulty_level: str) -> AIPersonality:
        """Get or create personality for a unit"""
        if unit_id not in self.personalities:
            # Create personality based on difficulty
            if difficulty_level == "easy":
                personality_type = PersonalityType.DEFENSIVE
            elif difficulty_level == "normal":
                personality_type = PersonalityType.TACTICAL
            elif difficulty_level == "hard":
                personality_type = PersonalityType.AGGRESSIVE
            else:  # expert
                personality_type = PersonalityType.ADAPTIVE
            
            self.personalities[unit_id] = PersonalityFactory.create_personality(personality_type)
        
        return self.personalities[unit_id]
    
    def _get_learning_system(self, personality: AIPersonality) -> LearningSystem:
        """Get or create learning system for personality"""
        personality_id = f"{personality.personality_type}_{id(personality)}"
        
        if personality_id not in self.learning_systems:
            self.learning_systems[personality_id] = LearningSystem(personality)
        
        return self.learning_systems[personality_id]
    
    async def _get_llm_reasoning(self, tactical_situation: TacticalSituation, 
                               chosen_action: Any, personality: AIPersonality) -> str:
        """Get enhanced reasoning from LLM"""
        try:
            situation_summary = {
                "advantages": tactical_situation.tactical_advantages,
                "vulnerabilities": tactical_situation.vulnerabilities,
                "formations": tactical_situation.formations,
                "momentum": tactical_situation.momentum
            }
            
            prompt = f"""
{personality.get_personality_prompt_modifier()}

Tactical Situation:
{json.dumps(situation_summary, indent=2)}

Chosen Action: {chosen_action}

Provide a concise tactical reasoning for this decision (2-3 sentences):
            """
            
            reasoning = await self.ollama_client.generate("llama2:7b", prompt, temperature=0.6, max_tokens=150)
            return reasoning.strip()
            
        except Exception as e:
            logger.warning("LLM reasoning generation failed", error=str(e))
            return "Tactical decision based on battlefield analysis"
    
    async def analyze_tactical_situation(self, request: TacticalAnalysisRequest) -> TacticalAnalysisResponse:
        """Perform detailed tactical analysis"""
        try:
            # This would get real battlefield state from game engine
            battlefield_state = BattlefieldState(
                session_id=request.session_id,
                turn_number=1,
                current_unit_id=request.focus_unit_id,
                units=[],
                grid_size=(10, 10)
            )
            
            tactical_situation = TacticalSituation(battlefield_state, request.focus_unit_id or "unknown")
            
            # Convert tactical situation to response format
            threat_assessment = {
                "threat_map": {f"{pos[0]},{pos[1]}": threat for pos, threat in tactical_situation.threat_map.items()},
                "immediate_threats": tactical_situation.vulnerabilities,
                "threat_level": sum(v.get("severity", 0) for v in tactical_situation.vulnerabilities if v.get("type") == "surrounded")
            }
            
            opportunity_assessment = {
                "flanking_opportunities": tactical_situation._find_flanking_opportunities(),
                "tactical_advantages": tactical_situation.tactical_advantages,
                "formations": tactical_situation.formations
            }
            
            positioning_analysis = {
                "control_zones": tactical_situation.control_zones,
                "formations": tactical_situation.formations,
                "momentum": tactical_situation.momentum
            }
            
            # Generate recommendations
            recommendations = self._generate_tactical_recommendations(tactical_situation)
            
            return TacticalAnalysisResponse(
                session_id=request.session_id,
                focus_unit_id=request.focus_unit_id,
                threat_assessment=threat_assessment,
                opportunity_assessment=opportunity_assessment,
                positioning_analysis=positioning_analysis,
                recommendations=recommendations,
                confidence=0.8
            )
            
        except Exception as e:
            logger.error("Tactical analysis failed", error=str(e))
            raise
    
    def _generate_tactical_recommendations(self, tactical_situation: TacticalSituation) -> List[str]:
        """Generate tactical recommendations based on situation"""
        recommendations = []
        
        # Based on advantages
        for advantage in tactical_situation.tactical_advantages:
            if advantage["type"] == "flanking":
                recommendations.append(f"Execute flanking maneuver against {advantage['targets'][0] if advantage['targets'] else 'enemy'}")
            elif advantage["type"] == "numerical":
                recommendations.append("Press numerical advantage with coordinated attack")
            elif advantage["type"] == "positioning":
                recommendations.append("Maintain center control advantage")
        
        # Based on vulnerabilities
        for vulnerability in tactical_situation.vulnerabilities:
            if vulnerability["type"] == "low_health":
                recommendations.append("Consider defensive positioning or healing")
            elif vulnerability["type"] == "isolation":
                recommendations.append("Move towards allied support")
            elif vulnerability["type"] == "surrounded":
                recommendations.append("Break out of encirclement immediately")
        
        # Based on formations
        ally_formations = tactical_situation.formations.get("ally", [])
        enemy_formations = tactical_situation.formations.get("enemy", [])
        
        if TacticalPattern.PHALANX in enemy_formations:
            recommendations.append("Use flanking tactics against enemy phalanx")
        if TacticalPattern.SKIRMISH in ally_formations:
            recommendations.append("Coordinate scattered units for focused assault")
        
        # Default recommendations if none generated
        if not recommendations:
            momentum = tactical_situation.momentum
            if momentum["ally"] > 0.6:
                recommendations.append("Press advantage with aggressive tactics")
            elif momentum["ally"] < 0.4:
                recommendations.append("Adopt defensive posture and regroup")
            else:
                recommendations.append("Maintain flexible positioning")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def evaluate_unit(self, request: UnitEvaluationRequest) -> UnitEvaluationResponse:
        """Evaluate a unit's tactical situation and capabilities"""
        try:
            # This would get real data from game engine
            battlefield_state = BattlefieldState(
                session_id=request.session_id,
                turn_number=1,
                current_unit_id=request.unit_id,
                units=[],
                grid_size=(10, 10)
            )
            
            tactical_situation = TacticalSituation(battlefield_state, request.unit_id)
            
            # Calculate evaluation metrics
            combat_effectiveness = self._evaluate_combat_effectiveness(tactical_situation)
            positional_advantage = self._evaluate_positional_advantage(tactical_situation)
            resource_efficiency = self._evaluate_resource_efficiency(tactical_situation)
            survival_probability = self._evaluate_survival_probability(tactical_situation)
            strategic_value = self._evaluate_strategic_value(tactical_situation)
            
            recommendations = self._generate_unit_recommendations(tactical_situation)
            
            return UnitEvaluationResponse(
                unit_id=request.unit_id,
                combat_effectiveness=combat_effectiveness,
                positional_advantage=positional_advantage,
                resource_efficiency=resource_efficiency,
                survival_probability=survival_probability,
                strategic_value=strategic_value,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error("Unit evaluation failed", error=str(e))
            raise
    
    def _evaluate_combat_effectiveness(self, tactical_situation: TacticalSituation) -> float:
        """Evaluate unit's combat effectiveness"""
        if not tactical_situation.focus_unit:
            return 0.0
        
        unit = tactical_situation.focus_unit
        
        # Base combat power
        attack_power = (unit.attributes.get("physical_attack", 10) + 
                       unit.attributes.get("magical_attack", 10))
        
        # Health factor
        hp_ratio = unit.hp / unit.max_hp
        
        # Resource availability
        mp_ratio = unit.mp / max(unit.max_mp, 1)
        
        # Position factor (safer positions = higher effectiveness)
        position_safety = 1.0 - (tactical_situation.threat_map.get(
            (unit.position.x, unit.position.y), 0) / 100.0)
        
        effectiveness = (attack_power / 30.0) * hp_ratio * (0.7 + 0.3 * mp_ratio) * position_safety
        
        return max(0.0, min(1.0, effectiveness))
    
    def _evaluate_positional_advantage(self, tactical_situation: TacticalSituation) -> float:
        """Evaluate unit's positional advantage"""
        if not tactical_situation.focus_unit:
            return 0.0
        
        unit = tactical_situation.focus_unit
        position = (unit.position.x, unit.position.y)
        
        # Control zone advantage
        if position in tactical_situation.control_zones["ally"]:
            zone_advantage = 0.8
        elif position in tactical_situation.control_zones["contested"]:
            zone_advantage = 0.5
        elif position in tactical_situation.control_zones["neutral"]:
            zone_advantage = 0.3
        else:  # enemy zone
            zone_advantage = 0.1
        
        # Flanking opportunities
        flanking_ops = len(tactical_situation._find_flanking_opportunities())
        flanking_advantage = min(1.0, flanking_ops / 3.0)
        
        # Support from allies
        support_count = len([ally for ally in tactical_situation.allies 
                           if abs(ally.position.x - unit.position.x) + abs(ally.position.y - unit.position.y) <= 2])
        support_advantage = min(1.0, support_count / 2.0)
        
        return (zone_advantage + flanking_advantage + support_advantage) / 3.0
    
    def _evaluate_resource_efficiency(self, tactical_situation: TacticalSituation) -> float:
        """Evaluate unit's resource usage efficiency"""
        if not tactical_situation.focus_unit:
            return 0.0
        
        unit = tactical_situation.focus_unit
        
        # MP efficiency
        mp_ratio = unit.mp / max(unit.max_mp, 1)
        
        # HP efficiency (not taking unnecessary damage)
        hp_ratio = unit.hp / unit.max_hp
        
        # Action point efficiency (simplified)
        ap_ratio = unit.ap / max(unit.max_ap, 1)
        
        return (mp_ratio + hp_ratio + ap_ratio) / 3.0
    
    def _evaluate_survival_probability(self, tactical_situation: TacticalSituation) -> float:
        """Evaluate unit's survival probability"""
        if not tactical_situation.focus_unit:
            return 0.0
        
        unit = tactical_situation.focus_unit
        
        # Health factor
        hp_ratio = unit.hp / unit.max_hp
        
        # Threat factor
        position_threat = tactical_situation.threat_map.get((unit.position.x, unit.position.y), 0)
        threat_factor = max(0.0, 1.0 - position_threat / 50.0)
        
        # Vulnerability factor
        vulnerability_count = len([v for v in tactical_situation.vulnerabilities 
                                 if v.get("unit_id") == unit.id])
        vulnerability_factor = max(0.0, 1.0 - vulnerability_count * 0.2)
        
        # Support factor
        support_count = len([ally for ally in tactical_situation.allies 
                           if abs(ally.position.x - unit.position.x) + abs(ally.position.y - unit.position.y) <= 3])
        support_factor = min(1.0, 0.5 + support_count * 0.2)
        
        return hp_ratio * threat_factor * vulnerability_factor * support_factor
    
    def _evaluate_strategic_value(self, tactical_situation: TacticalSituation) -> float:
        """Evaluate unit's strategic value to the team"""
        if not tactical_situation.focus_unit:
            return 0.0
        
        unit = tactical_situation.focus_unit
        
        # Combat value relative to team
        unit_power = (unit.attributes.get("physical_attack", 10) + 
                     unit.attributes.get("magical_attack", 10))
        team_power = sum(
            ally.attributes.get("physical_attack", 10) + ally.attributes.get("magical_attack", 10)
            for ally in tactical_situation.allies
        ) + unit_power
        
        relative_power = unit_power / max(team_power, 1)
        
        # Position value (center control, key positions)
        center_x, center_y = tactical_situation.battlefield_state.grid_size[0] // 2, tactical_situation.battlefield_state.grid_size[1] // 2
        distance_from_center = abs(unit.position.x - center_x) + abs(unit.position.y - center_y)
        position_value = 1.0 - (distance_from_center / 10.0)
        
        # Special abilities value (simplified)
        special_value = 0.5  # Would be calculated based on unit type and abilities
        
        return (relative_power + position_value + special_value) / 3.0
    
    def _generate_unit_recommendations(self, tactical_situation: TacticalSituation) -> List[str]:
        """Generate specific recommendations for the unit"""
        recommendations = []
        
        if not tactical_situation.focus_unit:
            return ["Unable to analyze unit"]
        
        # Health-based recommendations
        hp_ratio = tactical_situation.focus_unit.hp / tactical_situation.focus_unit.max_hp
        if hp_ratio < 0.3:
            recommendations.append("Seek healing or defensive position - critically wounded")
        elif hp_ratio < 0.6:
            recommendations.append("Consider cautious tactics - moderate damage taken")
        
        # Position-based recommendations
        vulnerabilities = [v for v in tactical_situation.vulnerabilities 
                         if v.get("unit_id") == tactical_situation.focus_unit.id]
        
        for vuln in vulnerabilities:
            if vuln["type"] == "isolation":
                recommendations.append("Move towards allied support")
            elif vuln["type"] == "surrounded":
                recommendations.append("Break out of encirclement immediately")
            elif vuln["type"] == "low_resources":
                recommendations.append("Conserve MP for critical actions")
        
        # Opportunity-based recommendations
        flanking_ops = tactical_situation._find_flanking_opportunities()
        if flanking_ops:
            best_op = flanking_ops[0]
            if best_op["advantage_score"] > 0.7:
                recommendations.append(f"Execute flanking attack on {best_op['target_id']}")
        
        # Formation-based recommendations
        ally_formations = tactical_situation.formations.get("ally", [])
        if TacticalPattern.SKIRMISH in ally_formations:
            recommendations.append("Coordinate with scattered allies for concentrated attack")
        elif TacticalPattern.PHALANX in ally_formations:
            recommendations.append("Maintain formation cohesion")
        
        return recommendations[:4]  # Limit to top 4 recommendations
    
    async def benchmark_performance(self, iterations: int = 10) -> List[Dict[str, Any]]:
        """Benchmark AI performance"""
        results = []
        
        for i in range(iterations):
            start_time = time.time()
            
            # Create test request
            test_request = AIDecisionRequest(
                session_id=f"benchmark_{i}",
                unit_id=f"test_unit_{i}",
                difficulty_level="normal"
            )
            
            # Make decision
            try:
                response = await self.make_decision(test_request)
                execution_time = time.time() - start_time
                
                results.append({
                    "iteration": i,
                    "execution_time": execution_time,
                    "confidence": response.confidence,
                    "success": True
                })
                
            except Exception as e:
                execution_time = time.time() - start_time
                results.append({
                    "iteration": i,
                    "execution_time": execution_time,
                    "confidence": 0.0,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def get_config(self) -> Dict[str, Any]:
        """Get AI configuration"""
        return {
            "personalities_loaded": len(self.personalities),
            "learning_systems": len(self.learning_systems),
            "performance_metrics": self.performance_metrics
        }
    
    async def update_config(self, model_name: str, settings: Dict[str, Any]):
        """Update AI configuration"""
        # This would update model settings, personality parameters, etc.
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get AI statistics"""
        return {
            "performance_metrics": self.performance_metrics,
            "personalities": {
                personality_id: personality.get_stats()
                for personality_id, personality in self.personalities.items()
            },
            "learning_systems": {
                system_id: system.get_learning_stats()
                for system_id, system in self.learning_systems.items()
            }
        }