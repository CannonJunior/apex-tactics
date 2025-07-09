#!/usr/bin/env python3
"""
Test script for hotkey MCP tool implementation.

This script tests the dynamic hotkey talent system for AI agents.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai.simple_mcp_tools import SimpleMCPToolRegistry
from ai.unit_ai_controller import UnitAIController, AIPersonality, AISkillLevel


class MockUnit:
    """Mock unit for testing."""
    def __init__(self, name: str, character_instance_id: str = None):
        self.name = name
        self.x = 0
        self.y = 0
        self.hp = 100
        self.max_hp = 100
        self.ap = 5
        self.max_ap = 5
        self.character_instance_id = character_instance_id
        self.alive = True
        self.attack_range = 1
        self.magic_range = 2
        self.physical_attack = 10
        self.magical_attack = 8
        self.physical_defense = 5
        self.magical_defense = 3
        self.current_move_points = 3
        self.is_enemy_unit = True
    
    def take_damage(self, damage: int, damage_type: str):
        """Simulate taking damage."""
        self.hp = max(0, self.hp - damage)
        if self.hp <= 0:
            self.alive = False
        print(f"💥 {self.name} takes {damage} {damage_type} damage, HP: {self.hp}/{self.max_hp}")
    
    def can_move_to(self, x: int, y: int, grid) -> bool:
        """Check if unit can move to position."""
        distance = abs(x - self.x) + abs(y - self.y)
        return distance <= self.current_move_points


class MockCharacter:
    """Mock character with hotkey abilities."""
    def __init__(self):
        self.hotkey_abilities = [
            {
                'name': 'Fire Bolt',
                'talent_id': 'fire_bolt',
                'action_type': 'attack',
                'cost': {'ap': 2, 'mp': 3},
                'description': 'Launch a fiery projectile'
            },
            None,  # Empty slot
            {
                'name': 'Heal',
                'talent_id': 'heal',
                'action_type': 'heal',
                'cost': {'ap': 1, 'mp': 2},
                'description': 'Restore health to target'
            },
            None,  # Empty slot
            None,  # Empty slot
            {
                'name': 'Shield',
                'talent_id': 'shield',
                'action_type': 'buff',
                'cost': {'ap': 1, 'mp': 1},
                'description': 'Create protective barrier'
            },
            None,  # Empty slot
            None   # Empty slot
        ]


class MockCharacterStateManager:
    """Mock character state manager."""
    def __init__(self):
        self.characters = {
            'test_character_123': MockCharacter()
        }
    
    def get_character_instance(self, character_id: str):
        return self.characters.get(character_id)


class MockGameController:
    """Mock game controller for testing."""
    def __init__(self):
        # Create test units with proper positioning
        test_unit = MockUnit("TestUnit", "test_character_123")
        test_unit.x, test_unit.y = 1, 1
        
        enemy_unit = MockUnit("EnemyUnit", "enemy_character_456")
        enemy_unit.x, enemy_unit.y = 2, 2  # Closer to test unit (distance 2)
        enemy_unit.is_enemy_unit = False  # This is a player unit (enemy of AI)
        
        self.units = [test_unit, enemy_unit]
        self.character_state_manager = MockCharacterStateManager()
        self.grid = MockGrid()
        self.turn_manager = MockTurnManager()
        
        # Add units to grid
        self.grid.add_unit(test_unit)
        self.grid.add_unit(enemy_unit)
    
    def end_current_turn(self):
        print("🔄 Turn ended")


class MockGrid:
    """Mock grid for testing."""
    def __init__(self):
        self.width = 10
        self.height = 10
        self.units = {}
    
    def is_valid(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height
    
    def get_unit_at(self, x: int, y: int):
        return self.units.get((x, y))
    
    def add_unit(self, unit):
        self.units[(unit.x, unit.y)] = unit
    
    def remove_unit(self, unit):
        if (unit.x, unit.y) in self.units:
            del self.units[(unit.x, unit.y)]


class MockTurnManager:
    """Mock turn manager for testing."""
    def __init__(self):
        self.current_turn = 1
    
    def current_unit(self):
        return MockUnit("CurrentUnit")


def test_hotkey_mcp_tools():
    """Test the hotkey MCP tool implementation."""
    print("🧪 Testing Hotkey MCP Tool Implementation")
    print("=" * 50)
    
    # Setup
    game_controller = MockGameController()
    tool_registry = SimpleMCPToolRegistry(game_controller)
    
    # Test unit with character instance
    test_unit = game_controller.units[0]  # TestUnit with character_instance_id
    
    print(f"📋 Test Unit: {test_unit.name}")
    print(f"   Character Instance ID: {test_unit.character_instance_id}")
    print(f"   AP: {test_unit.ap}")
    print()
    
    # Test getting available actions (should include hotkey talents)
    print("🔍 Getting Available Actions...")
    actions_result = tool_registry.execute_tool('get_available_actions', unit_id=f"{test_unit.name}_{id(test_unit)}")
    
    if actions_result.success:
        actions = actions_result.data.get('actions', [])
        print(f"✅ Found {len(actions)} available actions:")
        
        talent_actions = [action for action in actions if action.get('talent_id') is not None]
        print(f"   Talent actions: {len(talent_actions)}")
        
        for action in talent_actions:
            print(f"   - {action['type']}: {action['description']} (AP: {action['ap_cost']})")
        
        print()
        
        # Test executing a talent
        if talent_actions:
            print("🔥 Testing Talent Execution...")
            first_talent = talent_actions[0]
            slot_index = first_talent['slot_index']
            talent_id = first_talent['talent_id']
            
            print(f"   Executing talent '{talent_id}' in slot {slot_index + 1}: {first_talent['ability_name']}")
            
            # Test with target position (use enemy unit position)
            enemy_unit = game_controller.units[1]  # EnemyUnit at (3, 3)
            execution_result = tool_registry.execute_tool(
                'execute_hotkey_talent',
                unit_id=f"{test_unit.name}_{id(test_unit)}",
                slot_index=slot_index,
                target_x=enemy_unit.x,
                target_y=enemy_unit.y
            )
            
            if execution_result.success:
                print(f"   ✅ Talent executed successfully!")
                print(f"   Result: {execution_result.data}")
            else:
                print(f"   ❌ Talent execution failed: {execution_result.error_message}")
        else:
            print("   ⚠️ No talent actions available for testing")
    else:
        print(f"❌ Failed to get available actions: {actions_result.error_message}")
    
    print()
    
    # Test new tactical analysis
    print("🔍 Testing New Tactical Analysis...")
    tactical_result = tool_registry.execute_tool('get_tactical_analysis', unit_id=f"{test_unit.name}_{id(test_unit)}")
    
    if tactical_result.success:
        tactical_data = tactical_result.data
        print(f"   ✅ Tactical analysis retrieved successfully")
        
        # Show unit info
        print(f"   📍 Unit Info:")
        print(f"      Position: ({tactical_data['unit_position']['x']}, {tactical_data['unit_position']['y']})")
        print(f"      Current AP: {tactical_data['current_ap']}")
        
        # Show enemy units
        enemy_units = tactical_data.get('enemy_units', [])
        print(f"   🎯 Enemy Units: {len(enemy_units)}")
        for enemy in enemy_units:
            print(f"      {enemy['name']}: ({enemy['position']['x']}, {enemy['position']['y']}) - {enemy['hp']}/{enemy['max_hp']} HP")
        
        # Show move-action combinations
        combinations = tactical_data.get('move_action_combinations', [])
        print(f"   🎲 Move-Action Combinations: {len(combinations)}")
        for i, combo in enumerate(combinations[:3]):  # Show top 3
            move_to = combo['move_to']
            best_action = combo['best_action']
            print(f"      {i+1}. Move to ({move_to['x']}, {move_to['y']}) (AP: {combo['move_ap_cost']})")
            if best_action:
                print(f"         -> {best_action['action_type']} {best_action['target']} for {best_action['damage']} damage (AP: {best_action['ap_cost']})")
            else:
                print(f"         -> No action available")
        
        # Show optimal combination
        optimal = tactical_data.get('optimal_combination')
        if optimal:
            print(f"   🏆 Optimal Combination:")
            print(f"      Move to: ({optimal['move_to']['x']}, {optimal['move_to']['y']})")
            if optimal['action']:
                print(f"      Action: {optimal['action']['action_type']} {optimal['action']['target']} for {optimal['total_damage']} damage")
                print(f"      Total AP: {optimal['ap_required']}")
        
        print()
    else:
        print(f"   ❌ Failed to get tactical analysis: {tactical_result.error_message}")
    
    # Test AI Controller with enhanced battlefield information
    print("🤖 Testing AI Controller with Enhanced Battlefield State...")
    ai_controller = UnitAIController(
        unit_id=f"{test_unit.name}_{id(test_unit)}",
        tool_registry=tool_registry,
        personality=AIPersonality.TACTICAL,
        skill_level=AISkillLevel.STRATEGIC
    )
    
    # Test AI decision making (should include hotkey talents)
    print("   Making AI decision...")
    decision = ai_controller.make_decision()
    
    if decision:
        print(f"   ✅ AI made decision: {decision.action_id}")
        print(f"   Reasoning: {decision.reasoning}")
        print(f"   Confidence: {decision.confidence}")
        
        if decision.action_id in ['fire_bolt', 'heal', 'shield']:
            print(f"   🎯 AI chose to use a specific talent: {decision.action_id}!")
        
    else:
        print("   ❌ AI failed to make decision")
    
    print()
    print("🧪 Hotkey MCP Tool Test Complete!")


if __name__ == "__main__":
    test_hotkey_mcp_tools()