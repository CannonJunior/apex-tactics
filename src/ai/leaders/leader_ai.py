"""
Leader AI System

Specialized AI for leader units with unique battlefield control abilities.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import random
import time

from core.ecs.entity import Entity
from core.ecs.component import Transform
from core.math.vector import Vector3, Vector2Int
from components.stats.attributes import AttributeStats
from components.combat.attack import AttackComponent
from components.combat.damage import DamageComponent
from ai.difficulty.difficulty_manager import DifficultyManager


class LeaderType(Enum):
    """Types of leader units with distinct specializations"""
    TACTICAL_COMMANDER = "tactical_commander"    # Formation and coordination specialist
    BATTLE_MASTER = "battle_master"             # Combat effectiveness enhancer
    STRATEGIC_GENIUS = "strategic_genius"       # Long-term planning and adaptation
    INSPIRATIONAL_LEADER = "inspirational"     # Morale and unit buffs


class LeaderAbility(Enum):
    """Special abilities available to leader units"""
    # Tactical Commander abilities
    COORDINATE_ATTACK = "coordinate_attack"
    FORMATION_COMMAND = "formation_command"
    TACTICAL_RETREAT = "tactical_retreat"
    FLANKING_MANEUVER = "flanking_maneuver"
    
    # Battle Master abilities
    BATTLE_FURY = "battle_fury"
    PRECISION_STRIKE = "precision_strike"
    DEFENSIVE_STANCE = "defensive_stance"
    COUNTER_ATTACK = "counter_attack"
    
    # Strategic Genius abilities
    PREDICT_MOVEMENT = "predict_movement"
    ADAPTIVE_STRATEGY = "adaptive_strategy"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    BATTLEFIELD_ANALYSIS = "battlefield_analysis"
    
    # Inspirational Leader abilities
    RALLY_TROOPS = "rally_troops"
    INSPIRING_PRESENCE = "inspiring_presence"
    HEROIC_CHARGE = "heroic_charge"
    LAST_STAND = "last_stand"


@dataclass
class LeaderAbilityDefinition:
    """Definition of a leader ability"""
    ability: LeaderAbility
    name: str
    description: str
    cooldown: float          # Seconds between uses
    range: int               # Ability range in grid units
    area_effect: bool        # Whether ability affects multiple units
    resource_cost: int       # Resource points required
    activation_condition: str # Condition required for activation


class LeaderAI:
    """
    Specialized AI for leader units with unique battlefield control abilities.
    
    Leaders provide strategic coordination, tactical bonuses, and special abilities
    that affect multiple units and battlefield dynamics.
    """
    
    def __init__(self, leader_entity: Entity, leader_type: LeaderType, 
                 difficulty_manager: Optional[DifficultyManager] = None):
        self.leader_entity = leader_entity
        self.leader_type = leader_type
        self.difficulty_manager = difficulty_manager
        
        # Leader state
        self.leadership_range = 5  # Grid units within which leader affects allies
        self.command_points = 100  # Resource for special abilities
        self.max_command_points = 100
        self.ability_cooldowns: Dict[LeaderAbility, float] = {}
        
        # Available abilities based on leader type
        self.available_abilities = self._get_leader_abilities()
        
        # Strategic state
        self.current_strategy = "balanced"
        self.formation_target = None
        self.priority_targets: List[Entity] = []
        self.allied_units: List[Entity] = []
        
        # Performance tracking
        self.abilities_used = 0
        self.successful_commands = 0
        self.battle_start_time = time.time()
        
        # Initialize ability definitions
        self.ability_definitions = self._create_ability_definitions()
    
    def _get_leader_abilities(self) -> List[LeaderAbility]:
        """Get available abilities based on leader type"""
        ability_map = {
            LeaderType.TACTICAL_COMMANDER: [
                LeaderAbility.COORDINATE_ATTACK,
                LeaderAbility.FORMATION_COMMAND,
                LeaderAbility.TACTICAL_RETREAT,
                LeaderAbility.FLANKING_MANEUVER
            ],
            LeaderType.BATTLE_MASTER: [
                LeaderAbility.BATTLE_FURY,
                LeaderAbility.PRECISION_STRIKE,
                LeaderAbility.DEFENSIVE_STANCE,
                LeaderAbility.COUNTER_ATTACK
            ],
            LeaderType.STRATEGIC_GENIUS: [
                LeaderAbility.PREDICT_MOVEMENT,
                LeaderAbility.ADAPTIVE_STRATEGY,
                LeaderAbility.RESOURCE_OPTIMIZATION,
                LeaderAbility.BATTLEFIELD_ANALYSIS
            ],
            LeaderType.INSPIRATIONAL_LEADER: [
                LeaderAbility.RALLY_TROOPS,
                LeaderAbility.INSPIRING_PRESENCE,
                LeaderAbility.HEROIC_CHARGE,
                LeaderAbility.LAST_STAND
            ]
        }
        return ability_map.get(self.leader_type, [])
    
    def _create_ability_definitions(self) -> Dict[LeaderAbility, LeaderAbilityDefinition]:
        """Create definitions for all leader abilities"""
        return {
            # Tactical Commander abilities
            LeaderAbility.COORDINATE_ATTACK: LeaderAbilityDefinition(
                ability=LeaderAbility.COORDINATE_ATTACK,
                name="Coordinate Attack",
                description="Multiple allied units attack the same target simultaneously",
                cooldown=30.0,
                range=8,
                area_effect=True,
                resource_cost=25,
                activation_condition="multiple_allies_in_range"
            ),
            LeaderAbility.FORMATION_COMMAND: LeaderAbilityDefinition(
                ability=LeaderAbility.FORMATION_COMMAND,
                name="Formation Command",
                description="Organize allies into optimal tactical formation",
                cooldown=20.0,
                range=6,
                area_effect=True,
                resource_cost=20,
                activation_condition="allies_dispersed"
            ),
            LeaderAbility.TACTICAL_RETREAT: LeaderAbilityDefinition(
                ability=LeaderAbility.TACTICAL_RETREAT,
                name="Tactical Retreat",
                description="Coordinated withdrawal while maintaining formation",
                cooldown=45.0,
                range=10,
                area_effect=True,
                resource_cost=30,
                activation_condition="allies_under_threat"
            ),
            LeaderAbility.FLANKING_MANEUVER: LeaderAbilityDefinition(
                ability=LeaderAbility.FLANKING_MANEUVER,
                name="Flanking Maneuver",
                description="Position allies for coordinated flank attack",
                cooldown=35.0,
                range=8,
                area_effect=True,
                resource_cost=35,
                activation_condition="enemy_flanking_opportunity"
            ),
            
            # Battle Master abilities  
            LeaderAbility.BATTLE_FURY: LeaderAbilityDefinition(
                ability=LeaderAbility.BATTLE_FURY,
                name="Battle Fury",
                description="Boost damage and attack speed of nearby allies",
                cooldown=40.0,
                range=4,
                area_effect=True,
                resource_cost=30,
                activation_condition="combat_engaged"
            ),
            LeaderAbility.PRECISION_STRIKE: LeaderAbilityDefinition(
                ability=LeaderAbility.PRECISION_STRIKE,
                name="Precision Strike",
                description="Guarantee critical hit on next attack",
                cooldown=25.0,
                range=1,
                area_effect=False,
                resource_cost=20,
                activation_condition="high_value_target"
            ),
            LeaderAbility.DEFENSIVE_STANCE: LeaderAbilityDefinition(
                ability=LeaderAbility.DEFENSIVE_STANCE,
                name="Defensive Stance",
                description="Increase defense and damage resistance of allies",
                cooldown=30.0,
                range=5,
                area_effect=True,
                resource_cost=25,
                activation_condition="under_heavy_attack"
            ),
            LeaderAbility.COUNTER_ATTACK: LeaderAbilityDefinition(
                ability=LeaderAbility.COUNTER_ATTACK,
                name="Counter Attack",
                description="Automatically retaliate against enemy attacks",
                cooldown=20.0,
                range=3,
                area_effect=True,
                resource_cost=15,
                activation_condition="recently_attacked"
            ),
            
            # Strategic Genius abilities
            LeaderAbility.PREDICT_MOVEMENT: LeaderAbilityDefinition(
                ability=LeaderAbility.PREDICT_MOVEMENT,
                name="Predict Movement",
                description="Anticipate enemy movements and counter them",
                cooldown=50.0,
                range=12,
                area_effect=False,
                resource_cost=40,
                activation_condition="enemy_pattern_detected"
            ),
            LeaderAbility.ADAPTIVE_STRATEGY: LeaderAbilityDefinition(
                ability=LeaderAbility.ADAPTIVE_STRATEGY,
                name="Adaptive Strategy",
                description="Change tactical approach based on battlefield state",
                cooldown=60.0,
                range=15,
                area_effect=True,
                resource_cost=45,
                activation_condition="strategy_not_working"
            ),
            LeaderAbility.RESOURCE_OPTIMIZATION: LeaderAbilityDefinition(
                ability=LeaderAbility.RESOURCE_OPTIMIZATION,
                name="Resource Optimization",
                description="Improve resource efficiency for all allies",
                cooldown=45.0,
                range=8,
                area_effect=True,
                resource_cost=35,
                activation_condition="resource_shortage"
            ),
            LeaderAbility.BATTLEFIELD_ANALYSIS: LeaderAbilityDefinition(
                ability=LeaderAbility.BATTLEFIELD_ANALYSIS,
                name="Battlefield Analysis",
                description="Reveal optimal tactical opportunities",
                cooldown=30.0,
                range=20,
                area_effect=False,
                resource_cost=25,
                activation_condition="tactical_opportunity"
            ),
            
            # Inspirational Leader abilities
            LeaderAbility.RALLY_TROOPS: LeaderAbilityDefinition(
                ability=LeaderAbility.RALLY_TROOPS,
                name="Rally Troops",
                description="Restore morale and health to allied units",
                cooldown=35.0,
                range=6,
                area_effect=True,
                resource_cost=30,
                activation_condition="allies_low_health"
            ),
            LeaderAbility.INSPIRING_PRESENCE: LeaderAbilityDefinition(
                ability=LeaderAbility.INSPIRING_PRESENCE,
                name="Inspiring Presence",
                description="Passive boost to all allied capabilities",
                cooldown=0.0,  # Passive ability
                range=5,
                area_effect=True,
                resource_cost=0,
                activation_condition="always"
            ),
            LeaderAbility.HEROIC_CHARGE: LeaderAbilityDefinition(
                ability=LeaderAbility.HEROIC_CHARGE,
                name="Heroic Charge",
                description="Lead a devastating charge attack",
                cooldown=50.0,
                range=8,
                area_effect=True,
                resource_cost=40,
                activation_condition="charge_opportunity"
            ),
            LeaderAbility.LAST_STAND: LeaderAbilityDefinition(
                ability=LeaderAbility.LAST_STAND,
                name="Last Stand",
                description="Massive combat boost when critically wounded",
                cooldown=120.0,
                range=4,
                area_effect=True,
                resource_cost=50,
                activation_condition="critical_health"
            )
        }
    
    def update_leader_ai(self, allied_units: List[Entity], enemy_units: List[Entity], 
                        delta_time: float) -> Optional[Dict[str, Any]]:
        """
        Update leader AI and determine next action.
        
        Args:
            allied_units: List of friendly units
            enemy_units: List of enemy units
            delta_time: Time elapsed since last update
            
        Returns:
            Leader action to execute or None
        """
        self.allied_units = allied_units
        
        # Update ability cooldowns
        self._update_cooldowns(delta_time)
        
        # Regenerate command points
        self._regenerate_command_points(delta_time)
        
        # Assess battlefield situation
        battlefield_assessment = self._assess_battlefield(allied_units, enemy_units)
        
        # Determine strategic approach
        self._update_strategy(battlefield_assessment)
        
        # Check for ability usage opportunities
        ability_action = self._evaluate_ability_usage(allied_units, enemy_units, battlefield_assessment)
        if ability_action:
            return ability_action
        
        # Determine standard leader action
        return self._determine_leader_action(allied_units, enemy_units, battlefield_assessment)
    
    def _update_cooldowns(self, delta_time: float):
        """Update ability cooldowns"""
        current_time = time.time()
        for ability, end_time in list(self.ability_cooldowns.items()):
            if current_time >= end_time:
                del self.ability_cooldowns[ability]
    
    def _regenerate_command_points(self, delta_time: float):
        """Regenerate command points over time"""
        regen_rate = 2.0  # Points per second
        self.command_points = min(self.max_command_points, 
                                self.command_points + regen_rate * delta_time)
    
    def _assess_battlefield(self, allied_units: List[Entity], enemy_units: List[Entity]) -> Dict[str, Any]:
        """Assess current battlefield situation"""
        leader_pos = self._get_leader_position()
        if not leader_pos:
            return {}
        
        # Count units in leadership range
        allies_in_range = []
        enemies_in_range = []
        
        for unit in allied_units:
            if self._get_distance_to_unit(unit) <= self.leadership_range:
                allies_in_range.append(unit)
        
        for unit in enemy_units:
            if self._get_distance_to_unit(unit) <= self.leadership_range * 1.5:
                enemies_in_range.append(unit)
        
        # Assess unit health status
        allies_low_health = sum(1 for unit in allies_in_range if self._is_unit_low_health(unit))
        
        # Assess formation quality
        formation_score = self._assess_formation_quality(allies_in_range)
        
        # Assess tactical opportunities
        flanking_opportunities = self._detect_flanking_opportunities(allied_units, enemy_units)
        
        return {
            'allies_in_range': len(allies_in_range),
            'enemies_in_range': len(enemies_in_range),
            'allies_low_health': allies_low_health,
            'formation_score': formation_score,
            'flanking_opportunities': flanking_opportunities,
            'combat_intensity': min(len(enemies_in_range) / 3.0, 1.0),
            'ally_units': allies_in_range,
            'enemy_units': enemies_in_range
        }
    
    def _update_strategy(self, battlefield_assessment: Dict[str, Any]):
        """Update current strategic approach"""
        enemies_nearby = battlefield_assessment.get('enemies_in_range', 0)
        allies_nearby = battlefield_assessment.get('allies_in_range', 0)
        formation_score = battlefield_assessment.get('formation_score', 0.5)
        
        if enemies_nearby > allies_nearby:
            self.current_strategy = "defensive"
        elif formation_score < 0.4:
            self.current_strategy = "regroup"
        elif battlefield_assessment.get('flanking_opportunities', 0) > 0:
            self.current_strategy = "flanking"
        else:
            self.current_strategy = "aggressive"
    
    def _evaluate_ability_usage(self, allied_units: List[Entity], enemy_units: List[Entity], 
                              battlefield_assessment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate whether to use a special ability"""
        
        for ability in self.available_abilities:
            if self._can_use_ability(ability) and self._should_use_ability(ability, battlefield_assessment):
                return self._create_ability_action(ability, battlefield_assessment)
        
        return None
    
    def _can_use_ability(self, ability: LeaderAbility) -> bool:
        """Check if ability can be used (cooldown and resources)"""
        if ability in self.ability_cooldowns:
            return False
        
        definition = self.ability_definitions.get(ability)
        if not definition:
            return False
        
        return self.command_points >= definition.resource_cost
    
    def _should_use_ability(self, ability: LeaderAbility, battlefield_assessment: Dict[str, Any]) -> bool:
        """Determine if ability should be used based on conditions"""
        definition = self.ability_definitions.get(ability)
        if not definition:
            return False
        
        condition = definition.activation_condition
        
        # Check activation conditions
        if condition == "multiple_allies_in_range":
            return battlefield_assessment.get('allies_in_range', 0) >= 3
        elif condition == "allies_dispersed":
            return battlefield_assessment.get('formation_score', 1.0) < 0.4
        elif condition == "allies_under_threat":
            return (battlefield_assessment.get('enemies_in_range', 0) > 
                   battlefield_assessment.get('allies_in_range', 0))
        elif condition == "enemy_flanking_opportunity":
            return battlefield_assessment.get('flanking_opportunities', 0) > 0
        elif condition == "combat_engaged":
            return battlefield_assessment.get('combat_intensity', 0) > 0.5
        elif condition == "high_value_target":
            return len(battlefield_assessment.get('enemy_units', [])) > 0
        elif condition == "under_heavy_attack":
            return battlefield_assessment.get('allies_low_health', 0) >= 2
        elif condition == "recently_attacked":
            return battlefield_assessment.get('combat_intensity', 0) > 0.3
        elif condition == "allies_low_health":
            return battlefield_assessment.get('allies_low_health', 0) >= 1
        elif condition == "charge_opportunity":
            return (self.current_strategy == "aggressive" and 
                   battlefield_assessment.get('allies_in_range', 0) >= 2)
        elif condition == "critical_health":
            return self._is_unit_low_health(self.leader_entity)
        elif condition == "always":
            return True
        
        return False
    
    def _create_ability_action(self, ability: LeaderAbility, 
                             battlefield_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create action dictionary for ability use"""
        definition = self.ability_definitions[ability]
        
        # Spend command points and set cooldown
        self.command_points -= definition.resource_cost
        self.ability_cooldowns[ability] = time.time() + definition.cooldown
        self.abilities_used += 1
        
        action = {
            'action_type': 'leader_ability',
            'ability': ability.value,
            'ability_name': definition.name,
            'leader_id': self.leader_entity.id,
            'range': definition.range,
            'area_effect': definition.area_effect,
            'targets': self._select_ability_targets(ability, battlefield_assessment),
            'timestamp': time.time()
        }
        
        return action
    
    def _select_ability_targets(self, ability: LeaderAbility, 
                              battlefield_assessment: Dict[str, Any]) -> List[int]:
        """Select targets for ability"""
        ally_units = battlefield_assessment.get('ally_units', [])
        enemy_units = battlefield_assessment.get('enemy_units', [])
        
        # Target selection based on ability type
        if ability in [LeaderAbility.COORDINATE_ATTACK, LeaderAbility.PRECISION_STRIKE]:
            # Target enemies
            return [unit.id for unit in enemy_units[:1]]  # Primary target
        elif ability in [LeaderAbility.RALLY_TROOPS, LeaderAbility.BATTLE_FURY, 
                        LeaderAbility.FORMATION_COMMAND]:
            # Target allies
            return [unit.id for unit in ally_units]
        else:
            # Mixed or positional abilities
            return []
    
    def _determine_leader_action(self, allied_units: List[Entity], enemy_units: List[Entity],
                               battlefield_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Determine standard leader action (movement/attack)"""
        
        # Apply difficulty scaling
        if self.difficulty_manager:
            mistake_chance = self.difficulty_manager.get_ai_modifier('mistake_chance')
            if random.random() < mistake_chance:
                return self._make_intentional_mistake(battlefield_assessment)
        
        # Choose action based on strategy and situation
        if self.current_strategy == "defensive":
            return self._create_defensive_action(battlefield_assessment)
        elif self.current_strategy == "regroup":
            return self._create_regrouping_action(battlefield_assessment)
        elif self.current_strategy == "flanking":
            return self._create_flanking_action(battlefield_assessment)
        else:  # aggressive
            return self._create_aggressive_action(battlefield_assessment)
    
    def _create_defensive_action(self, battlefield_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create defensive action for leader"""
        return {
            'action_type': 'move_defensive',
            'leader_id': self.leader_entity.id,
            'strategy': 'defensive',
            'priority': 0.8
        }
    
    def _create_regrouping_action(self, battlefield_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create regrouping action for leader"""
        return {
            'action_type': 'move_regroup',
            'leader_id': self.leader_entity.id,
            'strategy': 'regroup',
            'priority': 0.7
        }
    
    def _create_flanking_action(self, battlefield_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create flanking action for leader"""
        return {
            'action_type': 'move_flank',
            'leader_id': self.leader_entity.id,
            'strategy': 'flanking',
            'priority': 0.9
        }
    
    def _create_aggressive_action(self, battlefield_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create aggressive action for leader"""
        enemy_units = battlefield_assessment.get('enemy_units', [])
        if enemy_units:
            return {
                'action_type': 'attack',
                'leader_id': self.leader_entity.id,
                'target_id': enemy_units[0].id,
                'strategy': 'aggressive',
                'priority': 1.0
            }
        else:
            return {
                'action_type': 'move_aggressive',
                'leader_id': self.leader_entity.id,
                'strategy': 'aggressive',
                'priority': 0.6
            }
    
    def _make_intentional_mistake(self, battlefield_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Make an intentional tactical mistake for difficulty scaling"""
        mistake_types = [
            'move_suboptimal',
            'attack_wrong_target',
            'waste_ability',
            'poor_positioning'
        ]
        
        mistake_type = random.choice(mistake_types)
        
        return {
            'action_type': mistake_type,
            'leader_id': self.leader_entity.id,
            'is_mistake': True,
            'priority': 0.3
        }
    
    # Helper methods
    
    def _get_leader_position(self) -> Optional[Vector3]:
        """Get leader's current position"""
        transform = self.leader_entity.get_component(Transform)
        return transform.position if transform else None
    
    def _get_distance_to_unit(self, unit: Entity) -> float:
        """Get distance from leader to specified unit"""
        leader_pos = self._get_leader_position()
        if not leader_pos:
            return float('inf')
        
        unit_transform = unit.get_component(Transform)
        if not unit_transform:
            return float('inf')
        
        return leader_pos.distance_to(unit_transform.position)
    
    def _is_unit_low_health(self, unit: Entity) -> bool:
        """Check if unit has low health"""
        attributes = unit.get_component(AttributeStats)
        if not attributes:
            return False
        
        health_ratio = attributes.current_hp / attributes.max_hp if attributes.max_hp > 0 else 0
        return health_ratio < 0.4  # Less than 40% health
    
    def _assess_formation_quality(self, units: List[Entity]) -> float:
        """Assess quality of unit formation (0.0-1.0)"""
        if len(units) < 2:
            return 1.0
        
        # Simple formation assessment based on unit spacing
        positions = []
        for unit in units:
            transform = unit.get_component(Transform)
            if transform:
                positions.append((transform.position.x, transform.position.z))
        
        if len(positions) < 2:
            return 0.5
        
        # Calculate average distance between units
        total_distance = 0
        count = 0
        
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                distance = ((positions[i][0] - positions[j][0]) ** 2 + 
                           (positions[i][1] - positions[j][1]) ** 2) ** 0.5
                total_distance += distance
                count += 1
        
        if count == 0:
            return 0.5
        
        average_distance = total_distance / count
        
        # Optimal formation has units 2-4 units apart
        optimal_distance = 3.0
        formation_score = max(0.0, 1.0 - abs(average_distance - optimal_distance) / optimal_distance)
        
        return formation_score
    
    def _detect_flanking_opportunities(self, allied_units: List[Entity], 
                                     enemy_units: List[Entity]) -> int:
        """Detect number of flanking opportunities"""
        # Simplified flanking detection
        opportunities = 0
        
        for enemy in enemy_units:
            enemy_transform = enemy.get_component(Transform)
            if not enemy_transform:
                continue
            
            # Check if allies can surround this enemy
            ally_positions_around_enemy = 0
            for ally in allied_units:
                ally_transform = ally.get_component(Transform)
                if ally_transform:
                    distance = enemy_transform.position.distance_to(ally_transform.position)
                    if 2 <= distance <= 4:  # Good flanking distance
                        ally_positions_around_enemy += 1
            
            if ally_positions_around_enemy >= 2:
                opportunities += 1
        
        return opportunities
    
    def get_leader_status(self) -> Dict[str, Any]:
        """Get comprehensive leader status"""
        return {
            'leader_type': self.leader_type.value,
            'command_points': self.command_points,
            'max_command_points': self.max_command_points,
            'current_strategy': self.current_strategy,
            'available_abilities': [ability.value for ability in self.available_abilities],
            'abilities_on_cooldown': list(self.ability_cooldowns.keys()),
            'abilities_used': self.abilities_used,
            'successful_commands': self.successful_commands,
            'leadership_range': self.leadership_range,
            'performance_ratio': self.successful_commands / max(self.abilities_used, 1),
            'battle_duration': time.time() - self.battle_start_time
        }