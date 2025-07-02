"""
Test for UI Configuration Replacement

Simple test to verify that UI configuration values are loaded from assets
instead of being hard-coded.
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
    from core.assets.config_manager import ConfigManager
    CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import config system: {e}")
    CONFIG_AVAILABLE = False


class TestUIConfigReplacement(unittest.TestCase):
    """Test that UI values are loaded from configuration instead of hard-coded."""
    
    def setUp(self):
        """Set up test environment with temporary asset files."""
        if not CONFIG_AVAILABLE:
            self.skipTest("Configuration system not available")
        
        # Create temporary directory for test assets
        self.temp_dir = tempfile.mkdtemp()
        self.assets_path = Path(self.temp_dir)
        
        # Create test configuration files
        self._create_test_ui_config()
        
        # Initialize config manager with test assets
        self.config_manager = ConfigManager(str(self.assets_path))
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_ui_config(self):
        """Create test UI configuration file."""
        # Create directory structure
        (self.assets_path / 'data' / 'ui').mkdir(parents=True, exist_ok=True)
        
        # Test UI config - using DIFFERENT values from the original hard-coded ones
        # This proves the values are being loaded from config, not hard-coded
        ui_config = {
            "ui_layout": {
                "control_panel": {
                    "main_panel": {
                        "scale": {"x": 0.9, "y": 0.3, "z": 0.02},  # Original: (0.8, 0.25, 0.01)
                        "position": {"x": 0.1, "y": -0.2, "z": 0.1},  # Original: (0, -0.3, 0)
                        "color": {"r": 0.2, "g": 0.2, "b": 0.25, "a": 0.8}  # Original: (0.1, 0.1, 0.15, 0.9)
                    },
                    "text_elements": {
                        "unit_info": {
                            "position": {"x": 0.05, "y": 0.1, "z": 0.02},  # Original: (0, 0.08, 0.01)
                            "scale": 0.9  # Original: 0.8
                        },
                        "end_turn_button": {
                            "position": {"x": 0.05, "y": -0.07, "z": 0.02},  # Original: (0, -0.08, 0.01)
                            "scale": 0.09  # Original: 0.08
                        }
                    },
                    "carousel": {
                        "label": {
                            "position": {"x": -0.4, "y": -0.4, "z": 0.05},  # Original: (-0.45, -0.45, 0)
                            "scale": 0.9,  # Original: 0.8
                            "text": "Battle Order:"  # Original: "Turn Order:"
                        }
                    }
                }
            }
        }
        
        # Write test file
        with open(self.assets_path / 'data' / 'ui' / 'layout_config.json', 'w') as f:
            json.dump(ui_config, f)
    
    def test_control_panel_scale_replaced(self):
        """Test that control panel scale is loaded from config, not hard-coded."""
        # Get scale from configuration
        panel_scale = self.config_manager.get_scale(
            'ui_layout.ui_layout.control_panel.main_panel.scale'
        )
        
        # Should get our test values, not the original hard-coded ones
        self.assertEqual(panel_scale, (0.9, 0.3, 0.02))
        
        # Verify it's NOT the original hard-coded value
        self.assertNotEqual(panel_scale, (0.8, 0.25, 0.01))
    
    def test_control_panel_position_replaced(self):
        """Test that control panel position is loaded from config."""
        panel_position = self.config_manager.get_scale(
            'ui_layout.ui_layout.control_panel.main_panel.position'
        )
        
        # Should get our test values
        self.assertEqual(panel_position, (0.1, -0.2, 0.1))
        
        # Verify it's NOT the original hard-coded value
        self.assertNotEqual(panel_position, (0, -0.3, 0))
    
    def test_control_panel_color_replaced(self):
        """Test that control panel color is loaded from config."""
        panel_color = self.config_manager.get_color(
            'ui_layout.ui_layout.control_panel.main_panel.color'
        )
        
        # The get_color method returns a color object, so we test the source data
        color_data = self.config_manager.get_value(
            'ui_layout.ui_layout.control_panel.main_panel.color'
        )
        
        expected = {"r": 0.2, "g": 0.2, "b": 0.25, "a": 0.8}
        self.assertEqual(color_data, expected)
    
    def test_text_element_positions_replaced(self):
        """Test that text element positions are loaded from config."""
        unit_info_pos = self.config_manager.get_scale(
            'ui_layout.ui_layout.control_panel.text_elements.unit_info.position'
        )
        
        # Should get our test values
        self.assertEqual(unit_info_pos, (0.05, 0.1, 0.02))
        
        # Verify it's NOT the original hard-coded value
        self.assertNotEqual(unit_info_pos, (0, 0.08, 0.01))
    
    def test_text_element_scales_replaced(self):
        """Test that text element scales are loaded from config."""
        unit_info_scale = self.config_manager.get_value(
            'ui_layout.ui_layout.control_panel.text_elements.unit_info.scale'
        )
        
        # Should get our test value
        self.assertEqual(unit_info_scale, 0.9)
        
        # Verify it's NOT the original hard-coded value
        self.assertNotEqual(unit_info_scale, 0.8)
    
    def test_carousel_text_replaced(self):
        """Test that carousel text is loaded from config."""
        carousel_text = self.config_manager.get_value(
            'ui_layout.ui_layout.control_panel.carousel.label.text'
        )
        
        # Should get our test value
        self.assertEqual(carousel_text, "Battle Order:")
        
        # Verify it's NOT the original hard-coded value
        self.assertNotEqual(carousel_text, "Turn Order:")
    
    def test_carousel_position_replaced(self):
        """Test that carousel position is loaded from config."""
        carousel_pos = self.config_manager.get_scale(
            'ui_layout.ui_layout.control_panel.carousel.label.position'
        )
        
        # Should get our test values
        self.assertEqual(carousel_pos, (-0.4, -0.4, 0.05))
        
        # Verify it's NOT the original hard-coded value
        self.assertNotEqual(carousel_pos, (-0.45, -0.45, 0))
    
    def test_fallback_to_defaults(self):
        """Test that system falls back to defaults when config missing."""
        # Test a path that doesn't exist in our config
        missing_value = self.config_manager.get_value(
            'ui_layout.ui_layout.control_panel.nonexistent.value',
            'default_fallback'
        )
        
        self.assertEqual(missing_value, 'default_fallback')
    
    def test_hot_reload_functionality(self):
        """Test that configuration can be hot-reloaded with new values."""
        # Modify the config file with new values
        updated_config = {
            "ui_layout": {
                "control_panel": {
                    "carousel": {
                        "label": {
                            "text": "Turn Sequence:",
                            "scale": 1.2
                        }
                    }
                }
            }
        }
        
        with open(self.assets_path / 'data' / 'ui' / 'layout_config.json', 'w') as f:
            json.dump(updated_config, f)
        
        # Hot reload the configuration
        self.config_manager.hot_reload('ui_layout')
        
        # Check that new values are loaded
        new_text = self.config_manager.get_value(
            'ui_layout.ui_layout.control_panel.carousel.label.text'
        )
        new_scale = self.config_manager.get_value(
            'ui_layout.ui_layout.control_panel.carousel.label.scale'
        )
        
        self.assertEqual(new_text, "Turn Sequence:")
        self.assertEqual(new_scale, 1.2)


def run_ui_config_test(timeout_seconds: int = 10) -> bool:
    """
    Run UI configuration replacement tests with timeout.
    
    Args:
        timeout_seconds: Maximum time to run tests
        
    Returns:
        True if all tests passed, False otherwise
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"UI config tests timed out after {timeout_seconds} seconds")
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        # Run tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestUIConfigReplacement)
        
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
        print(f"❌ UI config test execution failed: {e}")
        return False
    finally:
        # Ensure alarm is reset
        signal.alarm(0)


if __name__ == '__main__':
    # Run tests with detailed output when called directly
    unittest.main(verbosity=2)