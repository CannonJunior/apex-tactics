"""
Leader Behavior Implementations

Concrete implementations of leader AI behaviors and ability effects.
"""

from typing import Dict, List, Optional, Tuple, Any
import random
import math
import time

from core.ecs.entity import Entity
from core.ecs.component import Transform
from core.math.vector import Vector3, Vector2Int
from components.stats.attributes import AttributeStats
from components.combat.attack import AttackComponent
from components.combat.damage import DamageComponent
from components.combat.defense import DefenseComponent
from .leader_ai import LeaderAI, LeaderType, LeaderAbility


class LeaderBehaviors:
    """
    Implements specific behaviors and ability effects for leader units.
    
    Provides the actual implementation of leader abilities and their
    effects on the battlefield and allied units.
    """
    
    def __init__(self):
        self.active_effects: Dict[str, Dict] = {}  # Track ongoing effects
        self.ability_handlers = self._create_ability_handlers()
    
    def _create_ability_handlers(self) -> Dict[LeaderAbility, callable]:
        """Create mapping of abilities to their implementation functions"""
        return {
            # Tactical Commander abilities
            LeaderAbility.COORDINATE_ATTACK: self._execute_coordinate_attack,
            LeaderAbility.FORMATION_COMMAND: self._execute_formation_command,
            LeaderAbility.TACTICAL_RETREAT: self._execute_tactical_retreat,
            LeaderAbility.FLANKING_MANEUVER: self._execute_flanking_maneuver,
            
            # Battle Master abilities
            LeaderAbility.BATTLE_FURY: self._execute_battle_fury,
            LeaderAbility.PRECISION_STRIKE: self._execute_precision_strike,
            LeaderAbility.DEFENSIVE_STANCE: self._execute_defensive_stance,
            LeaderAbility.COUNTER_ATTACK: self._execute_counter_attack,
            
            # Strategic Genius abilities
            LeaderAbility.PREDICT_MOVEMENT: self._execute_predict_movement,
            LeaderAbility.ADAPTIVE_STRATEGY: self._execute_adaptive_strategy,
            LeaderAbility.RESOURCE_OPTIMIZATION: self._execute_resource_optimization,
            LeaderAbility.BATTLEFIELD_ANALYSIS: self._execute_battlefield_analysis,
            
            # Inspirational Leader abilities
            LeaderAbility.RALLY_TROOPS: self._execute_rally_troops,
            LeaderAbility.INSPIRING_PRESENCE: self._execute_inspiring_presence,
            LeaderAbility.HEROIC_CHARGE: self._execute_heroic_charge,
            LeaderAbility.LAST_STAND: self._execute_last_stand
        }
    
    def execute_leader_ability(self, ability: LeaderAbility, leader: Entity, 
                             targets: List[Entity], battlefield_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a leader ability with full effects.
        
        Args:
            ability: Ability to execute
            leader: Leader unit executing ability
            targets: Target units for ability
            battlefield_context: Current battlefield state
            
        Returns:
            Results of ability execution
        """
        handler = self.ability_handlers.get(ability)
        if not handler:
            return {'success': False, 'error': f'No handler for ability {ability.value}'}
        
        try:
            result = handler(leader, targets, battlefield_context)
            result['ability'] = ability.value
            result['leader_id'] = leader.id
            result['execution_time'] = time.time()
            return result
        except Exception as e:
            return {
                'success': False,
                'error': f'Error executing {ability.value}: {str(e)}',
                'ability': ability.value,
                'leader_id': leader.id
            }
    
    # Tactical Commander Abilities
    
    def _execute_coordinate_attack(self, leader: Entity, targets: List[Entity], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coordinated attack on primary target"""
        if not targets:
            return {'success': False, 'error': 'No targets specified'}
        
        primary_target = targets[0]
        allies_in_range = context.get('ally_units', [])
        
        # Find allies that can attack the target
        attackers = []
        for ally in allies_in_range:
            if self._can_unit_attack_target(ally, primary_target):
                attackers.append(ally)
        
        if len(attackers) < 2:
            return {'success': False, 'error': 'Insufficient attackers for coordination'}
        
        # Apply coordination bonuses
        coordination_bonus = {
            'accuracy_boost': 0.2,
            'damage_boost': 0.15,
            'critical_chance_boost': 0.1
        }
        
        # Store effect for application during combat
        effect_id = f"coordinate_attack_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'coordinate_attack',
            'leader_id': leader.id,
            'target_id': primary_target.id,
            'attackers': [unit.id for unit in attackers],
            'bonuses': coordination_bonus,
            'duration': 10.0,  # seconds
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'attackers_count': len(attackers),
            'target_id': primary_target.id,
            'bonuses_applied': coordination_bonus,
            'effect_id': effect_id
        }
    
    def _execute_formation_command(self, leader: Entity, targets: List[Entity], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Organize allies into optimal formation"""
        allies = context.get('ally_units', [])
        if len(allies) < 2:
            return {'success': False, 'error': 'Not enough allies to form formation'}
        
        leader_transform = leader.get_component(Transform)
        if not leader_transform:
            return {'success': False, 'error': 'Leader has no position'}
        
        # Calculate optimal formation positions
        formation_positions = self._calculate_formation_positions(
            leader_transform.position, len(allies), "defensive_line"
        )
        
        # Apply formation bonuses
        formation_bonus = {
            'defense_boost': 0.15,
            'formation_cohesion': 0.25,
            'mutual_support': True
        }
        
        # Store formation effect
        effect_id = f"formation_command_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'formation_command',
            'leader_id': leader.id,
            'allies': [unit.id for unit in allies],
            'positions': formation_positions,
            'bonuses': formation_bonus,
            'duration': 30.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'allies_affected': len(allies),
            'formation_type': 'defensive_line',
            'positions': formation_positions,
            'bonuses_applied': formation_bonus,
            'effect_id': effect_id
        }
    
    def _execute_tactical_retreat(self, leader: Entity, targets: List[Entity], 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coordinated tactical retreat"""
        allies = context.get('ally_units', [])
        if not allies:
            return {'success': False, 'error': 'No allies to retreat'}
        
        leader_transform = leader.get_component(Transform)
        if not leader_transform:
            return {'success': False, 'error': 'Leader has no position'}
        
        # Calculate retreat positions
        retreat_positions = self._calculate_retreat_positions(
            leader_transform.position, allies, context.get('enemy_units', [])
        )
        
        # Apply retreat bonuses (reduced damage while retreating)
        retreat_bonus = {
            'damage_reduction': 0.3,
            'movement_speed_boost': 0.5,
            'evasion_boost': 0.2
        }
        
        effect_id = f"tactical_retreat_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'tactical_retreat',
            'leader_id': leader.id,
            'allies': [unit.id for unit in allies],
            'retreat_positions': retreat_positions,
            'bonuses': retreat_bonus,
            'duration': 15.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'allies_affected': len(allies),
            'retreat_positions': retreat_positions,
            'bonuses_applied': retreat_bonus,
            'effect_id': effect_id
        }
    
    def _execute_flanking_maneuver(self, leader: Entity, targets: List[Entity], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Position allies for flanking attack"""
        allies = context.get('ally_units', [])
        enemies = context.get('enemy_units', [])
        
        if not allies or not enemies:
            return {'success': False, 'error': 'Insufficient units for flanking'}
        
        # Select primary enemy target for flanking
        primary_enemy = enemies[0]
        enemy_transform = primary_enemy.get_component(Transform)
        if not enemy_transform:
            return {'success': False, 'error': 'Enemy has no position'}
        
        # Calculate flanking positions
        flanking_positions = self._calculate_flanking_positions(
            enemy_transform.position, allies
        )
        
        # Apply flanking bonuses
        flanking_bonus = {
            'damage_boost': 0.25,
            'critical_chance_boost': 0.15,
            'accuracy_boost': 0.1,
            'surprise_attack': True
        }
        
        effect_id = f"flanking_maneuver_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'flanking_maneuver',
            'leader_id': leader.id,
            'allies': [unit.id for unit in allies],
            'target_id': primary_enemy.id,
            'flanking_positions': flanking_positions,
            'bonuses': flanking_bonus,
            'duration': 20.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'allies_affected': len(allies),
            'target_id': primary_enemy.id,
            'flanking_positions': flanking_positions,
            'bonuses_applied': flanking_bonus,
            'effect_id': effect_id
        }
    
    # Battle Master Abilities
    
    def _execute_battle_fury(self, leader: Entity, targets: List[Entity], 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Boost combat effectiveness of nearby allies"""
        allies = context.get('ally_units', [])
        if not allies:
            return {'success': False, 'error': 'No allies in range'}
        
        # Apply battle fury bonuses
        fury_bonus = {
            'damage_boost': 0.3,
            'attack_speed_boost': 0.4,
            'critical_chance_boost': 0.2,
            'fear_immunity': True
        }
        
        effect_id = f"battle_fury_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'battle_fury',
            'leader_id': leader.id,
            'allies': [unit.id for unit in allies],
            'bonuses': fury_bonus,
            'duration': 25.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'allies_affected': len(allies),
            'bonuses_applied': fury_bonus,
            'effect_id': effect_id
        }
    
    def _execute_precision_strike(self, leader: Entity, targets: List[Entity], 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """Guarantee critical hit on next attack"""
        if not targets:
            return {'success': False, 'error': 'No target specified'}
        
        target = targets[0]
        
        # Apply precision strike effect
        precision_bonus = {
            'guaranteed_critical': True,
            'damage_boost': 0.5,
            'armor_penetration_boost': 0.3
        }
        
        effect_id = f"precision_strike_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'precision_strike',
            'leader_id': leader.id,
            'target_id': target.id,
            'bonuses': precision_bonus,
            'duration': 5.0,  # Short duration, one attack
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'target_id': target.id,
            'bonuses_applied': precision_bonus,
            'effect_id': effect_id
        }
    
    def _execute_defensive_stance(self, leader: Entity, targets: List[Entity], 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """Increase defense and damage resistance"""
        allies = context.get('ally_units', [])
        if not allies:
            return {'success': False, 'error': 'No allies in range'}
        
        # Apply defensive bonuses
        defensive_bonus = {
            'defense_boost': 0.4,
            'damage_resistance': 0.25,
            'status_resistance': 0.3,
            'healing_boost': 0.2
        }
        
        effect_id = f"defensive_stance_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'defensive_stance',
            'leader_id': leader.id,
            'allies': [unit.id for unit in allies],
            'bonuses': defensive_bonus,
            'duration': 30.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'allies_affected': len(allies),
            'bonuses_applied': defensive_bonus,
            'effect_id': effect_id
        }
    
    def _execute_counter_attack(self, leader: Entity, targets: List[Entity], 
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """Enable automatic retaliation"""
        allies = context.get('ally_units', [])
        if not allies:
            return {'success': False, 'error': 'No allies in range'}
        
        # Apply counter-attack bonuses
        counter_bonus = {
            'counter_attack_chance': 0.8,
            'counter_damage_boost': 0.2,
            'retaliation_speed': 0.5
        }
        
        effect_id = f"counter_attack_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'counter_attack',
            'leader_id': leader.id,
            'allies': [unit.id for unit in allies],
            'bonuses': counter_bonus,
            'duration': 20.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'allies_affected': len(allies),
            'bonuses_applied': counter_bonus,
            'effect_id': effect_id
        }
    
    # Strategic Genius Abilities
    
    def _execute_predict_movement(self, leader: Entity, targets: List[Entity], 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """Anticipate and counter enemy movements"""
        enemies = context.get('enemy_units', [])
        if not enemies:
            return {'success': False, 'error': 'No enemies to predict'}
        
        # Analyze enemy movement patterns (simplified)
        predicted_positions = {}
        for enemy in enemies:
            enemy_transform = enemy.get_component(Transform)
            if enemy_transform:
                # Simple prediction: assume enemy will move toward closest ally
                predicted_pos = self._predict_enemy_movement(enemy, context.get('ally_units', []))
                predicted_positions[enemy.id] = predicted_pos
        
        # Apply prediction bonuses
        prediction_bonus = {
            'pre_emptive_positioning': True,
            'movement_anticipation': 0.4,
            'counter_preparation': 0.3
        }
        
        effect_id = f"predict_movement_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'predict_movement',
            'leader_id': leader.id,
            'predicted_positions': predicted_positions,
            'bonuses': prediction_bonus,
            'duration': 15.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'enemies_analyzed': len(enemies),
            'predicted_positions': predicted_positions,
            'bonuses_applied': prediction_bonus,
            'effect_id': effect_id
        }
    
    def _execute_adaptive_strategy(self, leader: Entity, targets: List[Entity], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Change tactical approach based on battlefield state"""
        # Analyze current tactical effectiveness
        current_strategy = context.get('current_strategy', 'balanced')
        
        # Determine optimal strategy based on battlefield analysis
        battlefield_score = self._analyze_battlefield_effectiveness(context)
        optimal_strategy = self._determine_optimal_strategy(battlefield_score, context)
        
        # Apply strategy bonuses
        strategy_bonus = {
            'tactical_flexibility': 0.3,
            'adaptation_speed': 0.4,
            'strategic_awareness': 0.5
        }
        
        effect_id = f"adaptive_strategy_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'adaptive_strategy',
            'leader_id': leader.id,
            'old_strategy': current_strategy,
            'new_strategy': optimal_strategy,
            'bonuses': strategy_bonus,
            'duration': 45.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'strategy_change': f"{current_strategy} -> {optimal_strategy}",
            'battlefield_score': battlefield_score,
            'bonuses_applied': strategy_bonus,
            'effect_id': effect_id
        }
    
    def _execute_resource_optimization(self, leader: Entity, targets: List[Entity], 
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Improve resource efficiency for allies"""
        allies = context.get('ally_units', [])
        if not allies:
            return {'success': False, 'error': 'No allies to optimize'}
        
        # Apply resource optimization bonuses
        optimization_bonus = {
            'resource_efficiency': 0.3,
            'ability_cost_reduction': 0.2,
            'resource_generation_boost': 0.25
        }
        
        effect_id = f"resource_optimization_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'resource_optimization',
            'leader_id': leader.id,
            'allies': [unit.id for unit in allies],
            'bonuses': optimization_bonus,
            'duration': 60.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'allies_affected': len(allies),
            'bonuses_applied': optimization_bonus,
            'effect_id': effect_id
        }
    
    def _execute_battlefield_analysis(self, leader: Entity, targets: List[Entity], 
                                    context: Dict[str, Any]) -> Dict[str, Any]:
        """Reveal tactical opportunities and threats"""
        # Perform comprehensive battlefield analysis
        analysis_result = {
            'tactical_opportunities': self._identify_tactical_opportunities(context),
            'threat_assessment': self._assess_threats(context),
            'optimal_positions': self._calculate_optimal_positions(context),
            'strategic_recommendations': self._generate_strategic_recommendations(context)
        }
        
        # Apply analysis bonuses
        analysis_bonus = {
            'situational_awareness': 0.5,
            'tactical_insight': 0.4,
            'strategic_vision': 0.3
        }
        
        effect_id = f"battlefield_analysis_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'battlefield_analysis',
            'leader_id': leader.id,
            'analysis_result': analysis_result,
            'bonuses': analysis_bonus,
            'duration': 30.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'analysis': analysis_result,
            'bonuses_applied': analysis_bonus,
            'effect_id': effect_id
        }
    
    # Inspirational Leader Abilities
    
    def _execute_rally_troops(self, leader: Entity, targets: List[Entity], 
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Restore morale and health to allies"""
        allies = context.get('ally_units', [])
        if not allies:
            return {'success': False, 'error': 'No allies to rally'}
        
        # Apply healing and morale bonuses
        rally_bonus = {
            'health_restoration': 0.3,  # Restore 30% health
            'morale_boost': 0.4,
            'status_cleansing': True,
            'temporary_hp_boost': 0.2
        }
        
        # Actually restore health to allies
        healed_units = []
        for ally in allies:
            attributes = ally.get_component(AttributeStats)
            if attributes and attributes.current_hp < attributes.max_hp:
                healing_amount = int(attributes.max_hp * rally_bonus['health_restoration'])
                attributes.current_hp = min(attributes.max_hp, 
                                          attributes.current_hp + healing_amount)
                healed_units.append(ally.id)
        
        effect_id = f"rally_troops_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'rally_troops',
            'leader_id': leader.id,
            'allies': [unit.id for unit in allies],
            'healed_units': healed_units,
            'bonuses': rally_bonus,
            'duration': 20.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'allies_affected': len(allies),
            'units_healed': len(healed_units),
            'bonuses_applied': rally_bonus,
            'effect_id': effect_id
        }
    
    def _execute_inspiring_presence(self, leader: Entity, targets: List[Entity], 
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """Passive boost to all allied capabilities"""
        allies = context.get('ally_units', [])
        if not allies:
            return {'success': False, 'error': 'No allies in range'}
        
        # Apply inspirational bonuses (passive, ongoing)
        inspiration_bonus = {
            'all_stats_boost': 0.1,
            'fear_immunity': True,
            'morale_sustain': 0.3,
            'leadership_aura': True
        }
        
        effect_id = f"inspiring_presence_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'inspiring_presence',
            'leader_id': leader.id,
            'allies': [unit.id for unit in allies],
            'bonuses': inspiration_bonus,
            'duration': 120.0,  # Long duration passive effect
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'allies_affected': len(allies),
            'bonuses_applied': inspiration_bonus,
            'effect_id': effect_id
        }
    
    def _execute_heroic_charge(self, leader: Entity, targets: List[Entity], 
                             context: Dict[str, Any]) -> Dict[str, Any]:
        """Lead a devastating charge attack"""
        allies = context.get('ally_units', [])
        enemies = context.get('enemy_units', [])
        
        if not allies or not enemies:
            return {'success': False, 'error': 'Insufficient units for charge'}
        
        # Calculate charge bonuses
        charge_bonus = {
            'movement_speed_boost': 1.0,  # Double movement speed
            'charge_damage_boost': 0.5,
            'impact_damage': 0.3,
            'momentum_bonus': True
        }
        
        effect_id = f"heroic_charge_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'heroic_charge',
            'leader_id': leader.id,
            'allies': [unit.id for unit in allies],
            'charge_targets': [unit.id for unit in enemies],
            'bonuses': charge_bonus,
            'duration': 8.0,  # Short, intense effect
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'allies_charging': len(allies),
            'targets': len(enemies),
            'bonuses_applied': charge_bonus,
            'effect_id': effect_id
        }
    
    def _execute_last_stand(self, leader: Entity, targets: List[Entity], 
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Massive combat boost when critically wounded"""
        leader_attributes = leader.get_component(AttributeStats)
        if not leader_attributes:
            return {'success': False, 'error': 'Leader has no health component'}
        
        # Check if leader is actually critically wounded
        health_ratio = leader_attributes.current_hp / leader_attributes.max_hp
        if health_ratio > 0.3:
            return {'success': False, 'error': 'Leader not critically wounded'}
        
        allies = context.get('ally_units', [])
        
        # Apply massive last stand bonuses
        last_stand_bonus = {
            'damage_boost': 1.0,  # Double damage
            'defense_boost': 0.8,
            'critical_chance_boost': 0.5,
            'fear_immunity': True,
            'death_defiance': True,
            'inspire_desperation': 0.6
        }
        
        effect_id = f"last_stand_{leader.id}_{time.time()}"
        self.active_effects[effect_id] = {
            'type': 'last_stand',
            'leader_id': leader.id,
            'allies': [unit.id for unit in allies],
            'leader_health_ratio': health_ratio,
            'bonuses': last_stand_bonus,
            'duration': 30.0,
            'start_time': time.time()
        }
        
        return {
            'success': True,
            'leader_health': f"{health_ratio:.1%}",
            'allies_inspired': len(allies),
            'bonuses_applied': last_stand_bonus,
            'effect_id': effect_id
        }
    
    # Helper Methods
    
    def _can_unit_attack_target(self, attacker: Entity, target: Entity) -> bool:
        """Check if unit can attack target"""
        attack_comp = attacker.get_component(AttackComponent)
        if not attack_comp:
            return False
        
        attacker_transform = attacker.get_component(Transform)
        target_transform = target.get_component(Transform)
        
        if not attacker_transform or not target_transform:
            return False
        
        distance = attacker_transform.position.distance_to(target_transform.position)
        return distance <= attack_comp.get_effective_range()
    
    def _calculate_formation_positions(self, leader_pos: Vector3, unit_count: int, 
                                     formation_type: str) -> List[Tuple[float, float]]:
        """Calculate optimal formation positions"""
        positions = []
        
        if formation_type == "defensive_line":
            # Arrange units in a defensive line behind leader
            for i in range(unit_count):
                offset_x = (i - unit_count // 2) * 2.0
                offset_z = -2.0  # Behind leader
                positions.append((leader_pos.x + offset_x, leader_pos.z + offset_z))
        
        return positions
    
    def _calculate_retreat_positions(self, leader_pos: Vector3, allies: List[Entity], 
                                   enemies: List[Entity]) -> List[Tuple[float, float]]:
        """Calculate safe retreat positions"""
        # Simple retreat: move away from enemies
        retreat_positions = []
        
        # Calculate average enemy position
        enemy_center = Vector3(0, 0, 0)
        enemy_count = 0
        for enemy in enemies:
            enemy_transform = enemy.get_component(Transform)
            if enemy_transform:
                enemy_center = enemy_center + enemy_transform.position
                enemy_count += 1
        
        if enemy_count > 0:
            enemy_center = enemy_center / enemy_count
            
            # Retreat in opposite direction
            retreat_direction = (leader_pos - enemy_center).normalized()
            
            for i, ally in enumerate(allies):
                retreat_offset = retreat_direction * 4.0  # 4 units away
                lateral_offset = (i - len(allies) // 2) * 1.5
                retreat_pos = leader_pos + retreat_offset + Vector3(lateral_offset, 0, 0)
                retreat_positions.append((retreat_pos.x, retreat_pos.z))
        
        return retreat_positions
    
    def _calculate_flanking_positions(self, target_pos: Vector3, 
                                    allies: List[Entity]) -> List[Tuple[float, float]]:
        """Calculate positions for flanking attack"""
        flanking_positions = []
        
        # Arrange allies around target in a circle
        ally_count = len(allies)
        for i in range(ally_count):
            angle = (2 * math.pi * i) / ally_count
            flank_distance = 3.0
            
            flank_x = target_pos.x + math.cos(angle) * flank_distance
            flank_z = target_pos.z + math.sin(angle) * flank_distance
            
            flanking_positions.append((flank_x, flank_z))
        
        return flanking_positions
    
    def _predict_enemy_movement(self, enemy: Entity, allies: List[Entity]) -> Tuple[float, float]:
        """Predict where enemy will move next"""
        enemy_transform = enemy.get_component(Transform)
        if not enemy_transform:
            return (0, 0)
        
        # Simple prediction: enemy will move toward closest ally
        closest_ally = None
        closest_distance = float('inf')
        
        for ally in allies:
            ally_transform = ally.get_component(Transform)
            if ally_transform:
                distance = enemy_transform.position.distance_to(ally_transform.position)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_ally = ally
        
        if closest_ally:
            ally_transform = closest_ally.get_component(Transform)
            # Predict enemy will move halfway toward ally
            predicted_pos = (enemy_transform.position + ally_transform.position) / 2
            return (predicted_pos.x, predicted_pos.z)
        
        return (enemy_transform.position.x, enemy_transform.position.z)
    
    def _analyze_battlefield_effectiveness(self, context: Dict[str, Any]) -> float:
        """Analyze how effective current tactics are"""
        # Simplified effectiveness analysis
        allies = context.get('ally_units', [])
        enemies = context.get('enemy_units', [])
        
        if not allies or not enemies:
            return 0.5
        
        # Compare unit counts and health ratios
        ally_strength = self._calculate_force_strength(allies)
        enemy_strength = self._calculate_force_strength(enemies)
        
        if ally_strength + enemy_strength == 0:
            return 0.5
        
        effectiveness = ally_strength / (ally_strength + enemy_strength)
        return effectiveness
    
    def _calculate_force_strength(self, units: List[Entity]) -> float:
        """Calculate total strength of unit group"""
        total_strength = 0.0
        
        for unit in units:
            attributes = unit.get_component(AttributeStats)
            if attributes:
                health_ratio = attributes.current_hp / attributes.max_hp if attributes.max_hp > 0 else 0
                unit_strength = health_ratio * (attributes.strength + attributes.speed + attributes.fortitude)
                total_strength += unit_strength
        
        return total_strength
    
    def _determine_optimal_strategy(self, battlefield_score: float, 
                                  context: Dict[str, Any]) -> str:
        """Determine optimal strategy based on battlefield analysis"""
        if battlefield_score > 0.7:
            return "aggressive"
        elif battlefield_score < 0.3:
            return "defensive"
        elif context.get('formation_score', 0.5) < 0.4:
            return "regroup"
        else:
            return "balanced"
    
    def _identify_tactical_opportunities(self, context: Dict[str, Any]) -> List[str]:
        """Identify current tactical opportunities"""
        opportunities = []
        
        if context.get('flanking_opportunities', 0) > 0:
            opportunities.append("flanking_attack")
        
        if context.get('formation_score', 0.5) > 0.8:
            opportunities.append("coordinated_advance")
        
        if context.get('allies_low_health', 0) > 0:
            opportunities.append("tactical_healing")
        
        return opportunities
    
    def _assess_threats(self, context: Dict[str, Any]) -> List[str]:
        """Assess current threats"""
        threats = []
        
        if context.get('enemies_in_range', 0) > context.get('allies_in_range', 0):
            threats.append("numerical_disadvantage")
        
        if context.get('formation_score', 0.5) < 0.3:
            threats.append("formation_breakdown")
        
        if context.get('combat_intensity', 0) > 0.8:
            threats.append("heavy_combat")
        
        return threats
    
    def _calculate_optimal_positions(self, context: Dict[str, Any]) -> Dict[str, Tuple[float, float]]:
        """Calculate optimal positions for units"""
        # Simplified optimal positioning
        optimal_positions = {}
        
        allies = context.get('ally_units', [])
        for i, ally in enumerate(allies):
            # Simple positioning: spread out in a defensive formation
            optimal_positions[ally.id] = (i * 2.0, 0.0)
        
        return optimal_positions
    
    def _generate_strategic_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        if context.get('formation_score', 0.5) < 0.5:
            recommendations.append("improve_formation")
        
        if context.get('flanking_opportunities', 0) > 0:
            recommendations.append("execute_flanking")
        
        if context.get('allies_low_health', 0) > 1:
            recommendations.append("prioritize_healing")
        
        return recommendations
    
    def get_active_effects(self, leader_id: Optional[int] = None) -> Dict[str, Dict]:
        """Get currently active leader effects"""
        current_time = time.time()
        active = {}
        
        for effect_id, effect_data in self.active_effects.items():
            # Remove expired effects
            if current_time - effect_data['start_time'] > effect_data['duration']:
                continue
            
            # Filter by leader if specified
            if leader_id is not None and effect_data['leader_id'] != leader_id:
                continue
            
            active[effect_id] = effect_data
        
        # Clean up expired effects
        self.active_effects = active
        
        return active
    
    def cleanup_expired_effects(self):
        """Remove expired effects"""
        current_time = time.time()
        
        expired_effects = []
        for effect_id, effect_data in self.active_effects.items():
            if current_time - effect_data['start_time'] > effect_data['duration']:
                expired_effects.append(effect_id)
        
        for effect_id in expired_effects:
            del self.active_effects[effect_id]