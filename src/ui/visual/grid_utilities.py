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
    Create clean visual grid lines for tactical battlefield display using master UI config.
    
    Args:
        grid_size: Size of the grid (default 8x8)
        line_color: RGBA color tuple for grid lines (default from master UI config)
        
    Returns:
        List of Entity objects representing the grid lines
        
    Raises:
        ImportError: If Ursina is not available
    """
    if not URSINA_AVAILABLE:
        raise ImportError("Ursina is required for create_clean_grid_lines")
    
    # Load master UI configuration for grid lines
    try:
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        # Grid line configuration from master UI config
        grid_config = ui_config.get('ui_visual.grid_utilities.grid_lines', {})
        
        # Use provided color or get from master UI config
        if line_color is None:
            line_color = ui_config.get_color_rgba('ui_visual.grid_utilities.grid_lines.color', (0.4, 0.4, 0.4, 0.5))
            if URSINA_AVAILABLE and isinstance(line_color, tuple):
                line_color = color.Color(*line_color)
        
        # Line dimensions from master UI config
        line_model = grid_config.get('model', 'cube')
        line_width = grid_config.get('line_width', 0.02)
        line_height = grid_config.get('line_height', 0.01)
        vertical_y_position = grid_config.get('vertical_y_position', 0)
        horizontal_y_position = grid_config.get('horizontal_y_position', 0)
    except ImportError:
        # Fallback values if master UI config not available
        if line_color is None:
            line_color = color.Color(0.4, 0.4, 0.4, 0.5)
        line_model = 'cube'
        line_width = 0.02
        line_height = 0.01
        vertical_y_position = 0
        horizontal_y_position = 0
    
    grid_entities = []
    
    # Vertical lines
    for x in range(grid_size + 1):
        line = Entity(
            model=line_model,
            color=line_color,
            scale=(line_width, line_height, grid_size),
            position=(x, vertical_y_position, grid_size / 2)
        )
        grid_entities.append(line)
    
    # Horizontal lines  
    for z in range(grid_size + 1):
        line = Entity(
            model=line_model,
            color=line_color,
            scale=(grid_size, line_height, line_width),
            position=(grid_size / 2, horizontal_y_position, z)
        )
        grid_entities.append(line)
    
    return grid_entities


def create_ground_plane(size: Tuple[float, float] = (20, 20), 
                       position: Tuple[float, float, float] = (4, -0.1, 4),
                       ground_color = None) -> Optional[Entity]:
    """
    Create a ground plane for better battlefield visibility using master UI config.
    
    Args:
        size: (width, height) of the ground plane (default from master UI config)
        position: (x, y, z) position of the ground plane (default from master UI config)
        ground_color: Color for the ground plane (default from master UI config)
        
    Returns:
        Entity object representing the ground plane, or None if Ursina unavailable
    """
    if not URSINA_AVAILABLE:
        return None
    
    # Load master UI configuration for ground plane
    try:
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        # Ground plane configuration from master UI config
        ground_config = ui_config.get('ui_visual.grid_utilities.ground_plane', {})
        
        # Use provided values or get from master UI config
        if size == (20, 20):  # Check if using default size
            config_size = ground_config.get('size', {'width': 20, 'height': 20})
            size = (config_size['width'], config_size['height'])
        
        if position == (4, -0.1, 4):  # Check if using default position
            config_position = ground_config.get('position', {'x': 4, 'y': -0.1, 'z': 4})
            position = (config_position['x'], config_position['y'], config_position['z'])
        
        if ground_color is None:
            ground_color = ui_config.get_color('ui_visual.grid_utilities.ground_plane.color', '#2F2F2F')
        
        # Ground plane properties from master UI config
        ground_model = ground_config.get('model', 'plane')
        ground_texture = ground_config.get('texture', 'white_cube')
        ground_scale_y = ground_config.get('scale_y', 1)
    except ImportError:
        # Fallback values if master UI config not available
        if ground_color is None:
            ground_color = color.dark_gray
        ground_model = 'plane'
        ground_texture = 'white_cube'
        ground_scale_y = 1
    
    ground = Entity(
        model=ground_model,
        texture=ground_texture,
        color=ground_color,
        scale=(size[0], ground_scale_y, size[1]),
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