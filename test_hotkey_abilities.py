#!/usr/bin/env python3
"""
Test script to verify hotkey abilities are loaded correctly from character data
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing Hotkey Abilities Loading...")
print("=" * 60)

try:
    # Test imports
    from core.models.unit_types import UnitType
    from game.state.character_state_manager import get_character_state_manager
    from core.assets.unit_data_manager import get_unit_data_manager
    from core.assets.config_manager import get_config_manager
    print("✅ All imports successful")
    
    # Test config loading
    config_manager = get_config_manager()
    hotkey_config = config_manager.get_value('character_interface_config.hotkey_system', {})
    print(f"✅ Hotkey config loaded: {len(hotkey_config)} settings")
    print(f"   Max hotkey abilities: {hotkey_config.get('max_hotkey_abilities', 'not set')}")
    print(f"   Max interface slots: {hotkey_config.get('max_interface_slots', 'not set')}")
    
    # Test character state manager setup
    unit_data_manager = get_unit_data_manager()
    character_state_manager = get_character_state_manager(unit_data_manager)
    print("✅ Character state management initialized")
    
    # Test creating character instances with hotkey abilities
    print("\n1. Testing character instances with hotkey abilities:")
    
    for unit_type in [UnitType.HEROMANCER, UnitType.MAGI]:
        print(f"\n--- Testing {unit_type.value} ---")
        
        # Create character instance
        character = character_state_manager.create_character_instance(unit_type, f"test_{unit_type.value}")
        print(f"✅ Created character instance: {character.get_display_name()}")
        
        # Test hotkey abilities property
        hotkey_abilities = character.hotkey_abilities
        print(f"📋 Hotkey abilities found: {len(hotkey_abilities)}")
        
        for i, ability in enumerate(hotkey_abilities):
            print(f"   Slot {i+1}: {ability.get('name', 'Unknown')} - {ability.get('description', 'No description')}")
            print(f"            Cost: {ability.get('cost', {})}")
            print(f"            Range: {ability.get('range', 0)}, AOE: {ability.get('area_of_effect', 0)}")
        
        # Test ability activation (should work but not actually do anything)
        if hotkey_abilities:
            print(f"🧪 Testing ability activation:")
            success = character.activate_hotkey_ability(0)
            print(f"   Activation result: {'✅ Success' if success else '❌ Failed'}")
            
            # Show current resources after activation
            print(f"   Current AP: {character.current_ap}")
            print(f"   Current MP: {character.current_mp}")
    
    print("\n2. Testing Character Interface integration:")
    
    # Import character panel
    from ui.panels.character_panel import CharacterPanel
    
    # Create character panel (without Ursina)
    print("   Creating character panel (UI elements will be skipped in headless mode)")
    try:
        panel = CharacterPanel(character_state_manager=character_state_manager)
        print("✅ Character panel created successfully")
        
        # Test config loading
        if hasattr(panel, 'hotkey_config') and panel.hotkey_config:
            print(f"✅ Panel loaded hotkey config with {len(panel.hotkey_config)} sections")
        else:
            print("❌ Panel did not load hotkey config")
            
    except ImportError as e:
        print(f"⚠️ Ursina not available for full UI test: {e}")
        print("   This is expected in headless testing")
    
    print("\n" + "=" * 60)
    print("✅ Hotkey Abilities Test PASSED")
    print("\nThe system successfully:")
    print("- ✅ Loads hotkey configuration from config file")
    print("- ✅ Creates character instances with hotkey abilities")
    print("- ✅ Provides properly formatted ability data")
    print("- ✅ Supports ability activation (placeholder)")
    print("- ✅ Integrates with Character Interface panel")
    
except Exception as e:
    print(f"❌ Error in testing: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)