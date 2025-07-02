"""
Test for Control Panel Configuration Replacement

Tests that the control panel correctly loads values from configuration files
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
    from core.assets.config_manager import ConfigManager
    CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import config system: {e}")
    CONFIG_AVAILABLE = False

# Mock Ursina components for testing
class MockText:
    def __init__(self, text, parent=None):
        self.text = text
        self.parent = parent
        self.position = (0, 0, 0)
        self.scale = 1.0

class MockEntity:
    def __init__(self, **kwargs):
        self.model = kwargs.get('model')
        self.scale = kwargs.get('scale', (1, 1, 1))
        self.color = kwargs.get('color')
        self.position = kwargs.get('position', (0, 0, 0))
        self.parent = kwargs.get('parent')

class MockButton:
    def __init__(self, **kwargs):
        self.text = kwargs.get('text', '')
        self.parent = kwargs.get('parent')
        self.position = (0, 0, 0)
        self.scale = 1.0
        self.on_click = None

class MockCamera:
    ui = None

# Mock the ursina imports
sys.modules['ursina'] = type(sys)('ursina')
sys.modules['ursina'].Text = MockText
sys.modules['ursina'].Entity = MockEntity
sys.modules['ursina'].Button = MockButton
sys.modules['ursina'].color = type(sys)('color')
sys.modules['ursina'].color.Color = lambda r, g, b, a: f"Color({r},{g},{b},{a})"
sys.modules['ursina'].camera = MockCamera()
sys.modules['ursina'].destroy = lambda x: None

# Now import the control panel after mocking
try:
    from ui.panels.control_panel import CharacterAttackInterface
    CONTROL_PANEL_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import control panel: {e}")
    CONTROL_PANEL_AVAILABLE = False


class TestControlPanelConfiguration(unittest.TestCase):
    """Test that control panel uses configuration values instead of hard-coded ones."""
    
    def setUp(self):
        """Set up test environment with temporary asset files."""
        if not CONFIG_AVAILABLE or not CONTROL_PANEL_AVAILABLE:
            self.skipTest("Configuration system or control panel not available")
        
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
        
        # Test UI config with modified values to verify they're being used
        ui_config = {
            "ui_layout": {
                "control_panel": {
                    "main_panel": {
                        "scale": {"x": 0.9, "y": 0.3, "z": 0.02},  # Modified from defaults
                        "position": {"x": 0.1, "y": -0.2, "z": 0.1},  # Modified from defaults
                        "color": {"r": 0.2, "g": 0.2, "b": 0.25, "a": 0.8}  # Modified from defaults
                    },
                    "text_elements": {
                        "unit_info": {
                            "position": {"x": 0.05, "y": 0.1, "z": 0.02},  # Modified
                            "scale": 0.9  # Modified
                        },
                        "camera_controls": {
                            "position": {"x": 0.05, "y": 0.05, "z": 0.02},  # Modified
                            "scale": 0.7  # Modified
                        },
                        "game_controls": {
                            "position": {"x": 0.05, "y": 0.01, "z": 0.02},  # Modified
                            "scale": 0.7  # Modified
                        },
                        "stats_display": {
                            "position": {"x": 0.05, "y": -0.03, "z": 0.02},  # Modified
                            "scale": 0.7  # Modified
                        }
                    },
                    "end_turn_button": {
                        "position": {"x": 0.05, "y": -0.07, "z": 0.02},  # Modified
                        "scale": 0.09  # Modified
                    },
                    "carousel": {
                        "label": {
                            "position": {"x": -0.4, "y": -0.4, "z": 0.05},  # Modified
                            "scale": 0.9,  # Modified
                            "text": "Battle Order:"  # Modified text
                        }
                    }
                }
            }
        }
        
        # Write test file
        with open(self.assets_path / 'data' / 'ui' / 'layout_config.json', 'w') as f:
            json.dump(ui_config, f)
    
    def test_config_values_loaded(self):
        """Test that configuration values are loaded correctly."""
        # Test that the config manager loads our test values
        panel_scale = self.config_manager.get_scale(
            'ui_layout.ui_layout.control_panel.main_panel.scale', 
            (0.8, 0.25, 0.01)  # Default values
        )
        
        # Should get our modified values, not the defaults
        self.assertEqual(panel_scale, (0.9, 0.3, 0.02))
        
        # Test carousel text
        carousel_text = self.config_manager.get_value(
            'ui_layout.ui_layout.control_panel.carousel.label.text', 
            'Turn Order:'  # Default
        )
        self.assertEqual(carousel_text, "Battle Order:")
    
    def test_control_panel_uses_config(self):
        """Test that control panel actually uses configuration values."""
        # This test verifies that the control panel constructor doesn't crash
        # and creates objects with the expected configured values
        
        try:
            # Create control panel instance
            panel = CharacterAttackInterface()
            
            # Verify it was created successfully
            self.assertIsNotNone(panel)
            
            # Test that carousel label uses configured text
            self.assertIsNotNone(panel.carousel_label)
            self.assertEqual(panel.carousel_label.text, "Battle Order:")
            
            # Test that panel has correct configuration-based properties
            # Note: In a real test environment with Ursina, we'd check actual positions
            self.assertIsNotNone(panel.panel)
            
        except Exception as e:
            self.fail(f"Control panel creation failed: {e}")
    
    def test_fallback_values(self):
        """Test that fallback values work when config is missing."""
        # Create a config manager with missing file
        empty_config = ConfigManager(str(Path(self.temp_dir) / 'nonexistent'))
        
        # Should use fallback values
        default_scale = empty_config.get_scale(
            'ui_layout.ui_layout.control_panel.main_panel.scale',
            (0.8, 0.25, 0.01)
        )
        self.assertEqual(default_scale, (0.8, 0.25, 0.01))
    
    def test_config_hot_reload(self):
        """Test that configuration can be hot-reloaded."""
        # Modify the config file
        modified_config = {
            "ui_layout": {
                "control_panel": {
                    "carousel": {
                        "label": {
                            "text": "Updated Order:"
                        }
                    }
                }
            }
        }
        
        with open(self.assets_path / 'data' / 'ui' / 'layout_config.json', 'w') as f:
            json.dump(modified_config, f)
        
        # Hot reload
        self.config_manager.hot_reload('ui_layout')
        
        # Check updated value
        new_text = self.config_manager.get_value(
            'ui_layout.ui_layout.control_panel.carousel.label.text',
            'Turn Order:'
        )
        self.assertEqual(new_text, "Updated Order:")


def run_control_panel_test(timeout_seconds: int = 10) -> bool:
    """
    Run control panel configuration tests with timeout.
    
    Args:
        timeout_seconds: Maximum time to run tests
        
    Returns:
        True if all tests passed, False otherwise
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Control panel tests timed out after {timeout_seconds} seconds")
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        # Run tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestControlPanelConfiguration)
        
        # Run with quiet output for timeout testing
        runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        # Reset alarm
        signal.alarm(0)
        
        return result.wasSuccessful()
        
    except TimeoutError as e:
        print(f"❌ {e}")
        return False
    except Exception as e:
        print(f"❌ Control panel test execution failed: {e}")
        return False
    finally:
        # Ensure alarm is reset
        signal.alarm(0)


if __name__ == '__main__':
    # Run tests with detailed output when called directly
    unittest.main(verbosity=2)