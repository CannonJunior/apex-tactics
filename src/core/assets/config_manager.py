"""
Configuration Manager for Apex Tactics

Centralized system for loading and managing game configuration values from asset files.
Supports dynamic updates, hot-reloading, and modifier application for game effects.
"""

import json
import os
import time
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path

try:
    from ursina import color
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


class ModifierEffect:
    """Represents a temporary modifier that can be applied to configuration values."""
    
    def __init__(self, name: str, modifier_func: Callable, duration: float = 0, persistent: bool = False):
        self.name = name
        self.modifier_func = modifier_func
        self.duration = duration
        self.persistent = persistent
        self.start_time = time.time()
        self.applied = True
    
    def is_expired(self) -> bool:
        """Check if this temporary modifier has expired."""
        if self.persistent:
            return False
        return time.time() - self.start_time > self.duration
    
    def apply(self, value: Any) -> Any:
        """Apply this modifier to a value."""
        if self.applied and not self.is_expired():
            return self.modifier_func(value)
        return value


class ConfigManager:
    """
    Centralized configuration manager for all game values.
    
    Features:
    - Loads configuration from multiple JSON files
    - Supports hot-reloading during development
    - Applies dynamic modifiers for game effects
    - Provides type-safe value access with fallbacks
    - Caches values for performance
    """
    
    def __init__(self, assets_root: str = None):
        """Initialize configuration manager."""
        if assets_root is None:
            # Get project root directory (assuming this file is in src/core/assets/)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, "..", "..", "..")
            assets_root = os.path.join(project_root, "assets")
        
        self.assets_root = Path(assets_root).resolve()
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.last_loaded: Dict[str, float] = {}
        self.modifiers: Dict[str, List[ModifierEffect]] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_timeout = 0.1  # Cache values for 100ms
        self.last_cache_clear = time.time()
        
        # Define configuration file mappings
        self.config_files = {
            'combat': 'data/gameplay/combat_values.json',
            'movement': 'data/gameplay/movement_values.json', 
            'ui_layout': 'data/ui/layout_config.json',
            'animations': 'data/visual/animation_config.json',
            'ui_styles': 'ui_styles.json',
            'units': 'data/units/unit_generation.json'
        }
        
        # Load all configurations
        self.load_all_configs()
    
    def load_all_configs(self):
        """Load all configuration files."""
        for config_name, file_path in self.config_files.items():
            self.load_config(config_name, file_path)
    
    def load_config(self, config_name: str, file_path: str) -> bool:
        """
        Load a specific configuration file.
        
        Args:
            config_name: Internal name for the configuration
            file_path: Relative path from assets root
            
        Returns:
            True if loaded successfully
        """
        full_path = self.assets_root / file_path
        
        try:
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.configs[config_name] = data
                    self.last_loaded[config_name] = time.time()
                    print(f"✅ Loaded config '{config_name}' from {file_path}")
                    return True
            else:
                print(f"⚠️ Config file not found: {full_path}")
                self._load_default_config(config_name)
                return False
        except Exception as e:
            print(f"❌ Error loading config '{config_name}': {e}")
            self._load_default_config(config_name)
            return False
    
    def _load_default_config(self, config_name: str):
        """Load default fallback configuration."""
        defaults = {
            'combat': {
                'combat_values': {
                    'base_combat_values': {
                        'attack_range': {'default': 1},
                        'magic_range': {'default': 2},
                        'magic_mp_cost': {'default': 10}
                    }
                }
            },
            'movement': {
                'movement_values': {
                    'movement_calculations': {
                        'movement_points': {'speed_divisor': 2, 'base_addition': 2}
                    }
                }
            },
            'ui_layout': {
                'ui_layout': {
                    'control_panel': {
                        'positioning': {'scale': {'x': 0.8, 'y': 0.25, 'z': 0.01}}
                    }
                }
            }
        }
        
        self.configs[config_name] = defaults.get(config_name, {})
        print(f"📦 Using default config for '{config_name}'")
    
    def get_value(self, path: str, default: Any = None, apply_modifiers: bool = True) -> Any:
        """
        Get a configuration value by dot-separated path.
        
        Args:
            path: Dot-separated path like 'combat.base_combat_values.attack_range.default'
            default: Default value if path not found
            apply_modifiers: Whether to apply active modifiers
            
        Returns:
            Configuration value with modifiers applied
        """
        # Check cache first
        cache_key = f"{path}_{apply_modifiers}"
        current_time = time.time()
        
        if cache_key in self.cache:
            cached_value, cache_time = self.cache[cache_key]
            if current_time - cache_time < self.cache_timeout:
                return cached_value
        
        # Clear old cache entries periodically
        if current_time - self.last_cache_clear > 1.0:
            self._clear_expired_cache()
            self.last_cache_clear = current_time
        
        # Navigate to the value
        parts = path.split('.')
        current = self.configs
        
        try:
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    current = default
                    break
            
            # Apply modifiers if requested
            if apply_modifiers and current is not None:
                current = self._apply_modifiers(path, current)
            
            # Cache the result
            self.cache[cache_key] = (current, current_time)
            return current
            
        except Exception:
            return default
    
    def _apply_modifiers(self, path: str, value: Any) -> Any:
        """Apply all active modifiers for a given path."""
        if path in self.modifiers:
            # Remove expired modifiers
            self.modifiers[path] = [m for m in self.modifiers[path] if not m.is_expired()]
            
            # Apply remaining modifiers
            for modifier in self.modifiers[path]:
                value = modifier.apply(value)
        
        return value
    
    def _clear_expired_cache(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, cache_time) in self.cache.items()
            if current_time - cache_time > self.cache_timeout
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def add_modifier(self, path: str, name: str, modifier_func: Callable, 
                    duration: float = 0, persistent: bool = False):
        """
        Add a modifier to a configuration value.
        
        Args:
            path: Configuration path to modify
            name: Unique name for the modifier
            modifier_func: Function that takes and returns a value
            duration: How long the modifier lasts (0 = permanent until removed)
            persistent: Whether modifier survives hot-reloads
        """
        if path not in self.modifiers:
            self.modifiers[path] = []
        
        # Remove existing modifier with same name
        self.modifiers[path] = [m for m in self.modifiers[path] if m.name != name]
        
        # Add new modifier
        modifier = ModifierEffect(name, modifier_func, duration, persistent)
        self.modifiers[path].append(modifier)
        
        # Clear cache for this path
        cache_keys_to_remove = [key for key in self.cache.keys() if key.startswith(f"{path}_")]
        for key in cache_keys_to_remove:
            del self.cache[key]
        
        print(f"🔧 Added modifier '{name}' to '{path}'")
    
    def remove_modifier(self, path: str, name: str):
        """Remove a specific modifier."""
        if path in self.modifiers:
            self.modifiers[path] = [m for m in self.modifiers[path] if m.name != name]
            # Clear cache for this path
            cache_keys_to_remove = [key for key in self.cache.keys() if key.startswith(f"{path}_")]
            for key in cache_keys_to_remove:
                del self.cache[key]
            print(f"🗑️ Removed modifier '{name}' from '{path}'")
    
    def clear_modifiers(self, path: str = None):
        """Clear modifiers for a path or all paths."""
        if path:
            self.modifiers[path] = []
        else:
            self.modifiers.clear()
        self.cache.clear()
        print(f"🧹 Cleared modifiers for {'all paths' if path is None else path}")
    
    def hot_reload(self, config_name: str = None):
        """
        Reload configuration files during development.
        
        Args:
            config_name: Specific config to reload, or None for all
        """
        self.cache.clear()  # Clear cache after reload
        
        if config_name:
            if config_name in self.config_files:
                self.load_config(config_name, self.config_files[config_name])
            else:
                print(f"❌ Unknown config name: {config_name}")
        else:
            print("🔄 Hot-reloading all configurations...")
            self.load_all_configs()
    
    # Convenience methods for common configuration types
    
    def get_color(self, path: str, default_rgba: tuple = (1.0, 1.0, 1.0, 1.0)) -> Any:
        """Get a color value and convert to Ursina color if available."""
        color_data = self.get_value(path, None)
        
        if color_data and isinstance(color_data, dict):
            r = color_data.get('r', default_rgba[0])
            g = color_data.get('g', default_rgba[1])
            b = color_data.get('b', default_rgba[2])
            a = color_data.get('a', default_rgba[3])
        else:
            r, g, b, a = default_rgba
        
        # Convert to Ursina color if available
        if URSINA_AVAILABLE:
            return color.Color(r, g, b, a)
        else:
            return {'r': r, 'g': g, 'b': b, 'a': a}
    
    def get_position(self, path: str, default: tuple = (0, 0)) -> tuple:
        """Get a position value as a tuple."""
        pos_data = self.get_value(path, None)
        
        if pos_data and isinstance(pos_data, dict):
            return (pos_data.get('x', default[0]), pos_data.get('y', default[1]))
        return default
    
    def get_scale(self, path: str, default: tuple = (1.0, 1.0, 1.0)) -> tuple:
        """Get a scale value as a tuple."""
        scale_data = self.get_value(path, None)
        
        if scale_data and isinstance(scale_data, dict):
            return (
                scale_data.get('x', default[0]),
                scale_data.get('y', default[1]),
                scale_data.get('z', default[2])
            )
        return default
    
    def get_formula_result(self, formula_path: str, variables: Dict[str, Any], default: Any = 0) -> Any:
        """
        Evaluate a formula from configuration with provided variables.
        
        Args:
            formula_path: Path to formula string in config
            variables: Variables to substitute in formula
            default: Default result if formula fails
            
        Returns:
            Evaluated formula result
        """
        formula = self.get_value(formula_path, None)
        if not formula:
            return default
        
        try:
            # Simple formula evaluation with variable substitution
            # Note: In production, consider using a safer expression evaluator
            for var_name, var_value in variables.items():
                formula = formula.replace(var_name, str(var_value))
            
            # Evaluate the formula (CAUTION: using eval - consider safer alternatives)
            result = eval(formula)
            return result
        except Exception as e:
            print(f"⚠️ Error evaluating formula '{formula}': {e}")
            return default
    
    def list_modifiers(self) -> Dict[str, List[str]]:
        """List all active modifiers by path."""
        result = {}
        for path, modifiers in self.modifiers.items():
            active_modifiers = [m.name for m in modifiers if not m.is_expired()]
            if active_modifiers:
                result[path] = active_modifiers
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get configuration manager statistics."""
        return {
            'loaded_configs': list(self.configs.keys()),
            'cache_size': len(self.cache),
            'active_modifiers': sum(len(mods) for mods in self.modifiers.values()),
            'last_reload': max(self.last_loaded.values()) if self.last_loaded else 0
        }


# Global instance for easy access
_config_manager_instance: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        ConfigManager singleton instance
    """
    global _config_manager_instance
    
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    
    return _config_manager_instance


def set_config_manager(config_manager: Optional[ConfigManager]):
    """
    Set the global configuration manager instance (for testing).
    
    Args:
        config_manager: ConfigManager instance to use globally, or None to reset
    """
    global _config_manager_instance
    _config_manager_instance = config_manager


def reload_configs():
    """Reload all configuration files."""
    config_manager = get_config_manager()
    config_manager.hot_reload()


# Convenience functions for common operations
def get_combat_value(path: str, default: Any = None) -> Any:
    """Get a combat-related configuration value."""
    return get_config_manager().get_value(f"combat.combat_values.{path}", default)


def get_ui_value(path: str, default: Any = None) -> Any:
    """Get a UI-related configuration value."""
    return get_config_manager().get_value(f"ui_layout.ui_layout.{path}", default)


def get_movement_value(path: str, default: Any = None) -> Any:
    """Get a movement-related configuration value."""
    return get_config_manager().get_value(f"movement.movement_values.{path}", default)


def get_unit_value(path: str, default: Any = None) -> Any:
    """Get a unit-related configuration value."""
    return get_config_manager().get_value(f"units.unit_generation.{path}", default)


def add_game_effect(path: str, effect_name: str, multiplier: float, duration: float = 0):
    """
    Add a simple multiplier effect to a game value.
    
    Args:
        path: Configuration path to modify
        effect_name: Name of the effect
        multiplier: Multiplier to apply to the value
        duration: How long the effect lasts (0 = permanent)
    """
    def multiply_effect(value):
        if isinstance(value, (int, float)):
            return value * multiplier
        return value
    
    get_config_manager().add_modifier(path, effect_name, multiply_effect, duration)