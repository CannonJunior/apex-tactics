# Asset Management Systems

This document outlines the comprehensive asset management system for the Tactical RPG 3D Engine, supporting dependency tracking, versioning, streaming, LOD (Level of Detail), and multi-platform localization.

## Core Asset Management Architecture

### Asset Registry System

The central asset registry maintains metadata and relationships for all game assets:

```python
# Asset Registry Database Schema
{
    "asset_id": "unique_identifier",
    "name": "human_readable_name",
    "type": "model|texture|audio|data|localization",
    "version": "semantic_version",
    "platform_variants": {
        "ursina": "path/to/ursina/asset",
        "unity": "path/to/unity/asset", 
        "ios": "path/to/ios/asset",
        "console": "path/to/console/asset"
    },
    "lod_levels": {
        "lod0": "highest_quality_path",
        "lod1": "medium_quality_path", 
        "lod2": "low_quality_path",
        "lod3": "lowest_quality_path"
    },
    "dependencies": ["list_of_asset_ids"],
    "dependents": ["list_of_assets_using_this"],
    "metadata": {
        "file_size": "bytes",
        "creation_date": "timestamp",
        "last_modified": "timestamp",
        "creator": "artist_name",
        "tags": ["tag1", "tag2"],
        "streaming_priority": "high|medium|low",
        "memory_budget": "estimated_memory_usage"
    },
    "localization": {
        "localizable": "boolean",
        "localization_keys": ["key1", "key2"],
        "variants": {
            "en": "english_variant_path",
            "es": "spanish_variant_path",
            "fr": "french_variant_path"
        }
    }
}
```

### Asset Manager Implementation

```python
class AssetManager:
    def __init__(self):
        self.registry = AssetRegistry()
        self.cache = AssetCache()
        self.streaming_manager = StreamingManager()
        self.lod_manager = LODManager()
        self.localization_manager = LocalizationManager()
        self.dependency_tracker = DependencyTracker()
        
    def load_asset(self, asset_id: str, lod_level: int = 0) -> Asset:
        """Load asset with appropriate LOD level"""
        metadata = self.registry.get_metadata(asset_id)
        
        # Check cache first
        cached_asset = self.cache.get(asset_id, lod_level)
        if cached_asset and cached_asset.version == metadata.version:
            return cached_asset
            
        # Determine appropriate LOD level
        target_lod = self.lod_manager.calculate_lod(asset_id, lod_level)
        
        # Load asset with platform-specific variant
        platform = self.get_current_platform()
        asset_path = metadata.platform_variants[platform]
        lod_path = metadata.lod_levels[f"lod{target_lod}"]
        
        asset = self._load_from_disk(lod_path or asset_path)
        asset.metadata = metadata
        
        # Cache the loaded asset
        self.cache.store(asset_id, asset, target_lod)
        
        return asset
        
    def update_asset(self, asset_id: str, new_version: str):
        """Update asset and propagate changes to dependents"""
        # Update asset metadata
        self.registry.update_version(asset_id, new_version)
        
        # Invalidate cache
        self.cache.invalidate(asset_id)
        
        # Update all dependent assets
        dependents = self.dependency_tracker.get_dependents(asset_id)
        for dependent_id in dependents:
            self._propagate_update(dependent_id, asset_id)
            
    def _propagate_update(self, dependent_id: str, updated_asset_id: str):
        """Propagate asset updates to dependent assets"""
        # Invalidate dependent from cache
        self.cache.invalidate(dependent_id)
        
        # Notify systems that use this asset
        self.event_bus.publish(AssetUpdatedEvent(
            asset_id=dependent_id,
            trigger_asset=updated_asset_id
        ))
```

## Dependency Tracking System

### Dependency Graph Management

```python
class DependencyTracker:
    def __init__(self):
        self.dependency_graph = DirectedGraph()
        self.reverse_dependencies = {}
        
    def add_dependency(self, asset_id: str, dependency_id: str):
        """Add a dependency relationship"""
        self.dependency_graph.add_edge(asset_id, dependency_id)
        
        if dependency_id not in self.reverse_dependencies:
            self.reverse_dependencies[dependency_id] = set()
        self.reverse_dependencies[dependency_id].add(asset_id)
        
    def get_dependencies(self, asset_id: str) -> List[str]:
        """Get all assets this asset depends on"""
        return self.dependency_graph.get_successors(asset_id)
        
    def get_dependents(self, asset_id: str) -> List[str]:
        """Get all assets that depend on this asset"""
        return list(self.reverse_dependencies.get(asset_id, set()))
        
    def validate_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependency chains"""
        return self.dependency_graph.find_cycles()
        
    def get_load_order(self, asset_ids: List[str]) -> List[str]:
        """Calculate optimal loading order based on dependencies"""
        return self.dependency_graph.topological_sort(asset_ids)
```

### Asset Version Control

```python
class AssetVersionManager:
    def __init__(self):
        self.version_history = {}
        self.compatibility_matrix = {}
        
    def create_version(self, asset_id: str, version: str, 
                      changes: Dict[str, Any]) -> bool:
        """Create new asset version with change tracking"""
        if asset_id not in self.version_history:
            self.version_history[asset_id] = []
            
        version_info = {
            "version": version,
            "timestamp": datetime.now(),
            "changes": changes,
            "compatibility": self._calculate_compatibility(asset_id, version)
        }
        
        self.version_history[asset_id].append(version_info)
        return True
        
    def check_compatibility(self, asset_id: str, dependent_version: str, 
                          dependency_version: str) -> bool:
        """Check if asset versions are compatible"""
        key = f"{asset_id}:{dependent_version}:{dependency_version}"
        return self.compatibility_matrix.get(key, True)
        
    def get_compatible_version(self, asset_id: str, 
                             requirements: Dict[str, str]) -> str:
        """Find compatible asset version for given requirements"""
        versions = self.version_history.get(asset_id, [])
        
        for version_info in reversed(versions):  # Start with latest
            if self._meets_requirements(version_info, requirements):
                return version_info["version"]
                
        return None
```

## Streaming and LOD System

### Dynamic Streaming Manager

```python
class StreamingManager:
    def __init__(self):
        self.streaming_zones = {}
        self.active_streams = {}
        self.memory_budget = MemoryBudget()
        self.performance_monitor = PerformanceMonitor()
        
    def register_streaming_zone(self, zone_id: str, 
                               center: Vector3, radius: float):
        """Register a streaming zone for dynamic loading"""
        self.streaming_zones[zone_id] = StreamingZone(
            center=center,
            radius=radius,
            assets=self._get_zone_assets(zone_id)
        )
        
    def update_streaming(self, player_position: Vector3, 
                        camera_direction: Vector3):
        """Update streaming based on player position and view"""
        # Calculate distances to streaming zones
        zone_distances = {}
        for zone_id, zone in self.streaming_zones.items():
            distance = (player_position - zone.center).magnitude
            zone_distances[zone_id] = distance
            
        # Determine zones to load/unload
        zones_to_load = self._calculate_zones_to_load(
            zone_distances, player_position, camera_direction
        )
        zones_to_unload = self._calculate_zones_to_unload(
            zone_distances, zones_to_load
        )
        
        # Execute streaming operations
        for zone_id in zones_to_unload:
            self._unload_zone(zone_id)
            
        for zone_id in zones_to_load:
            self._load_zone(zone_id)
            
    def _load_zone(self, zone_id: str):
        """Load assets for a streaming zone"""
        zone = self.streaming_zones[zone_id]
        
        for asset_id in zone.assets:
            if asset_id not in self.active_streams:
                # Start asynchronous loading
                future = self._async_load_asset(asset_id)
                self.active_streams[asset_id] = future
                
    def _async_load_asset(self, asset_id: str) -> Future:
        """Asynchronously load asset in background thread"""
        return self.thread_pool.submit(self._load_asset_worker, asset_id)
        
    def _load_asset_worker(self, asset_id: str):
        """Worker function for background asset loading"""
        try:
            asset = self.asset_manager.load_asset(asset_id)
            self.cache.store(asset_id, asset)
            return asset
        except Exception as e:
            logging.error(f"Failed to load asset {asset_id}: {e}")
            return None
```

### Level of Detail (LOD) Manager

```python
class LODManager:
    def __init__(self):
        self.lod_settings = LODSettings()
        self.performance_tracker = PerformanceTracker()
        self.hardware_detector = HardwareDetector()
        
    def calculate_lod(self, asset_id: str, requested_lod: int = 0) -> int:
        """Calculate appropriate LOD level based on various factors"""
        # Get asset metadata
        metadata = self.asset_manager.registry.get_metadata(asset_id)
        
        # Factor 1: Distance from camera/player
        distance_factor = self._calculate_distance_factor(asset_id)
        
        # Factor 2: Current performance metrics
        performance_factor = self._calculate_performance_factor()
        
        # Factor 3: Hardware capabilities
        hardware_factor = self._calculate_hardware_factor()
        
        # Factor 4: Memory pressure
        memory_factor = self._calculate_memory_factor()
        
        # Factor 5: Asset importance/priority
        priority_factor = self._calculate_priority_factor(metadata)
        
        # Combine factors to determine LOD level
        lod_score = (
            distance_factor * 0.3 +
            performance_factor * 0.2 +
            hardware_factor * 0.2 +
            memory_factor * 0.2 +
            priority_factor * 0.1
        )
        
        # Map score to LOD level (0 = highest quality, 3 = lowest)
        if lod_score <= 0.25:
            return 0  # Highest quality
        elif lod_score <= 0.5:
            return 1  # High quality
        elif lod_score <= 0.75:
            return 2  # Medium quality
        else:
            return 3  # Lowest quality
            
    def _calculate_distance_factor(self, asset_id: str) -> float:
        """Calculate LOD factor based on distance from camera"""
        asset_position = self.asset_manager.get_world_position(asset_id)
        camera_position = self.camera_manager.get_position()
        
        distance = (asset_position - camera_position).magnitude
        
        # Define distance thresholds
        near_threshold = 10.0
        far_threshold = 50.0
        
        if distance <= near_threshold:
            return 0.0  # Close = high quality
        elif distance >= far_threshold:
            return 1.0  # Far = low quality
        else:
            # Linear interpolation between thresholds
            return (distance - near_threshold) / (far_threshold - near_threshold)
            
    def _calculate_performance_factor(self) -> float:
        """Calculate LOD factor based on current performance"""
        current_fps = self.performance_tracker.get_current_fps()
        target_fps = self.lod_settings.target_fps
        
        if current_fps >= target_fps:
            return 0.0  # Good performance = high quality
        else:
            # Poor performance = lower quality
            performance_ratio = current_fps / target_fps
            return 1.0 - performance_ratio
```

## Multi-Platform Localization System

### Localization Manager

```python
class LocalizationManager:
    def __init__(self):
        self.current_language = "en"
        self.fallback_language = "en"
        self.localization_data = {}
        self.platform_specific_data = {}
        self.region_settings = RegionSettings()
        
    def initialize(self, language: str, region: str = None):
        """Initialize localization system"""
        self.current_language = language
        if region:
            self.region_settings.set_region(region)
            
        # Load base localization data
        self._load_localization_data(language)
        
        # Load platform-specific localizations
        platform = self._detect_platform()
        self._load_platform_localization(platform, language)
        
    def get_localized_string(self, key: str, **kwargs) -> str:
        """Get localized string with parameter substitution"""
        # Try current language first
        text = self._get_string(key, self.current_language)
        
        # Fall back to default language if not found
        if text is None and self.current_language != self.fallback_language:
            text = self._get_string(key, self.fallback_language)
            
        # Fall back to key itself if still not found
        if text is None:
            text = key
            logging.warning(f"Missing localization key: {key}")
            
        # Substitute parameters
        if kwargs and '{' in text:
            text = text.format(**kwargs)
            
        return text
        
    def get_localized_asset(self, asset_id: str) -> str:
        """Get localized version of an asset"""
        metadata = self.asset_manager.registry.get_metadata(asset_id)
        
        if not metadata.localization.localizable:
            return asset_id
            
        # Check for language-specific variant
        variants = metadata.localization.variants
        if self.current_language in variants:
            return variants[self.current_language]
            
        # Fall back to default language
        if self.fallback_language in variants:
            return variants[self.fallback_language]
            
        # Return original asset if no localized version
        return asset_id
        
    def _load_localization_data(self, language: str):
        """Load localization data for specified language"""
        localization_files = [
            f"data/localization/{language}/ui_text.json",
            f"data/localization/{language}/dialogue.json", 
            f"data/localization/{language}/item_descriptions.json",
            f"data/localization/{language}/ability_descriptions.json",
            f"data/localization/{language}/story_text.json"
        ]
        
        for file_path in localization_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.localization_data[language] = {
                        **self.localization_data.get(language, {}),
                        **data
                    }
```

### Platform-Specific Localization

```python
class PlatformLocalizationManager:
    def __init__(self):
        self.platform_mappings = {
            "ursina": "pc",
            "unity_standalone": "pc", 
            "unity_ios": "mobile",
            "unity_android": "mobile",
            "unity_console": "console"
        }
        
    def get_platform_specific_text(self, key: str, platform: str) -> str:
        """Get platform-specific localized text"""
        platform_category = self.platform_mappings.get(platform, "pc")
        
        platform_key = f"{key}_{platform_category}"
        platform_text = self.localization_manager.get_localized_string(platform_key)
        
        # Fall back to generic text if platform-specific not found
        if platform_text == platform_key:  # Key not found
            return self.localization_manager.get_localized_string(key)
            
        return platform_text
        
    def adapt_ui_text_for_platform(self, text: str, platform: str) -> str:
        """Adapt UI text based on platform constraints"""
        if platform in ["unity_ios", "unity_android"]:
            # Mobile platforms - shorter text
            return self._truncate_for_mobile(text)
        elif platform == "unity_console":
            # Console platforms - controller-friendly text
            return self._adapt_for_controller(text)
        else:
            # PC platforms - full text
            return text
```

## Localization File Structure

### Base Localization Structure

```
data/localization/
├── templates/                     # Localization templates
│   ├── ui_template.json          # UI text template
│   ├── dialogue_template.json    # Dialogue template  
│   ├── items_template.json       # Item description template
│   └── story_template.json       # Story text template
├── en/                           # English (base language)
│   ├── ui_text.json              # UI interface text
│   ├── dialogue.json             # Character dialogue
│   ├── item_descriptions.json    # Equipment/item descriptions
│   ├── ability_descriptions.json # Ability descriptions
│   ├── story_text.json           # Story and cutscene text
│   ├── tutorial_text.json        # Tutorial instructions
│   └── platform_specific/        # Platform-specific variants
│       ├── mobile.json           # Mobile-specific text
│       ├── console.json          # Console-specific text
│       └── pc.json               # PC-specific text
├── es/                           # Spanish localization
│   ├── ui_text.json
│   ├── dialogue.json
│   ├── item_descriptions.json
│   ├── ability_descriptions.json
│   ├── story_text.json
│   ├── tutorial_text.json
│   └── platform_specific/
├── fr/                           # French localization
├── de/                           # German localization
├── ja/                           # Japanese localization
├── ko/                           # Korean localization
├── zh_cn/                        # Simplified Chinese
├── zh_tw/                        # Traditional Chinese
├── pt_br/                        # Brazilian Portuguese
├── ru/                           # Russian localization
└── it/                           # Italian localization
```

### Region-Specific Settings

```python
class RegionSettings:
    def __init__(self):
        self.region_configs = {
            "US": {
                "currency_symbol": "$",
                "date_format": "MM/DD/YYYY",
                "number_format": "1,234.56",
                "measurement_units": "imperial"
            },
            "EU": {
                "currency_symbol": "€", 
                "date_format": "DD/MM/YYYY",
                "number_format": "1.234,56",
                "measurement_units": "metric"
            },
            "JP": {
                "currency_symbol": "¥",
                "date_format": "YYYY/MM/DD", 
                "number_format": "1,234.56",
                "measurement_units": "metric"
            }
        }
        
    def format_currency(self, amount: float, region: str) -> str:
        """Format currency based on region"""
        config = self.region_configs.get(region, self.region_configs["US"])
        symbol = config["currency_symbol"]
        return f"{symbol}{amount:.2f}"
        
    def format_date(self, date: datetime, region: str) -> str:
        """Format date based on regional preferences"""
        config = self.region_configs.get(region, self.region_configs["US"])
        format_str = config["date_format"]
        return date.strftime(format_str.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d"))
```

## Asset Pipeline Integration

### Build System Integration

```python
class AssetBuildPipeline:
    def __init__(self):
        self.asset_manager = AssetManager()
        self.platform_converters = {
            "ursina": UrsinaAssetConverter(),
            "unity": UnityAssetConverter(),
            "ios": IOSAssetConverter(),
            "console": ConsoleAssetConverter()
        }
        
    def build_assets_for_platform(self, platform: str, 
                                 asset_list: List[str] = None):
        """Build and convert assets for specific platform"""
        if asset_list is None:
            asset_list = self.asset_manager.get_all_asset_ids()
            
        converter = self.platform_converters[platform]
        
        for asset_id in asset_list:
            try:
                # Get source asset
                source_asset = self.asset_manager.load_asset(asset_id)
                
                # Convert for platform
                converted_asset = converter.convert(source_asset)
                
                # Generate LOD variants
                lod_variants = self._generate_lod_variants(converted_asset)
                
                # Save platform-specific versions
                self._save_platform_asset(asset_id, platform, 
                                        converted_asset, lod_variants)
                
                # Update registry with platform variant paths
                self._update_registry_platform_paths(asset_id, platform)
                
            except Exception as e:
                logging.error(f"Failed to build asset {asset_id} for {platform}: {e}")
                
    def _generate_lod_variants(self, asset: Asset) -> Dict[int, Asset]:
        """Generate LOD variants for an asset"""
        lod_variants = {}
        
        if asset.type == AssetType.MODEL:
            lod_variants[0] = asset  # Original quality
            lod_variants[1] = self._reduce_polygon_count(asset, 0.7)
            lod_variants[2] = self._reduce_polygon_count(asset, 0.4) 
            lod_variants[3] = self._reduce_polygon_count(asset, 0.2)
        elif asset.type == AssetType.TEXTURE:
            lod_variants[0] = asset  # Original resolution
            lod_variants[1] = self._reduce_texture_resolution(asset, 0.75)
            lod_variants[2] = self._reduce_texture_resolution(asset, 0.5)
            lod_variants[3] = self._reduce_texture_resolution(asset, 0.25)
            
        return lod_variants
```

## Performance Monitoring and Optimization

### Asset Performance Monitor

```python
class AssetPerformanceMonitor:
    def __init__(self):
        self.load_times = {}
        self.memory_usage = {}
        self.access_patterns = {}
        self.performance_thresholds = {
            "max_load_time": 0.1,  # 100ms
            "max_memory_per_asset": 50 * 1024 * 1024,  # 50MB
            "cache_hit_ratio_target": 0.8
        }
        
    def track_asset_load(self, asset_id: str, load_time: float, 
                        memory_used: int):
        """Track performance metrics for asset loading"""
        self.load_times[asset_id] = load_time
        self.memory_usage[asset_id] = memory_used
        
        # Check against performance thresholds
        if load_time > self.performance_thresholds["max_load_time"]:
            logging.warning(f"Asset {asset_id} load time exceeded threshold: {load_time}s")
            
        if memory_used > self.performance_thresholds["max_memory_per_asset"]:
            logging.warning(f"Asset {asset_id} memory usage exceeded threshold: {memory_used} bytes")
            
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        total_load_time = sum(self.load_times.values())
        total_memory = sum(self.memory_usage.values())
        avg_load_time = total_load_time / len(self.load_times) if self.load_times else 0
        
        return {
            "total_assets": len(self.load_times),
            "total_load_time": total_load_time,
            "average_load_time": avg_load_time,
            "total_memory_usage": total_memory,
            "slowest_assets": self._get_slowest_assets(5),
            "largest_assets": self._get_largest_assets(5),
            "cache_hit_ratio": self._calculate_cache_hit_ratio()
        }
```

## Integration Points

### Unity Export System

```python
class UnityExportManager:
    def __init__(self):
        self.asset_manager = AssetManager()
        self.unity_package_builder = UnityPackageBuilder()
        
    def export_for_unity(self, export_path: str):
        """Export complete asset system for Unity import"""
        # Create Unity-compatible asset structure
        unity_assets = self._convert_assets_for_unity()
        
        # Generate Unity asset database
        unity_asset_db = self._generate_unity_asset_database()
        
        # Create Unity package
        package = self.unity_package_builder.create_package(
            assets=unity_assets,
            asset_database=unity_asset_db,
            scripts=self._export_unity_scripts()
        )
        
        # Save package
        package.save(export_path)
        
    def _convert_assets_for_unity(self) -> Dict[str, Any]:
        """Convert Ursina assets to Unity-compatible format"""
        # Implementation for asset conversion
        pass
```

This comprehensive asset management system provides:

- **Dependency Tracking**: Automatic updates when dependencies change
- **Version Control**: Semantic versioning with compatibility checking  
- **Streaming System**: Dynamic loading based on player position and performance
- **LOD Management**: Automatic quality adjustment based on distance, performance, and hardware
- **Multi-Platform Support**: Asset variants for different platforms and devices
- **Localization**: Comprehensive multi-language support with regional settings
- **Performance Monitoring**: Real-time tracking of asset loading and memory usage
- **Unity Integration**: Export system for seamless Unity portability