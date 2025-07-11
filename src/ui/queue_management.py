"""
Queue Management UI Framework

Provides visual interfaces for the action queue system, including:
- Action timeline display
- Unit action queue panels
- AI coordination displays
- Drag-and-drop action reordering
- Action prediction and preview
"""

from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

try:
    from ursina import *
    from ursina.shaders import lit_with_shadows_shader
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False
    # Mock classes for testing without Ursina
    class Entity:
        def __init__(self, **kwargs): 
            self.children = []
        def destroy(self): 
            pass
    class Button:
        def __init__(self, **kwargs): 
            self.on_click = None
    class Text:
        def __init__(self, **kwargs): 
            self.text = kwargs.get('text', '')
    class camera:
        ui = None

from game.managers.action_manager import ActionManager
from game.queue.action_queue import ActionPriority
from game.config.feature_flags import FeatureFlags


class UITheme(Enum):
    """UI theme styles for queue management."""
    TACTICAL = "tactical"      # Military-style dark theme
    FANTASY = "fantasy"        # Fantasy RPG theme
    MINIMAL = "minimal"        # Clean minimal theme
    CLASSIC = "classic"        # Traditional RPG theme


@dataclass
class UIConfig:
    """Configuration for queue management UI."""
    theme: UITheme = UITheme.TACTICAL
    enable_animations: bool = True
    enable_drag_drop: bool = True
    enable_previews: bool = True
    auto_update_interval: float = 0.5  # Seconds
    max_timeline_actions: int = 20
    show_ai_coordination: bool = True
    
    def __post_init__(self):
        """Load configuration from master UI config if available."""
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Override with master UI config values if available
            queue_config = ui_config.get('ui_queue_management.config', {})
            if queue_config:
                theme_str = queue_config.get('theme', self.theme.value)
                self.theme = UITheme(theme_str) if theme_str in [t.value for t in UITheme] else self.theme
                self.enable_animations = queue_config.get('enable_animations', self.enable_animations)
                self.enable_drag_drop = queue_config.get('enable_drag_drop', self.enable_drag_drop)
                self.enable_previews = queue_config.get('enable_previews', self.enable_previews)
                self.auto_update_interval = queue_config.get('auto_update_interval', self.auto_update_interval)
                self.max_timeline_actions = queue_config.get('max_timeline_actions', self.max_timeline_actions)
                self.show_ai_coordination = queue_config.get('show_ai_coordination', self.show_ai_coordination)
        except ImportError:
            pass  # Master UI config not available


@dataclass
class ActionDisplayData:
    """Data for displaying an action in the UI."""
    action_id: str
    action_name: str
    unit_id: str
    unit_name: str
    target_info: str
    priority: str
    execution_order: int
    is_ai_action: bool = False
    estimated_damage: Optional[int] = None
    resource_costs: Dict[str, int] = field(default_factory=dict)
    confidence: float = 1.0  # For AI actions


class QueueTimelineDisplay:
    """
    Visual timeline showing the order of action execution.
    
    Displays actions as a horizontal timeline with:
    - Action icons and names
    - Unit portraits
    - Execution order
    - Priority indicators
    - AI vs Player distinction
    """
    
    def __init__(self, parent_entity: Entity, action_manager: ActionManager, 
                 ui_config: UIConfig):
        self.parent = parent_entity
        self.action_manager = action_manager
        self.config = ui_config
        
        # UI elements
        self.timeline_container = None
        self.action_slots: List[Entity] = []
        self.timeline_actions: List[ActionDisplayData] = []
        
        # Theme configuration
        self.theme_colors = self._get_theme_colors()
        
        # Create UI
        self._create_timeline_ui()
        
        # Update tracking
        self.last_update = 0.0
        self.needs_refresh = True
    
    def _get_theme_colors(self) -> Dict[str, Tuple[float, float, float]]:
        """Get color scheme for current theme using master UI config."""
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Get theme colors from master UI config
            theme_name = self.config.theme.value
            theme_config = ui_config.get(f'ui_queue_management.themes.{theme_name}', {})
            
            if theme_config:
                return {
                    'background': ui_config.get_color_tuple(f'ui_queue_management.themes.{theme_name}.background', (0.1, 0.1, 0.15)),
                    'player_action': ui_config.get_color_tuple(f'ui_queue_management.themes.{theme_name}.player_action', (0.2, 0.4, 0.8)),
                    'ai_action': ui_config.get_color_tuple(f'ui_queue_management.themes.{theme_name}.ai_action', (0.8, 0.3, 0.2)),
                    'high_priority': ui_config.get_color_tuple(f'ui_queue_management.themes.{theme_name}.high_priority', (0.9, 0.7, 0.1)),
                    'normal_priority': ui_config.get_color_tuple(f'ui_queue_management.themes.{theme_name}.normal_priority', (0.7, 0.7, 0.7)),
                    'low_priority': ui_config.get_color_tuple(f'ui_queue_management.themes.{theme_name}.low_priority', (0.5, 0.5, 0.5)),
                    'text': ui_config.get_color_tuple(f'ui_queue_management.themes.{theme_name}.text', (0.9, 0.9, 0.9))
                }
        except ImportError:
            pass
        
        # Fallback to hardcoded themes
        themes = {
            UITheme.TACTICAL: {
                'background': (0.1, 0.1, 0.15),
                'player_action': (0.2, 0.4, 0.8),
                'ai_action': (0.8, 0.3, 0.2),
                'high_priority': (0.9, 0.7, 0.1),
                'normal_priority': (0.7, 0.7, 0.7),
                'low_priority': (0.5, 0.5, 0.5),
                'text': (0.9, 0.9, 0.9)
            },
            UITheme.FANTASY: {
                'background': (0.15, 0.1, 0.05),
                'player_action': (0.3, 0.6, 0.9),
                'ai_action': (0.9, 0.4, 0.2),
                'high_priority': (1.0, 0.8, 0.2),
                'normal_priority': (0.8, 0.8, 0.8),
                'low_priority': (0.6, 0.6, 0.6),
                'text': (1.0, 0.95, 0.85)
            },
            UITheme.MINIMAL: {
                'background': (0.95, 0.95, 0.95),
                'player_action': (0.2, 0.5, 0.8),
                'ai_action': (0.8, 0.3, 0.3),
                'high_priority': (0.9, 0.6, 0.1),
                'normal_priority': (0.4, 0.4, 0.4),
                'low_priority': (0.7, 0.7, 0.7),
                'text': (0.1, 0.1, 0.1)
            },
            UITheme.CLASSIC: {
                'background': (0.2, 0.15, 0.1),
                'player_action': (0.1, 0.4, 0.7),
                'ai_action': (0.7, 0.2, 0.1),
                'high_priority': (0.8, 0.6, 0.0),
                'normal_priority': (0.6, 0.6, 0.6),
                'low_priority': (0.4, 0.4, 0.4),
                'text': (0.9, 0.9, 0.8)
            }
        }
        return themes.get(self.config.theme, themes[UITheme.TACTICAL])
    
    def _create_timeline_ui(self):
        """Create the timeline UI structure using master UI config."""
        if not URSINA_AVAILABLE:
            print("📱 Timeline UI created (Ursina not available)")
            return
        
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Timeline container configuration from master UI config
            container_config = ui_config.get('ui_queue_management.timeline.container', {})
            container_model = container_config.get('model', 'cube')
            container_scale = container_config.get('scale', (12, 1.5, 0.1))
            container_position = container_config.get('position', (0, 8, 0))
            
            # Timeline title configuration from master UI config
            title_config = ui_config.get('ui_queue_management.timeline.title', {})
            title_text = title_config.get('text', 'Action Timeline')
            title_position = title_config.get('position', (-5.5, 0.6, -0.1))
            title_scale = title_config.get('scale', 2)
        except ImportError:
            # Fallback values if master UI config not available
            container_model = 'cube'
            container_scale = (12, 1.5, 0.1)
            container_position = (0, 8, 0)
            title_text = 'Action Timeline'
            title_position = (-5.5, 0.6, -0.1)
            title_scale = 2
        
        # Main timeline container
        self.timeline_container = Entity(
            parent=self.parent,
            model=container_model,
            color=self.theme_colors['background'],
            scale=container_scale,
            position=container_position
        )
        
        # Timeline title
        Text(
            title_text,
            parent=self.timeline_container,
            position=title_position,
            scale=title_scale,
            color=self.theme_colors['text']
        )
        
        # Create action slots
        self._create_action_slots()
        
        print("📱 Action Timeline UI created")
    
    def _create_action_slots(self):
        """Create slots for timeline actions using master UI config."""
        if not URSINA_AVAILABLE:
            return
        
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Action slots configuration from master UI config
            slots_config = ui_config.get('ui_queue_management.timeline.action_slots', {})
            slot_width = slots_config.get('slot_width', 0.8)
            start_x = slots_config.get('start_x', -5.5)
            slot_model = slots_config.get('model', 'cube')
            slot_color = ui_config.get_color_tuple('ui_queue_management.timeline.action_slots.color', (0.3, 0.3, 0.3))
            slot_height = slots_config.get('slot_height', 0.8)
            slot_thickness = slots_config.get('thickness', 0.05)
            slot_y = slots_config.get('y_position', -0.2)
            slot_z = slots_config.get('z_position', -0.05)
            slot_spacing = slots_config.get('spacing', 0.1)
            
            # Slot number configuration from master UI config
            number_config = slots_config.get('slot_number', {})
            number_y_offset = number_config.get('y_offset', -0.5)
            number_z_offset = number_config.get('z_offset', -0.1)
            number_scale = number_config.get('scale', 1.5)
        except ImportError:
            # Fallback values
            slot_width = 0.8
            start_x = -5.5
            slot_model = 'cube'
            slot_color = (0.3, 0.3, 0.3)
            slot_height = 0.8
            slot_thickness = 0.05
            slot_y = -0.2
            slot_z = -0.05
            slot_spacing = 0.1
            number_y_offset = -0.5
            number_z_offset = -0.1
            number_scale = 1.5
        
        self.action_slots = []
        
        for i in range(self.config.max_timeline_actions):
            slot = Entity(
                parent=self.timeline_container,
                model=slot_model,
                color=slot_color,
                scale=(slot_width, slot_height, slot_thickness),
                position=(start_x + i * (slot_width + slot_spacing), slot_y, slot_z)
            )
            
            # Slot number
            Text(
                str(i + 1),
                parent=slot,
                position=(0, number_y_offset, number_z_offset),
                scale=number_scale,
                color=self.theme_colors['text']
            )
            
            self.action_slots.append(slot)
    
    def update_timeline(self, timeline_data: List[ActionDisplayData]):
        """Update timeline with new action data."""
        if not self.needs_refresh and time.time() - self.last_update < self.config.auto_update_interval:
            return
        
        self.timeline_actions = timeline_data[:self.config.max_timeline_actions]
        self._refresh_timeline_display()
        
        self.last_update = time.time()
        self.needs_refresh = False
        
        print(f"📱 Timeline updated: {len(self.timeline_actions)} actions")
    
    def _refresh_timeline_display(self):
        """Refresh the visual display of timeline actions."""
        if not URSINA_AVAILABLE:
            return
        
        # Clear existing action displays
        for slot in self.action_slots:
            if hasattr(slot, 'children'):
                for child in list(slot.children):
                    if hasattr(child, 'action_data'):
                        child.destroy()
        
        # Display new actions
        for i, action_data in enumerate(self.timeline_actions):
            if i >= len(self.action_slots):
                break
            
            self._display_action_in_slot(self.action_slots[i], action_data)
    
    def _display_action_in_slot(self, slot: Entity, action_data: ActionDisplayData):
        """Display an action in a timeline slot."""
        if not URSINA_AVAILABLE:
            return
        
        # Action color based on type and priority
        if action_data.is_ai_action:
            base_color = self.theme_colors['ai_action']
        else:
            base_color = self.theme_colors['player_action']
        
        # Priority modifier
        if action_data.priority == 'HIGH':
            priority_color = self.theme_colors['high_priority']
        elif action_data.priority == 'LOW':
            priority_color = self.theme_colors['low_priority']
        else:
            priority_color = self.theme_colors['normal_priority']
        
        # Blend colors
        final_color = tuple((b + p) / 2 for b, p in zip(base_color, priority_color))
        
        # Action indicator
        action_visual = Entity(
            parent=slot,
            model='cube',
            color=final_color,
            scale=(0.7, 0.6, 0.1),
            position=(0, 0.1, -0.1)
        )
        action_visual.action_data = action_data
        
        # Action name
        Text(
            action_data.action_name[:8],  # Truncate long names
            parent=action_visual,
            position=(0, 0.4, -0.1),
            scale=1.2,
            color=self.theme_colors['text']
        )
        
        # Unit name
        Text(
            action_data.unit_name[:6],
            parent=action_visual,
            position=(0, -0.4, -0.1),
            scale=1.0,
            color=self.theme_colors['text']
        )
        
        # AI indicator
        if action_data.is_ai_action:
            Text(
                "AI",
                parent=action_visual,
                position=(0.25, 0.25, -0.1),
                scale=0.8,
                color=(1, 1, 0)
            )
    
    def force_refresh(self):
        """Force timeline refresh on next update."""
        self.needs_refresh = True
    
    def destroy(self):
        """Clean up timeline UI."""
        if self.timeline_container and URSINA_AVAILABLE:
            self.timeline_container.destroy()


class UnitActionQueuePanel:
    """
    Panel showing queued actions for a specific unit.
    
    Features:
    - List of unit's queued actions
    - Drag-and-drop reordering
    - Action details on hover
    - Remove/cancel actions
    - Add new actions
    """
    
    def __init__(self, parent_entity: Entity, unit_id: str, 
                 action_manager: ActionManager, ui_config: UIConfig):
        self.parent = parent_entity
        self.unit_id = unit_id
        self.action_manager = action_manager
        self.config = ui_config
        
        # UI elements
        self.panel_container = None
        self.action_list: List[Entity] = []
        self.unit_actions: List[ActionDisplayData] = []
        
        # Interaction state
        self.dragging_action = None
        self.drag_start_pos = None
        
        # Theme
        self.theme_colors = self._get_theme_colors()
        
        # Create UI
        self._create_panel_ui()
        
        print(f"📱 Unit Action Queue Panel created for {unit_id}")
    
    def _get_theme_colors(self) -> Dict[str, Tuple[float, float, float]]:
        """Get theme colors (shared with timeline)."""
        # Reuse theme logic from QueueTimelineDisplay
        return QueueTimelineDisplay(None, None, self.config)._get_theme_colors()
    
    def _create_panel_ui(self):
        """Create the unit action panel UI using master UI config."""
        if not URSINA_AVAILABLE:
            print(f"📱 Unit panel UI created for {self.unit_id} (Ursina not available)")
            return
        
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Panel container configuration from master UI config
            panel_config = ui_config.get('ui_queue_management.unit_panel.container', {})
            panel_model = panel_config.get('model', 'cube')
            panel_scale = panel_config.get('scale', (4, 6, 0.1))
            panel_position = panel_config.get('position', (6, 2, 0))
            
            # Panel title configuration from master UI config
            title_config = ui_config.get('ui_queue_management.unit_panel.title', {})
            title_position = title_config.get('position', (0, 2.5, -0.1))
            title_scale = title_config.get('scale', 1.5)
            title_template = title_config.get('text_template', '{unit_id} Actions')
            
            # Add button configuration from master UI config
            button_config = ui_config.get('ui_queue_management.unit_panel.add_button', {})
            button_text = button_config.get('text', '+ Add Action')
            button_scale = button_config.get('scale', (1.5, 0.4))
            button_position = button_config.get('position', (0, -2.5, -0.1))
        except ImportError:
            # Fallback values
            panel_model = 'cube'
            panel_scale = (4, 6, 0.1)
            panel_position = (6, 2, 0)
            title_position = (0, 2.5, -0.1)
            title_scale = 1.5
            title_template = '{unit_id} Actions'
            button_text = '+ Add Action'
            button_scale = (1.5, 0.4)
            button_position = (0, -2.5, -0.1)
        
        # Main panel container
        self.panel_container = Entity(
            parent=self.parent,
            model=panel_model,
            color=self.theme_colors['background'],
            scale=panel_scale,
            position=panel_position
        )
        
        # Panel title
        Text(
            title_template.format(unit_id=self.unit_id),
            parent=self.panel_container,
            position=title_position,
            scale=title_scale,
            color=self.theme_colors['text']
        )
        
        # Add action button
        add_button = Button(
            text=button_text,
            parent=self.panel_container,
            scale=button_scale,
            position=button_position,
            color=self.theme_colors['player_action']
        )
        add_button.on_click = self._on_add_action_clicked
    
    def update_unit_actions(self, actions: List[ActionDisplayData]):
        """Update the unit's action list."""
        self.unit_actions = actions
        self._refresh_action_list()
        print(f"📱 Unit {self.unit_id} actions updated: {len(actions)} actions")
    
    def _refresh_action_list(self):
        """Refresh the visual action list."""
        if not URSINA_AVAILABLE:
            return
        
        # Clear existing action items
        for action_item in self.action_list:
            action_item.destroy()
        self.action_list.clear()
        
        # Create new action items
        start_y = 1.8
        item_height = 0.7
        
        for i, action_data in enumerate(self.unit_actions):
            y_pos = start_y - i * item_height
            action_item = self._create_action_item(action_data, y_pos, i)
            self.action_list.append(action_item)
    
    def _create_action_item(self, action_data: ActionDisplayData, y_pos: float, index: int) -> Entity:
        """Create a visual item for an action."""
        if not URSINA_AVAILABLE:
            return None
        
        # Action item container
        item = Entity(
            parent=self.panel_container,
            model='cube',
            color=self.theme_colors['player_action'],
            scale=(3.5, 0.6, 0.05),
            position=(0, y_pos, -0.05)
        )
        item.action_data = action_data
        item.action_index = index
        
        # Action name
        Text(
            action_data.action_name,
            parent=item,
            position=(-1.2, 0.1, -0.1),
            scale=1.2,
            color=self.theme_colors['text']
        )
        
        # Target info
        Text(
            action_data.target_info,
            parent=item,
            position=(-1.2, -0.2, -0.1),
            scale=0.9,
            color=self.theme_colors['text']
        )
        
        # Priority indicator
        priority_color = {
            'HIGH': self.theme_colors['high_priority'],
            'NORMAL': self.theme_colors['normal_priority'],
            'LOW': self.theme_colors['low_priority']
        }.get(action_data.priority, self.theme_colors['normal_priority'])
        
        Text(
            action_data.priority,
            parent=item,
            position=(1.2, 0, -0.1),
            scale=1.0,
            color=priority_color
        )
        
        # Remove button
        remove_btn = Button(
            text="×",
            parent=item,
            scale=(0.3, 0.3),
            position=(1.5, 0, -0.1),
            color=(0.8, 0.2, 0.2)
        )
        remove_btn.on_click = lambda: self._on_remove_action(index)
        
        # Drag functionality (if enabled)
        if self.config.enable_drag_drop:
            item.on_click = lambda: self._start_drag(item)
        
        return item
    
    def _on_add_action_clicked(self):
        """Handle add action button click."""
        print(f"📱 Add action clicked for {self.unit_id}")
        # In a full implementation, this would open an action selection dialog
        
    def _on_remove_action(self, action_index: int):
        """Handle remove action button click."""
        if 0 <= action_index < len(self.unit_actions):
            action_data = self.unit_actions[action_index]
            print(f"📱 Removing action {action_data.action_name} from {self.unit_id}")
            
            # Remove from action manager
            success = self.action_manager.remove_unit_action(self.unit_id, action_index)
            if success:
                # Update local list
                self.unit_actions.pop(action_index)
                self._refresh_action_list()
    
    def _start_drag(self, item: Entity):
        """Start dragging an action item."""
        if self.config.enable_drag_drop:
            self.dragging_action = item
            self.drag_start_pos = item.position
            print(f"📱 Started dragging {item.action_data.action_name}")
    
    def destroy(self):
        """Clean up panel UI."""
        if self.panel_container and URSINA_AVAILABLE:
            self.panel_container.destroy()


class AICoordinationDisplay:
    """
    Display showing AI coordination and battle plans.
    
    Features:
    - Current AI battle plan
    - Unit assignments and objectives
    - AI confidence levels
    - Coordination timeline
    - Performance metrics
    """
    
    def __init__(self, parent_entity: Entity, action_manager: ActionManager, ui_config: UIConfig):
        self.parent = parent_entity
        self.action_manager = action_manager
        self.config = ui_config
        
        # UI elements
        self.coordination_panel = None
        self.battle_plan_text = None
        self.unit_assignments: Dict[str, Entity] = {}
        
        # Data
        self.current_battle_plan = None
        self.ai_metrics = {}
        
        # Theme
        self.theme_colors = self._get_theme_colors()
        
        # Create UI
        if self.config.show_ai_coordination:
            self._create_coordination_ui()
        
        print("📱 AI Coordination Display created")
    
    def _get_theme_colors(self) -> Dict[str, Tuple[float, float, float]]:
        """Get theme colors."""
        return QueueTimelineDisplay(None, None, self.config)._get_theme_colors()
    
    def _create_coordination_ui(self):
        """Create AI coordination UI using master UI config."""
        if not URSINA_AVAILABLE:
            print("📱 AI coordination UI created (Ursina not available)")
            return
        
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Coordination panel configuration from master UI config
            coord_config = ui_config.get('ui_queue_management.ai_coordination.panel', {})
            panel_model = coord_config.get('model', 'cube')
            panel_scale = coord_config.get('scale', (5, 4, 0.1))
            panel_position = coord_config.get('position', (-6, 2, 0))
            
            # Title configuration from master UI config
            title_config = ui_config.get('ui_queue_management.ai_coordination.title', {})
            title_text = title_config.get('text', 'AI Coordination')
            title_position = title_config.get('position', (0, 1.7, -0.1))
            title_scale = title_config.get('scale', 1.5)
            
            # Section configurations from master UI config
            sections_config = ui_config.get('ui_queue_management.ai_coordination.sections', {})
            battle_plan_config = sections_config.get('battle_plan', {})
            battle_plan_label = battle_plan_config.get('label', 'Battle Plan:')
            battle_plan_label_pos = battle_plan_config.get('label_position', (-2, 1.2, -0.1))
            battle_plan_text_pos = battle_plan_config.get('text_position', (-2, 0.8, -0.1))
            battle_plan_default = battle_plan_config.get('default_text', 'No active plan')
            
            metrics_config = sections_config.get('metrics', {})
            metrics_label = metrics_config.get('label', 'AI Performance:')
            metrics_label_pos = metrics_config.get('label_position', (-2, 0.2, -0.1))
            
            # Text scales from master UI config
            label_scale = sections_config.get('label_scale', 1.2)
            text_scale = sections_config.get('text_scale', 1.0)
        except ImportError:
            # Fallback values
            panel_model = 'cube'
            panel_scale = (5, 4, 0.1)
            panel_position = (-6, 2, 0)
            title_text = 'AI Coordination'
            title_position = (0, 1.7, -0.1)
            title_scale = 1.5
            battle_plan_label = 'Battle Plan:'
            battle_plan_label_pos = (-2, 1.2, -0.1)
            battle_plan_text_pos = (-2, 0.8, -0.1)
            battle_plan_default = 'No active plan'
            metrics_label = 'AI Performance:'
            metrics_label_pos = (-2, 0.2, -0.1)
            label_scale = 1.2
            text_scale = 1.0
        
        # Main coordination panel
        self.coordination_panel = Entity(
            parent=self.parent,
            model=panel_model,
            color=self.theme_colors['background'],
            scale=panel_scale,
            position=panel_position
        )
        
        # Panel title
        Text(
            title_text,
            parent=self.coordination_panel,
            position=title_position,
            scale=title_scale,
            color=self.theme_colors['ai_action']
        )
        
        # Battle plan section
        Text(
            battle_plan_label,
            parent=self.coordination_panel,
            position=battle_plan_label_pos,
            scale=label_scale,
            color=self.theme_colors['text']
        )
        
        self.battle_plan_text = Text(
            battle_plan_default,
            parent=self.coordination_panel,
            position=battle_plan_text_pos,
            scale=text_scale,
            color=self.theme_colors['text']
        )
        
        # Metrics section
        Text(
            metrics_label,
            parent=self.coordination_panel,
            position=metrics_label_pos,
            scale=label_scale,
            color=self.theme_colors['text']
        )
        
        # Performance metrics will be dynamically updated
    
    def update_ai_coordination(self, battle_plan: Optional[Dict[str, Any]], 
                             metrics: Dict[str, Any]):
        """Update AI coordination display."""
        self.current_battle_plan = battle_plan
        self.ai_metrics = metrics
        
        if not URSINA_AVAILABLE:
            print(f"📱 AI coordination updated: Plan={battle_plan is not None}")
            return
        
        # Update battle plan text
        if battle_plan and self.battle_plan_text:
            plan_text = battle_plan.get('objective', 'Tactical coordination')
            self.battle_plan_text.text = plan_text[:30]  # Truncate long text
        
        print(f"📱 AI coordination display updated")
    
    def destroy(self):
        """Clean up coordination UI."""
        if self.coordination_panel and URSINA_AVAILABLE:
            self.coordination_panel.destroy()


class QueueManagementUIManager:
    """
    Main manager for all queue management UI components.
    
    Coordinates:
    - Timeline display
    - Unit action panels
    - AI coordination display
    - UI updates and synchronization
    """
    
    def __init__(self, action_manager: ActionManager, ui_config: Optional[UIConfig] = None):
        self.action_manager = action_manager
        self.config = ui_config or UIConfig()
        
        # UI components
        self.timeline_display: Optional[QueueTimelineDisplay] = None
        self.unit_panels: Dict[str, UnitActionQueuePanel] = {}
        self.ai_coordination: Optional[AICoordinationDisplay] = None
        
        # UI root
        self.ui_root = None
        
        # Update tracking
        self.last_update = 0.0
        self.is_active = False
        
        print("📱 Queue Management UI Manager initialized")
    
    def initialize_ui(self, camera_entity=None):
        """Initialize all UI components."""
        if not FeatureFlags.USE_NEW_QUEUE_UI:
            print("📱 Queue UI disabled by feature flags")
            return False
        
        try:
            # Create UI root
            if URSINA_AVAILABLE:
                try:
                    self.ui_root = Entity(parent=camera.ui if camera_entity is None else camera_entity)
                except:
                    # Fallback if Ursina not properly initialized
                    self.ui_root = Entity()
            else:
                self.ui_root = Entity()
            
            # Initialize components
            self.timeline_display = QueueTimelineDisplay(
                self.ui_root, self.action_manager, self.config
            )
            
            self.ai_coordination = AICoordinationDisplay(
                self.ui_root, self.action_manager, self.config
            )
            
            self.is_active = True
            print("📱 Queue Management UI initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Queue Management UI: {e}")
            return False
    
    def create_unit_panel(self, unit_id: str) -> bool:
        """Create action queue panel for a specific unit."""
        if not self.is_active or unit_id in self.unit_panels:
            return False
        
        try:
            panel = UnitActionQueuePanel(
                self.ui_root, unit_id, self.action_manager, self.config
            )
            self.unit_panels[unit_id] = panel
            print(f"📱 Created unit panel for {unit_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create unit panel for {unit_id}: {e}")
            return False
    
    def update_ui(self, force_update: bool = False):
        """Update all UI components with current game state."""
        if not self.is_active:
            return
        
        current_time = time.time()
        if not force_update and current_time - self.last_update < self.config.auto_update_interval:
            return
        
        try:
            # Update timeline
            if self.timeline_display:
                timeline_data = self._get_timeline_data()
                self.timeline_display.update_timeline(timeline_data)
            
            # Update unit panels
            for unit_id, panel in self.unit_panels.items():
                unit_actions = self._get_unit_actions_data(unit_id)
                panel.update_unit_actions(unit_actions)
            
            # Update AI coordination
            if self.ai_coordination:
                battle_plan, metrics = self._get_ai_coordination_data()
                self.ai_coordination.update_ai_coordination(battle_plan, metrics)
            
            self.last_update = current_time
            
        except Exception as e:
            print(f"❌ Error updating Queue Management UI: {e}")
    
    def _get_timeline_data(self) -> List[ActionDisplayData]:
        """Get timeline data from action manager."""
        try:
            # Get unit stats for timeline resolution
            unit_stats = self._get_unit_stats()
            timeline_preview = self.action_manager.get_action_queue_preview(unit_stats)
            
            timeline_data = []
            for i, entry in enumerate(timeline_preview):
                action_data = ActionDisplayData(
                    action_id=entry.get('action_id', 'unknown'),
                    action_name=entry.get('action_name', 'Unknown Action'),
                    unit_id=entry.get('unit_id', 'unknown'),
                    unit_name=entry.get('unit_id', 'Unknown').replace('_', ' ').title(),
                    target_info=f"{entry.get('targets', 0)} targets",
                    priority=entry.get('priority', 'NORMAL'),
                    execution_order=entry.get('execution_order', i),
                    is_ai_action='ai' in entry.get('unit_id', '').lower()
                )
                timeline_data.append(action_data)
            
            return timeline_data
            
        except Exception as e:
            print(f"❌ Error getting timeline data: {e}")
            return []
    
    def _get_unit_actions_data(self, unit_id: str) -> List[ActionDisplayData]:
        """Get action data for a specific unit."""
        try:
            unit_preview = self.action_manager.get_unit_queue_preview(unit_id)
            
            actions_data = []
            for entry in unit_preview:
                action_data = ActionDisplayData(
                    action_id=entry.get('action_id', 'unknown'),
                    action_name=entry.get('action_name', 'Unknown Action'),
                    unit_id=unit_id,
                    unit_name=unit_id.replace('_', ' ').title(),
                    target_info=f"{entry.get('targets', 0)} targets",
                    priority=entry.get('priority', 'NORMAL'),
                    execution_order=entry.get('index', 0),
                    is_ai_action='ai' in unit_id.lower()
                )
                actions_data.append(action_data)
            
            return actions_data
            
        except Exception as e:
            print(f"❌ Error getting unit actions for {unit_id}: {e}")
            return []
    
    def _get_ai_coordination_data(self) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """Get AI coordination data."""
        try:
            # Get AI system status if available
            if hasattr(self.action_manager, 'ai_integration_manager'):
                ai_manager = self.action_manager.ai_integration_manager
                status = ai_manager.get_ai_system_status()
                
                battle_plan = None
                if 'orchestration_status' in status:
                    orchestration = status['orchestration_status']
                    battle_plan = orchestration.get('current_battle_plan')
                
                metrics = status.get('performance_metrics', {})
                return battle_plan, metrics
            
            return None, {}
            
        except Exception as e:
            print(f"❌ Error getting AI coordination data: {e}")
            return None, {}
    
    def _get_unit_stats(self) -> Dict[str, Any]:
        """Get unit stats for timeline calculations."""
        unit_stats = {}
        try:
            for unit_id, unit in self.action_manager.game_controller.units.items():
                unit_stats[unit_id] = {
                    'initiative': getattr(unit, 'initiative', 50)
                }
        except Exception as e:
            print(f"❌ Error getting unit stats: {e}")
        
        return unit_stats
    
    def set_theme(self, theme: UITheme):
        """Change UI theme."""
        self.config.theme = theme
        
        # Force refresh all components
        if self.timeline_display:
            self.timeline_display.theme_colors = self.timeline_display._get_theme_colors()
            self.timeline_display.force_refresh()
        
        for panel in self.unit_panels.values():
            panel.theme_colors = panel._get_theme_colors()
            panel._refresh_action_list()
        
        print(f"📱 UI theme changed to {theme.value}")
    
    def shutdown(self):
        """Shutdown and cleanup UI manager."""
        self.is_active = False
        
        # Destroy components
        if self.timeline_display:
            self.timeline_display.destroy()
        
        for panel in self.unit_panels.values():
            panel.destroy()
        
        if self.ai_coordination:
            self.ai_coordination.destroy()
        
        # Destroy UI root
        if self.ui_root and hasattr(self.ui_root, 'destroy'):
            self.ui_root.destroy()
        
        print("📱 Queue Management UI Manager shut down")