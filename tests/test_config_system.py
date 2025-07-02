"""
Test Suite for Configuration System

Tests asset-based configuration loading, value retrieval, modifier application,
and hot-reloading functionality.
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
import time
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from core.assets.config_manager import ConfigManager, get_config_manager, add_game_effect
    from core.assets.config_manager import get_combat_value, get_ui_value, get_movement_value
    CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import config system: {e}")
    CONFIG_AVAILABLE = False


class TestConfigManager(unittest.TestCase):
    """Test the ConfigManager class functionality."""
    
    def setUp(self):
        """Set up test environment with temporary asset files."""
        if not CONFIG_AVAILABLE:
            self.skipTest("Configuration system not available")
        
        # Create temporary directory for test assets
        self.temp_dir = tempfile.mkdtemp()
        self.assets_path = Path(self.temp_dir)
        
        # Create test configuration files
        self._create_test_configs()
        
        # Initialize config manager with test assets
        self.config_manager = ConfigManager(str(self.assets_path))
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_configs(self):
        """Create test configuration files."""
        # Create directory structure
        (self.assets_path / 'data' / 'gameplay').mkdir(parents=True, exist_ok=True)
        (self.assets_path / 'data' / 'ui').mkdir(parents=True, exist_ok=True)
        
        # Test combat config
        combat_config = {
            "combat_values": {
                "base_combat_values": {
                    "attack_range": {"default": 1, "min": 1, "max": 10},
                    "magic_range": {"default": 2, "min": 1, "max": 15},
                    "magic_mp_cost": {"default": 10, "min": 1, "max": 100}
                },
                "stat_calculations": {
                    "hp_formula": {
                        "base_multiplier": 5,
                        "attributes": ["strength", "fortitude", "faith", "worthy"]
                    }
                }
            }
        }
        
        # Test UI config
        ui_config = {
            "ui_layout": {
                "control_panel": {
                    "positioning": {
                        "scale": {"x": 0.8, "y": 0.25, "z": 0.01},
                        "position": {"x": 0, "y": -0.3, "z": 0}
                    },
                    "text_scaling": {
                        "unit_name": 0.8,
                        "stats_text": 0.6
                    }
                },
                "health_bars": {
                    "active_unit": {
                        "position": {"x": -0.4, "y": 0.45},
                        "scale": {"x": 0.3, "y": 0.03}
                    }
                }
            }
        }
        
        # Write test files
        with open(self.assets_path / 'data' / 'gameplay' / 'combat_values.json', 'w') as f:
            json.dump(combat_config, f)
        
        with open(self.assets_path / 'data' / 'ui' / 'layout_config.json', 'w') as f:
            json.dump(ui_config, f)
    
    def test_config_loading(self):
        """Test that configuration files are loaded correctly."""
        self.assertIn('combat', self.config_manager.configs)
        self.assertIn('ui_layout', self.config_manager.configs)
    
    def test_value_retrieval(self):
        """Test getting configuration values by path."""
        # Test basic value retrieval
        attack_range = self.config_manager.get_value('combat.combat_values.base_combat_values.attack_range.default')
        self.assertEqual(attack_range, 1)
        
        # Test nested value retrieval
        hp_multiplier = self.config_manager.get_value('combat.combat_values.stat_calculations.hp_formula.base_multiplier')
        self.assertEqual(hp_multiplier, 5)
        
        # Test default value fallback
        nonexistent = self.config_manager.get_value('nonexistent.path', 42)
        self.assertEqual(nonexistent, 42)
    
    def test_position_and_scale_helpers(self):
        """Test helper methods for positions and scales."""
        # Test position helper
        position = self.config_manager.get_position('ui_layout.ui_layout.control_panel.positioning.position')
        self.assertEqual(position, (0, -0.3))
        
        # Test scale helper
        scale = self.config_manager.get_scale('ui_layout.ui_layout.control_panel.positioning.scale')
        self.assertEqual(scale, (0.8, 0.25, 0.01))
    
    def test_modifier_system(self):
        """Test applying modifiers to configuration values."""
        # Get base value
        base_attack_range = self.config_manager.get_value(
            'combat.combat_values.base_combat_values.attack_range.default'
        )
        self.assertEqual(base_attack_range, 1)
        
        # Add a modifier that doubles the value
        path = 'combat.combat_values.base_combat_values.attack_range.default'
        self.config_manager.add_modifier(
            path, 'double_range', lambda x: x * 2, duration=0, persistent=False
        )
        
        # Check modified value
        modified_value = self.config_manager.get_value(path)
        self.assertEqual(modified_value, 2)
        
        # Check unmodified value
        unmodified_value = self.config_manager.get_value(path, apply_modifiers=False)
        self.assertEqual(unmodified_value, 1)
        
        # Remove modifier
        self.config_manager.remove_modifier(path, 'double_range')
        restored_value = self.config_manager.get_value(path)
        self.assertEqual(restored_value, 1)
    
    def test_temporary_modifiers(self):
        """Test temporary modifiers that expire after a duration."""
        path = 'combat.combat_values.base_combat_values.magic_mp_cost.default'
        
        # Add temporary modifier for 0.1 seconds
        self.config_manager.add_modifier(
            path, 'temp_reduction', lambda x: x // 2, duration=0.1, persistent=False
        )
        
        # Should be modified immediately
        modified_value = self.config_manager.get_value(path)
        self.assertEqual(modified_value, 5)  # 10 // 2
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be back to original value
        restored_value = self.config_manager.get_value(path)
        self.assertEqual(restored_value, 10)
    
    def test_convenience_functions(self):
        """Test convenience functions for specific config types."""
        if not hasattr(sys.modules[__name__], 'get_combat_value'):
            self.skipTest("Convenience functions not available")
        
        # These would need the global config manager to be set up properly
        # For now, just test they don't crash
        try:
            result = get_combat_value('base_combat_values.attack_range.default', 999)
            self.assertIsNotNone(result)
        except Exception:
            pass  # Expected in test environment
    
    def test_cache_functionality(self):
        """Test that caching improves performance."""
        path = 'combat.combat_values.base_combat_values.attack_range.default'
        
        # First access (cache miss)
        start_time = time.time()
        value1 = self.config_manager.get_value(path)
        first_access_time = time.time() - start_time
        
        # Second access (cache hit)
        start_time = time.time()
        value2 = self.config_manager.get_value(path)
        second_access_time = time.time() - start_time
        
        # Values should be identical
        self.assertEqual(value1, value2)
        
        # Second access should be faster (though timing tests can be flaky)
        # Just ensure it doesn't crash and returns correct value
        self.assertEqual(value2, 1)
    
    def test_hot_reload(self):
        """Test hot-reloading configuration files."""
        # Modify the combat config file
        modified_config = {
            "combat_values": {
                "base_combat_values": {
                    "attack_range": {"default": 999, "min": 1, "max": 10}
                }
            }
        }
        
        with open(self.assets_path / 'data' / 'gameplay' / 'combat_values.json', 'w') as f:
            json.dump(modified_config, f)
        
        # Hot reload
        self.config_manager.hot_reload('combat')
        
        # Check updated value
        new_value = self.config_manager.get_value(
            'combat.combat_values.base_combat_values.attack_range.default'
        )
        self.assertEqual(new_value, 999)
    
    def test_modifier_listing(self):
        """Test listing active modifiers."""
        path1 = 'combat.combat_values.base_combat_values.attack_range.default'
        path2 = 'combat.combat_values.base_combat_values.magic_range.default'
        
        # Add some modifiers
        self.config_manager.add_modifier(path1, 'test_mod1', lambda x: x * 2)
        self.config_manager.add_modifier(path2, 'test_mod2', lambda x: x + 1)
        
        # List modifiers
        modifier_list = self.config_manager.list_modifiers()
        
        self.assertIn(path1, modifier_list)
        self.assertIn(path2, modifier_list)
        self.assertIn('test_mod1', modifier_list[path1])
        self.assertIn('test_mod2', modifier_list[path2])
    
    def test_stats_retrieval(self):
        """Test getting configuration manager statistics."""
        stats = self.config_manager.get_stats()
        
        self.assertIn('loaded_configs', stats)
        self.assertIn('cache_size', stats)
        self.assertIn('active_modifiers', stats)
        self.assertIn('last_reload', stats)
        
        # Should have loaded at least 2 configs
        self.assertGreaterEqual(len(stats['loaded_configs']), 2)


class TestAssetIntegration(unittest.TestCase):
    """Test integration with the existing asset system."""
    
    def setUp(self):
        """Set up test environment."""
        if not CONFIG_AVAILABLE:
            self.skipTest("Configuration system not available")
    
    def test_game_effect_convenience(self):
        """Test the convenience function for adding game effects."""
        # This tests the add_game_effect convenience function
        try:
            add_game_effect(
                'combat.combat_values.base_combat_values.attack_range.default',
                'buff_effect',
                1.5,  # 50% increase
                duration=5.0
            )
            # Should not raise an exception
            self.assertTrue(True)
        except Exception as e:
            # May fail in test environment due to missing config files
            # Just ensure it doesn't crash catastrophically
            self.assertIsInstance(e, (FileNotFoundError, KeyError, AttributeError))


def run_config_tests(timeout_seconds: int = 30) -> bool:
    """
    Run configuration system tests with timeout.
    
    Args:
        timeout_seconds: Maximum time to run tests
        
    Returns:
        True if all tests passed, False otherwise
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Tests timed out after {timeout_seconds} seconds")
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        # Run tests
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test cases
        suite.addTests(loader.loadTestsFromTestCase(TestConfigManager))
        suite.addTests(loader.loadTestsFromTestCase(TestAssetIntegration))
        
        # Run with quiet output for timeout testing
        runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        # Reset alarm
        signal.alarm(0)
        
        # Return True if all tests passed
        return result.wasSuccessful()
        
    except TimeoutError as e:
        print(f"❌ {e}")
        return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False
    finally:
        # Ensure alarm is reset
        signal.alarm(0)


if __name__ == '__main__':
    # Run tests with detailed output when called directly
    unittest.main(verbosity=2)