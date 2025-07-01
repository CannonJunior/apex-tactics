"""
Battle Manager System

High-level battle management combining turn management with combat systems.
"""

from typing import List, Dict, Optional, Callable
from core.ecs.entity import Entity
from core.ecs.world import World
from core.math.vector import Vector3
from systems.combat_system import CombatSystem
from .turn_manager import TurnManager, TurnPhase
from .action_queue import BattleAction, ActionType
from components.combat.damage import AttackType, DamageResult
from components.stats.attributes import AttributeStats


class BattleManager:
    """
    Coordinates all aspects of tactical combat.
    
    Integrates turn management, combat systems, and battle flow.
    """
    
    def __init__(self, world: World):
        self.world = world
        self.turn_manager = TurnManager()
        self.combat_system = CombatSystem()
        
        # Battle participants
        self.units: Dict[int, Entity] = {}
        self.player_units: List[int] = []
        self.ai_units: List[int] = []
        
        # Battle state
        self.is_battle_active = False
        self.victory_conditions: List[Callable] = []
        self.defeat_conditions: List[Callable] = []
        
        # Setup phase callbacks
        self._setup_phase_callbacks()
    
    def _setup_phase_callbacks(self):
        """Setup callbacks for different turn phases"""
        self.turn_manager.add_phase_callback(TurnPhase.PLANNING, self._on_planning_phase)
        self.turn_manager.add_phase_callback(TurnPhase.EXECUTION, self._on_execution_phase)
        self.turn_manager.add_phase_callback(TurnPhase.RESOLUTION, self._on_resolution_phase)
    
    def start_battle(self, player_units: List[Entity], ai_units: List[Entity]):
        """
        Start a new battle.
        
        Args:
            player_units: Units controlled by player
            ai_units: Units controlled by AI
        """
        self.is_battle_active = True
        
        # Store unit references
        all_units = player_units + ai_units
        self.units = {unit.id: unit for unit in all_units}
        self.player_units = [unit.id for unit in player_units]
        self.ai_units = [unit.id for unit in ai_units]
        
        # Start turn management
        self.turn_manager.start_combat(all_units)
        
        print(f"Battle started with {len(player_units)} player units vs {len(ai_units)} AI units")
    
    def _on_planning_phase(self, old_phase: TurnPhase, new_phase: TurnPhase):
        """Handle planning phase"""
        current_unit_id = self.turn_manager.get_current_unit()
        if current_unit_id:
            if current_unit_id in self.ai_units:
                # AI units plan automatically
                self._plan_ai_action(current_unit_id)
            # Player units wait for input
    
    def _on_execution_phase(self, old_phase: TurnPhase, new_phase: TurnPhase):
        """Handle execution phase"""
        # Execute all queued actions
        executed_actions = self.turn_manager.execute_turn_actions()
        
        # Process each action through combat system
        for action in executed_actions:
            self._process_battle_action(action)
    
    def _on_resolution_phase(self, old_phase: TurnPhase, new_phase: TurnPhase):
        """Handle resolution phase"""
        # Check victory/defeat conditions
        if self._check_victory_conditions():
            self.end_battle("victory")
        elif self._check_defeat_conditions():
            self.end_battle("defeat")
        else:
            # Continue to next unit
            self.turn_manager.advance_to_next_unit()
    
    def _plan_ai_action(self, unit_id: int):
        """
        Plan action for AI unit.
        
        Args:
            unit_id: ID of AI unit to plan for
        """
        # Simple AI: find nearest enemy and attack
        unit = self.units.get(unit_id)
        if not unit:
            return
        
        # Find nearest enemy
        nearest_enemy = self._find_nearest_enemy(unit_id)
        if nearest_enemy:
            # Queue attack action
            attack_action = BattleAction(
                unit_id=unit_id,
                action_type=ActionType.ATTACK,
                target_unit_id=nearest_enemy.id,
                priority=5
            )
            self.turn_manager.queue_action(attack_action)
        else:
            # No enemies found, wait
            self.turn_manager.skip_unit_turn(unit_id)
    
    def _find_nearest_enemy(self, unit_id: int) -> Optional[Entity]:
        """Find nearest enemy unit"""
        unit = self.units.get(unit_id)
        if not unit:
            return None
        
        # Determine enemy list
        if unit_id in self.player_units:
            enemy_ids = self.ai_units
        else:
            enemy_ids = self.player_units
        
        # Find nearest enemy
        nearest_enemy = None
        nearest_distance = float('inf')
        
        unit_transform = unit.get_component(Transform)
        if not unit_transform:
            return None
        
        for enemy_id in enemy_ids:
            enemy = self.units.get(enemy_id)
            if not enemy:
                continue
            
            enemy_transform = enemy.get_component(Transform)
            if not enemy_transform:
                continue
            
            distance = unit_transform.position.distance_to(enemy_transform.position)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_enemy = enemy
        
        return nearest_enemy
    
    def _process_battle_action(self, action: BattleAction):
        """
        Process a battle action through the combat system.
        
        Args:
            action: Action to process
        """
        attacker = self.units.get(action.unit_id)
        if not attacker:
            return
        
        if action.action_type == ActionType.ATTACK:
            if action.target_unit_id:
                target = self.units.get(action.target_unit_id)
                if target:
                    # Single target attack
                    damage_result = self.combat_system.calculate_damage(
                        attacker, target, AttackType.PHYSICAL
                    )
                    if damage_result:
                        is_alive = self.combat_system.apply_damage(target, damage_result)
                        if not is_alive:
                            print(f"Unit {target.id} was defeated!")
            
            elif action.target_position:
                # Area attack
                all_units_list = [(unit_id, unit) for unit_id, unit in self.units.items()]
                damage_results = self.combat_system.perform_area_attack(
                    attacker, action.target_position, all_units_list
                )
                
                for damage_result in damage_results:
                    target = self.units.get(damage_result.target_unit_id)
                    if target:
                        is_alive = self.combat_system.apply_damage(target, damage_result)
                        if not is_alive:
                            print(f"Unit {target.id} was defeated!")
        
        elif action.action_type == ActionType.MOVE:
            # Handle movement
            if action.target_position:
                transform = attacker.get_component(Transform)
                if transform:
                    transform.position = action.target_position
        
        # Handle other action types as needed
    
    def queue_player_action(self, action: BattleAction) -> bool:
        """
        Queue action for player unit.
        
        Args:
            action: Player action to queue
            
        Returns:
            True if action was successfully queued
        """
        if action.unit_id not in self.player_units:
            return False
        
        if not self.turn_manager.can_unit_act(action.unit_id):
            return False
        
        success = self.turn_manager.queue_action(action)
        if success:
            # Advance to execution phase if action was queued
            self.turn_manager._advance_phase(TurnPhase.EXECUTION)
        
        return success
    
    def _check_victory_conditions(self) -> bool:
        """Check if victory conditions are met"""
        # Default: all AI units defeated
        for unit_id in self.ai_units:
            unit = self.units.get(unit_id)
            if unit:
                attributes = unit.get_component(AttributeStats)
                if attributes and attributes.current_hp > 0:
                    return False
        return True
    
    def _check_defeat_conditions(self) -> bool:
        """Check if defeat conditions are met"""
        # Default: all player units defeated
        for unit_id in self.player_units:
            unit = self.units.get(unit_id)
            if unit:
                attributes = unit.get_component(AttributeStats)
                if attributes and attributes.current_hp > 0:
                    return False
        return True
    
    def end_battle(self, result: str):
        """
        End the current battle.
        
        Args:
            result: Battle result ("victory", "defeat", "draw")
        """
        print(f"Battle ended: {result}")
        self.is_battle_active = False
        self.turn_manager.end_combat()
        
        # Clear unit references
        self.units.clear()
        self.player_units.clear()
        self.ai_units.clear()
    
    def get_battle_state(self) -> dict:
        """Get comprehensive battle state"""
        return {
            'is_active': self.is_battle_active,
            'turn_summary': self.turn_manager.get_turn_summary(),
            'player_units': len(self.player_units),
            'ai_units': len(self.ai_units),
            'current_unit': self.turn_manager.get_current_unit(),
            'can_act': self.turn_manager.can_unit_act(self.turn_manager.get_current_unit() or -1)
        }