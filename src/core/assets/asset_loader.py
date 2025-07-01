"""
Asset Loader System

Handles loading and caching of game assets including images, data files, audio, and animations.
Provides a centralized system for asset management with error handling and fallbacks.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging

try:
    from ursina import load_texture, Audio
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


class AssetLoader:
    """
    Centralized asset loading and caching system.
    
    Features:
    - JSON data file loading with validation
    - Image/texture loading with fallbacks
    - Audio file loading
    - Asset caching for performance
    - Error handling and logging
    """
    
    def __init__(self, assets_root: str = None):
        """
        Initialize the asset loader.
        
        Args:
            assets_root: Path to the assets directory (defaults to project assets folder)
        """
        if assets_root is None:
            # Default to assets directory in project root
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            assets_root = project_root / "assets"
        
        self.assets_root = Path(assets_root)
        
        # Asset caches
        self._data_cache: Dict[str, Any] = {}
        self._texture_cache: Dict[str, Any] = {}
        self._audio_cache: Dict[str, Any] = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Ensure assets directory exists
        self._ensure_assets_structure()
        
        print(f"✅ AssetLoader initialized with root: {self.assets_root}")
    
    def _ensure_assets_structure(self):
        """Ensure the assets directory structure exists."""
        subdirs = [
            "data/items",
            "data/abilities", 
            "data/zones",
            "data/units",
            "data/characters",
            "images/items",
            "images/units",
            "images/ui",
            "images/icons",
            "images/tiles",
            "audio/sfx",
            "audio/music",
            "animations"
        ]
        
        for subdir in subdirs:
            (self.assets_root / subdir).mkdir(parents=True, exist_ok=True)
    
    def load_data(self, filepath: str, cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Load JSON data file.
        
        Args:
            filepath: Path to JSON file relative to assets/data/
            cache: Whether to cache the loaded data
            
        Returns:
            Loaded data as dictionary, or None if loading failed
        """
        cache_key = f"data:{filepath}"
        
        # Check cache first
        if cache and cache_key in self._data_cache:
            return self._data_cache[cache_key]
        
        full_path = self.assets_root / "data" / filepath
        
        try:
            if not full_path.exists():
                self.logger.warning(f"Data file not found: {full_path}")
                return None
            
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cache the data
            if cache:
                self._data_cache[cache_key] = data
            
            self.logger.info(f"Loaded data file: {filepath}")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {filepath}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading data file {filepath}: {e}")
            return None
    
    def load_texture(self, filepath: str, fallback: str = "white_cube") -> Optional[Any]:
        """
        Load texture/image file.
        
        Args:
            filepath: Path to image file relative to assets/images/
            fallback: Fallback texture name if loading fails
            
        Returns:
            Loaded texture object, or fallback texture
        """
        if not URSINA_AVAILABLE:
            self.logger.warning("Ursina not available, cannot load textures")
            return None
        
        cache_key = f"texture:{filepath}"
        
        # Check cache first
        if cache_key in self._texture_cache:
            return self._texture_cache[cache_key]
        
        full_path = self.assets_root / "images" / filepath
        
        try:
            if full_path.exists():
                texture = load_texture(str(full_path))
                self._texture_cache[cache_key] = texture
                self.logger.info(f"Loaded texture: {filepath}")
                return texture
            else:
                self.logger.warning(f"Texture file not found: {full_path}, using fallback: {fallback}")
                # Load fallback texture
                fallback_texture = load_texture(fallback)
                self._texture_cache[cache_key] = fallback_texture
                return fallback_texture
                
        except Exception as e:
            self.logger.error(f"Error loading texture {filepath}: {e}")
            # Try fallback
            try:
                fallback_texture = load_texture(fallback)
                return fallback_texture
            except:
                return None
    
    def load_audio(self, filepath: str) -> Optional[Any]:
        """
        Load audio file.
        
        Args:
            filepath: Path to audio file relative to assets/audio/
            
        Returns:
            Loaded audio object, or None if loading failed
        """
        if not URSINA_AVAILABLE:
            self.logger.warning("Ursina not available, cannot load audio")
            return None
        
        cache_key = f"audio:{filepath}"
        
        # Check cache first
        if cache_key in self._audio_cache:
            return self._audio_cache[cache_key]
        
        full_path = self.assets_root / "audio" / filepath
        
        try:
            if not full_path.exists():
                self.logger.warning(f"Audio file not found: {full_path}")
                return None
            
            audio = Audio(str(full_path))
            self._audio_cache[cache_key] = audio
            self.logger.info(f"Loaded audio: {filepath}")
            return audio
            
        except Exception as e:
            self.logger.error(f"Error loading audio {filepath}: {e}")
            return None
    
    def save_data(self, data: Dict[str, Any], filepath: str) -> bool:
        """
        Save data to JSON file.
        
        Args:
            data: Data to save
            filepath: Path to save file relative to assets/data/
            
        Returns:
            True if successful, False otherwise
        """
        full_path = self.assets_root / "data" / filepath
        
        try:
            # Ensure directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved data file: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data file {filepath}: {e}")
            return False
    
    def list_assets(self, asset_type: str) -> List[str]:
        """
        List all assets of a given type.
        
        Args:
            asset_type: Type of assets ('data', 'images', 'audio')
            
        Returns:
            List of asset filenames
        """
        asset_dir = self.assets_root / asset_type
        
        if not asset_dir.exists():
            return []
        
        assets = []
        for file_path in asset_dir.rglob("*"):
            if file_path.is_file():
                # Get relative path from asset type directory
                relative_path = file_path.relative_to(asset_dir)
                assets.append(str(relative_path))
        
        return sorted(assets)
    
    def clear_cache(self, cache_type: str = "all"):
        """
        Clear asset caches.
        
        Args:
            cache_type: Type of cache to clear ('data', 'texture', 'audio', 'all')
        """
        if cache_type in ['data', 'all']:
            self._data_cache.clear()
        if cache_type in ['texture', 'all']:
            self._texture_cache.clear()
        if cache_type in ['audio', 'all']:
            self._audio_cache.clear()
        
        self.logger.info(f"Cleared {cache_type} cache(s)")
    
    def get_asset_path(self, asset_type: str, filename: str) -> Path:
        """
        Get full path to an asset file.
        
        Args:
            asset_type: Type of asset ('data', 'images', 'audio')
            filename: Filename or relative path
            
        Returns:
            Full path to the asset
        """
        return self.assets_root / asset_type / filename
    
    def asset_exists(self, asset_type: str, filename: str) -> bool:
        """
        Check if an asset file exists.
        
        Args:
            asset_type: Type of asset ('data', 'images', 'audio')
            filename: Filename or relative path
            
        Returns:
            True if asset exists, False otherwise
        """
        return self.get_asset_path(asset_type, filename).exists()


# Global asset loader instance
_asset_loader: Optional[AssetLoader] = None


def get_asset_loader() -> AssetLoader:
    """Get the global asset loader instance."""
    global _asset_loader
    if _asset_loader is None:
        _asset_loader = AssetLoader()
    return _asset_loader


def load_data(filepath: str, cache: bool = True) -> Optional[Dict[str, Any]]:
    """Convenience function to load data using the global asset loader."""
    return get_asset_loader().load_data(filepath, cache)


def load_texture(filepath: str, fallback: str = "white_cube") -> Optional[Any]:
    """Convenience function to load texture using the global asset loader."""
    return get_asset_loader().load_texture(filepath, fallback)


def load_audio(filepath: str) -> Optional[Any]:
    """Convenience function to load audio using the global asset loader."""
    return get_asset_loader().load_audio(filepath)


def save_data(data: Dict[str, Any], filepath: str) -> bool:
    """Convenience function to save data using the global asset loader."""
    return get_asset_loader().save_data(data, filepath)