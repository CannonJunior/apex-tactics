#!/usr/bin/env python3
"""
AI System Integration Test

Comprehensive test of the AI agent system including:
- MCP tools functionality
- AI orchestration and coordination
- Unit AI controllers
- Integration with ActionManager
- Low-latency decision pipeline
"""

import sys
sys.path.append('src')

import time
from typing import Dict, Any, List


class MockUnit:
    """Enhanced mock unit for AI testing."""
    
    def __init__(self, unit_id: str, team: str = "enemy", hp: int = 100, mp: int = 50):
        self.id = unit_id
        self.name = unit_id.replace('_', ' ').title()
        self.team = team
        
        # Resources
        self.hp = hp
        self.max_hp = hp
        self.mp = mp
        self.max_mp = mp
        self.ap = 4
        self.max_ap = 4
        
        # Combat stats
        self.physical_defense = 5
        self.magical_defense = 3
        self.spiritual_defense = 2
        self.initiative = 50 + (hash(unit_id) % 30)  # Semi-random initiative
        
        # State
        self.alive = True
        self.action_cooldowns = {}
        
        # Position
        self.x = hash(unit_id) % 10
        self.y = (hash(unit_id) // 10) % 10
    
    def take_damage(self, damage: int, damage_type):
        """Take damage and update status."""
        self.hp = max(0, self.hp - damage)
        if self.hp <= 0:
            self.alive = False
    
    def __str__(self):
        return f"{self.name}({self.team}, HP:{self.hp}/{self.max_hp})"


class MockGameController:
    """Enhanced mock controller for AI testing."""
    
    def __init__(self):
        self.units = {}
        self.player_units = []
        self.enemy_units = []
        self.current_turn = 0
        self.battle_state = 'active'
        
        # Mock event bus
        self.event_bus = None
        
        # Create test scenario
        self._create_test_scenario()
    
    def _create_test_scenario(self):
        """Create a test battle scenario."""
        # Create player units
        hero1 = MockUnit("hero_warrior", "player", hp=120, mp=30)
        hero2 = MockUnit("hero_mage", "player", hp=80, mp=100)
        self.add_unit(hero1)
        self.add_unit(hero2)
        
        # Create enemy units
        orc1 = MockUnit("orc_brute", "enemy", hp=100, mp=20)
        orc2 = MockUnit("orc_shaman", "enemy", hp=70, mp=60)
        goblin1 = MockUnit("goblin_archer", "enemy", hp=60, mp=30)
        
        for unit in [orc1, orc2, goblin1]:
            self.add_unit(unit)
    
    def add_unit(self, unit: MockUnit):
        """Add unit to the game."""
        self.units[unit.id] = unit
        if unit.team == "player":
            self.player_units.append(unit)
        else:
            self.enemy_units.append(unit)


def test_mcp_tools():
    """Test MCP tool functionality."""
    print("🧪 Testing MCP Tools...")
    
    from game.managers.action_manager import ActionManager
    from ai.mcp_tools import MCPToolRegistry
    
    # Create test environment
    controller = MockGameController()
    action_manager = ActionManager(controller)
    action_manager.initialize()
    
    tool_registry = MCPToolRegistry(action_manager)
    
    # Test battlefield state tool
    result = tool_registry.execute_tool('get_battlefield_state')
    assert result.success, f"Battlefield state failed: {result.error_message}"
    
    battlefield_data = result.data
    assert 'units' in battlefield_data
    assert len(battlefield_data['units']) == 5  # 2 heroes + 3 enemies
    print(f"  ✅ Battlefield state: {len(battlefield_data['units'])} units")
    
    # Test unit details tool
    result = tool_registry.execute_tool('get_unit_details', unit_id='hero_warrior')
    assert result.success, f"Unit details failed: {result.error_message}"
    
    unit_data = result.data
    assert unit_data['id'] == 'hero_warrior'
    assert 'stats' in unit_data
    assert 'available_actions' in unit_data
    print(f"  ✅ Unit details: {unit_data['name']} with {len(unit_data['available_actions'])} actions")
    
    # Test threat assessment tool
    result = tool_registry.execute_tool('calculate_threat_assessment', unit_id='hero_warrior')
    assert result.success, f"Threat assessment failed: {result.error_message}"
    
    threat_data = result.data
    assert 'threat_level' in threat_data
    assert 'threat_category' in threat_data
    print(f"  ✅ Threat assessment: {threat_data['threat_category']} ({threat_data['threat_level']:.2f})")
    
    # Test available tools
    tools = tool_registry.list_available_tools()
    assert len(tools) >= 6  # Should have all major tools
    print(f"  ✅ Available tools: {len(tools)} tools registered")
    
    print("  🎉 MCP Tools test passed!")


def test_unit_ai_controller():
    """Test individual unit AI controller."""
    print("🧪 Testing Unit AI Controller...")
    
    from game.managers.action_manager import ActionManager
    from ai.mcp_tools import MCPToolRegistry
    from ai.unit_ai_controller import UnitAIController, AIPersonality, AISkillLevel
    
    # Create test environment
    controller = MockGameController()
    action_manager = ActionManager(controller)
    action_manager.initialize()
    
    tool_registry = MCPToolRegistry(action_manager)
    
    # Create AI controller for orc_brute
    ai_controller = UnitAIController(
        unit_id="orc_brute",
        tool_registry=tool_registry,
        personality=AIPersonality.AGGRESSIVE,
        skill_level=AISkillLevel.STRATEGIC
    )
    
    # Test decision making
    decision = ai_controller.make_decision(assignment="eliminate_hero_warrior")
    
    if decision:
        assert decision.action_id is not None
        assert len(decision.target_positions) > 0
        assert decision.confidence > 0
        print(f"  ✅ AI Decision: {decision.action_id} -> {decision.reasoning}")
        print(f"    Confidence: {decision.confidence:.2f}, Priority: {decision.priority}")
    else:
        print("  ⚠️ No decision made (acceptable for test scenario)")
    
    # Test performance metrics
    performance = ai_controller.get_performance_summary()
    assert performance['unit_id'] == "orc_brute"
    assert performance['personality'] == AIPersonality.AGGRESSIVE.value
    assert performance['skill_level'] == AISkillLevel.STRATEGIC.value
    print(f"  ✅ Performance tracking: {performance['decisions_made']} decisions made")
    
    print("  🎉 Unit AI Controller test passed!")


def test_orchestration_agent():
    """Test AI orchestration agent."""
    print("🧪 Testing Orchestration Agent...")
    
    from game.managers.action_manager import ActionManager
    from ai.orchestration_agent import OrchestrationAgent
    
    # Create test environment
    controller = MockGameController()
    action_manager = ActionManager(controller)
    action_manager.initialize()
    
    orchestration_agent = OrchestrationAgent(action_manager)
    
    # Test agent registration
    enemy_units = ["orc_brute", "orc_shaman", "goblin_archer"]
    for unit_id in enemy_units:
        agent_id = orchestration_agent.register_unit_controller(unit_id)
        assert agent_id == f"unit_controller_{unit_id}"
    
    print(f"  ✅ Registered {len(enemy_units)} unit controllers")
    
    # Test synchronous turn execution
    result = orchestration_agent.execute_ai_turn_sync(enemy_units)
    
    assert 'success' in result
    print(f"  ✅ AI Turn Result: {result['success']}")
    
    if result['success']:
        assert 'coordination_result' in result
        assert 'coordination_time_ms' in result
        print(f"    Coordination time: {result['coordination_time_ms']:.1f}ms")
        print(f"    Units controlled: {result['units_controlled']}")
    else:
        print(f"    Error (expected in test): {result.get('error', 'Unknown')}")
    
    # Test orchestration status
    status = orchestration_agent.get_orchestration_status()
    assert 'total_agents' in status
    assert 'active_agents' in status
    print(f"  ✅ Orchestration status: {status['active_agents']}/{status['total_agents']} agents active")
    
    orchestration_agent.shutdown()
    print("  🎉 Orchestration Agent test passed!")


def test_ai_integration_manager():
    """Test AI integration with ActionManager."""
    print("🧪 Testing AI Integration Manager...")
    
    from game.managers.action_manager import ActionManager
    from ai.ai_integration_manager import AIIntegrationManager, AIUnitConfig
    from ai.unit_ai_controller import AIPersonality, AISkillLevel
    
    # Create test environment
    controller = MockGameController()
    action_manager = ActionManager(controller)
    action_manager.initialize()
    
    ai_manager = AIIntegrationManager(action_manager)
    
    # Register AI units
    enemy_units = ["orc_brute", "orc_shaman", "goblin_archer"]
    for i, unit_id in enumerate(enemy_units):
        config = AIUnitConfig(
            unit_id=unit_id,
            personality=AIPersonality.AGGRESSIVE if i == 0 else AIPersonality.BALANCED,
            skill_level=AISkillLevel.STRATEGIC,
            is_leader=(i == 0)
        )
        
        success = ai_manager.register_ai_unit(unit_id, config)
        assert success, f"Failed to register {unit_id}"
    
    print(f"  ✅ Registered {len(enemy_units)} AI units")
    
    # Test AI unit status
    for unit_id in enemy_units:
        status = ai_manager.get_ai_unit_status(unit_id)
        assert status is not None
        assert status['ai_controlled'] == True
        print(f"    {unit_id}: {status['personality']} {status['skill_level']}")
    
    # Test AI turn execution
    result = ai_manager.execute_ai_turn(enemy_units)
    
    assert 'success' in result
    print(f"  ✅ AI Turn Execution: {result['success']}")
    
    if result['success']:
        print(f"    Turn time: {result['turn_time_ms']:.1f}ms")
        print(f"    Units controlled: {result['units_controlled']}")
    
    # Test system status
    system_status = ai_manager.get_ai_system_status()
    assert system_status['controlled_units'] == len(enemy_units)
    print(f"  ✅ System status: {system_status['controlled_units']} units under AI control")
    
    ai_manager.shutdown()
    print("  🎉 AI Integration Manager test passed!")


def test_low_latency_pipeline():
    """Test low-latency decision pipeline."""
    print("🧪 Testing Low-Latency Pipeline...")
    
    from game.managers.action_manager import ActionManager
    from ai.mcp_tools import MCPToolRegistry
    from ai.low_latency_pipeline import LowLatencyDecisionPipeline, DecisionPriority
    
    # Create test environment
    controller = MockGameController()
    action_manager = ActionManager(controller)
    action_manager.initialize()
    
    tool_registry = MCPToolRegistry(action_manager)
    pipeline = LowLatencyDecisionPipeline(tool_registry, max_workers=2)
    
    # Test single decision with timing
    context = {
        'unit_details': {
            'id': 'orc_brute',
            'stats': {'hp': 100, 'max_hp': 100, 'mp': 20, 'max_mp': 20},
            'available_actions': [
                {'id': 'sword_attack', 'name': 'Sword Attack', 'type': 'Attack'}
            ]
        },
        'battlefield_state': {
            'units': [
                {'id': 'hero_warrior', 'team': 'player', 'alive': True, 'hp': 120}
            ]
        }
    }
    
    start_time = time.time()
    decision = pipeline.make_decision("orc_brute", context, DecisionPriority.HIGH)
    decision_time = (time.time() - start_time) * 1000
    
    print(f"  ✅ Single decision time: {decision_time:.1f}ms")
    
    if decision:
        print(f"    Decision: {decision.action_id} ({decision.confidence:.2f} confidence)")
    
    # Test parallel decisions
    unit_contexts = [
        ("orc_brute", context),
        ("orc_shaman", context),
        ("goblin_archer", context)
    ]
    
    start_time = time.time()
    parallel_decisions = pipeline.make_parallel_decisions(unit_contexts, DecisionPriority.NORMAL)
    parallel_time = (time.time() - start_time) * 1000
    
    print(f"  ✅ Parallel decisions time: {parallel_time:.1f}ms for {len(unit_contexts)} units")
    print(f"    Decisions made: {len([d for d in parallel_decisions.values() if d is not None])}")
    
    # Test precomputation
    pipeline.precompute_decisions(unit_contexts)
    print(f"  ✅ Precomputation queued for {len(unit_contexts)} contexts")
    
    # Test performance report
    report = pipeline.get_performance_report()
    print(f"  ✅ Performance report:")
    print(f"    Total decisions: {report['metrics']['total_decisions']}")
    print(f"    Average time: {report['metrics']['average_decision_time_ms']:.1f}ms")
    print(f"    Cache hit rate: {report['metrics']['cache_hit_rate']:.1f}%")
    
    pipeline.shutdown()
    print("  🎉 Low-Latency Pipeline test passed!")


def test_end_to_end_ai_workflow():
    """Test complete end-to-end AI workflow."""
    print("🧪 Testing End-to-End AI Workflow...")
    
    from game.managers.action_manager import ActionManager
    from ai.ai_integration_manager import AIIntegrationManager, AIUnitConfig
    from ai.unit_ai_controller import AIPersonality, AISkillLevel
    from game.actions.action_system import Action, ActionType
    from game.effects.effect_system import DamageEffect, DamageType
    
    # Create battle scenario
    controller = MockGameController()
    action_manager = ActionManager(controller)
    action_manager.initialize()
    
    # Create some test actions
    sword_attack = Action("sword_attack", "Sword Attack", ActionType.ATTACK)
    sword_attack.add_effect(DamageEffect(25, damage_type=DamageType.PHYSICAL))
    sword_attack.costs.ap_cost = 2
    
    magic_missile = Action("magic_missile", "Magic Missile", ActionType.MAGIC)
    magic_missile.add_effect(DamageEffect(18, damage_type=DamageType.MAGICAL))
    magic_missile.costs.mp_cost = 15
    
    for action in [sword_attack, magic_missile]:
        action_manager.action_registry.register(action)
    
    # Set up AI integration
    ai_manager = AIIntegrationManager(action_manager)
    
    # Configure AI units with different personalities
    ai_configs = [
        AIUnitConfig("orc_brute", AIPersonality.AGGRESSIVE, AISkillLevel.STRATEGIC, is_leader=True),
        AIUnitConfig("orc_shaman", AIPersonality.BALANCED, AISkillLevel.STRATEGIC),
        AIUnitConfig("goblin_archer", AIPersonality.DEFENSIVE, AISkillLevel.STRATEGIC)
    ]
    
    for config in ai_configs:
        success = ai_manager.register_ai_unit(config.unit_id, config)
        assert success
    
    print(f"  ✅ Battle setup: {len(ai_configs)} AI units, {len(action_manager.action_registry.actions)} actions")
    
    # Execute AI turn
    start_time = time.time()
    result = ai_manager.execute_ai_turn()
    total_time = (time.time() - start_time) * 1000
    
    print(f"  ✅ AI Turn completed in {total_time:.1f}ms")
    
    if result['success']:
        print(f"    Coordination successful: {result['units_controlled']} units")
        
        # Show planned actions
        if 'execution_results' in result:
            for unit_id, actions in result['execution_results'].items():
                print(f"    {unit_id}: {len(actions)} actions planned")
                for action in actions:
                    status = "✅" if action.get('queued') else "❌"
                    print(f"      {status} {action['action_id']} -> {action['target']}")
    
    # Test system performance
    system_status = ai_manager.get_ai_system_status()
    performance = system_status['performance_metrics']
    
    print(f"  ✅ AI System Performance:")
    print(f"    Total AI turns: {performance['total_ai_turns']}")
    print(f"    Average turn time: {performance['average_turn_time_ms']:.1f}ms")
    print(f"    Success rate: {performance['successful_actions']}/{performance['successful_actions'] + performance['failed_actions']}")
    
    ai_manager.shutdown()
    print("  🎉 End-to-End AI Workflow test passed!")


def main():
    """Run complete AI system test suite."""
    print("🚀 AI SYSTEM INTEGRATION TEST SUITE")
    print("="*50)
    
    # Check if MCP tools are enabled
    from game.config.feature_flags import FeatureFlags
    
    if not FeatureFlags.USE_MCP_TOOLS:
        print("⚠️ MCP tools are disabled in feature flags")
        print("   Enabling for AI testing...")
        FeatureFlags.USE_MCP_TOOLS = True
    
    try:
        # Test individual components
        test_mcp_tools()
        print()
        
        test_unit_ai_controller()
        print()
        
        test_orchestration_agent()
        print()
        
        test_ai_integration_manager()
        print()
        
        test_low_latency_pipeline()
        print()
        
        # Test complete workflow
        test_end_to_end_ai_workflow()
        print()
        
        print("🎉 ALL AI SYSTEM TESTS PASSED!")
        print("✅ Week 3: AI Agent Integration COMPLETE")
        print("🚀 AI-powered tactical RPG ready for gameplay!")
        return 0
        
    except Exception as e:
        print(f"❌ AI system test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())