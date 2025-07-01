"""
Turn-Based Action Queue System

Manages action sequencing and execution in tactical combat.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Callable, Any
from core.math.vector import Vector3


class ActionType(Enum):
    """Types of actions that can be queued"""
    MOVE = "move"
    ATTACK = "attack"
    ABILITY = "ability"
    ITEM = "item"
    WAIT = "wait"
    DEFEND = "defend"


@dataclass
class BattleAction:
    """
    Represents a single action in the turn-based system.
    """
    unit_id: int
    action_type: ActionType
    target_unit_id: Optional[int] = None
    target_position: Optional[Vector3] = None
    ability_name: Optional[str] = None
    item_id: Optional[int] = None
    priority: int = 0  # Higher priority executes first
    
    # Action execution callback
    execute_callback: Optional[Callable] = None
    
    # Action validation
    is_valid: bool = True
    validation_message: str = ""
    
    def __post_init__(self):
        """Validate action parameters after initialization"""
        self._validate_action()
    
    def _validate_action(self):
        """Validate that action has required parameters"""
        if self.action_type == ActionType.MOVE:
            if not self.target_position:
                self.is_valid = False
                self.validation_message = "Move action requires target position"
        
        elif self.action_type == ActionType.ATTACK:
            if not self.target_unit_id and not self.target_position:
                self.is_valid = False
                self.validation_message = "Attack action requires target"
        
        elif self.action_type == ActionType.ABILITY:
            if not self.ability_name:
                self.is_valid = False
                self.validation_message = "Ability action requires ability name"
        
        elif self.action_type == ActionType.ITEM:
            if not self.item_id:
                self.is_valid = False
                self.validation_message = "Item action requires item ID"


class ActionQueue:
    """
    Manages the queue of actions for turn-based combat.
    
    Actions are sorted by priority and executed in order.
    """
    
    def __init__(self):
        self.actions: List[BattleAction] = []
        self.executed_actions: List[BattleAction] = []
        self.current_turn = 0
    
    def add_action(self, action: BattleAction) -> bool:
        """
        Add action to the queue.
        
        Args:
            action: Battle action to queue
            
        Returns:
            True if action was successfully added
        """
        if not action.is_valid:
            return False
        
        self.actions.append(action)
        self._sort_actions()
        return True
    
    def remove_action(self, unit_id: int) -> bool:
        """
        Remove all queued actions for a specific unit.
        
        Args:
            unit_id: ID of unit whose actions to remove
            
        Returns:
            True if any actions were removed
        """
        initial_count = len(self.actions)
        self.actions = [action for action in self.actions if action.unit_id != unit_id]
        return len(self.actions) < initial_count
    
    def get_next_action(self) -> Optional[BattleAction]:
        """
        Get the next action to execute without removing it.
        
        Returns:
            Next action or None if queue is empty
        """
        if not self.actions:
            return None
        return self.actions[0]
    
    def execute_next_action(self) -> Optional[BattleAction]:
        """
        Execute and remove the next action from the queue.
        
        Returns:
            Executed action or None if queue is empty
        """
        if not self.actions:
            return None
        
        action = self.actions.pop(0)
        self.executed_actions.append(action)
        
        # Execute action callback if provided
        if action.execute_callback:
            try:
                action.execute_callback(action)
            except Exception as e:
                print(f"Error executing action: {e}")
        
        return action
    
    def execute_all_actions(self) -> List[BattleAction]:
        """
        Execute all queued actions.
        
        Returns:
            List of executed actions
        """
        executed = []
        while self.actions:
            action = self.execute_next_action()
            if action:
                executed.append(action)
        return executed
    
    def _sort_actions(self):
        """Sort actions by priority (highest first), then by action type"""
        def action_sort_key(action: BattleAction) -> tuple:
            # Priority (higher first), then action type order
            type_order = {
                ActionType.ITEM: 0,     # Items first (healing, buffs)
                ActionType.ABILITY: 1,  # Abilities second
                ActionType.ATTACK: 2,   # Attacks third
                ActionType.MOVE: 3,     # Movement fourth
                ActionType.DEFEND: 4,   # Defense fifth
                ActionType.WAIT: 5      # Wait last
            }
            return (-action.priority, type_order.get(action.action_type, 99))
        
        self.actions.sort(key=action_sort_key)
    
    def get_actions_for_unit(self, unit_id: int) -> List[BattleAction]:
        """Get all queued actions for a specific unit"""
        return [action for action in self.actions if action.unit_id == unit_id]
    
    def has_action_for_unit(self, unit_id: int) -> bool:
        """Check if unit has any queued actions"""
        return any(action.unit_id == unit_id for action in self.actions)
    
    def get_queue_summary(self) -> dict:
        """Get summary of current action queue"""
        action_counts = {}
        for action in self.actions:
            action_type = action.action_type.value
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        return {
            'total_actions': len(self.actions),
            'action_counts': action_counts,
            'next_action': self.get_next_action().action_type.value if self.actions else None,
            'turn_number': self.current_turn
        }
    
    def clear_queue(self):
        """Clear all queued actions"""
        self.actions.clear()
    
    def start_new_turn(self):
        """Start a new turn, incrementing turn counter"""
        self.current_turn += 1
        # Note: Don't clear actions automatically - let turn manager decide
    
    def get_action_history(self, last_n: int = 10) -> List[BattleAction]:
        """
        Get recent action history.
        
        Args:
            last_n: Number of recent actions to return
            
        Returns:
            List of recently executed actions
        """
        return self.executed_actions[-last_n:] if self.executed_actions else []