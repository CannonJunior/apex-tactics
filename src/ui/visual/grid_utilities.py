"""
Grid Utilities

Simple utility functions for creating basic visual grid elements using Ursina.
Contains functions for creating grid lines, ground planes, and other basic grid visuals.
"""

from typing import List, Optional, Tuple

try:
    from ursina import Entity, color
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


def create_clean_grid_lines(grid_size: int = 8, line_color: Optional[Tuple[float, float, float, float]] = None) -> List[Entity]:
    """
    Create clean visual grid lines for tactical battlefield display.
    
    Args:
        grid_size: Size of the grid (default 8x8)
        line_color: RGBA color tuple for grid lines (default semi-transparent gray)
        
    Returns:
        List of Entity objects representing the grid lines
        
    Raises:
        ImportError: If Ursina is not available
    """
    if not URSINA_AVAILABLE:
        raise ImportError("Ursina is required for create_clean_grid_lines")
    
    if line_color is None:
        line_color = color.Color(0.4, 0.4, 0.4, 0.5)
    
    grid_entities = []
    
    # Vertical lines
    for x in range(grid_size + 1):
        line = Entity(
            model='cube',
            color=line_color,
            scale=(0.02, 0.01, grid_size),
            position=(x, 0, grid_size / 2)
        )
        grid_entities.append(line)
    
    # Horizontal lines  
    for z in range(grid_size + 1):
        line = Entity(
            model='cube', 
            color=line_color,
            scale=(grid_size, 0.01, 0.02),
            position=(grid_size / 2, 0, z)
        )
        grid_entities.append(line)
    
    return grid_entities


def create_ground_plane(size: Tuple[float, float] = (20, 20), 
                       position: Tuple[float, float, float] = (4, -0.1, 4),
                       ground_color = None) -> Optional[Entity]:
    """
    Create a ground plane for better battlefield visibility.
    
    Args:
        size: (width, height) of the ground plane
        position: (x, y, z) position of the ground plane
        ground_color: Color for the ground plane (default dark gray)
        
    Returns:
        Entity object representing the ground plane, or None if Ursina unavailable
    """
    if not URSINA_AVAILABLE:
        return None
    
    if ground_color is None:
        ground_color = color.dark_gray
    
    ground = Entity(
        model='plane', 
        texture='white_cube', 
        color=ground_color, 
        scale=(size[0], 1, size[1]), 
        position=position
    )
    
    return ground


def cleanup_grid_entities(entities: List[Entity]):
    """
    Clean up and destroy a list of grid entities.
    
    Args:
        entities: List of Entity objects to destroy
    """
    if not URSINA_AVAILABLE:
        return
    
    from ursina import destroy
    
    for entity in entities:
        if entity:
            destroy(entity)