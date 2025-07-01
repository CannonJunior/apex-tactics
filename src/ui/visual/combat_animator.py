"""
Combat Animation Framework

Visual animation system for combat actions, effects, and unit movements.
"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
import time
import math

try:
    from ursina import Entity, Vec3, color, destroy, scene, Animation, Sequence, Func
    from ursina import camera, lerp, curve
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from core.math.vector import Vector3, Vector2Int
from core.ecs.entity import Entity as GameEntity


class AnimationType(Enum):
    """Types of combat animations"""
    MOVEMENT = "movement"
    ATTACK = "attack"
    DAMAGE = "damage"
    HEAL = "heal"
    ABILITY = "ability"
    DEATH = "death"
    LEVEL_UP = "level_up"
    EQUIPMENT_CHANGE = "equipment_change"


@dataclass
class AnimationEvent:
    """Data for a single animation event"""
    animation_type: AnimationType
    target_entity: GameEntity
    duration: float
    start_time: float
    parameters: Dict[str, Any]
    callback: Optional[Callable] = None


class CombatAnimator:
    """
    Combat animation system for visual feedback during battles.
    
    Manages complex animation sequences, effects, and visual feedback
    for all combat-related actions in the tactical RPG.
    """
    
    def __init__(self, tile_size: float = 1.0):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for CombatAnimator")
        
        self.tile_size = tile_size
        
        # Animation queue and state
        self.animation_queue: List[AnimationEvent] = []
        self.active_animations: Dict[str, AnimationEvent] = {}
        self.animation_id_counter = 0
        
        # Visual entities for animations
        self.unit_entities: Dict[int, Entity] = {}  # game_entity_id -> visual_entity
        self.effect_entities: List[Entity] = []
        self.projectile_entities: List[Entity] = []
        
        # Animation configuration
        self.animation_speeds = {
            AnimationType.MOVEMENT: 1.0,
            AnimationType.ATTACK: 1.5,
            AnimationType.DAMAGE: 2.0,
            AnimationType.HEAL: 1.2,
            AnimationType.ABILITY: 1.0,
            AnimationType.DEATH: 0.8,
            AnimationType.LEVEL_UP: 1.5
        }
        
        # Camera animation state
        self.camera_follow_target: Optional[Entity] = None
        self.camera_shake_intensity = 0.0
        self.camera_shake_duration = 0.0
        self.camera_original_position = None
        
    def register_unit_entity(self, game_entity: GameEntity, visual_entity: Entity):
        """Register a visual entity for a game unit"""
        self.unit_entities[game_entity.id] = visual_entity
    
    def unregister_unit_entity(self, game_entity: GameEntity):
        """Unregister a visual entity for a game unit"""
        if game_entity.id in self.unit_entities:
            del self.unit_entities[game_entity.id]
    
    def update(self, delta_time: float):
        """Update all active animations"""
        current_time = time.time()
        
        # Process animation queue
        self._process_animation_queue(current_time)
        
        # Update active animations
        self._update_active_animations(current_time, delta_time)
        
        # Update camera effects
        self._update_camera_effects(delta_time)
        
        # Update visual effects
        self._update_visual_effects(delta_time)
    
    def _process_animation_queue(self, current_time: float):
        """Process queued animations and start them if ready"""
        animations_to_start = []
        
        for animation in self.animation_queue:
            if current_time >= animation.start_time:
                animations_to_start.append(animation)
        
        for animation in animations_to_start:
            self._start_animation(animation)
            self.animation_queue.remove(animation)
    
    def _start_animation(self, animation_event: AnimationEvent):
        """Start a specific animation"""
        animation_id = f"{animation_event.animation_type.value}_{self.animation_id_counter}"
        self.animation_id_counter += 1
        
        self.active_animations[animation_id] = animation_event
        
        # Execute the appropriate animation based on type
        if animation_event.animation_type == AnimationType.MOVEMENT:
            self._animate_movement(animation_id, animation_event)
        elif animation_event.animation_type == AnimationType.ATTACK:
            self._animate_attack(animation_id, animation_event)
        elif animation_event.animation_type == AnimationType.DAMAGE:
            self._animate_damage(animation_id, animation_event)
        elif animation_event.animation_type == AnimationType.HEAL:
            self._animate_heal(animation_id, animation_event)
        elif animation_event.animation_type == AnimationType.ABILITY:
            self._animate_ability(animation_id, animation_event)
        elif animation_event.animation_type == AnimationType.DEATH:
            self._animate_death(animation_id, animation_event)
        elif animation_event.animation_type == AnimationType.LEVEL_UP:
            self._animate_level_up(animation_id, animation_event)
    
    def _update_active_animations(self, current_time: float, delta_time: float):
        """Update progress of active animations"""
        completed_animations = []
        
        for animation_id, animation_event in self.active_animations.items():
            elapsed = current_time - animation_event.start_time
            
            if elapsed >= animation_event.duration:
                completed_animations.append(animation_id)
                
                # Execute callback if provided
                if animation_event.callback:
                    animation_event.callback()
        
        # Remove completed animations
        for animation_id in completed_animations:
            del self.active_animations[animation_id]
    
    # Animation implementations
    
    def _animate_movement(self, animation_id: str, animation_event: AnimationEvent):
        """Animate unit movement"""
        visual_entity = self.unit_entities.get(animation_event.target_entity.id)
        if not visual_entity:
            return
        
        target_position = animation_event.parameters.get('target_position')
        if not target_position:
            return
        
        # Convert to Ursina Vec3
        target_vec3 = Vec3(target_position.x, target_position.y, target_position.z)
        
        # Create smooth movement animation
        visual_entity.animate_position(
            target_vec3,
            duration=animation_event.duration,
            curve=curve.out_expo
        )
        
        # Add dust cloud effect
        self._create_movement_effect(visual_entity.position, target_vec3)
    
    def _animate_attack(self, animation_id: str, animation_event: AnimationEvent):
        """Animate attack action"""
        attacker_entity = self.unit_entities.get(animation_event.target_entity.id)
        target_entity_id = animation_event.parameters.get('target_entity_id')
        target_entity = self.unit_entities.get(target_entity_id) if target_entity_id else None
        
        if not attacker_entity:
            return
        
        attack_type = animation_event.parameters.get('attack_type', 'melee')
        
        if attack_type == 'melee':
            self._animate_melee_attack(attacker_entity, target_entity, animation_event.duration)
        elif attack_type == 'ranged':
            self._animate_ranged_attack(attacker_entity, target_entity, animation_event.duration)
        elif attack_type == 'spell':
            self._animate_spell_attack(attacker_entity, target_entity, animation_event.duration)
    
    def _animate_melee_attack(self, attacker: Entity, target: Optional[Entity], duration: float):
        """Animate melee attack"""
        if not target:
            return
        
        original_position = attacker.position
        
        # Move toward target
        direction = (target.position - attacker.position).normalized()
        attack_position = target.position - direction * 0.5
        
        # Attack sequence: move forward, pause, move back
        sequence = Sequence(
            Func(attacker.animate_position, attack_position, duration * 0.3, curve.out_quad),
            Func(self._create_impact_effect, target.position),
            Func(self._shake_camera, 0.3, 0.1),
            Func(attacker.animate_position, original_position, duration * 0.3, curve.in_quad)
        )
        
        sequence.start()
    
    def _animate_ranged_attack(self, attacker: Entity, target: Optional[Entity], duration: float):
        """Animate ranged attack with projectile"""
        if not target:
            return
        
        # Create projectile
        projectile = Entity(
            model='cube',
            scale=0.1,
            position=attacker.position + Vec3(0, 0.5, 0),
            color=color.yellow
        )
        
        self.projectile_entities.append(projectile)
        
        # Animate projectile to target
        projectile.animate_position(
            target.position + Vec3(0, 0.5, 0),
            duration=duration * 0.7,
            curve=curve.linear
        )
        
        # Create impact effect when projectile reaches target
        def create_impact():
            self._create_impact_effect(target.position)
            destroy(projectile)
            if projectile in self.projectile_entities:
                self.projectile_entities.remove(projectile)
        
        # Schedule impact effect
        sequence = Sequence(
            duration * 0.7,
            Func(create_impact)
        )
        sequence.start()
    
    def _animate_spell_attack(self, caster: Entity, target: Optional[Entity], duration: float):
        """Animate spell/magical attack"""
        if not target:
            return
        
        # Create magical effect at caster
        self._create_spell_effect(caster.position, color.blue, duration * 0.5)
        
        # Create spell projectile or area effect
        spell_type = "projectile"  # Could be parameter
        
        if spell_type == "projectile":
            # Similar to ranged but with magical effects
            self._animate_ranged_attack(caster, target, duration)
        else:
            # Area effect spell
            self._create_area_spell_effect(target.position, duration)
    
    def _animate_damage(self, animation_id: str, animation_event: AnimationEvent):
        """Animate damage taken"""
        visual_entity = self.unit_entities.get(animation_event.target_entity.id)
        if not visual_entity:
            return
        
        damage_amount = animation_event.parameters.get('damage_amount', 0)
        damage_type = animation_event.parameters.get('damage_type', 'physical')
        
        # Screen shake for large damage
        if damage_amount > 20:
            self._shake_camera(0.5, 0.2)
        
        # Entity shake/flash
        original_color = visual_entity.color
        
        # Flash red for damage
        visual_entity.color = color.red
        visual_entity.animate_color(original_color, duration=animation_event.duration)
        
        # Shake animation
        original_position = visual_entity.position
        shake_sequence = Sequence()
        
        for i in range(5):
            offset = Vec3(
                (i % 2 - 0.5) * 0.1,
                0,
                ((i + 1) % 2 - 0.5) * 0.1
            )
            shake_sequence.append(Func(setattr, visual_entity, 'position', original_position + offset))
            shake_sequence.append(animation_event.duration / 10)
        
        shake_sequence.append(Func(setattr, visual_entity, 'position', original_position))
        shake_sequence.start()
        
        # Create damage number popup
        self._create_damage_number(visual_entity.position, damage_amount, damage_type)
    
    def _animate_heal(self, animation_id: str, animation_event: AnimationEvent):
        """Animate healing effect"""
        visual_entity = self.unit_entities.get(animation_event.target_entity.id)
        if not visual_entity:
            return
        
        heal_amount = animation_event.parameters.get('heal_amount', 0)
        
        # Green glow effect
        original_color = visual_entity.color
        visual_entity.color = color.green
        visual_entity.animate_color(original_color, duration=animation_event.duration)
        
        # Healing particles
        self._create_heal_effect(visual_entity.position, animation_event.duration)
        
        # Create heal number popup
        self._create_heal_number(visual_entity.position, heal_amount)
    
    def _animate_ability(self, animation_id: str, animation_event: AnimationEvent):
        """Animate ability usage"""
        visual_entity = self.unit_entities.get(animation_event.target_entity.id)
        if not visual_entity:
            return
        
        ability_type = animation_event.parameters.get('ability_type', 'generic')
        area_positions = animation_event.parameters.get('area_positions', [])
        
        # Create ability-specific effects
        if ability_type == 'area_heal':
            for pos in area_positions:
                self._create_heal_effect(Vec3(pos.x, pos.y, pos.z), animation_event.duration)
        elif ability_type == 'area_damage':
            for pos in area_positions:
                self._create_explosion_effect(Vec3(pos.x, pos.y, pos.z), animation_event.duration)
        else:
            # Generic ability effect
            self._create_spell_effect(visual_entity.position, color.purple, animation_event.duration)
    
    def _animate_death(self, animation_id: str, animation_event: AnimationEvent):
        """Animate unit death"""
        visual_entity = self.unit_entities.get(animation_event.target_entity.id)
        if not visual_entity:
            return
        
        # Death animation: fall and fade
        death_sequence = Sequence(
            Func(visual_entity.animate_rotation, Vec3(90, 0, 0), animation_event.duration * 0.7),
            Func(visual_entity.animate_color, color.Color(0.5, 0.5, 0.5, 0.3), animation_event.duration)
        )
        death_sequence.start()
        
        # Create death effect
        self._create_death_effect(visual_entity.position)
    
    def _animate_level_up(self, animation_id: str, animation_event: AnimationEvent):
        """Animate level up effect"""
        visual_entity = self.unit_entities.get(animation_event.target_entity.id)
        if not visual_entity:
            return
        
        # Golden glow and upward particles
        original_color = visual_entity.color
        visual_entity.color = color.gold
        visual_entity.animate_color(original_color, duration=animation_event.duration)
        
        # Level up effect
        self._create_level_up_effect(visual_entity.position, animation_event.duration)
    
    # Effect creation methods
    
    def _create_movement_effect(self, start_pos: Vec3, end_pos: Vec3):
        """Create dust cloud effect for movement"""
        dust_effect = Entity(
            model='cube',
            scale=0.3,
            position=start_pos,
            color=color.Color(0.8, 0.7, 0.6, 0.5)
        )
        
        self.effect_entities.append(dust_effect)
        
        # Animate and destroy
        dust_effect.animate_scale(0, duration=1.0)
        dust_effect.animate_color(color.Color(0.8, 0.7, 0.6, 0), duration=1.0)
        
        def cleanup():
            destroy(dust_effect)
            if dust_effect in self.effect_entities:
                self.effect_entities.remove(dust_effect)
        
        sequence = Sequence(1.0, Func(cleanup))
        sequence.start()
    
    def _create_impact_effect(self, position: Vec3):
        """Create impact effect at position"""
        impact = Entity(
            model='cube',
            scale=0.5,
            position=position,
            color=color.white
        )
        
        self.effect_entities.append(impact)
        
        # Flash and disappear
        impact.animate_scale(0.1, duration=0.2)
        impact.animate_color(color.Color(1, 1, 1, 0), duration=0.2)
        
        def cleanup():
            destroy(impact)
            if impact in self.effect_entities:
                self.effect_entities.remove(impact)
        
        sequence = Sequence(0.2, Func(cleanup))
        sequence.start()
    
    def _create_spell_effect(self, position: Vec3, effect_color: color.Color, duration: float):
        """Create magical spell effect"""
        spell_effect = Entity(
            model='sphere',
            scale=0.3,
            position=position + Vec3(0, 1, 0),
            color=effect_color
        )
        
        self.effect_entities.append(spell_effect)
        
        # Grow and fade
        spell_effect.animate_scale(1.0, duration=duration * 0.5)
        spell_effect.animate_color(color.Color(effect_color.r, effect_color.g, effect_color.b, 0), 
                                 duration=duration)
        
        def cleanup():
            destroy(spell_effect)
            if spell_effect in self.effect_entities:
                self.effect_entities.remove(spell_effect)
        
        sequence = Sequence(duration, Func(cleanup))
        sequence.start()
    
    def _create_heal_effect(self, position: Vec3, duration: float):
        """Create healing effect"""
        heal_effect = Entity(
            model='sphere',
            scale=0.2,
            position=position + Vec3(0, 0.5, 0),
            color=color.green
        )
        
        self.effect_entities.append(heal_effect)
        
        # Float upward and fade
        heal_effect.animate_position(position + Vec3(0, 2, 0), duration=duration)
        heal_effect.animate_color(color.Color(0, 1, 0, 0), duration=duration)
        
        def cleanup():
            destroy(heal_effect)
            if heal_effect in self.effect_entities:
                self.effect_entities.remove(heal_effect)
        
        sequence = Sequence(duration, Func(cleanup))
        sequence.start()
    
    def _create_damage_number(self, position: Vec3, damage: int, damage_type: str):
        """Create floating damage number"""
        # This would typically use text entities or billboards
        # For now, create a simple colored cube representing damage
        damage_color = color.red if damage_type == 'physical' else color.blue
        
        damage_indicator = Entity(
            model='cube',
            scale=0.1,
            position=position + Vec3(0, 1, 0),
            color=damage_color
        )
        
        self.effect_entities.append(damage_indicator)
        
        # Float up and fade
        damage_indicator.animate_position(position + Vec3(0, 2, 0), duration=1.5)
        damage_indicator.animate_color(color.Color(damage_color.r, damage_color.g, damage_color.b, 0), 
                                     duration=1.5)
        
        def cleanup():
            destroy(damage_indicator)
            if damage_indicator in self.effect_entities:
                self.effect_entities.remove(damage_indicator)
        
        sequence = Sequence(1.5, Func(cleanup))
        sequence.start()
    
    def _create_heal_number(self, position: Vec3, heal_amount: int):
        """Create floating heal number"""
        heal_indicator = Entity(
            model='cube',
            scale=0.1,
            position=position + Vec3(0, 1, 0),
            color=color.lime
        )
        
        self.effect_entities.append(heal_indicator)
        
        # Float up and fade
        heal_indicator.animate_position(position + Vec3(0, 2, 0), duration=1.5)
        heal_indicator.animate_color(color.Color(0, 1, 0.5, 0), duration=1.5)
        
        def cleanup():
            destroy(heal_indicator)
            if heal_indicator in self.effect_entities:
                self.effect_entities.remove(heal_indicator)
        
        sequence = Sequence(1.5, Func(cleanup))
        sequence.start()
    
    def _create_death_effect(self, position: Vec3):
        """Create death effect"""
        death_effect = Entity(
            model='sphere',
            scale=0.5,
            position=position,
            color=color.Color(0.2, 0.2, 0.2, 0.8)
        )
        
        self.effect_entities.append(death_effect)
        
        # Expand and fade
        death_effect.animate_scale(2.0, duration=2.0)
        death_effect.animate_color(color.Color(0.2, 0.2, 0.2, 0), duration=2.0)
        
        def cleanup():
            destroy(death_effect)
            if death_effect in self.effect_entities:
                self.effect_entities.remove(death_effect)
        
        sequence = Sequence(2.0, Func(cleanup))
        sequence.start()
    
    def _create_level_up_effect(self, position: Vec3, duration: float):
        """Create level up effect"""
        level_effect = Entity(
            model='sphere',
            scale=0.1,
            position=position,
            color=color.gold
        )
        
        self.effect_entities.append(level_effect)
        
        # Burst effect
        level_effect.animate_scale(3.0, duration=duration * 0.3)
        level_effect.animate_color(color.Color(1, 0.8, 0, 0), duration=duration)
        
        def cleanup():
            destroy(level_effect)
            if level_effect in self.effect_entities:
                self.effect_entities.remove(level_effect)
        
        sequence = Sequence(duration, Func(cleanup))
        sequence.start()
    
    def _create_explosion_effect(self, position: Vec3, duration: float):
        """Create explosion effect"""
        explosion = Entity(
            model='sphere',
            scale=0.2,
            position=position,
            color=color.orange
        )
        
        self.effect_entities.append(explosion)
        
        # Explosive growth and fade
        explosion.animate_scale(2.5, duration=duration * 0.4)
        explosion.animate_color(color.Color(1, 0.5, 0, 0), duration=duration)
        
        def cleanup():
            destroy(explosion)
            if explosion in self.effect_entities:
                self.effect_entities.remove(explosion)
        
        sequence = Sequence(duration, Func(cleanup))
        sequence.start()
    
    def _create_area_spell_effect(self, center: Vec3, duration: float):
        """Create area effect spell"""
        for i in range(8):  # Create multiple effect entities in a circle
            angle = (i / 8) * 2 * math.pi
            offset = Vec3(math.cos(angle) * 2, 0, math.sin(angle) * 2)
            effect_pos = center + offset
            
            self._create_spell_effect(effect_pos, color.purple, duration)
    
    # Camera effects
    
    def _shake_camera(self, intensity: float, duration: float):
        """Apply camera shake effect"""
        self.camera_shake_intensity = intensity
        self.camera_shake_duration = duration
        
        if self.camera_original_position is None:
            self.camera_original_position = camera.position
    
    def _update_camera_effects(self, delta_time: float):
        """Update camera shake and other effects"""
        if self.camera_shake_duration > 0:
            self.camera_shake_duration -= delta_time
            
            if self.camera_shake_duration > 0:
                # Apply shake
                shake_offset = Vec3(
                    (math.sin(time.time() * 20) * self.camera_shake_intensity),
                    (math.cos(time.time() * 20) * self.camera_shake_intensity),
                    0
                )
                
                if self.camera_original_position:
                    camera.position = self.camera_original_position + shake_offset
            else:
                # Restore original position
                if self.camera_original_position:
                    camera.position = self.camera_original_position
                    self.camera_original_position = None
                
                self.camera_shake_intensity = 0
    
    def _update_visual_effects(self, delta_time: float):
        """Update any persistent visual effects"""
        # This could include particle systems, environmental effects, etc.
        pass
    
    # Public animation interface
    
    def queue_movement_animation(self, unit: GameEntity, target_position: Vector3, 
                                duration: Optional[float] = None, 
                                delay: float = 0.0, callback: Optional[Callable] = None):
        """Queue a movement animation"""
        if duration is None:
            duration = 1.0 / self.animation_speeds[AnimationType.MOVEMENT]
        
        animation = AnimationEvent(
            animation_type=AnimationType.MOVEMENT,
            target_entity=unit,
            duration=duration,
            start_time=time.time() + delay,
            parameters={'target_position': target_position},
            callback=callback
        )
        
        self.animation_queue.append(animation)
    
    def queue_attack_animation(self, attacker: GameEntity, target: Optional[GameEntity] = None,
                              attack_type: str = 'melee', duration: Optional[float] = None,
                              delay: float = 0.0, callback: Optional[Callable] = None):
        """Queue an attack animation"""
        if duration is None:
            duration = 1.0 / self.animation_speeds[AnimationType.ATTACK]
        
        parameters = {
            'attack_type': attack_type,
            'target_entity_id': target.id if target else None
        }
        
        animation = AnimationEvent(
            animation_type=AnimationType.ATTACK,
            target_entity=attacker,
            duration=duration,
            start_time=time.time() + delay,
            parameters=parameters,
            callback=callback
        )
        
        self.animation_queue.append(animation)
    
    def queue_damage_animation(self, target: GameEntity, damage_amount: int, 
                              damage_type: str = 'physical', duration: Optional[float] = None,
                              delay: float = 0.0, callback: Optional[Callable] = None):
        """Queue a damage animation"""
        if duration is None:
            duration = 1.0 / self.animation_speeds[AnimationType.DAMAGE]
        
        parameters = {
            'damage_amount': damage_amount,
            'damage_type': damage_type
        }
        
        animation = AnimationEvent(
            animation_type=AnimationType.DAMAGE,
            target_entity=target,
            duration=duration,
            start_time=time.time() + delay,
            parameters=parameters,
            callback=callback
        )
        
        self.animation_queue.append(animation)
    
    def queue_heal_animation(self, target: GameEntity, heal_amount: int,
                            duration: Optional[float] = None, delay: float = 0.0,
                            callback: Optional[Callable] = None):
        """Queue a healing animation"""
        if duration is None:
            duration = 1.0 / self.animation_speeds[AnimationType.HEAL]
        
        parameters = {'heal_amount': heal_amount}
        
        animation = AnimationEvent(
            animation_type=AnimationType.HEAL,
            target_entity=target,
            duration=duration,
            start_time=time.time() + delay,
            parameters=parameters,
            callback=callback
        )
        
        self.animation_queue.append(animation)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get animation system statistics"""
        return {
            'queued_animations': len(self.animation_queue),
            'active_animations': len(self.active_animations),
            'visual_effects': len(self.effect_entities),
            'projectiles': len(self.projectile_entities),
            'registered_units': len(self.unit_entities)
        }
    
    def cleanup(self):
        """Clean up all animation entities"""
        # Clean up effect entities
        for effect in self.effect_entities:
            destroy(effect)
        self.effect_entities.clear()
        
        # Clean up projectiles
        for projectile in self.projectile_entities:
            destroy(projectile)
        self.projectile_entities.clear()
        
        # Clear queues
        self.animation_queue.clear()
        self.active_animations.clear()