"""
Safe Tooltip Wrapper

Provides a crash-safe tooltip implementation that prevents the AttributeError: 'Tooltip' object has no attribute 'margin'
error that's been crashing the UI session.
"""

import logging

# Set up logging for tooltip issues
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class SafeTooltip:
    """Safe tooltip wrapper that prevents crashes"""
    
    def __init__(self, text="", **kwargs):
        """Initialize safe tooltip that never crashes"""
        self.text = text
        self.enabled = False
        self.background = SafeBackground()
        logger.debug(f"SafeTooltip created with text: {text}")
    
    def update(self):
        """Safe update method that does nothing"""
        pass
    
    def destroy(self):
        """Safe destroy method"""
        pass

class SafeBackground:
    """Safe background object for tooltip"""
    
    def __init__(self):
        self._color = None
    
    @property 
    def color(self):
        return self._color
    
    @color.setter
    def color(self, value):
        self._color = value

# Try to import real Tooltip, but fall back to safe version
try:
    from ursina import Tooltip as UrsinaTooltip
    
    # Test if the real Tooltip has the margin attribute issue
    test_tooltip = UrsinaTooltip("test")
    if not hasattr(test_tooltip, 'margin'):
        logger.warning("Ursina Tooltip missing margin attribute - using SafeTooltip")
        Tooltip = SafeTooltip
        TOOLTIP_SAFE = False
    else:
        Tooltip = UrsinaTooltip
        TOOLTIP_SAFE = True
        
    # Clean up test tooltip
    try:
        test_tooltip.destroy()
    except:
        pass
        
except Exception as e:
    logger.error(f"Ursina Tooltip not available or broken: {e}")
    Tooltip = SafeTooltip
    TOOLTIP_SAFE = False

def create_safe_tooltip(text, **kwargs):
    """Create a tooltip safely, never crashes"""
    try:
        if TOOLTIP_SAFE:
            return UrsinaTooltip(text, **kwargs)
        else:
            return SafeTooltip(text, **kwargs)
    except Exception as e:
        logger.error(f"Tooltip creation failed: {e}")
        return SafeTooltip(text, **kwargs)

# Export the safe version
__all__ = ['Tooltip', 'SafeTooltip', 'create_safe_tooltip', 'TOOLTIP_SAFE']