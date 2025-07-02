"""
Combat System

Handles all combat mechanics including damage calculations, status effects,
ability usage, and combat resolution for tactical RPG gameplay.
"""

import asyncio
import math
import random
from typing import Dict, Any, List, Optional, Tuple, Set, Type
from dataclasses import dataclass, field
from enum import Enum

import structlog

from ...core.ecs import System, EntityID, ECSManager, BaseComponent, Entity
from ...core.events import EventBus, GameEvent, EventType
from ...core.math import GridPosition, clamp
from ..components.stats_component import StatsComponent
from ..components.position_component import PositionComponent
from ..components.team_component import TeamComponent
from ..components.equipment_component import EquipmentComponent
from ..components.status_effects_component import StatusEffectsComponent

logger = structlog.get_logger()


class DamageType(str, Enum):
    """Types of damage"""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    SPIRITUAL = "spiritual"
    TRUE = "true"  # Ignores all defenses


class AttackType(str, Enum):
    """Types of attacks"""
    MELEE = "melee"
    RANGED = "ranged"
    SPELL = "spell"
    ABILITY = "ability"


class CombatResult(str, Enum):
    """Combat action results"""
    HIT = "hit"
    MISS = "miss"
    CRITICAL = "critical"
    BLOCKED = "blocked"
    DODGED = "dodged"


@dataclass
class DamageInstance:
    """Single instance of damage"""
    amount: float
    damage_type: DamageType
    source_entity: EntityID
    target_entity: EntityID
    attack_type: AttackType
    is_critical: bool = False
    penetration: float = 0.0  # Defense penetration percentage
    
    def calculate_final_damage(self, target_defense: float) -> float:
        """Calculate final damage after defense"""
        if self.damage_type == DamageType.TRUE:
            return self.amount
        
        # Apply penetration
        effective_defense = target_defense * (1.0 - self.penetration)
        
        # Hybrid damage formula: prevents zero damage while maintaining tactical depth
        # Formula: damage * (100 / (100 + effective_defense)) + damage * 0.1
        damage_reduction = 100.0 / (100.0 + effective_defense)
        guaranteed_damage = self.amount * 0.1  # 10% guaranteed damage
        
        return (self.amount * damage_reduction) + guaranteed_damage


@dataclass
class CombatAction:
    """Combat action data"""
    attacker: EntityID
    target: EntityID
    action_type: AttackType
    base_damage: float
    damage_type: DamageType
    accuracy: float
    critical_chance: float
    range_value: int
    area_effect: bool = False
    area_radius: int = 0
    mp_cost: int = 0
    ability_id: Optional[str] = None


@dataclass
class CombatOutcome:
    """Result of a combat action"""
    action: CombatAction
    result: CombatResult
    damage_dealt: float
    targets_hit: List[EntityID]
    effects_applied: List[str] = field(default_factory=list)
    mp_consumed: int = 0
    experience_gained: int = 0


class CombatSystem(System):
    """Main combat system"""
    
    def __init__(self, ecs: ECSManager, event_bus: EventBus):
        super().__init__()
        self.ecs = ecs
        self.event_bus = event_bus
        self.execution_order = 30  # After movement, before AI
        
        # Combat configuration
        self.base_hit_chance = 0.85
        self.base_critical_chance = 0.05
        self.critical_damage_multiplier = 1.5
        self.height_advantage_bonus = 0.1
        self.flanking_damage_bonus = 0.25
        
        # Status effect durations
        self.status_effect_durations = {
            "poison": 3,
            "burn": 2,
            "freeze": 1,
            "stun": 1,
            "buff_attack": 3,
            "buff_defense": 3
        }
        
        # Damage type effectiveness
        self.damage_effectiveness = {
            DamageType.PHYSICAL: {
                "heavily_armored": 0.7,
                "lightly_armored": 1.2,
                "magical_shield": 1.0
            },
            DamageType.MAGICAL: {
                "heavily_armored": 1.2,
                "lightly_armored": 0.8,
                "magical_shield": 0.6
            },
            DamageType.SPIRITUAL: {
                "heavily_armored": 1.0,
                "lightly_armored": 1.0,
                "magical_shield": 1.3
            }
        }
        
        logger.info("Combat system initialized")
    
    def get_required_components(self) -> Set[Type[BaseComponent]]:
        """Return required components for this system"""
        return {StatsComponent, PositionComponent, TeamComponent}
    
    def update(self, delta_time: float, entities: List[Entity]):
        """Update combat system for all entities"""
        # This is the required abstract method signature
        # The actual combat logic is handled separately by session-specific methods
        pass
    
    async def update_for_session(self, session_id: str, delta_time: float):
        """Update combat system (process status effects)"""
        entities_with_status = self.get_entities_with_components(
            session_id, StatusEffectsComponent
        )
        
        for entity_id in entities_with_status:
            await self._process_status_effects(session_id, entity_id, delta_time)
    
    async def execute_attack(self, session_id: str, action_data: Dict[str, Any]) -> bool:
        """Execute an attack action"""
        try:
            # Parse action data
            attacker_id = EntityID(action_data["attacker_id"])
            target_id = EntityID(action_data["target_id"])
            attack_type = AttackType(action_data.get("attack_type", "melee"))
            ability_id = action_data.get("ability_id")
            
            # Validate attack
            if not await self._validate_attack(session_id, attacker_id, target_id, attack_type):
                return False
            
            # Create combat action
            combat_action = await self._create_combat_action(
                session_id, attacker_id, target_id, attack_type, ability_id
            )
            
            if not combat_action:
                return False
            
            # Execute combat
            outcome = await self._execute_combat_action(session_id, combat_action)
            
            # Apply results
            await self._apply_combat_outcome(session_id, outcome)
            
            # Emit combat event
            await self.event_bus.emit(GameEvent(
                type=EventType.UNIT_ATTACKED,
                session_id=session_id,
                data={
                    "attacker": str(attacker_id),
                    "target": str(target_id),
                    "outcome": outcome.__dict__
                }
            ))
            
            return True
            
        except Exception as e:
            logger.error("Attack execution failed", session_id=session_id, error=str(e))
            return False
    
    async def validate_attack(self, session_id: str, action_data: Dict[str, Any]) -> bool:
        """Validate if an attack can be executed"""
        try:
            attacker_id = EntityID(action_data["attacker_id"])
            target_id = EntityID(action_data["target_id"])
            attack_type = AttackType(action_data.get("attack_type", "melee"))
            
            return await self._validate_attack(session_id, attacker_id, target_id, attack_type)
        except Exception:
            return False
    
    async def _validate_attack(self, session_id: str, attacker_id: EntityID, 
                              target_id: EntityID, attack_type: AttackType) -> bool:
        """Internal attack validation"""
        # Check if entities exist
        attacker_stats = self.ecs.get_component(attacker_id, StatsComponent)
        target_stats = self.ecs.get_component(target_id, StatsComponent)
        
        if not attacker_stats or not target_stats:
            return False
        
        # Check if attacker is alive
        if attacker_stats.current_hp <= 0:
            return False
        
        # Check if target is alive
        if target_stats.current_hp <= 0:
            return False
        
        # Check teams (can't attack same team unless friendly fire is enabled)
        attacker_team = self.ecs.get_component(attacker_id, TeamComponent)
        target_team = self.ecs.get_component(target_id, TeamComponent)
        
        if attacker_team and target_team:
            if attacker_team.team == target_team.team:
                return False  # No friendly fire for now
        
        # Check range
        attacker_pos = self.ecs.get_component(attacker_id, PositionComponent)
        target_pos = self.ecs.get_component(target_id, PositionComponent)
        
        if attacker_pos and target_pos:
            distance = attacker_pos.position.manhattan_distance(target_pos.position)
            
            if attack_type == AttackType.MELEE:
                max_range = attacker_stats.attributes.get("melee_range", 1)
            else:
                max_range = attacker_stats.attributes.get("ranged_range", 3)
            
            if distance > max_range:
                return False
        
        # Check MP for abilities
        ability_cost = 0
        if attack_type in [AttackType.SPELL, AttackType.ABILITY]:
            ability_cost = 2  # Default ability cost
        
        if attacker_stats.current_mp < ability_cost:
            return False
        
        return True
    
    async def _create_combat_action(self, session_id: str, attacker_id: EntityID, 
                                   target_id: EntityID, attack_type: AttackType,
                                   ability_id: Optional[str]) -> Optional[CombatAction]:
        """Create combat action from entities"""
        attacker_stats = self.ecs.get_component(attacker_id, StatsComponent)
        if not attacker_stats:
            return None
        
        # Determine base damage and damage type
        if attack_type == AttackType.MELEE:
            base_damage = attacker_stats.attributes.get("physical_attack", 10)
            damage_type = DamageType.PHYSICAL
            accuracy = 0.9
            critical_chance = 0.1
            range_value = attacker_stats.attributes.get("melee_range", 1)
        
        elif attack_type == AttackType.RANGED:
            base_damage = attacker_stats.attributes.get("ranged_attack", 8)
            damage_type = DamageType.PHYSICAL
            accuracy = 0.8
            critical_chance = 0.15
            range_value = attacker_stats.attributes.get("ranged_range", 3)
        
        elif attack_type == AttackType.SPELL:
            base_damage = attacker_stats.attributes.get("magical_attack", 12)
            damage_type = DamageType.MAGICAL
            accuracy = 0.85
            critical_chance = 0.08
            range_value = attacker_stats.attributes.get("spell_range", 4)
        
        else:  # ABILITY
            base_damage = attacker_stats.attributes.get("ability_power", 15)
            damage_type = DamageType.SPIRITUAL
            accuracy = 0.9
            critical_chance = 0.12
            range_value = attacker_stats.attributes.get("ability_range", 2)
        
        # Apply equipment bonuses
        equipment = self.ecs.get_component(attacker_id, EquipmentComponent)
        if equipment:
            base_damage *= equipment.get_damage_multiplier()
            accuracy += equipment.get_accuracy_bonus()
            critical_chance += equipment.get_critical_bonus()
        
        return CombatAction(
            attacker=attacker_id,
            target=target_id,
            action_type=attack_type,
            base_damage=base_damage,
            damage_type=damage_type,
            accuracy=clamp(accuracy, 0.05, 0.95),
            critical_chance=clamp(critical_chance, 0.0, 0.5),
            range_value=range_value,
            mp_cost=2 if attack_type in [AttackType.SPELL, AttackType.ABILITY] else 0,
            ability_id=ability_id
        )
    
    async def _execute_combat_action(self, session_id: str, action: CombatAction) -> CombatOutcome:
        """Execute the combat action and determine outcome"""
        outcome = CombatOutcome(
            action=action,
            result=CombatResult.MISS,
            damage_dealt=0.0,
            targets_hit=[],
            mp_consumed=action.mp_cost
        )
        
        # Calculate accuracy modifiers
        final_accuracy = await self._calculate_final_accuracy(session_id, action)
        
        # Roll for hit
        hit_roll = random.random()
        if hit_roll > final_accuracy:
            outcome.result = CombatResult.MISS
            return outcome
        
        # Hit! Now calculate damage
        outcome.result = CombatResult.HIT
        outcome.targets_hit.append(action.target)
        
        # Roll for critical
        crit_roll = random.random()
        is_critical = crit_roll <= action.critical_chance
        
        if is_critical:
            outcome.result = CombatResult.CRITICAL
        
        # Calculate damage
        damage_dealt = await self._calculate_damage(
            session_id, action, is_critical
        )
        
        outcome.damage_dealt = damage_dealt
        
        # Handle area effects
        if action.area_effect:
            additional_targets = await self._get_area_targets(
                session_id, action.target, action.area_radius
            )
            
            for target in additional_targets:
                if target != action.target:
                    area_damage = damage_dealt * 0.7  # Reduced area damage
                    outcome.targets_hit.append(target)
                    # Apply area damage (simplified)
        
        return outcome
    
    async def _calculate_final_accuracy(self, session_id: str, action: CombatAction) -> float:
        """Calculate final accuracy with all modifiers"""
        base_accuracy = action.accuracy
        
        # Get attacker and target positions
        attacker_pos = self.ecs.get_component(action.attacker, PositionComponent)
        target_pos = self.ecs.get_component(action.target, PositionComponent)
        
        if not attacker_pos or not target_pos:
            return base_accuracy
        
        # Height advantage bonus
        height_diff = attacker_pos.height - target_pos.height
        if height_diff > 0:
            base_accuracy += self.height_advantage_bonus
        
        # Range penalty for ranged attacks
        if action.action_type == AttackType.RANGED:
            distance = attacker_pos.position.manhattan_distance(target_pos.position)
            if distance > action.range_value * 0.7:  # Long range penalty
                base_accuracy -= 0.1
        
        # Status effect modifiers
        attacker_status = self.ecs.get_component(action.attacker, StatusEffectsComponent)
        if attacker_status:
            if "blind" in attacker_status.active_effects:
                base_accuracy -= 0.3
            elif "focused" in attacker_status.active_effects:
                base_accuracy += 0.15
        
        target_status = self.ecs.get_component(action.target, StatusEffectsComponent)
        if target_status:
            if "dodge_boost" in target_status.active_effects:
                base_accuracy -= 0.2
            elif "stunned" in target_status.active_effects:
                base_accuracy += 0.25
        
        return clamp(base_accuracy, 0.05, 0.95)
    
    async def _calculate_damage(self, session_id: str, action: CombatAction, 
                               is_critical: bool) -> float:
        """Calculate final damage"""
        base_damage = action.base_damage
        
        # Critical hit multiplier
        if is_critical:
            base_damage *= self.critical_damage_multiplier
        
        # Damage variance (±10%)
        variance = random.uniform(0.9, 1.1)
        base_damage *= variance
        
        # Get target defense
        target_stats = self.ecs.get_component(action.target, StatsComponent)
        if not target_stats:
            return base_damage
        
        # Select appropriate defense
        if action.damage_type == DamageType.PHYSICAL:
            defense = target_stats.attributes.get("physical_defense", 0)
        elif action.damage_type == DamageType.MAGICAL:
            defense = target_stats.attributes.get("magical_defense", 0)
        elif action.damage_type == DamageType.SPIRITUAL:
            defense = target_stats.attributes.get("spiritual_defense", 0)
        else:  # TRUE damage
            defense = 0
        
        # Apply equipment defense bonuses
        target_equipment = self.ecs.get_component(action.target, EquipmentComponent)
        if target_equipment:
            defense += target_equipment.get_defense_bonus(action.damage_type)
        
        # Check for flanking
        is_flanking = await self._check_flanking(session_id, action.attacker, action.target)
        if is_flanking:
            base_damage *= (1.0 + self.flanking_damage_bonus)
            defense *= 0.8  # Reduced defense when flanked
        
        # Create damage instance and calculate final damage
        damage_instance = DamageInstance(
            amount=base_damage,
            damage_type=action.damage_type,
            source_entity=action.attacker,
            target_entity=action.target,
            attack_type=action.action_type,
            is_critical=is_critical,
            penetration=0.0  # Could be modified by abilities/equipment
        )
        
        return damage_instance.calculate_final_damage(defense)
    
    async def _check_flanking(self, session_id: str, attacker_id: EntityID, 
                             target_id: EntityID) -> bool:
        """Check if attacker is flanking target"""
        # Simplified flanking check - would need facing direction in real implementation
        # For now, check if attacker is adjacent to target from side/back
        
        attacker_pos = self.ecs.get_component(attacker_id, PositionComponent)
        target_pos = self.ecs.get_component(target_id, PositionComponent)
        
        if not attacker_pos or not target_pos:
            return False
        
        # Count enemies adjacent to target
        adjacent_enemies = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                check_pos = GridPosition(
                    target_pos.position.x + dx,
                    target_pos.position.y + dy
                )
                
                # Check if there's an enemy at this position
                # This would need battlefield integration to check occupancy
                # For now, simplified check
                if (check_pos.x == attacker_pos.position.x and 
                    check_pos.y == attacker_pos.position.y):
                    adjacent_enemies += 1
        
        # Flanking if surrounded by multiple enemies
        return adjacent_enemies >= 2
    
    async def _get_area_targets(self, session_id: str, center_target: EntityID, 
                               radius: int) -> List[EntityID]:
        """Get targets in area effect radius"""
        targets = []
        center_pos = self.ecs.get_component(center_target, PositionComponent)
        
        if not center_pos:
            return targets
        
        # Get all entities with position components
        entities_with_pos = self.get_entities_with_components(session_id, PositionComponent)
        
        for entity_id in entities_with_pos:
            if entity_id == center_target:
                continue
            
            entity_pos = self.ecs.get_component(entity_id, PositionComponent)
            if entity_pos:
                distance = center_pos.position.manhattan_distance(entity_pos.position)
                if distance <= radius:
                    targets.append(entity_id)
        
        return targets
    
    async def _apply_combat_outcome(self, session_id: str, outcome: CombatOutcome):
        """Apply the results of combat"""
        # Consume MP from attacker
        if outcome.mp_consumed > 0:
            attacker_stats = self.ecs.get_component(outcome.action.attacker, StatsComponent)
            if attacker_stats:
                attacker_stats.current_mp = max(0, attacker_stats.current_mp - outcome.mp_consumed)
        
        # Apply damage to all targets
        for target_id in outcome.targets_hit:
            target_stats = self.ecs.get_component(target_id, StatsComponent)
            if target_stats:
                # Calculate damage to this specific target
                damage = outcome.damage_dealt
                if target_id != outcome.action.target:
                    damage *= 0.7  # Reduced area damage
                
                # Apply damage
                target_stats.current_hp = max(0, target_stats.current_hp - damage)
                
                # Check for death
                if target_stats.current_hp <= 0:
                    await self._handle_unit_death(session_id, target_id)
        
        # Apply status effects (if any)
        for effect in outcome.effects_applied:
            for target_id in outcome.targets_hit:
                await self._apply_status_effect(session_id, target_id, effect)
    
    async def _handle_unit_death(self, session_id: str, unit_id: EntityID):
        """Handle unit death"""
        # Emit death event
        await self.event_bus.emit(GameEvent(
            type=EventType.UNIT_DIED,
            session_id=session_id,
            data={"unit_id": str(unit_id)}
        ))
        
        # Remove from battlefield (would need battlefield integration)
        # For now, just mark as inactive
        unit_stats = self.ecs.get_component(unit_id, StatsComponent)
        if unit_stats:
            unit_stats.alive = False
        
        logger.info("Unit died", session_id=session_id, unit_id=str(unit_id))
    
    async def _apply_status_effect(self, session_id: str, target_id: EntityID, effect: str):
        """Apply status effect to target"""
        status_component = self.ecs.get_component(target_id, StatusEffectsComponent)
        if not status_component:
            status_component = StatusEffectsComponent()
            self.ecs.add_component(target_id, status_component)
        
        duration = self.status_effect_durations.get(effect, 1)
        status_component.add_effect(effect, duration)
        
        logger.debug("Status effect applied", 
                    session_id=session_id, 
                    target=str(target_id), 
                    effect=effect)
    
    async def _process_status_effects(self, session_id: str, entity_id: EntityID, delta_time: float):
        """Process status effects for an entity"""
        status_component = self.ecs.get_component(entity_id, StatusEffectsComponent)
        if not status_component:
            return
        
        effects_to_remove = []
        
        # Process each active effect
        for effect, remaining_duration in status_component.active_effects.items():
            new_duration = remaining_duration - delta_time
            
            if new_duration <= 0:
                effects_to_remove.append(effect)
            else:
                status_component.active_effects[effect] = new_duration
            
            # Apply per-turn effects
            await self._apply_status_effect_tick(session_id, entity_id, effect)
        
        # Remove expired effects
        for effect in effects_to_remove:
            status_component.remove_effect(effect)
    
    async def _apply_status_effect_tick(self, session_id: str, entity_id: EntityID, effect: str):
        """Apply per-turn status effect"""
        entity_stats = self.ecs.get_component(entity_id, StatsComponent)
        if not entity_stats:
            return
        
        if effect == "poison":
            # Poison deals damage over time
            poison_damage = entity_stats.max_hp * 0.05  # 5% max HP per turn
            entity_stats.current_hp = max(0, entity_stats.current_hp - poison_damage)
            
            if entity_stats.current_hp <= 0:
                await self._handle_unit_death(session_id, entity_id)
        
        elif effect == "burn":
            # Burn deals more damage but shorter duration
            burn_damage = entity_stats.max_hp * 0.08
            entity_stats.current_hp = max(0, entity_stats.current_hp - burn_damage)
            
            if entity_stats.current_hp <= 0:
                await self._handle_unit_death(session_id, entity_id)
        
        # Other effects like buffs, debuffs are handled during combat calculations
    
    def calculate_experience_gain(self, attacker_level: int, target_level: int, 
                                 damage_dealt: float, target_max_hp: float) -> int:
        """Calculate experience gained from combat"""
        base_exp = 10
        level_diff_bonus = max(0, target_level - attacker_level + 1)
        damage_ratio = min(1.0, damage_dealt / target_max_hp)
        
        total_exp = int(base_exp * (1 + level_diff_bonus * 0.2) * damage_ratio)
        return max(1, total_exp)
    
    async def get_combat_preview(self, session_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get preview of combat action without executing it"""
        try:
            attacker_id = EntityID(action_data["attacker_id"])
            target_id = EntityID(action_data["target_id"])
            attack_type = AttackType(action_data.get("attack_type", "melee"))
            
            # Create combat action
            action = await self._create_combat_action(
                session_id, attacker_id, target_id, attack_type, None
            )
            
            if not action:
                return {"error": "Invalid combat action"}
            
            # Calculate expected damage range
            min_damage = action.base_damage * 0.9
            max_damage = action.base_damage * 1.1
            crit_damage = max_damage * self.critical_damage_multiplier
            
            # Get target defense for damage calculation
            target_stats = self.ecs.get_component(target_id, StatsComponent)
            if target_stats:
                if action.damage_type == DamageType.PHYSICAL:
                    defense = target_stats.attributes.get("physical_defense", 0)
                elif action.damage_type == DamageType.MAGICAL:
                    defense = target_stats.attributes.get("magical_defense", 0)
                else:
                    defense = target_stats.attributes.get("spiritual_defense", 0)
                
                # Apply defense formula
                min_final = (min_damage * (100 / (100 + defense))) + (min_damage * 0.1)
                max_final = (max_damage * (100 / (100 + defense))) + (max_damage * 0.1)
                crit_final = (crit_damage * (100 / (100 + defense))) + (crit_damage * 0.1)
            else:
                min_final = min_damage
                max_final = max_damage
                crit_final = crit_damage
            
            accuracy = await self._calculate_final_accuracy(session_id, action)
            
            return {
                "accuracy": accuracy,
                "critical_chance": action.critical_chance,
                "damage_range": {
                    "min": round(min_final, 1),
                    "max": round(max_final, 1),
                    "critical": round(crit_final, 1)
                },
                "mp_cost": action.mp_cost,
                "can_execute": await self._validate_attack(session_id, attacker_id, target_id, attack_type)
            }
            
        except Exception as e:
            logger.error("Combat preview failed", error=str(e))
            return {"error": "Preview calculation failed"}
    
    def get_combat_stats(self) -> Dict[str, Any]:
        """Get combat system statistics"""
        return {
            "system_name": "CombatSystem",
            "base_hit_chance": self.base_hit_chance,
            "base_critical_chance": self.base_critical_chance,
            "critical_multiplier": self.critical_damage_multiplier,
            "flanking_bonus": self.flanking_damage_bonus,
            "status_effects_count": len(self.status_effect_durations)
        }