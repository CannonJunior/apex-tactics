"""
Action Prediction and Preview System

Provides visual previews and predictions for actions in the queue:
- Damage/healing predictions
- Status effect previews
- Resource cost visualization
- Battle outcome projections
- AI confidence indicators
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import math

try:
    from ursina import *
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False
    class Entity:
        def __init__(self, **kwargs): 
            self.children = []
        def destroy(self): 
            pass
    class Text:
        def __init__(self, **kwargs): 
            self.text = kwargs.get('text', '')

from game.managers.action_manager import ActionManager
from game.actions.action_system import Action
from game.effects.effect_system import EffectType, DamageType


class PredictionType(Enum):
    """Types of action predictions."""
    DAMAGE = "damage"
    HEALING = "healing"
    STATUS_EFFECT = "status_effect"
    RESOURCE_CHANGE = "resource_change"
    POSITIONING = "positioning"
    BATTLE_OUTCOME = "battle_outcome"


@dataclass
class ActionPrediction:
    """Prediction data for an action."""
    action_id: str
    prediction_type: PredictionType
    target_id: str
    
    # Numerical predictions
    min_value: float = 0.0
    max_value: float = 0.0
    expected_value: float = 0.0
    confidence: float = 1.0
    
    # Status predictions
    status_effects: List[str] = field(default_factory=list)
    duration: int = 0
    
    # Resource predictions
    resource_changes: Dict[str, int] = field(default_factory=dict)
    
    # Text description
    description: str = ""
    tooltip: str = ""


@dataclass
class BattleStatePrediction:
    """Prediction of battle state after action execution."""
    turn_number: int
    unit_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    victory_probability: float = 0.5
    estimated_turns_remaining: int = 10
    key_changes: List[str] = field(default_factory=list)


class ActionPredictionEngine:
    """
    Engine for calculating action predictions and battle outcomes.
    
    Features:
    - Damage/healing calculations with variance
    - Status effect duration predictions
    - Resource cost/benefit analysis
    - Multi-step battle outcome projections
    - AI confidence integration
    """
    
    def __init__(self, action_manager: ActionManager):
        self.action_manager = action_manager
        self.game_controller = action_manager.game_controller
        
        # Prediction configuration
        self.damage_variance = 0.15  # ±15% damage variance
        self.prediction_depth = 3    # Look ahead 3 turns
        self.confidence_threshold = 0.7
        
        # Cache for expensive calculations
        self.prediction_cache: Dict[str, ActionPrediction] = {}
        self.battle_state_cache: Dict[str, BattleStatePrediction] = {}
        
        print("🔮 Action Prediction Engine initialized")
    
    def predict_action_outcome(self, action_id: str, caster_id: str, 
                             target_ids: List[str]) -> List[ActionPrediction]:
        """
        Predict the outcome of an action.
        
        Args:
            action_id: ID of action to predict
            caster_id: ID of unit performing action
            target_ids: IDs of target units
            
        Returns:
            List of predictions for each target
        """
        predictions = []
        
        # Get action and units
        action = self.action_manager.action_registry.get(action_id)
        if not action:
            return predictions
        
        caster = self.game_controller.units.get(caster_id)
        if not caster:
            return predictions
        
        # Predict for each target
        for target_id in target_ids:
            target = self.game_controller.units.get(target_id)
            if not target:
                continue
            
            target_predictions = self._predict_for_target(action, caster, target)
            predictions.extend(target_predictions)
        
        return predictions
    
    def _predict_for_target(self, action: Action, caster: Any, target: Any) -> List[ActionPrediction]:
        """Predict action effects for a specific target."""
        predictions = []
        
        # Predict each effect
        for effect in action.effects:
            prediction = self._predict_effect(effect, action, caster, target)
            if prediction:
                predictions.append(prediction)
        
        return predictions
    
    def _predict_effect(self, effect: Any, action: Action, caster: Any, target: Any) -> Optional[ActionPrediction]:
        """Predict a specific effect outcome."""
        if effect.type == EffectType.DAMAGE:
            return self._predict_damage_effect(effect, action, caster, target)
        elif effect.type == EffectType.HEALING:
            return self._predict_healing_effect(effect, action, caster, target)
        elif effect.type == EffectType.STAT_MODIFIER:
            return self._predict_stat_effect(effect, action, caster, target)
        elif effect.type == EffectType.RESOURCE_CHANGE:
            return self._predict_resource_effect(effect, action, caster, target)
        else:
            return self._predict_generic_effect(effect, action, caster, target)
    
    def _predict_damage_effect(self, effect: Any, action: Action, caster: Any, target: Any) -> ActionPrediction:
        """Predict damage effect outcome."""
        base_damage = effect.magnitude
        
        # Apply defense
        defense = 0
        if hasattr(effect, 'damage_type'):
            if effect.damage_type == DamageType.PHYSICAL:
                defense = getattr(target, 'physical_defense', 0)
            elif effect.damage_type == DamageType.MAGICAL:
                defense = getattr(target, 'magical_defense', 0)
            elif effect.damage_type == DamageType.SPIRITUAL:
                defense = getattr(target, 'spiritual_defense', 0)
        
        # Calculate damage range
        effective_damage = max(1, base_damage - defense)
        min_damage = max(1, effective_damage * (1 - self.damage_variance))
        max_damage = effective_damage * (1 + self.damage_variance)
        expected_damage = effective_damage
        
        # Calculate confidence based on accuracy, range, etc.
        confidence = 0.9  # Base confidence
        if hasattr(action, 'accuracy') and action.accuracy < 100:
            confidence *= action.accuracy / 100
        
        return ActionPrediction(
            action_id=action.id,
            prediction_type=PredictionType.DAMAGE,
            target_id=getattr(target, 'id', 'unknown'),
            min_value=min_damage,
            max_value=max_damage,
            expected_value=expected_damage,
            confidence=confidence,
            description=f"Deal {expected_damage:.0f} damage",
            tooltip=f"Damage range: {min_damage:.0f}-{max_damage:.0f}"
        )
    
    def _predict_healing_effect(self, effect: Any, action: Action, caster: Any, target: Any) -> ActionPrediction:
        """Predict healing effect outcome."""
        base_healing = effect.magnitude
        
        # Calculate actual healing (can't exceed max HP)
        current_hp = getattr(target, 'hp', 0)
        max_hp = getattr(target, 'max_hp', 0)
        
        actual_healing = min(base_healing, max_hp - current_hp)
        
        # Healing variance is typically lower than damage
        healing_variance = self.damage_variance * 0.5
        min_healing = max(0, actual_healing * (1 - healing_variance))
        max_healing = min(max_hp - current_hp, actual_healing * (1 + healing_variance))
        
        return ActionPrediction(
            action_id=action.id,
            prediction_type=PredictionType.HEALING,
            target_id=getattr(target, 'id', 'unknown'),
            min_value=min_healing,
            max_value=max_healing,
            expected_value=actual_healing,
            confidence=0.95,  # Healing is usually more reliable
            description=f"Restore {actual_healing:.0f} HP",
            tooltip=f"Healing range: {min_healing:.0f}-{max_healing:.0f}"
        )
    
    def _predict_stat_effect(self, effect: Any, action: Action, caster: Any, target: Any) -> ActionPrediction:
        """Predict stat modifier effect."""
        stat_name = getattr(effect, 'stat_name', 'unknown')
        modifier = effect.magnitude
        duration = effect.duration
        
        return ActionPrediction(
            action_id=action.id,
            prediction_type=PredictionType.STATUS_EFFECT,
            target_id=getattr(target, 'id', 'unknown'),
            expected_value=modifier,
            confidence=0.9,
            status_effects=[f"{stat_name} {modifier:+d}"],
            duration=duration,
            description=f"{stat_name} {modifier:+d} for {duration} turns",
            tooltip=f"Temporarily modifies {stat_name}"
        )
    
    def _predict_resource_effect(self, effect: Any, action: Action, caster: Any, target: Any) -> ActionPrediction:
        """Predict resource change effect."""
        resource_type = getattr(effect, 'resource_type', None)
        amount = effect.magnitude
        
        resource_name = resource_type.value if resource_type else 'resource'
        
        # Calculate actual change (bounded by max resources)
        if resource_type:
            current = getattr(target, resource_name, 0)
            max_resource = getattr(target, f'max_{resource_name}', 0)
            
            if amount > 0:  # Restoration
                actual_change = min(amount, max_resource - current)
            else:  # Drain
                actual_change = max(amount, -current)
        else:
            actual_change = amount
        
        return ActionPrediction(
            action_id=action.id,
            prediction_type=PredictionType.RESOURCE_CHANGE,
            target_id=getattr(target, 'id', 'unknown'),
            expected_value=actual_change,
            confidence=0.95,
            resource_changes={resource_name: actual_change},
            description=f"{resource_name.upper()} {actual_change:+d}",
            tooltip=f"Changes {resource_name} by {actual_change}"
        )
    
    def _predict_generic_effect(self, effect: Any, action: Action, caster: Any, target: Any) -> ActionPrediction:
        """Predict generic/unknown effect."""
        return ActionPrediction(
            action_id=action.id,
            prediction_type=PredictionType.STATUS_EFFECT,
            target_id=getattr(target, 'id', 'unknown'),
            expected_value=effect.magnitude,
            confidence=0.5,
            description=f"{effect.type.value} effect",
            tooltip="Effect details unknown"
        )
    
    def predict_battle_state(self, turns_ahead: int = 1) -> BattleStatePrediction:
        """
        Predict battle state after executing queued actions.
        
        Args:
            turns_ahead: How many turns to simulate ahead
            
        Returns:
            BattleStatePrediction with projected outcomes
        """
        # Create a copy of current game state for simulation
        simulated_states = self._simulate_battle_turns(turns_ahead)
        
        if not simulated_states:
            return BattleStatePrediction(turn_number=0)
        
        final_state = simulated_states[-1]
        
        # Analyze final state
        victory_prob = self._calculate_victory_probability(final_state)
        estimated_turns = self._estimate_remaining_turns(final_state)
        key_changes = self._identify_key_changes(final_state)
        
        return BattleStatePrediction(
            turn_number=len(simulated_states),
            unit_states=final_state,
            victory_probability=victory_prob,
            estimated_turns_remaining=estimated_turns,
            key_changes=key_changes
        )
    
    def _simulate_battle_turns(self, turns: int) -> List[Dict[str, Any]]:
        """Simulate battle turns to predict outcomes."""
        simulated_states = []
        
        # Get current state
        current_state = self._get_current_battle_state()
        
        for turn in range(turns):
            # Simulate action execution
            new_state = self._simulate_turn_actions(current_state)
            simulated_states.append(new_state)
            current_state = new_state
            
            # Check for battle end conditions
            if self._is_battle_ended(new_state):
                break
        
        return simulated_states
    
    def _get_current_battle_state(self) -> Dict[str, Any]:
        """Get current battle state for simulation."""
        state = {}
        
        for unit_id, unit in self.game_controller.units.items():
            state[unit_id] = {
                'hp': getattr(unit, 'hp', 0),
                'max_hp': getattr(unit, 'max_hp', 0),
                'mp': getattr(unit, 'mp', 0),
                'max_mp': getattr(unit, 'max_mp', 0),
                'alive': getattr(unit, 'alive', True),
                'team': 'player' if unit in self.game_controller.player_units else 'enemy'
            }
        
        return state
    
    def _simulate_turn_actions(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the execution of one turn's actions."""
        # This is a simplified simulation
        # In a full implementation, this would execute queued actions
        # and apply their effects to the simulated state
        
        new_state = state.copy()
        
        # Apply some damage to simulate combat
        for unit_id, unit_data in new_state.items():
            if unit_data['alive'] and unit_data['team'] == 'player':
                # Simulate taking damage
                damage = 10  # Simplified damage
                unit_data['hp'] = max(0, unit_data['hp'] - damage)
                if unit_data['hp'] <= 0:
                    unit_data['alive'] = False
        
        return new_state
    
    def _calculate_victory_probability(self, state: Dict[str, Any]) -> float:
        """Calculate probability of player victory based on state."""
        player_strength = 0
        enemy_strength = 0
        
        for unit_data in state.values():
            if not unit_data['alive']:
                continue
            
            # Simple strength calculation based on HP percentage
            strength = unit_data['hp'] / unit_data['max_hp']
            
            if unit_data['team'] == 'player':
                player_strength += strength
            else:
                enemy_strength += strength
        
        total_strength = player_strength + enemy_strength
        if total_strength == 0:
            return 0.5
        
        return player_strength / total_strength
    
    def _estimate_remaining_turns(self, state: Dict[str, Any]) -> int:
        """Estimate remaining turns until battle ends."""
        # Simplified estimation based on total HP remaining
        total_hp = sum(unit['hp'] for unit in state.values() if unit['alive'])
        average_damage_per_turn = 20  # Simplified
        
        if average_damage_per_turn <= 0:
            return 99
        
        return max(1, int(total_hp / average_damage_per_turn))
    
    def _identify_key_changes(self, state: Dict[str, Any]) -> List[str]:
        """Identify key changes in the battle state."""
        changes = []
        
        # Check for unit defeats
        for unit_id, unit_data in state.items():
            if not unit_data['alive']:
                changes.append(f"{unit_id} defeated")
        
        # Check for low health units
        for unit_id, unit_data in state.items():
            if unit_data['alive'] and unit_data['hp'] / unit_data['max_hp'] < 0.3:
                changes.append(f"{unit_id} critically wounded")
        
        return changes
    
    def _is_battle_ended(self, state: Dict[str, Any]) -> bool:
        """Check if battle has ended in the simulated state."""
        player_alive = any(unit['alive'] for unit in state.values() if unit['team'] == 'player')
        enemy_alive = any(unit['alive'] for unit in state.values() if unit['team'] == 'enemy')
        
        return not (player_alive and enemy_alive)
    
    def clear_cache(self):
        """Clear prediction cache."""
        self.prediction_cache.clear()
        self.battle_state_cache.clear()
        print("🔮 Prediction cache cleared")


class PredictionDisplayWidget:
    """
    Widget for displaying action predictions in the UI.
    
    Features:
    - Damage/healing bars
    - Status effect icons
    - Confidence indicators
    - Tooltip details
    """
    
    def __init__(self, parent_entity: Entity, prediction_engine: ActionPredictionEngine):
        self.parent = parent_entity
        self.prediction_engine = prediction_engine
        
        # UI elements
        self.widget_container = None
        self.prediction_elements: List[Entity] = []
        
        # Current predictions
        self.current_predictions: List[ActionPrediction] = []
        
        # Create UI
        self._create_widget_ui()
        
        print("🔮 Prediction Display Widget created")
    
    def _create_widget_ui(self):
        """Create the prediction widget UI."""
        if not URSINA_AVAILABLE:
            print("🔮 Prediction widget UI created (Ursina not available)")
            return
        
        # Main widget container
        self.widget_container = Entity(
            parent=self.parent,
            model='cube',
            color=(0.1, 0.1, 0.1, 0.8),
            scale=(3, 2, 0.05),
            position=(0, -6, 0)
        )
        
        # Widget title
        Text(
            "Action Predictions",
            parent=self.widget_container,
            position=(0, 0.8, -0.1),
            scale=1.2,
            color=(1, 1, 1)
        )
    
    def show_predictions(self, predictions: List[ActionPrediction]):
        """Display a list of predictions."""
        self.current_predictions = predictions
        self._refresh_prediction_display()
        
        print(f"🔮 Showing {len(predictions)} predictions")
    
    def _refresh_prediction_display(self):
        """Refresh the visual display of predictions."""
        if not URSINA_AVAILABLE:
            return
        
        # Clear existing elements
        for element in self.prediction_elements:
            element.destroy()
        self.prediction_elements.clear()
        
        # Display new predictions
        start_y = 0.4
        item_height = 0.3
        
        for i, prediction in enumerate(self.current_predictions[:5]):  # Show max 5
            y_pos = start_y - i * item_height
            element = self._create_prediction_element(prediction, y_pos)
            self.prediction_elements.append(element)
    
    def _create_prediction_element(self, prediction: ActionPrediction, y_pos: float) -> Entity:
        """Create a visual element for a prediction."""
        if not URSINA_AVAILABLE:
            return None
        
        # Prediction item container
        item = Entity(
            parent=self.widget_container,
            model='cube',
            color=self._get_prediction_color(prediction),
            scale=(2.5, 0.25, 0.02),
            position=(0, y_pos, -0.02)
        )
        
        # Prediction text
        Text(
            prediction.description,
            parent=item,
            position=(-1, 0, -0.1),
            scale=1.0,
            color=(1, 1, 1)
        )
        
        # Confidence indicator
        confidence_color = (
            1 - prediction.confidence,  # Red component (high when confidence is low)
            prediction.confidence,       # Green component (high when confidence is high)
            0                           # Blue component
        )
        
        Entity(
            parent=item,
            model='cube',
            color=confidence_color,
            scale=(0.2, 0.8, 0.05),
            position=(1, 0, -0.02)
        )
        
        return item
    
    def _get_prediction_color(self, prediction: ActionPrediction) -> Tuple[float, float, float]:
        """Get color for prediction based on type."""
        colors = {
            PredictionType.DAMAGE: (0.8, 0.2, 0.2),
            PredictionType.HEALING: (0.2, 0.8, 0.2),
            PredictionType.STATUS_EFFECT: (0.6, 0.4, 0.8),
            PredictionType.RESOURCE_CHANGE: (0.2, 0.6, 0.8),
            PredictionType.POSITIONING: (0.8, 0.8, 0.2),
            PredictionType.BATTLE_OUTCOME: (0.8, 0.6, 0.2)
        }
        return colors.get(prediction.prediction_type, (0.5, 0.5, 0.5))
    
    def hide_predictions(self):
        """Hide the prediction display."""
        self.current_predictions.clear()
        self._refresh_prediction_display()
        print("🔮 Predictions hidden")
    
    def destroy(self):
        """Clean up widget."""
        if self.widget_container and URSINA_AVAILABLE:
            self.widget_container.destroy()