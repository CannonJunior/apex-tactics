#!/usr/bin/env python3
"""
Simple Action System Test

Tests just the core action system components without complex dependencies.
"""

import sys
sys.path.append('src')

# Test individual components
def test_effects():
    """Test effect system independently."""
    print("🧪 Testing Effects...")
    
    from game.effects.effect_system import DamageEffect, HealingEffect, DamageType
    
    class SimpleUnit:
        def __init__(self, hp=100):
            self.hp = hp
            self.max_hp = hp
            self.alive = True
            self.physical_defense = 5
        
        def take_damage(self, damage, damage_type):
            self.hp = max(0, self.hp - damage)
            if self.hp <= 0:
                self.alive = False
    
    unit = SimpleUnit()
    
    # Test damage
    damage = DamageEffect(25, damage_type=DamageType.PHYSICAL)
    result = damage.apply(unit, {})
    
    print(f"  Damage result: {result}")
    print(f"  Unit HP: {unit.hp}/100")
    assert result['success'] == True
    assert unit.hp == 80  # 100 - (25-5) = 80
    
    # Test healing
    heal = HealingEffect(15)
    result = heal.apply(unit, {})
    
    print(f"  Heal result: {result}")
    print(f"  Unit HP: {unit.hp}/100")
    assert result['success'] == True
    assert unit.hp == 95  # 80 + 15 = 95
    
    print("  ✅ Effects working correctly")


def test_actions():
    """Test action system independently."""
    print("🧪 Testing Actions...")
    
    from game.effects.effect_system import DamageEffect, DamageType
    from game.actions.action_system import Action, ActionType
    
    class SimpleUnit:
        def __init__(self, hp=100, mp=50):
            self.hp = hp
            self.max_hp = hp
            self.mp = mp
            self.max_mp = mp
            self.alive = True
            self.physical_defense = 3
            self.magical_defense = 2
            self.action_cooldowns = {}
            self.x = 0
            self.y = 0
        
        def take_damage(self, damage, damage_type):
            self.hp = max(0, self.hp - damage)
            if self.hp <= 0:
                self.alive = False
    
    caster = SimpleUnit()
    target = SimpleUnit()
    
    # Create action with effect
    fireball = Action("fireball", "Fireball", ActionType.MAGIC)
    fireball.add_effect(DamageEffect(20, damage_type=DamageType.MAGICAL))
    fireball.costs.mp_cost = 15
    
    # Test execution
    result = fireball.execute(caster, [target], {})
    
    print(f"  Action result: {result}")
    print(f"  Caster MP: {caster.mp}/{caster.max_mp}")
    print(f"  Target HP: {target.hp}/{target.max_hp}")
    
    assert result['success'] == True
    assert caster.mp == 35  # 50 - 15 = 35
    assert target.hp == 82  # 100 - (20-2) = 82
    
    print("  ✅ Actions working correctly")


def test_queue():
    """Test action queue independently."""
    print("🧪 Testing Queue...")
    
    from game.queue.action_queue import ActionQueue, ActionPriority
    from game.actions.action_system import Action, ActionType
    
    queue = ActionQueue()
    
    # Create simple actions
    attack1 = Action("attack1", "Attack 1", ActionType.ATTACK)
    attack2 = Action("attack2", "Attack 2", ActionType.ATTACK)
    
    # Queue actions
    queue.queue_action("unit1", attack1, [], ActionPriority.NORMAL)
    queue.queue_action("unit2", attack2, [], ActionPriority.HIGH)
    queue.queue_action("unit1", attack1, [], ActionPriority.LOW)
    
    # Test timeline
    unit_stats = {
        "unit1": {"initiative": 60},
        "unit2": {"initiative": 80}
    }
    
    timeline = queue.resolve_timeline(unit_stats)
    
    print(f"  Timeline length: {len(timeline)}")
    print(f"  First action priority: {timeline[0].queued_action.priority.name}")
    
    assert len(timeline) == 3
    # High priority should be first
    assert timeline[0].queued_action.priority == ActionPriority.HIGH
    
    print("  ✅ Queue working correctly")


def main():
    """Run simple tests."""
    print("🚀 Simple Action System Tests")
    
    try:
        test_effects()
        print()
        
        test_actions()
        print()
        
        test_queue()
        print()
        
        print("🎉 All simple tests passed!")
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())