"""
Stat System

Handles stat calculations and derived stat updates for all entities.
Implements the nine-attribute system from Advanced-Implementation-Guide.md
"""

from typing import Set, Type, List
import time
from core.ecs.system import BaseSystem
from core.ecs.entity import Entity
from core.ecs.component import BaseComponent
from core.utils.logging import Logger
from core.utils.performance import PerformanceMonitor
from components.stats.attributes import AttributeStats
from components.stats.resources import ResourceManager
from components.stats.modifiers import ModifierManager

class StatSystem(BaseSystem):
    """
    System for managing character stats and calculations.
    
    Processes entities with stat components and updates derived values.
    Implements the complete nine-attribute system with resources and modifiers.
    Performance target: <1ms for complex character sheets.
    """
    
    def __init__(self):
        super().__init__("StatSystem")
        self.priority = 10  # High priority for stat calculations
        self.performance_monitor = PerformanceMonitor()
        
        # Performance tracking
        self.entities_processed = 0
        self.total_calculation_time = 0.0
    
    def get_required_components(self) -> Set[Type[BaseComponent]]:
        """Stats system requires AttributeStats component"""
        return {AttributeStats}
    
    def update(self, delta_time: float, entities: List[Entity]):
        """
        Update stat calculations for all entities.
        
        Args:
            delta_time: Time elapsed since last update
            entities: Entities with AttributeStats components
        """
        with self.performance_monitor.measure("stat_system_update"):
            for entity in entities:
                self._update_entity_stats(entity, delta_time)
        
        self.entities_processed += len(entities)
    
    def _update_entity_stats(self, entity: Entity, delta_time: float):
        """
        Update stats for a single entity.
        
        Args:
            entity: Entity to update
            delta_time: Time elapsed since last update
        """
        start_time = time.perf_counter()
        
        # Get stat components
        attributes = entity.get_component(AttributeStats)
        resources = entity.get_component(ResourceManager)
        modifiers = entity.get_component(ModifierManager)
        
        if not attributes:
            return
        
        # Update resource manager if present
        if resources:
            # Update max values based on derived stats
            derived = attributes.derived_stats
            old_mp_max = resources.mp.max_value
            new_mp_max = derived.get('mp', resources.mp.max_value)
            
            if new_mp_max != old_mp_max:
                # Scale current MP proportionally when max changes
                if old_mp_max > 0:
                    mp_ratio = resources.mp.current_value / old_mp_max
                    resources.mp.max_value = new_mp_max
                    resources.mp.current_value = min(new_mp_max, int(new_mp_max * mp_ratio))
                else:
                    resources.mp.max_value = new_mp_max
                    resources.mp.current_value = new_mp_max  # Start full if was empty
            
            # Determine location type (placeholder - will be enhanced with grid integration)
            location_type = "normal"  # TODO: Get from grid position
            in_combat = False  # TODO: Get from combat state
            
            resources.update(delta_time, location_type, in_combat)
        
        # Update modifier manager if present
        if modifiers:
            modifiers.update(delta_time)
        
        # Apply modifiers to derived stats if modifiers exist
        if modifiers:
            self._apply_modifiers_to_stats(attributes, modifiers)
        
        # Performance tracking
        calculation_time = time.perf_counter() - start_time
        self.total_calculation_time += calculation_time
        
        # Warn if calculation exceeds target
        if calculation_time > 0.001:  # 1ms target
            Logger.warning(f"Slow stat calculation: {calculation_time*1000:.2f}ms for entity {entity.id[:8]}")
    
    def _apply_modifiers_to_stats(self, attributes: AttributeStats, 
                                 modifiers: ModifierManager):
        """
        Apply modifiers to attribute stats.
        
        Args:
            attributes: AttributeStats component
            modifiers: ModifierManager component
        """
        # Get base derived stats
        base_derived = attributes.derived_stats
        
        # Apply modifiers to each stat
        modified_stats = {}
        for stat_name, base_value in base_derived.items():
            final_value = modifiers.calculate_final_stat(base_value, stat_name)
            modified_stats[stat_name] = final_value
        
        # Store modified stats back to attributes component
        # (This would require extending AttributeStats to store modified values)
        # For now, modifiers are calculated on-demand
    
    def get_final_stat_value(self, entity: Entity, stat_name: str) -> int:
        """
        Get final stat value for entity with all modifiers applied.
        
        Args:
            entity: Entity to get stat for
            stat_name: Name of stat to calculate
            
        Returns:
            Final stat value
        """
        attributes = entity.get_component(AttributeStats)
        if not attributes:
            return 0
        
        # Get base attribute value directly
        base_value = getattr(attributes, stat_name, 0)
        
        # Apply modifiers if present
        modifiers = entity.get_component(ModifierManager)
        if modifiers:
            return modifiers.calculate_final_stat(base_value, stat_name)
        
        return base_value
    
    def get_attribute_value(self, entity: Entity, attribute_name: str) -> int:
        """
        Get base attribute value for entity.
        
        Args:
            entity: Entity to get attribute for
            attribute_name: Name of attribute (e.g., 'strength')
            
        Returns:
            Attribute value
        """
        attributes = entity.get_component(AttributeStats)
        if not attributes:
            return 0
        
        return getattr(attributes, attribute_name, 0)
    
    def modify_attribute(self, entity: Entity, attribute_name: str, 
                        new_value: int) -> bool:
        """
        Modify base attribute value.
        
        Args:
            entity: Entity to modify
            attribute_name: Name of attribute to modify
            new_value: New attribute value
            
        Returns:
            True if modification was successful
        """
        attributes = entity.get_component(AttributeStats)
        if not attributes:
            return False
        
        try:
            attributes.modify_attribute(attribute_name, new_value)
            return True
        except ValueError:
            return False
    
    def initialize(self):
        """Initialize stat system"""
        # Register stat components
        from core.ecs.component import ComponentRegistry
        ComponentRegistry.register(AttributeStats)
        ComponentRegistry.register(ResourceManager)
        ComponentRegistry.register(ModifierManager)
        
        Logger.info("StatSystem initialized with nine-attribute system")
    
    def shutdown(self):
        """Shutdown stat system"""
        # Generate performance report
        if self.entities_processed > 0:
            avg_time = self.total_calculation_time / self.entities_processed
            Logger.info(f"StatSystem shutdown - processed {self.entities_processed} entities, "
                       f"avg time: {avg_time*1000:.2f}ms per entity")
        else:
            Logger.info("StatSystem shutdown")
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics for the stat system"""
        return {
            'entities_processed': self.entities_processed,
            'total_calculation_time': self.total_calculation_time,
            'average_time_per_entity': (self.total_calculation_time / self.entities_processed 
                                      if self.entities_processed > 0 else 0),
            'performance_target_met': (self.total_calculation_time / self.entities_processed < 0.001
                                     if self.entities_processed > 0 else True)
        }