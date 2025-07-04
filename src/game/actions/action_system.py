"""
Unified Action System

Replaces separate attack, magic, and talent systems with a unified approach.
All unit actions are represented as Action objects with configurable effects.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json

from ..effects.effect_system import Effect, EffectFactory


class ActionType(Enum):
    """Visual/UI classification of actions."""
    ATTACK = "Attack"
    MAGIC = "Magic"
    SPIRIT = "Spirit"
    MOVE = "Move"
    INVENTORY = "Inventory"
    PASSIVE = "Passive"


class TargetType(Enum):
    """Who can be targeted by an action."""
    SELF = "self"
    ALLY = "ally"
    ENEMY = "enemy"
    ANY = "any"
    TILE = "tile"
    AREA = "area"


@dataclass
class TargetingData:
    """Configuration for how an action targets."""
    range: int = 1
    area_of_effect: int = 0
    target_type: TargetType = TargetType.ENEMY
    requires_line_of_sight: bool = False
    can_target_empty_tiles: bool = False
    max_targets: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'range': self.range,
            'area_of_effect': self.area_of_effect,
            'target_type': self.target_type.value,
            'requires_line_of_sight': self.requires_line_of_sight,
            'can_target_empty_tiles': self.can_target_empty_tiles,
            'max_targets': self.max_targets
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TargetingData':
        """Create from dictionary."""
        return cls(
            range=data.get('range', 1),
            area_of_effect=data.get('area_of_effect', 0),
            target_type=TargetType(data.get('target_type', 'enemy')),
            requires_line_of_sight=data.get('requires_line_of_sight', False),
            can_target_empty_tiles=data.get('can_target_empty_tiles', False),
            max_targets=data.get('max_targets', 1)
        )


@dataclass
class ActionCosts:
    """Resource costs for performing an action."""
    mp_cost: int = 0
    ap_cost: int = 0
    rage_cost: int = 0
    kwan_cost: int = 0
    item_quantity: int = 0
    talent_points: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'mp_cost': self.mp_cost,
            'ap_cost': self.ap_cost,
            'rage_cost': self.rage_cost,
            'kwan_cost': self.kwan_cost,
            'item_quantity': self.item_quantity,
            'talent_points': self.talent_points
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionCosts':
        """Create from dictionary."""
        return cls(
            mp_cost=data.get('mp_cost', 0),
            ap_cost=data.get('ap_cost', 0),
            rage_cost=data.get('rage_cost', 0),
            kwan_cost=data.get('kwan_cost', 0),
            item_quantity=data.get('item_quantity', 0),
            talent_points=data.get('talent_points', 0)
        )


class Action:
    """
    Unified action system - replaces separate attack/magic/talent classes.
    
    All unit actions are represented as Action objects with:
    - Effects that modify game state
    - Targeting configuration
    - Resource costs
    - Visual/audio presentation data
    """
    
    def __init__(self, action_id: str, name: str, action_type: ActionType = ActionType.ATTACK):
        """
        Initialize action.
        
        Args:
            action_id: Unique identifier for the action
            name: Display name for UI
            action_type: Visual classification (Attack, Magic, etc.)
        """
        self.id = action_id
        self.name = name
        self.type = action_type
        
        # Core functionality
        self.effects: List[Effect] = []
        self.targeting = TargetingData()
        self.costs = ActionCosts()
        
        # Metadata
        self.description = ""
        self.tier = "BASE"
        self.level = 1
        
        # Requirements
        self.requirements = {}
        
        # Presentation
        self.animation_data = {}
        self.sound_effects = {}
        self.visual_effects = {}
        
        # Gameplay
        self.cooldown = 0
        self.cast_time = 0
        self.accuracy = 100  # Base accuracy percentage
        
        # Special properties
        self.guaranteed_hit = False
        self.can_critical = True
        self.interrupts_movement = True
    
    def add_effect(self, effect: Effect):
        """Add an effect to this action."""
        self.effects.append(effect)
    
    def remove_effect(self, effect: Effect):
        """Remove an effect from this action."""
        if effect in self.effects:
            self.effects.remove(effect)
    
    def can_execute(self, caster: Any, targets: List[Any], game_state: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if action can be executed.
        
        Args:
            caster: Unit attempting to perform action
            targets: List of target units/positions
            game_state: Current game state
            
        Returns:
            Tuple of (can_execute, reason_if_not)
        """
        # Check resource costs
        if not self._can_afford_costs(caster):
            return False, "Insufficient resources"
        
        # Check targeting validity
        if not self._are_targets_valid(caster, targets, game_state):
            return False, "Invalid targets"
        
        # Check requirements
        if not self._meets_requirements(caster):
            return False, "Requirements not met"
        
        # Check cooldown
        if hasattr(caster, 'action_cooldowns') and caster.action_cooldowns.get(self.id, 0) > 0:
            return False, "Action on cooldown"
        
        return True, "Can execute"
    
    def execute(self, caster: Any, targets: List[Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the action.
        
        Args:
            caster: Unit performing the action
            targets: List of target units/positions  
            game_state: Current game state
            
        Returns:
            Dictionary containing execution results
        """
        # Validate execution
        can_execute, reason = self.can_execute(caster, targets, game_state)
        if not can_execute:
            return {
                'success': False,
                'reason': reason,
                'action_id': self.id,
                'caster': caster,
                'targets': targets
            }
        
        # Consume costs
        self._consume_costs(caster)
        
        # Apply effects
        effect_results = []
        for effect in self.effects:
            for target in targets:
                if effect.can_apply(target, game_state):
                    result = effect.apply(target, game_state)
                    result['effect_type'] = effect.type.value
                    result['target'] = target
                    effect_results.append(result)
        
        # Set cooldown
        if hasattr(caster, 'action_cooldowns'):
            caster.action_cooldowns[self.id] = self.cooldown
        
        return {
            'success': True,
            'action_id': self.id,
            'action_name': self.name,
            'caster': caster,
            'targets': targets,
            'effect_results': effect_results,
            'costs_consumed': self.costs.to_dict()
        }
    
    def get_preview_data(self, caster: Any, targets: List[Any]) -> Dict[str, Any]:
        """
        Get preview of what this action will do.
        
        Args:
            caster: Unit that would perform action
            targets: Potential targets
            
        Returns:
            Preview data for UI display
        """
        preview = {
            'action_id': self.id,
            'action_name': self.name,
            'action_type': self.type.value,
            'costs': self.costs.to_dict(),
            'targeting': self.targeting.to_dict(),
            'effect_previews': []
        }
        
        for effect in self.effects:
            for target in targets:
                preview_text = effect.get_preview_text(target)
                preview['effect_previews'].append({
                    'target': target,
                    'effect_type': effect.type.value,
                    'description': preview_text
                })
        
        return preview
    
    def _can_afford_costs(self, caster: Any) -> bool:
        """Check if caster can afford the action costs."""
        if self.costs.mp_cost > 0 and getattr(caster, 'mp', 0) < self.costs.mp_cost:
            return False
        if self.costs.ap_cost > 0 and getattr(caster, 'ap', 0) < self.costs.ap_cost:
            return False
        if self.costs.rage_cost > 0 and getattr(caster, 'rage', 0) < self.costs.rage_cost:
            return False
        if self.costs.kwan_cost > 0 and getattr(caster, 'kwan', 0) < self.costs.kwan_cost:
            return False
        return True
    
    def _consume_costs(self, caster: Any):
        """Consume the action costs from caster."""
        if self.costs.mp_cost > 0 and hasattr(caster, 'mp'):
            caster.mp = max(0, caster.mp - self.costs.mp_cost)
        if self.costs.ap_cost > 0 and hasattr(caster, 'ap'):
            caster.ap = max(0, caster.ap - self.costs.ap_cost)
        if self.costs.rage_cost > 0 and hasattr(caster, 'rage'):
            caster.rage = max(0, caster.rage - self.costs.rage_cost)
        if self.costs.kwan_cost > 0 and hasattr(caster, 'kwan'):
            caster.kwan = max(0, caster.kwan - self.costs.kwan_cost)
    
    def _are_targets_valid(self, caster: Any, targets: List[Any], game_state: Dict[str, Any]) -> bool:
        """Check if targets are valid for this action."""
        # Basic validation - can be expanded
        if len(targets) > self.targeting.max_targets:
            return False
        
        # Check if targets are in range
        for target in targets:
            if hasattr(target, 'x') and hasattr(target, 'y') and hasattr(caster, 'x') and hasattr(caster, 'y'):
                distance = abs(target.x - caster.x) + abs(target.y - caster.y)
                if distance > self.targeting.range:
                    return False
        
        return True
    
    def _meets_requirements(self, caster: Any) -> bool:
        """Check if caster meets action requirements."""
        # Check level requirement
        if 'level' in self.requirements and getattr(caster, 'level', 1) < self.requirements['level']:
            return False
        
        # Check stat requirements
        for stat, required_value in self.requirements.items():
            if stat != 'level' and hasattr(caster, stat):
                if getattr(caster, stat) < required_value:
                    return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize action to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'tier': self.tier,
            'level': self.level,
            'targeting': self.targeting.to_dict(),
            'costs': self.costs.to_dict(),
            'effects': [effect.to_dict() for effect in self.effects],
            'requirements': self.requirements,
            'accuracy': self.accuracy,
            'guaranteed_hit': self.guaranteed_hit,
            'cooldown': self.cooldown,
            'cast_time': self.cast_time
        }
    
    @classmethod
    def from_talent_data(cls, talent_data) -> 'Action':
        """
        Create Action from existing talent data structure.
        
        Args:
            talent_data: Talent data object with effects, costs, etc.
            
        Returns:
            Action object
        """
        # Create base action
        action_type = ActionType.ATTACK
        if hasattr(talent_data, 'action_type'):
            try:
                action_type = ActionType(talent_data.action_type)
            except ValueError:
                action_type = ActionType.ATTACK
        
        action = cls(
            action_id=getattr(talent_data, 'id', 'unknown'),
            name=getattr(talent_data, 'name', 'Unknown Action'),
            action_type=action_type
        )
        
        # Set metadata
        action.description = getattr(talent_data, 'description', '')
        action.tier = getattr(talent_data, 'tier', 'BASE')
        action.level = getattr(talent_data, 'level', 1)
        
        # Set requirements
        if hasattr(talent_data, 'requirements'):
            action.requirements = talent_data.requirements
        
        # Convert costs
        if hasattr(talent_data, 'cost'):
            action.costs = ActionCosts.from_dict(talent_data.cost)
        
        # Convert targeting from effects
        if hasattr(talent_data, 'effects'):
            # Extract targeting info from effects
            effects_dict = talent_data.effects
            action.targeting.range = int(effects_dict.get('range', 1))
            action.targeting.area_of_effect = int(effects_dict.get('area_of_effect', 0))
            
            # Set target type based on effect types
            if any('heal' in key.lower() for key in effects_dict.keys()):
                action.targeting.target_type = TargetType.ALLY
            elif 'target_type' in effects_dict:
                try:
                    action.targeting.target_type = TargetType(effects_dict['target_type'])
                except ValueError:
                    action.targeting.target_type = TargetType.ENEMY
            
            # Set special properties
            action.guaranteed_hit = effects_dict.get('guaranteed_hit', False)
        
        # Convert effects
        action.effects = EffectFactory.create_multiple_from_talent(talent_data)
        
        return action


class ActionRegistry:
    """Registry for managing all available actions."""
    
    def __init__(self):
        self.actions: Dict[str, Action] = {}
        self.actions_by_type: Dict[ActionType, List[Action]] = {
            action_type: [] for action_type in ActionType
        }
    
    def register(self, action: Action):
        """Register an action."""
        self.actions[action.id] = action
        self.actions_by_type[action.type].append(action)
        print(f"📝 Registered action: {action.id} ({action.type.value})")
    
    def get(self, action_id: str) -> Optional[Action]:
        """Get action by ID."""
        return self.actions.get(action_id)
    
    def get_by_type(self, action_type: ActionType) -> List[Action]:
        """Get all actions of specific type."""
        return self.actions_by_type.get(action_type, [])
    
    def get_available_for_unit(self, unit: Any) -> List[Action]:
        """Get all actions available to a specific unit."""
        available = []
        for action in self.actions.values():
            can_use, _ = action.can_execute(unit, [], {})
            if can_use:
                available.append(action)
        return available
    
    def create_from_talent_files(self, talent_data_list: List[Any]):
        """Create actions from existing talent data."""
        for talent_data in talent_data_list:
            action = Action.from_talent_data(talent_data)
            self.register(action)
    
    def get_all_actions(self) -> List[Action]:
        """Get all registered actions."""
        return list(self.actions.values())
    
    def list_actions(self):
        """List all registered actions."""
        print(f"\n📋 Action Registry ({len(self.actions)} actions):")
        for action_type in ActionType:
            actions = self.actions_by_type[action_type]
            if actions:
                print(f"  {action_type.value}: {len(actions)} actions")
                for action in actions:
                    print(f"    - {action.id}: {action.name}")


# Global action registry
_global_action_registry = None

def get_action_registry() -> ActionRegistry:
    """Get the global action registry."""
    global _global_action_registry
    if _global_action_registry is None:
        _global_action_registry = ActionRegistry()
    return _global_action_registry