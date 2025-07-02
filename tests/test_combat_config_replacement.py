"""
Test for Combat Configuration Replacement

Tests that the Unit class correctly loads combat values from configuration files
instead of using hard-coded values.
"""

import unittest
import sys
import os
import tempfile
import json
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from core.assets.config_manager import ConfigManager, set_config_manager
    from core.models.unit_types import UnitType
    from core.models.unit import Unit
    CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import required modules: {e}")
    CONFIG_AVAILABLE = False


class TestCombatConfigReplacement(unittest.TestCase):
    """Test that combat values are loaded from configuration instead of hard-coded."""
    
    def setUp(self):
        """Set up test environment with temporary asset files."""
        if not CONFIG_AVAILABLE:
            self.skipTest("Configuration system not available")
        
        # Create temporary directory for test assets
        self.temp_dir = tempfile.mkdtemp()
        self.assets_path = Path(self.temp_dir)
        
        # Create test configuration files
        self._create_test_combat_config()
        self._create_test_unit_config()
        
        # Initialize config manager with test assets
        self.config_manager = ConfigManager(str(self.assets_path))
        
        # Set as global config manager for unit creation
        set_config_manager(self.config_manager)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        
        # Reset global config manager
        set_config_manager(None)
        
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_combat_config(self):
        """Create test combat configuration file."""
        # Create directory structure
        (self.assets_path / 'data' / 'gameplay').mkdir(parents=True, exist_ok=True)
        
        # Test combat config with DIFFERENT values from defaults to prove loading
        combat_config = {
            "combat_values": {
                "stat_calculations": {
                    "hp_formula": {
                        "base_multiplier": 7,  # Original: 5
                        "attributes": ["strength", "fortitude", "faith", "worthy"]
                    },
                    "mp_formula": {
                        "base_multiplier": 4,  # Original: 3
                        "attributes": ["wisdom", "wonder", "spirit", "finesse"]
                    },
                    "rage_formula": {
                        "base_multiplier": 3,  # Original: 2
                        "attributes": ["strength", "fortitude"]
                    },
                    "kwan_formula": {
                        "base_multiplier": 3,  # Original: 2
                        "attributes": ["faith", "worthy", "spirit"]
                    }
                },
                "attack_calculations": {
                    "physical_attack": {
                        "divisor": 3,  # Original: 2
                        "attributes": ["speed", "strength", "finesse"]
                    },
                    "magical_attack": {
                        "divisor": 3,  # Original: 2
                        "attributes": ["wisdom", "wonder", "spirit"]
                    },
                    "spiritual_attack": {
                        "divisor": 3,  # Original: 2
                        "attributes": ["faith", "fortitude", "worthy"]
                    }
                },
                "defense_calculations": {
                    "physical_defense": {
                        "divisor": 4,  # Original: 3
                        "attributes": ["speed", "strength", "fortitude"]
                    },
                    "magical_defense": {
                        "divisor": 4,  # Original: 3
                        "attributes": ["wisdom", "wonder", "finesse"]
                    },
                    "spiritual_defense": {
                        "divisor": 4,  # Original: 3
                        "attributes": ["spirit", "faith", "worthy"]
                    }
                },
                "base_combat_values": {
                    "attack_range": {"default": 2},  # Original: 1
                    "attack_effect_area": {"default": 1},  # Original: 0
                    "magic_range": {"default": 3},  # Original: 2
                    "magic_effect_area": {"default": 2},  # Original: 1
                    "magic_mp_cost": {"default": 15}  # Original: 10
                }
            }
        }
        
        # Write test file
        with open(self.assets_path / 'data' / 'gameplay' / 'combat_values.json', 'w') as f:
            json.dump(combat_config, f)
    
    def _create_test_unit_config(self):
        """Create test unit configuration file."""
        (self.assets_path / 'data' / 'units').mkdir(parents=True, exist_ok=True)
        
        unit_config = {
            "unit_generation": {
                "attribute_generation": {
                    "base_ranges": {
                        "min_value": 8,  # Original: 5
                        "max_value": 18  # Original: 15
                    },
                    "type_bonuses": {
                        "min_bonus": 5,  # Original: 3
                        "max_bonus": 10  # Original: 8
                    }
                },
                "unit_types": {
                    "HEROMANCER": {
                        "bonus_attributes": ["speed", "strength", "finesse"],
                        "magic_spell": "Heroic Blast"
                    },
                    "MAGI": {
                        "bonus_attributes": ["wisdom", "wonder", "finesse"],
                        "magic_spell": "Arcane Explosion"
                    }
                },
                "default_action_options": [
                    "Move", "Attack", "Spirit", "Magic", "Inventory", "Special"  # Added "Special"
                ]
            }
        }
        
        with open(self.assets_path / 'data' / 'units' / 'unit_generation.json', 'w') as f:
            json.dump(unit_config, f)
    
    def _create_test_movement_config(self):
        """Create test movement configuration file."""
        movement_config = {
            "movement_values": {
                "movement_calculations": {
                    "movement_points": {
                        "speed_divisor": 3,  # Original: 2
                        "base_addition": 3   # Original: 2
                    }
                }
            }
        }
        
        with open(self.assets_path / 'data' / 'gameplay' / 'movement_values.json', 'w') as f:
            json.dump(movement_config, f)
    
    def test_stat_multipliers_replaced(self):
        """Test that stat calculation multipliers are loaded from config."""
        # Test HP multiplier
        hp_mult = self.config_manager.get_value('combat.combat_values.stat_calculations.hp_formula.base_multiplier')
        self.assertEqual(hp_mult, 7)  # Our test value, not original 5
        
        # Test MP multiplier
        mp_mult = self.config_manager.get_value('combat.combat_values.stat_calculations.mp_formula.base_multiplier')
        self.assertEqual(mp_mult, 4)  # Our test value, not original 3
        
        # Test Rage multiplier
        rage_mult = self.config_manager.get_value('combat.combat_values.stat_calculations.rage_formula.base_multiplier')
        self.assertEqual(rage_mult, 3)  # Our test value, not original 2
    
    def test_attack_defense_divisors_replaced(self):
        """Test that attack and defense divisors are loaded from config."""
        # Test physical attack divisor
        phys_div = self.config_manager.get_value('combat.combat_values.attack_calculations.physical_attack.divisor')
        self.assertEqual(phys_div, 3)  # Our test value, not original 2
        
        # Test magical defense divisor
        mag_def_div = self.config_manager.get_value('combat.combat_values.defense_calculations.magical_defense.divisor')
        self.assertEqual(mag_def_div, 4)  # Our test value, not original 3
    
    def test_base_combat_values_replaced(self):
        """Test that base combat values are loaded from config."""
        # Test attack range
        attack_range = self.config_manager.get_value('combat.combat_values.base_combat_values.attack_range.default')
        self.assertEqual(attack_range, 2)  # Our test value, not original 1
        
        # Test magic MP cost
        mp_cost = self.config_manager.get_value('combat.combat_values.base_combat_values.magic_mp_cost.default')
        self.assertEqual(mp_cost, 15)  # Our test value, not original 10
    
    def test_unit_creation_uses_config(self):
        """Test that unit creation uses configuration values."""
        # Create movement config
        self._create_test_movement_config()
        self.config_manager.hot_reload()  # Reload all configs
        
        # Create a test unit
        test_unit = Unit("TestHero", UnitType.HEROMANCER, 0, 0, 
                        strength=10, fortitude=10, faith=10, worthy=10,
                        wisdom=10, wonder=10, spirit=10, finesse=10, speed=10)
        
        # Test that HP uses new multiplier (7 instead of 5)
        expected_hp = (10 + 10 + 10 + 10) * 7  # 40 * 7 = 280
        self.assertEqual(test_unit.max_hp, expected_hp)
        self.assertNotEqual(test_unit.max_hp, 40 * 5)  # Not the original formula
        
        # Test that MP uses new multiplier (4 instead of 3)
        expected_mp = (10 + 10 + 10 + 10) * 4  # 40 * 4 = 160
        self.assertEqual(test_unit.max_mp, expected_mp)
        self.assertNotEqual(test_unit.max_mp, 40 * 3)  # Not the original formula
        
        # Test that base attack range uses config (2 instead of 1)
        self.assertEqual(test_unit.base_attack_range, 2)
        self.assertNotEqual(test_unit.base_attack_range, 1)
        
        # Test that magic MP cost uses config (15 instead of 10)
        self.assertEqual(test_unit.base_magic_mp_cost, 15)
        self.assertNotEqual(test_unit.base_magic_mp_cost, 10)
        
        # Test that action options use config (includes "Special")
        self.assertIn("Special", test_unit.action_options)
        self.assertEqual(len(test_unit.action_options), 6)  # Should have 6 actions now
    
    def test_attack_defense_formulas_use_config(self):
        """Test that attack and defense calculations use configuration divisors."""
        # Create a unit with known attributes
        test_unit = Unit("TestUnit", UnitType.MAGI, 0, 0,
                        speed=12, strength=12, finesse=12,
                        wisdom=12, wonder=12, spirit=12,
                        faith=12, fortitude=12, worthy=12)
        
        # Test physical attack uses new divisor (3 instead of 2)
        expected_phys_attack = (12 + 12 + 12) // 3  # 36 // 3 = 12
        self.assertEqual(test_unit.physical_attack, expected_phys_attack)
        self.assertNotEqual(test_unit.physical_attack, 36 // 2)  # Not original formula
        
        # Test magical defense uses new divisor (4 instead of 3)
        expected_mag_defense = (12 + 12 + 12) // 4  # 36 // 4 = 9
        self.assertEqual(test_unit.magical_defense, expected_mag_defense)
        self.assertNotEqual(test_unit.magical_defense, 36 // 3)  # Not original formula
    
    def test_attribute_ranges_use_config(self):
        """Test that attribute randomization uses configuration ranges."""
        # Get the configured ranges
        min_val = self.config_manager.get_value('units.unit_generation.attribute_generation.base_ranges.min_value')
        max_val = self.config_manager.get_value('units.unit_generation.attribute_generation.base_ranges.max_value')
        
        # Verify they're our test values
        self.assertEqual(min_val, 8)  # Our test value, not original 5
        self.assertEqual(max_val, 18)  # Our test value, not original 15
        
        # Create multiple units to test randomization range
        for _ in range(5):
            test_unit = Unit("TestUnit", UnitType.HEROMANCER, 0, 0)
            
            # All attributes should be within our configured range
            for attr in ['wisdom', 'wonder', 'worthy', 'faith', 'finesse', 
                        'fortitude', 'speed', 'spirit', 'strength']:
                attr_value = getattr(test_unit, attr)
                self.assertGreaterEqual(attr_value, min_val)
                # Note: Max could be higher due to type bonuses


def run_combat_config_test(timeout_seconds: int = 15) -> bool:
    """
    Run combat configuration replacement tests with timeout.
    
    Args:
        timeout_seconds: Maximum time to run tests
        
    Returns:
        True if all tests passed, False otherwise
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Combat config tests timed out after {timeout_seconds} seconds")
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        # Run tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestCombatConfigReplacement)
        
        # Run with minimal output for timeout testing
        runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        # Reset alarm
        signal.alarm(0)
        
        return result.wasSuccessful()
        
    except TimeoutError as e:
        print(f"❌ {e}")
        return False
    except Exception as e:
        print(f"❌ Combat config test execution failed: {e}")
        return False
    finally:
        # Ensure alarm is reset
        signal.alarm(0)


if __name__ == '__main__':
    # Run tests with detailed output when called directly
    unittest.main(verbosity=2)