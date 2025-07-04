#!/usr/bin/env python3
"""
Test Action System Integration

Quick integration test to verify the new unified action system works properly.
Tests the complete flow: Effect System → Action System → Action Manager → Action Queue
"""

import sys
sys.path.append('src')

from game.config.feature_flags import FeatureFlags
from game.effects.effect_system import DamageEffect, HealingEffect, DamageType
from game.actions.action_system import Action, ActionType, get_action_registry
from game.managers.action_manager import ActionManager
from game.queue.action_queue import ActionQueue, ActionPriority
from core.events.event_bus import get_event_bus


class MockUnit:
    """Mock unit for testing."""
    def __init__(self, unit_id: str, hp: int = 100, mp: int = 50):
        self.id = unit_id
        self.hp = hp
        self.max_hp = hp
        self.mp = mp
        self.max_mp = mp
        self.alive = True
        self.action_cooldowns = {}
        
        # Basic stats
        self.physical_defense = 5
        self.magical_defense = 3
        self.spiritual_defense = 2
        
        self.x = 0
        self.y = 0
    
    def take_damage(self, damage: int, damage_type):
        """Take damage and update alive status."""
        self.hp = max(0, self.hp - damage)
        if self.hp <= 0:
            self.alive = False
    
    def __str__(self):
        return f"{self.id}(HP:{self.hp}/{self.max_hp})"


class MockGameController:
    """Mock game controller for testing."""
    def __init__(self):
        self.units = {}
        self.player_units = []
        self.enemy_units = []
        self.event_bus = get_event_bus()
        self.current_turn = 0
        self.battle_state = 'active'
    
    def add_unit(self, unit: MockUnit):
        self.units[unit.id] = unit


def test_effect_system():
    """Test that effects work correctly."""
    print("🧪 Testing Effect System...")
    
    # Create test units
    attacker = MockUnit("warrior", hp=100)
    defender = MockUnit("enemy", hp=80)
    
    # Test damage effect
    damage_effect = DamageEffect(damage=25, damage_type=DamageType.PHYSICAL)
    result = damage_effect.apply(defender, {})
    
    assert result['success'] == True
    assert defender.hp == 60  # 80 - (25-5 defense) = 60
    print(f"  ✅ Damage effect: {defender}")
    
    # Test healing effect
    heal_effect = HealingEffect(healing=15)
    result = heal_effect.apply(defender, {})
    
    assert result['success'] == True
    assert defender.hp == 75  # 60 + 15 = 75
    print(f"  ✅ Healing effect: {defender}")


def test_action_system():
    """Test that actions work correctly."""
    print("🧪 Testing Action System...")
    
    # Create test units
    caster = MockUnit("mage", hp=100, mp=50)
    target = MockUnit("target", hp=100)
    
    # Create action with effects
    fireball = Action("fireball", "Fireball", ActionType.MAGIC)
    fireball.add_effect(DamageEffect(30, damage_type=DamageType.MAGICAL))
    fireball.costs.mp_cost = 20
    fireball.targeting.range = 3
    
    # Test action execution
    result = fireball.execute(caster, [target], {})
    
    assert result['success'] == True
    assert caster.mp == 30  # 50 - 20 = 30
    assert target.hp == 73  # 100 - (30-3 magical defense) = 73
    print(f"  ✅ Action execution: Caster MP={caster.mp}, Target HP={target.hp}")
    
    # Register action
    registry = get_action_registry()
    registry.register(fireball)
    
    assert registry.get("fireball") == fireball
    print(f"  ✅ Action registry: {len(registry.actions)} actions registered")


def test_action_queue():
    """Test that action queue works correctly."""
    print("🧪 Testing Action Queue...")
    
    queue = ActionQueue()
    
    # Create test action
    attack = Action("sword_attack", "Sword Attack", ActionType.ATTACK)
    attack.add_effect(DamageEffect(20, damage_type=DamageType.PHYSICAL))
    
    # Queue some actions
    queue.queue_action("unit1", attack, [], ActionPriority.NORMAL)
    queue.queue_action("unit2", attack, [], ActionPriority.HIGH)
    queue.queue_action("unit1", attack, [], ActionPriority.LOW)
    
    # Test timeline resolution
    unit_stats = {
        "unit1": {"initiative": 60},
        "unit2": {"initiative": 80}
    }
    
    timeline = queue.resolve_timeline(unit_stats)
    
    assert len(timeline) == 3
    # High priority should be first
    assert timeline[0].queued_action.priority == ActionPriority.HIGH
    print(f"  ✅ Action queue: {len(timeline)} actions in timeline")
    
    # Test preview
    preview = queue.preview_timeline(unit_stats)
    assert len(preview) == 3
    print(f"  ✅ Queue preview: {preview[0]['unit_id']} goes first")


def test_action_manager():
    """Test that action manager integrates everything."""
    print("🧪 Testing Action Manager...")
    
    # Create mock controller
    controller = MockGameController()
    
    # Create test units
    player_unit = MockUnit("player1", hp=100, mp=50)
    enemy_unit = MockUnit("enemy1", hp=80)
    
    controller.add_unit(player_unit)
    controller.add_unit(enemy_unit)
    
    # Create action manager
    manager = ActionManager(controller)
    manager.initialize()
    
    # Create and register a test action
    magic_missile = Action("magic_missile", "Magic Missile", ActionType.MAGIC)
    magic_missile.add_effect(DamageEffect(15, damage_type=DamageType.MAGICAL))
    magic_missile.costs.mp_cost = 10
    
    manager.action_registry.register(magic_missile)
    
    # Test queuing action
    success = manager.queue_action("player1", "magic_missile", [enemy_unit])
    assert success == True
    print(f"  ✅ Action queued successfully")
    
    # Test execution
    unit_stats = {
        "player1": {"initiative": 70},
        "enemy1": {"initiative": 50}
    }
    
    results = manager.execute_queued_actions(unit_stats)
    assert len(results) == 1
    assert results[0]['success'] == True
    print(f"  ✅ Action executed: {enemy_unit}")
    
    # Test statistics
    stats = manager.get_action_statistics()
    assert stats['actions_executed'] == 1
    print(f"  ✅ Statistics: {stats['actions_executed']} actions executed")


def main():
    """Run all integration tests."""
    print("🚀 Starting Action System Integration Tests")
    print(f"📋 Feature Flags: {FeatureFlags.get_active_features()}")
    print()
    
    try:
        test_effect_system()
        print()
        
        test_action_system()
        print()
        
        test_action_queue()
        print()
        
        test_action_manager()
        print()
        
        print("🎉 All tests passed! Action system integration successful.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())