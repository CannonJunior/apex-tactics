"""
Visual Effects System

Real-time visual effects and animations for the game engine,
providing particle effects, animations, and visual feedback.
"""

import asyncio
import math
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

import structlog

from ...core.events import EventBus, GameEvent, EventType
from ...core.math import Vector3

logger = structlog.get_logger()


class EffectType(str, Enum):
    """Types of visual effects"""
    DAMAGE_NUMBER = "damage_number"
    HEALING_NUMBER = "healing_number"
    STATUS_ICON = "status_icon"
    SPELL_CAST = "spell_cast"
    IMPACT = "impact"
    MOVEMENT_TRAIL = "movement_trail"
    SELECTION_RING = "selection_ring"
    TILE_PULSE = "tile_pulse"
    PARTICLE_BURST = "particle_burst"
    SCREEN_SHAKE = "screen_shake"


class AnimationType(str, Enum):
    """Animation types for effects"""
    FLOAT_UP = "float_up"
    FADE_OUT = "fade_out"
    SCALE_UP = "scale_up"
    BOUNCE = "bounce"
    SHAKE = "shake"
    PULSE = "pulse"
    ROTATE = "rotate"
    LINEAR_MOVE = "linear_move"


@dataclass
class VisualEffect:
    """Visual effect configuration"""
    effect_id: str
    effect_type: EffectType
    position: Vector3
    animation_type: AnimationType
    duration: float
    
    # Visual properties
    color: str = "#FFFFFF"
    size: float = 1.0
    text: str = ""
    icon: str = ""
    
    # Animation properties
    start_position: Vector3 = field(default_factory=lambda: Vector3(0, 0, 0))
    end_position: Optional[Vector3] = None
    velocity: Vector3 = field(default_factory=lambda: Vector3(0, 0, 0))
    rotation_speed: float = 0.0
    pulse_frequency: float = 1.0
    shake_intensity: float = 1.0
    
    # State
    start_time: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    progress: float = 0.0
    
    def update(self, delta_time: float) -> bool:
        """Update effect animation, return False if expired"""
        if not self.is_active:
            return False
        
        current_time = datetime.now()
        elapsed = (current_time - self.start_time).total_seconds()
        
        if elapsed >= self.duration:
            self.is_active = False
            return False
        
        self.progress = elapsed / self.duration
        
        # Update position based on animation type
        if self.animation_type == AnimationType.FLOAT_UP:
            self.position.y = self.start_position.y + (self.progress * 2.0)
            
        elif self.animation_type == AnimationType.LINEAR_MOVE and self.end_position:
            lerp_factor = self.progress
            self.position.x = self.start_position.x + (self.end_position.x - self.start_position.x) * lerp_factor
            self.position.y = self.start_position.y + (self.end_position.y - self.start_position.y) * lerp_factor
            self.position.z = self.start_position.z + (self.end_position.z - self.start_position.z) * lerp_factor
            
        elif self.animation_type == AnimationType.BOUNCE:
            bounce_height = abs(math.sin(self.progress * math.pi)) * 1.5
            self.position.y = self.start_position.y + bounce_height
            
        elif self.animation_type == AnimationType.SHAKE:
            shake_x = math.sin(elapsed * 20) * self.shake_intensity * 0.1 * (1.0 - self.progress)
            shake_z = math.cos(elapsed * 15) * self.shake_intensity * 0.1 * (1.0 - self.progress)
            self.position.x = self.start_position.x + shake_x
            self.position.z = self.start_position.z + shake_z
        
        return True


@dataclass
class ParticleSystem:
    """Particle system for visual effects"""
    system_id: str
    position: Vector3
    particle_count: int
    emission_rate: float
    particle_lifetime: float
    
    # Particle properties
    particle_size: float = 0.1
    particle_color: str = "#FFFFFF"
    spread_radius: float = 1.0
    velocity_range: Tuple[float, float] = (1.0, 3.0)
    gravity: float = -9.8
    
    # System state
    particles: List[Dict[str, Any]] = field(default_factory=list)
    last_emission: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    duration: float = 5.0
    start_time: datetime = field(default_factory=datetime.now)
    
    def update(self, delta_time: float) -> bool:
        """Update particle system"""
        if not self.is_active:
            return False
        
        current_time = datetime.now()
        elapsed = (current_time - self.start_time).total_seconds()
        
        if elapsed >= self.duration:
            self.is_active = False
            return len(self.particles) > 0  # Keep alive while particles exist
        
        # Emit new particles
        if elapsed < self.duration - self.particle_lifetime:
            time_since_emission = (current_time - self.last_emission).total_seconds()
            if time_since_emission >= (1.0 / self.emission_rate):
                self._emit_particle()
                self.last_emission = current_time
        
        # Update existing particles
        active_particles = []
        for particle in self.particles:
            if self._update_particle(particle, delta_time):
                active_particles.append(particle)
        
        self.particles = active_particles
        return self.is_active or len(self.particles) > 0
    
    def _emit_particle(self):
        """Emit a new particle"""
        import random
        
        # Random position within spread radius
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(0, self.spread_radius)
        offset_x = math.cos(angle) * radius
        offset_z = math.sin(angle) * radius
        
        # Random velocity
        velocity_magnitude = random.uniform(*self.velocity_range)
        velocity_angle = random.uniform(0, 2 * math.pi)
        velocity_x = math.cos(velocity_angle) * velocity_magnitude
        velocity_y = random.uniform(1.0, 3.0)
        velocity_z = math.sin(velocity_angle) * velocity_magnitude
        
        particle = {
            "position": Vector3(
                self.position.x + offset_x,
                self.position.y,
                self.position.z + offset_z
            ),
            "velocity": Vector3(velocity_x, velocity_y, velocity_z),
            "life": self.particle_lifetime,
            "max_life": self.particle_lifetime,
            "size": self.particle_size,
            "color": self.particle_color
        }
        
        self.particles.append(particle)
    
    def _update_particle(self, particle: Dict[str, Any], delta_time: float) -> bool:
        """Update individual particle, return False if expired"""
        particle["life"] -= delta_time
        
        if particle["life"] <= 0:
            return False
        
        # Update position
        particle["position"].x += particle["velocity"].x * delta_time
        particle["position"].y += particle["velocity"].y * delta_time
        particle["position"].z += particle["velocity"].z * delta_time
        
        # Apply gravity
        particle["velocity"].y += self.gravity * delta_time
        
        # Update size and alpha based on lifetime
        life_ratio = particle["life"] / particle["max_life"]
        particle["size"] = self.particle_size * life_ratio
        
        return True


class VisualEffectsManager:
    """Manages visual effects and animations"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        
        # Active effects
        self.active_effects: Dict[str, VisualEffect] = {}
        self.active_particles: Dict[str, ParticleSystem] = {}
        
        # Effect ID counter
        self.next_effect_id = 1
        
        # Performance tracking
        self.effects_created = 0
        self.effects_expired = 0
        self.last_cleanup_time = datetime.now()
        
        # Subscribe to game events
        self._subscribe_to_events()
        
        logger.info("Visual Effects Manager initialized")
    
    def _subscribe_to_events(self):
        """Subscribe to game events for automatic effects"""
        self.event_bus.subscribe(EventType.DAMAGE_DEALT, self._on_damage_dealt)
        self.event_bus.subscribe(EventType.HEALING_APPLIED, self._on_healing_applied)
        self.event_bus.subscribe(EventType.UNIT_MOVED, self._on_unit_moved)
        self.event_bus.subscribe(EventType.UNIT_ATTACKED, self._on_unit_attacked)
        self.event_bus.subscribe(EventType.STATUS_EFFECT_APPLIED, self._on_status_effect_applied)
        self.event_bus.subscribe(EventType.STATUS_EFFECT_REMOVED, self._on_status_effect_removed)
    
    async def create_effect(self, effect_type: EffectType, position: Vector3, 
                          animation_type: AnimationType = AnimationType.FLOAT_UP,
                          duration: float = 2.0, **kwargs) -> str:
        """Create a new visual effect"""
        effect_id = f"effect_{self.next_effect_id}"
        self.next_effect_id += 1
        
        effect = VisualEffect(
            effect_id=effect_id,
            effect_type=effect_type,
            position=Vector3(position.x, position.y, position.z),
            animation_type=animation_type,
            duration=duration,
            start_position=Vector3(position.x, position.y, position.z),
            **kwargs
        )
        
        self.active_effects[effect_id] = effect
        self.effects_created += 1
        
        logger.debug("Created visual effect", 
                    effect_id=effect_id,
                    type=effect_type.value,
                    position=f"({position.x:.1f}, {position.y:.1f}, {position.z:.1f})")
        
        return effect_id
    
    async def create_particle_system(self, position: Vector3, particle_count: int = 20,
                                   emission_rate: float = 10.0, particle_lifetime: float = 2.0,
                                   duration: float = 3.0, **kwargs) -> str:
        """Create a particle system"""
        system_id = f"particles_{self.next_effect_id}"
        self.next_effect_id += 1
        
        particle_system = ParticleSystem(
            system_id=system_id,
            position=Vector3(position.x, position.y, position.z),
            particle_count=particle_count,
            emission_rate=emission_rate,
            particle_lifetime=particle_lifetime,
            duration=duration,
            **kwargs
        )
        
        self.active_particles[system_id] = particle_system
        
        logger.debug("Created particle system",
                    system_id=system_id,
                    position=f"({position.x:.1f}, {position.y:.1f}, {position.z:.1f})")
        
        return system_id
    
    async def create_damage_number(self, position: Vector3, damage: int, damage_type: str = "physical") -> str:
        """Create floating damage number"""
        color = "#FF0000" if damage_type == "physical" else "#FF00FF" if damage_type == "magical" else "#FFAA00"
        
        return await self.create_effect(
            effect_type=EffectType.DAMAGE_NUMBER,
            position=Vector3(position.x + 0.3, position.y + 1.2, position.z),
            animation_type=AnimationType.FLOAT_UP,
            duration=2.0,
            text=f"-{damage}",
            color=color,
            size=1.2
        )
    
    async def create_healing_number(self, position: Vector3, healing: int) -> str:
        """Create floating healing number"""
        return await self.create_effect(
            effect_type=EffectType.HEALING_NUMBER,
            position=Vector3(position.x - 0.3, position.y + 1.2, position.z),
            animation_type=AnimationType.FLOAT_UP,
            duration=2.0,
            text=f"+{healing}",
            color="#00FF00",
            size=1.2
        )
    
    async def create_status_effect(self, position: Vector3, effect_name: str, applied: bool = True) -> str:
        """Create status effect visual"""
        icon = self._get_status_effect_icon(effect_name)
        color = "#FFFF00" if applied else "#AAAAAA"
        animation = AnimationType.PULSE if applied else AnimationType.FADE_OUT
        
        return await self.create_effect(
            effect_type=EffectType.STATUS_ICON,
            position=Vector3(position.x, position.y + 1.5, position.z),
            animation_type=animation,
            duration=2.5 if applied else 1.5,
            icon=icon,
            color=color,
            pulse_frequency=2.0
        )
    
    async def create_spell_cast_effect(self, position: Vector3, spell_name: str) -> str:
        """Create spell casting visual effect"""
        # Create main effect
        effect_id = await self.create_effect(
            effect_type=EffectType.SPELL_CAST,
            position=Vector3(position.x, position.y + 1.0, position.z),
            animation_type=AnimationType.SCALE_UP,
            duration=2.0,
            color="#00FFFF",
            size=2.0
        )
        
        # Add particle system
        await self.create_particle_system(
            position=Vector3(position.x, position.y + 0.5, position.z),
            particle_count=30,
            emission_rate=15.0,
            particle_lifetime=1.5,
            duration=2.0,
            particle_color="#00FFFF",
            spread_radius=1.5,
            velocity_range=(2.0, 4.0)
        )
        
        return effect_id
    
    async def create_impact_effect(self, position: Vector3, impact_type: str = "normal") -> str:
        """Create impact visual effect"""
        colors = {
            "normal": "#FFFF00",
            "critical": "#FF4400", 
            "miss": "#888888"
        }
        
        color = colors.get(impact_type, "#FFFF00")
        
        # Create impact flash
        effect_id = await self.create_effect(
            effect_type=EffectType.IMPACT,
            position=Vector3(position.x, position.y + 0.5, position.z),
            animation_type=AnimationType.SCALE_UP,
            duration=0.5,
            color=color,
            size=1.5
        )
        
        # Add impact particles
        await self.create_particle_system(
            position=Vector3(position.x, position.y + 0.5, position.z),
            particle_count=15,
            emission_rate=30.0,
            particle_lifetime=0.8,
            duration=0.5,
            particle_color=color,
            spread_radius=0.8,
            velocity_range=(3.0, 6.0)
        )
        
        return effect_id
    
    async def create_movement_trail(self, start_pos: Vector3, end_pos: Vector3) -> str:
        """Create movement trail effect"""
        return await self.create_effect(
            effect_type=EffectType.MOVEMENT_TRAIL,
            position=Vector3(start_pos.x, start_pos.y + 0.1, start_pos.z),
            animation_type=AnimationType.LINEAR_MOVE,
            duration=1.0,
            end_position=Vector3(end_pos.x, end_pos.y + 0.1, end_pos.z),
            color="#00AAFF",
            size=0.5
        )
    
    async def create_selection_ring(self, position: Vector3) -> str:
        """Create selection ring effect"""
        return await self.create_effect(
            effect_type=EffectType.SELECTION_RING,
            position=Vector3(position.x, position.y + 0.05, position.z),
            animation_type=AnimationType.PULSE,
            duration=float('inf'),  # Persistent until removed
            color="#FFFFFF",
            size=1.2,
            pulse_frequency=2.0
        )
    
    async def create_tile_pulse(self, position: Vector3, highlight_type: str = "movement") -> str:
        """Create tile pulse effect"""
        colors = {
            "movement": "#00FF00",
            "attack": "#FF0000",
            "effect": "#FFFF00"
        }
        
        color = colors.get(highlight_type, "#FFFFFF")
        
        return await self.create_effect(
            effect_type=EffectType.TILE_PULSE,
            position=Vector3(position.x, position.y + 0.02, position.z),
            animation_type=AnimationType.PULSE,
            duration=3.0,
            color=color,
            size=0.9,
            pulse_frequency=1.5
        )
    
    async def create_screen_shake(self, intensity: float = 1.0, duration: float = 0.5) -> str:
        """Create screen shake effect"""
        return await self.create_effect(
            effect_type=EffectType.SCREEN_SHAKE,
            position=Vector3(0, 0, 0),
            animation_type=AnimationType.SHAKE,
            duration=duration,
            shake_intensity=intensity
        )
    
    async def remove_effect(self, effect_id: str):
        """Remove a specific effect"""
        if effect_id in self.active_effects:
            del self.active_effects[effect_id]
            logger.debug("Removed visual effect", effect_id=effect_id)
        
        if effect_id in self.active_particles:
            del self.active_particles[effect_id]
            logger.debug("Removed particle system", effect_id=effect_id)
    
    async def clear_all_effects(self):
        """Clear all active effects"""
        effect_count = len(self.active_effects)
        particle_count = len(self.active_particles)
        
        self.active_effects.clear()
        self.active_particles.clear()
        
        logger.info("Cleared all visual effects", 
                   effects_cleared=effect_count,
                   particles_cleared=particle_count)
    
    async def update(self, delta_time: float):
        """Update all active effects"""
        current_time = datetime.now()
        
        # Update visual effects
        expired_effects = []
        for effect_id, effect in self.active_effects.items():
            if not effect.update(delta_time):
                expired_effects.append(effect_id)
        
        # Remove expired effects
        for effect_id in expired_effects:
            del self.active_effects[effect_id]
            self.effects_expired += 1
        
        # Update particle systems
        expired_particles = []
        for system_id, particle_system in self.active_particles.items():
            if not particle_system.update(delta_time):
                expired_particles.append(system_id)
        
        # Remove expired particle systems
        for system_id in expired_particles:
            del self.active_particles[system_id]
        
        # Periodic cleanup
        if (current_time - self.last_cleanup_time).total_seconds() > 10.0:
            await self._cleanup_old_effects()
            self.last_cleanup_time = current_time
    
    async def _cleanup_old_effects(self):
        """Clean up old or orphaned effects"""
        current_time = datetime.now()
        cleanup_threshold = timedelta(minutes=5)
        
        old_effects = []
        for effect_id, effect in self.active_effects.items():
            if current_time - effect.start_time > cleanup_threshold:
                old_effects.append(effect_id)
        
        for effect_id in old_effects:
            del self.active_effects[effect_id]
            logger.warning("Cleaned up old effect", effect_id=effect_id)
    
    # Event handlers
    async def _on_damage_dealt(self, event: GameEvent):
        """Handle damage dealt event"""
        target_position = event.data.get("target_position")
        damage = event.data.get("damage", 0)
        damage_type = event.data.get("damage_type", "physical")
        is_critical = event.data.get("is_critical", False)
        
        if target_position:
            position = Vector3(target_position["x"], target_position["y"], target_position["z"])
            
            # Create damage number
            await self.create_damage_number(position, damage, damage_type)
            
            # Create impact effect
            impact_type = "critical" if is_critical else "normal"
            await self.create_impact_effect(position, impact_type)
    
    async def _on_healing_applied(self, event: GameEvent):
        """Handle healing applied event"""
        target_position = event.data.get("target_position")
        healing = event.data.get("healing", 0)
        
        if target_position:
            position = Vector3(target_position["x"], target_position["y"], target_position["z"])
            await self.create_healing_number(position, healing)
    
    async def _on_unit_moved(self, event: GameEvent):
        """Handle unit movement event"""
        from_position = event.data.get("from_position")
        to_position = event.data.get("to_position")
        
        if from_position and to_position:
            start_pos = Vector3(from_position["x"], from_position["y"], from_position["z"])
            end_pos = Vector3(to_position["x"], to_position["y"], to_position["z"])
            await self.create_movement_trail(start_pos, end_pos)
    
    async def _on_unit_attacked(self, event: GameEvent):
        """Handle unit attack event"""
        attacker_position = event.data.get("attacker_position")
        target_position = event.data.get("target_position")
        
        if attacker_position:
            position = Vector3(attacker_position["x"], attacker_position["y"], attacker_position["z"])
            await self.create_spell_cast_effect(position, "attack")
    
    async def _on_status_effect_applied(self, event: GameEvent):
        """Handle status effect applied event"""
        target_position = event.data.get("target_position")
        effect_name = event.data.get("effect_name", "")
        
        if target_position:
            position = Vector3(target_position["x"], target_position["y"], target_position["z"])
            await self.create_status_effect(position, effect_name, applied=True)
    
    async def _on_status_effect_removed(self, event: GameEvent):
        """Handle status effect removed event"""
        target_position = event.data.get("target_position")
        effect_name = event.data.get("effect_name", "")
        
        if target_position:
            position = Vector3(target_position["x"], target_position["y"], target_position["z"])
            await self.create_status_effect(position, effect_name, applied=False)
    
    def _get_status_effect_icon(self, effect_name: str) -> str:
        """Get icon for status effect"""
        icons = {
            "poison": "☠️",
            "burn": "🔥",
            "bleed": "🩸",
            "regeneration": "💚",
            "blessed": "✨",
            "stunned": "😵",
            "slowed": "🐌",
            "hasted": "💨",
            "attack_boost": "💪",
            "defense_boost": "🛡️",
            "invisible": "👻",
            "protected": "🛡️",
            "vulnerable": "💥"
        }
        return icons.get(effect_name, "❓")
    
    def get_effect_data_for_ui(self) -> List[Dict[str, Any]]:
        """Get effect data for UI rendering"""
        effects_data = []
        
        # Visual effects
        for effect in self.active_effects.values():
            effects_data.append({
                "id": effect.effect_id,
                "type": effect.effect_type.value,
                "position": {
                    "x": effect.position.x,
                    "y": effect.position.y,
                    "z": effect.position.z
                },
                "animation": effect.animation_type.value,
                "progress": effect.progress,
                "color": effect.color,
                "size": effect.size,
                "text": effect.text,
                "icon": effect.icon
            })
        
        # Particle systems
        for particle_system in self.active_particles.values():
            for particle in particle_system.particles:
                effects_data.append({
                    "id": f"{particle_system.system_id}_particle",
                    "type": "particle",
                    "position": {
                        "x": particle["position"].x,
                        "y": particle["position"].y,
                        "z": particle["position"].z
                    },
                    "color": particle["color"],
                    "size": particle["size"],
                    "life_ratio": particle["life"] / particle["max_life"]
                })
        
        return effects_data
    
    def get_stats(self) -> Dict[str, Any]:
        """Get visual effects statistics"""
        total_particles = sum(len(ps.particles) for ps in self.active_particles.values())
        
        return {
            "active_effects": len(self.active_effects),
            "active_particle_systems": len(self.active_particles),
            "total_particles": total_particles,
            "effects_created": self.effects_created,
            "effects_expired": self.effects_expired
        }