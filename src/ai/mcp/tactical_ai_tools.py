"""
Advanced Tactical AI Tools for MCP Server

Enhanced tools for tactical analysis, decision-making, and battlefield management.
"""

import json
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from core.ecs.world import World
from core.ecs.entity import Entity
from core.ecs.component import Transform
from core.math.vector import Vector3, Vector2Int
from core.math.pathfinding import AStarPathfinder
from components.stats.attributes import AttributeStats
from components.combat.damage import DamageComponent, AttackType
from components.combat.defense import DefenseComponent
from components.combat.attack import AttackComponent
from game.battle.battle_manager import BattleManager


@dataclass
class TacticalAnalysis:
    """Comprehensive tactical analysis result"""
    unit_count: int
    average_power: float
    formation_strength: float
    terrain_advantage: float
    recommended_action: str
    confidence: float
    threat_assessment: Dict[str, float]


@dataclass
class UnitEvaluation:
    """Individual unit evaluation"""
    unit_id: int
    combat_effectiveness: float
    positioning_score: float
    threat_level: float
    tactical_value: float
    recommended_role: str


class TacticalAITools:
    """
    Advanced tactical AI analysis tools for MCP integration.
    
    Provides sophisticated battlefield analysis, unit evaluation,
    and tactical decision-making capabilities.
    """
    
    def __init__(self, world: World):
        self.world = world
        self.pathfinder = None
        self.battle_manager = None
    
    def set_pathfinder(self, pathfinder: AStarPathfinder):
        """Set pathfinder for tactical analysis"""
        self.pathfinder = pathfinder
    
    def set_battle_manager(self, battle_manager: BattleManager):
        """Set battle manager for combat analysis"""
        self.battle_manager = battle_manager
    
    def analyze_battlefield(self, units: List[Entity], grid_size: Tuple[int, int]) -> TacticalAnalysis:
        """
        Perform comprehensive battlefield analysis.
        
        Args:
            units: List of units on battlefield
            grid_size: (width, height) of tactical grid
            
        Returns:
            TacticalAnalysis with strategic recommendations
        """
        if not units:
            return TacticalAnalysis(
                unit_count=0,
                average_power=0.0,
                formation_strength=0.0,
                terrain_advantage=0.0,
                recommended_action="wait",
                confidence=0.0,
                threat_assessment={}
            )
        
        # Calculate unit metrics
        total_power = 0
        total_positioning = 0
        threat_map = {}
        
        for unit in units:
            evaluation = self.evaluate_unit(unit, units)
            total_power += evaluation.combat_effectiveness
            total_positioning += evaluation.positioning_score
            threat_map[str(unit.id)] = evaluation.threat_level
        
        unit_count = len(units)
        average_power = total_power / unit_count if unit_count > 0 else 0
        
        # Analyze formation
        formation_strength = self._analyze_formation(units)
        
        # Assess terrain advantage
        terrain_advantage = self._assess_terrain_advantage(units, grid_size)
        
        # Generate tactical recommendation
        recommended_action, confidence = self._generate_tactical_recommendation(
            average_power, formation_strength, terrain_advantage, threat_map
        )
        
        return TacticalAnalysis(
            unit_count=unit_count,
            average_power=average_power,
            formation_strength=formation_strength,
            terrain_advantage=terrain_advantage,
            recommended_action=recommended_action,
            confidence=confidence,
            threat_assessment=threat_map
        )
    
    def evaluate_unit(self, unit: Entity, all_units: List[Entity]) -> UnitEvaluation:
        """
        Evaluate individual unit's tactical value.
        
        Args:
            unit: Unit to evaluate
            all_units: All units on battlefield for context
            
        Returns:
            UnitEvaluation with detailed assessment
        """
        # Combat effectiveness (damage potential + survivability)
        combat_effectiveness = self._calculate_combat_effectiveness(unit)
        
        # Positioning score (strategic position value)
        positioning_score = self._calculate_positioning_score(unit, all_units)
        
        # Threat level (danger this unit poses to enemies)
        threat_level = self._calculate_threat_level(unit)
        
        # Overall tactical value
        tactical_value = (combat_effectiveness * 0.4 + 
                         positioning_score * 0.3 + 
                         threat_level * 0.3)
        
        # Recommend tactical role
        recommended_role = self._determine_tactical_role(unit)
        
        return UnitEvaluation(
            unit_id=unit.id,
            combat_effectiveness=combat_effectiveness,
            positioning_score=positioning_score,
            threat_level=threat_level,
            tactical_value=tactical_value,
            recommended_role=recommended_role
        )
    
    def find_optimal_position(self, unit: Entity, all_units: List[Entity], 
                            grid_size: Tuple[int, int]) -> Optional[Vector2Int]:
        """
        Find optimal position for unit using tactical analysis.
        
        Args:
            unit: Unit to position
            all_units: All units for tactical context
            grid_size: Battlefield dimensions
            
        Returns:
            Optimal grid position or None if none found
        """
        if not self.pathfinder:
            return None
        
        unit_transform = unit.get_component(Transform)
        if not unit_transform:
            return None
        
        current_pos = Vector2Int(
            int(unit_transform.position.x),
            int(unit_transform.position.z)
        )
        
        best_position = None
        best_score = -1.0
        
        # Evaluate positions within movement range
        movement_range = self._get_movement_range(unit)
        
        for dx in range(-movement_range, movement_range + 1):
            for dy in range(-movement_range, movement_range + 1):
                test_pos = Vector2Int(
                    current_pos.x + dx,
                    current_pos.y + dy
                )
                
                # Check if position is valid
                if (test_pos.x < 0 or test_pos.x >= grid_size[0] or
                    test_pos.y < 0 or test_pos.y >= grid_size[1]):
                    continue
                
                # Check if position is reachable
                if not self._is_position_reachable(current_pos, test_pos):
                    continue
                
                # Check if position is occupied
                if self._is_position_occupied(test_pos, all_units):
                    continue
                
                # Score this position
                score = self._score_position(unit, test_pos, all_units)
                
                if score > best_score:
                    best_score = score
                    best_position = test_pos
        
        return best_position
    
    def select_optimal_target(self, attacker: Entity, potential_targets: List[Entity]) -> Optional[Entity]:
        """
        Select optimal target for attack using AI analysis.
        
        Args:
            attacker: Unit performing attack
            potential_targets: List of potential enemy targets
            
        Returns:
            Best target entity or None
        """
        if not potential_targets:
            return None
        
        attack_component = attacker.get_component(AttackComponent)
        if not attack_component:
            return None
        
        best_target = None
        best_score = -1.0
        
        for target in potential_targets:
            # Check if target is in range
            if not self._is_target_in_range(attacker, target):
                continue
            
            # Calculate target priority score
            score = self._calculate_target_priority(attacker, target)
            
            if score > best_score:
                best_score = score
                best_target = target
        
        return best_target
    
    def plan_tactical_sequence(self, units: List[Entity], turns: int = 3) -> List[Dict[str, Any]]:
        """
        Plan multi-turn tactical sequence.
        
        Args:
            units: Units to plan for
            turns: Number of turns to plan ahead
            
        Returns:
            List of planned actions for each turn
        """
        plan = []
        
        for turn in range(turns):
            turn_plan = {
                'turn': turn + 1,
                'actions': [],
                'strategic_focus': self._determine_strategic_focus(units, turn)
            }
            
            for unit in units:
                action = self._plan_unit_action(unit, units, turn)
                if action:
                    turn_plan['actions'].append(action)
            
            plan.append(turn_plan)
        
        return plan
    
    # Private helper methods
    
    def _analyze_formation(self, units: List[Entity]) -> float:
        """Analyze formation strength (0.0-1.0)"""
        if len(units) < 2:
            return 0.5
        
        # Calculate unit spacing and clustering
        positions = []
        for unit in units:
            transform = unit.get_component(Transform)
            if transform:
                positions.append((transform.position.x, transform.position.z))
        
        if len(positions) < 2:
            return 0.5
        
        # Measure formation cohesion
        total_distance = 0
        count = 0
        
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                dist = math.sqrt(
                    (positions[i][0] - positions[j][0]) ** 2 +
                    (positions[i][1] - positions[j][1]) ** 2
                )
                total_distance += dist
                count += 1
        
        average_distance = total_distance / count if count > 0 else 0
        
        # Optimal distance is around 2-3 units apart
        optimal_distance = 2.5
        formation_score = max(0.0, 1.0 - abs(average_distance - optimal_distance) / optimal_distance)
        
        return formation_score
    
    def _assess_terrain_advantage(self, units: List[Entity], grid_size: Tuple[int, int]) -> float:
        """Assess terrain advantage (0.0-1.0)"""
        # Simplified terrain assessment
        # In a full implementation, this would analyze actual terrain features
        
        advantage_score = 0.0
        unit_count = len(units)
        
        if unit_count == 0:
            return 0.5
        
        for unit in units:
            transform = unit.get_component(Transform)
            if not transform:
                continue
            
            x, z = transform.position.x, transform.position.z
            
            # Score based on position relative to battlefield
            center_x, center_z = grid_size[0] / 2, grid_size[1] / 2
            
            # Distance from center (closer to edges can be advantageous for defense)
            distance_from_center = math.sqrt((x - center_x) ** 2 + (z - center_z) ** 2)
            max_distance = math.sqrt(center_x ** 2 + center_z ** 2)
            
            # Moderate distance from center is often optimal
            normalized_distance = distance_from_center / max_distance
            position_score = 1.0 - abs(normalized_distance - 0.7) / 0.7
            
            advantage_score += position_score
        
        return advantage_score / unit_count
    
    def _generate_tactical_recommendation(self, power: float, formation: float, 
                                        terrain: float, threats: Dict[str, float]) -> Tuple[str, float]:
        """Generate tactical recommendation with confidence"""
        
        # Calculate overall tactical strength
        tactical_strength = (power * 0.4 + formation * 0.3 + terrain * 0.3)
        
        # Analyze threat level
        avg_threat = sum(threats.values()) / len(threats) if threats else 0.5
        
        # Generate recommendation
        if tactical_strength > 0.7 and avg_threat < 0.6:
            return "aggressive_advance", 0.8
        elif tactical_strength > 0.5 and formation > 0.6:
            return "coordinated_attack", 0.7
        elif avg_threat > 0.7:
            return "defensive_formation", 0.75
        elif formation < 0.4:
            return "regroup", 0.6
        else:
            return "cautious_advance", 0.5
    
    def _calculate_combat_effectiveness(self, unit: Entity) -> float:
        """Calculate unit's combat effectiveness (0.0-1.0)"""
        damage_comp = unit.get_component(DamageComponent)
        defense_comp = unit.get_component(DefenseComponent)
        attributes = unit.get_component(AttributeStats)
        
        if not attributes:
            return 0.5
        
        # Base combat power from attributes
        attack_power = 0.0
        if damage_comp:
            attack_power = max(damage_comp.physical_power, damage_comp.magical_power, damage_comp.spiritual_power)
        
        defense_power = 0.0
        if defense_comp:
            defense_power = max(
                defense_comp.get_defense_value(AttackType.PHYSICAL),
                defense_comp.get_defense_value(AttackType.MAGICAL),
                defense_comp.get_defense_value(AttackType.SPIRITUAL)
            )
        
        # Survivability from HP
        survivability = attributes.current_hp / attributes.max_hp if attributes.max_hp > 0 else 0
        
        # Combine factors (normalized to 0-1 scale)
        effectiveness = (
            min(attack_power / 50.0, 1.0) * 0.4 +
            min(defense_power / 30.0, 1.0) * 0.3 +
            survivability * 0.3
        )
        
        return max(0.0, min(1.0, effectiveness))
    
    def _calculate_positioning_score(self, unit: Entity, all_units: List[Entity]) -> float:
        """Calculate positioning quality score (0.0-1.0)"""
        transform = unit.get_component(Transform)
        if not transform:
            return 0.5
        
        # Factors: distance to allies, distance to enemies, tactical position
        ally_distance_score = self._calculate_ally_distance_score(unit, all_units)
        enemy_distance_score = self._calculate_enemy_distance_score(unit, all_units)
        
        return (ally_distance_score + enemy_distance_score) / 2
    
    def _calculate_threat_level(self, unit: Entity) -> float:
        """Calculate threat level this unit poses (0.0-1.0)"""
        attack_comp = unit.get_component(AttackComponent)
        damage_comp = unit.get_component(DamageComponent)
        
        if not attack_comp or not damage_comp:
            return 0.3
        
        # Base threat from damage potential
        max_damage = max(damage_comp.physical_power, damage_comp.magical_power, damage_comp.spiritual_power)
        
        # Modify by range and area effect
        range_factor = min(attack_comp.attack_range / 3.0, 1.0)
        area_factor = 1.0 + (attack_comp.area_effect_radius * 0.2)
        
        threat = (max_damage / 50.0) * range_factor * area_factor
        
        return max(0.0, min(1.0, threat))
    
    def _determine_tactical_role(self, unit: Entity) -> str:
        """Determine optimal tactical role for unit"""
        damage_comp = unit.get_component(DamageComponent)
        defense_comp = unit.get_component(DefenseComponent)
        attack_comp = unit.get_component(AttackComponent)
        
        if not damage_comp or not defense_comp:
            return "support"
        
        max_attack = max(damage_comp.physical_power, damage_comp.magical_power, damage_comp.spiritual_power)
        max_defense = max(
            defense_comp.get_defense_value(AttackType.PHYSICAL),
            defense_comp.get_defense_value(AttackType.MAGICAL),
            defense_comp.get_defense_value(AttackType.SPIRITUAL)
        )
        
        attack_defense_ratio = max_attack / max(max_defense, 1)
        
        if attack_comp and attack_comp.area_effect_radius > 0:
            return "area_damage"
        elif attack_defense_ratio > 1.5:
            return "assault"
        elif attack_defense_ratio < 0.7:
            return "tank"
        else:
            return "balanced"
    
    def _get_movement_range(self, unit: Entity) -> int:
        """Get unit's movement range"""
        attributes = unit.get_component(AttributeStats)
        if not attributes:
            return 2
        
        # Movement based on speed attribute
        return max(1, attributes.speed // 3)
    
    def _is_position_reachable(self, from_pos: Vector2Int, to_pos: Vector2Int) -> bool:
        """Check if position is reachable"""
        if not self.pathfinder:
            # Simple distance check if no pathfinder
            distance = abs(to_pos.x - from_pos.x) + abs(to_pos.y - from_pos.y)
            return distance <= 3
        
        # Use pathfinder for accurate reachability
        path_result = self.pathfinder.find_path(from_pos, to_pos)
        return path_result is not None and len(path_result) > 0
    
    def _is_position_occupied(self, pos: Vector2Int, units: List[Entity]) -> bool:
        """Check if position is occupied by another unit"""
        for unit in units:
            transform = unit.get_component(Transform)
            if transform:
                unit_pos = Vector2Int(int(transform.position.x), int(transform.position.z))
                if unit_pos.x == pos.x and unit_pos.y == pos.y:
                    return True
        return False
    
    def _score_position(self, unit: Entity, pos: Vector2Int, all_units: List[Entity]) -> float:
        """Score a potential position for tactical value"""
        # Simplified position scoring
        # Consider: cover, line of sight, proximity to objectives, etc.
        
        score = 0.5  # Base score
        
        # Bonus for defensive positions (corners, edges)
        if pos.x == 0 or pos.y == 0:
            score += 0.1
        
        # Consider proximity to allies and enemies
        for other_unit in all_units:
            if other_unit.id == unit.id:
                continue
            
            other_transform = other_unit.get_component(Transform)
            if not other_transform:
                continue
            
            other_pos = Vector2Int(int(other_transform.position.x), int(other_transform.position.z))
            distance = abs(pos.x - other_pos.x) + abs(pos.y - other_pos.y)
            
            # Simplified ally/enemy detection - in full implementation would use team system
            if distance <= 2:  # Close proximity
                score += 0.05  # Bonus for mutual support
        
        return score
    
    def _is_target_in_range(self, attacker: Entity, target: Entity) -> bool:
        """Check if target is within attack range"""
        attack_comp = attacker.get_component(AttackComponent)
        if not attack_comp:
            return False
        
        attacker_transform = attacker.get_component(Transform)
        target_transform = target.get_component(Transform)
        
        if not attacker_transform or not target_transform:
            return False
        
        distance = attacker_transform.position.distance_to(target_transform.position)
        return distance <= attack_comp.get_effective_range()
    
    def _calculate_target_priority(self, attacker: Entity, target: Entity) -> float:
        """Calculate target priority score"""
        # Factors: damage potential, vulnerability, threat level, strategic value
        
        target_threat = self._calculate_threat_level(target)
        target_vulnerability = 1.0 - self._calculate_combat_effectiveness(target)
        
        # Higher priority for high-threat, vulnerable targets
        priority = target_threat * 0.6 + target_vulnerability * 0.4
        
        return priority
    
    def _plan_unit_action(self, unit: Entity, all_units: List[Entity], turn: int) -> Optional[Dict[str, Any]]:
        """Plan action for specific unit"""
        evaluation = self.evaluate_unit(unit, all_units)
        
        action = {
            'unit_id': unit.id,
            'action_type': 'move',
            'priority': evaluation.tactical_value,
            'reasoning': f"Unit role: {evaluation.recommended_role}"
        }
        
        return action
    
    def _determine_strategic_focus(self, units: List[Entity], turn: int) -> str:
        """Determine strategic focus for turn"""
        if turn == 0:
            return "positioning"
        elif turn == 1:
            return "engagement"
        else:
            return "objective"
    
    def _calculate_ally_distance_score(self, unit: Entity, all_units: List[Entity]) -> float:
        """Calculate score based on distance to allies"""
        # Simplified implementation
        return 0.5
    
    def _calculate_enemy_distance_score(self, unit: Entity, all_units: List[Entity]) -> float:
        """Calculate score based on distance to enemies"""
        # Simplified implementation
        return 0.5