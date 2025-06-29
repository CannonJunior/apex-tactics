# User Interaction System

## Overview

This directory contains the user interaction system that handles player inputs, modal dialogs, and interactive elements in Apex Tactics. The system provides a layer between raw input events and game logic, enabling intuitive tactical gameplay through mouse, keyboard, and UI interactions.

## Architecture

### Interaction Flow
```
Raw Input Events
    ↓
Input Handler (Processing & Validation)
    ↓
Interaction Manager (Coordination & State)
    ↓
Action Modals (User Confirmation)
    ↓
Game Logic (Action Execution)
```

### Component Responsibilities
- **Input Handler** - Processes raw input events and translates to game actions
- **Interaction Manager** - Coordinates between different interaction systems
- **Action Modals** - Provide user feedback and confirmation dialogs
- **Interactive Tiles** - Handle battlefield grid interactions and highlighting

## Core Components

### `input_handler.py` - Input Processing
Central input processing system that handles all user input:

#### Key Responsibilities
- **Keyboard Input** - Hotkeys, camera controls, panel toggles
- **Mouse Input** - Grid clicks, UI interactions, drag operations
- **Input Validation** - Ensure inputs are valid for current game state
- **Context Awareness** - Different input handling based on current mode

#### Input Processing Pattern
```python
class InputHandler:
    def __init__(self, game_controller):
        self.game_controller = game_controller
        self.current_mode = "normal"
        self.input_bindings = self._setup_input_bindings()
    
    def handle_input(self, event):
        """Process input event based on current context"""
        if self.current_mode == "movement":
            return self._handle_movement_input(event)
        elif self.current_mode == "attack":
            return self._handle_attack_input(event)
        elif self.current_mode == "menu":
            return self._handle_menu_input(event)
        else:
            return self._handle_normal_input(event)
    
    def _handle_grid_click(self, x, y):
        """Handle clicks on tactical grid"""
        if self.current_mode == "attack":
            self.game_controller.handle_attack_target_selection(x, y)
        elif self.current_mode == "movement":
            self.game_controller.handle_movement_target_selection(x, y)
        else:
            self.game_controller.handle_tile_click(x, y)
```

#### Input Binding System
```python
def _setup_input_bindings(self):
    """Define keyboard shortcuts and their actions"""
    return {
        # Panel toggles
        'i': lambda: self.toggle_panel('inventory'),
        'c': lambda: self.toggle_panel('character'),
        'p': lambda: self.toggle_panel('party'),
        
        # Game controls
        'space': lambda: self.end_turn(),
        'escape': lambda: self.cancel_current_action(),
        
        # Camera controls
        '1': lambda: self.set_camera_mode('orbit'),
        '2': lambda: self.set_camera_mode('free'),
        '3': lambda: self.set_camera_mode('top_down'),
        
        # Movement controls (when unit selected)
        'w': lambda: self.move_cursor(0, 1),
        'a': lambda: self.move_cursor(-1, 0),
        's': lambda: self.move_cursor(0, -1),
        'd': lambda: self.move_cursor(1, 0),
        'enter': lambda: self.confirm_action()
    }
```

### `interaction_manager.py` - Interaction Coordination
Manages the overall interaction state and coordinates between different systems:

#### State Management
```python
class InteractionManager:
    def __init__(self):
        self.interaction_mode = InteractionMode.NORMAL
        self.selected_unit = None
        self.target_cursor = None
        self.pending_action = None
        self.modal_stack = []
    
    def set_interaction_mode(self, mode: InteractionMode):
        """Change interaction mode and update UI accordingly"""
        self.interaction_mode = mode
        self._update_ui_for_mode(mode)
        self._clear_incompatible_state(mode)
    
    def push_modal(self, modal):
        """Add modal to stack and handle input routing"""
        self.modal_stack.append(modal)
        modal.show()
    
    def pop_modal(self):
        """Remove top modal and restore previous input handling"""
        if self.modal_stack:
            modal = self.modal_stack.pop()
            modal.hide()
            return modal
        return None
```

#### Interaction Modes
```python
class InteractionMode(Enum):
    NORMAL = "normal"           # Default state, unit selection
    MOVEMENT = "movement"       # Planning unit movement
    ATTACK = "attack"          # Selecting attack targets
    ABILITY = "ability"        # Using special abilities
    INVENTORY = "inventory"    # Managing equipment
    MENU = "menu"             # In UI menus
```

### `action_modal.py` - User Confirmation Dialogs
Provides modal dialogs for action confirmation and user feedback:

#### Modal Types
```python
class ActionModalType(Enum):
    MOVEMENT_CONFIRM = "movement_confirm"
    ATTACK_CONFIRM = "attack_confirm" 
    ABILITY_CONFIRM = "ability_confirm"
    ITEM_USE_CONFIRM = "item_use_confirm"
    END_TURN_CONFIRM = "end_turn_confirm"

class ActionModal:
    def __init__(self, modal_type, action_data, callback):
        self.modal_type = modal_type
        self.action_data = action_data
        self.callback = callback
        self.ui_elements = []
    
    def create_movement_modal(self, unit, destination):
        """Create modal for movement confirmation"""
        distance = calculate_distance(unit.position, destination)
        move_cost = calculate_move_cost(unit, destination)
        
        content = [
            Text(f"Move {unit.name} to ({destination.x}, {destination.y})?"),
            Text(f"Distance: {distance} tiles"),
            Text(f"Movement cost: {move_cost} AP"),
            self._create_confirm_buttons()
        ]
        
        return WindowPanel(
            title="Confirm Movement",
            content=content,
            popup=True
        )
    
    def create_attack_modal(self, attacker, targets):
        """Create modal for attack confirmation"""
        target_list = [f"• {target.name}" for target in targets]
        
        content = [
            Text(f"{attacker.name} will attack:"),
            *[Text(target) for target in target_list],
            Text(f"Weapon: {attacker.equipped_weapon.name}"),
            Text(f"Expected damage: {calculate_expected_damage(attacker, targets)}"),
            self._create_confirm_buttons()
        ]
        
        return WindowPanel(
            title="Confirm Attack",
            content=content,
            popup=True
        )
```

#### Modal Management
```python
def show_modal(self, modal_type, action_data):
    """Display appropriate modal for action type"""
    modal_creators = {
        ActionModalType.MOVEMENT_CONFIRM: self.create_movement_modal,
        ActionModalType.ATTACK_CONFIRM: self.create_attack_modal,
        ActionModalType.ABILITY_CONFIRM: self.create_ability_modal
    }
    
    creator = modal_creators.get(modal_type)
    if creator:
        modal = creator(action_data)
        self.interaction_manager.push_modal(modal)
        return modal
    
    return None
```

### `interactive_tile.py` - Grid Interaction
Handles individual tile interactions and visual feedback:

#### Tile States and Highlighting
```python
class InteractiveTile:
    def __init__(self, x, y, tile_entity):
        self.x = x
        self.y = y
        self.tile_entity = tile_entity
        self.highlight_state = TileHighlightState.NORMAL
        self.is_interactive = True
    
    def highlight(self, highlight_type):
        """Apply visual highlighting to tile"""
        highlight_colors = {
            TileHighlightState.SELECTED: color.yellow,
            TileHighlightState.MOVEMENT_RANGE: color.green,
            TileHighlightState.ATTACK_RANGE: color.red,
            TileHighlightState.ATTACK_AREA: color.orange,
            TileHighlightState.INVALID: color.dark_gray
        }
        
        self.highlight_state = highlight_type
        highlight_color = highlight_colors.get(highlight_type, color.white)
        self.tile_entity.color = highlight_color
    
    def clear_highlight(self):
        """Remove highlighting from tile"""
        self.highlight_state = TileHighlightState.NORMAL
        self.tile_entity.color = color.white
    
    def on_click(self):
        """Handle tile click events"""
        if not self.is_interactive:
            return False
        
        # Route click to interaction manager
        interaction_manager.handle_tile_click(self.x, self.y)
        return True
    
    def on_hover(self):
        """Handle tile hover events"""
        if self.is_interactive and self.highlight_state == TileHighlightState.NORMAL:
            self.tile_entity.color = color.light_gray
    
    def on_hover_exit(self):
        """Handle mouse leaving tile"""
        if self.highlight_state == TileHighlightState.NORMAL:
            self.tile_entity.color = color.white
```

#### Grid Highlighting System
```python
class GridHighlighter:
    def __init__(self, grid_tiles):
        self.grid_tiles = grid_tiles
        self.highlighted_tiles = set()
    
    def highlight_movement_range(self, unit):
        """Highlight all tiles unit can move to"""
        self.clear_all_highlights()
        
        for x in range(len(self.grid_tiles)):
            for y in range(len(self.grid_tiles[0])):
                if unit.can_move_to(x, y):
                    tile = self.grid_tiles[x][y]
                    tile.highlight(TileHighlightState.MOVEMENT_RANGE)
                    self.highlighted_tiles.add((x, y))
    
    def highlight_attack_range(self, unit):
        """Highlight all tiles unit can attack"""
        self.clear_all_highlights()
        
        attack_range = unit.attack_range
        unit_pos = (unit.x, unit.y)
        
        for x in range(len(self.grid_tiles)):
            for y in range(len(self.grid_tiles[0])):
                distance = calculate_manhattan_distance(unit_pos, (x, y))
                if 0 < distance <= attack_range:
                    tile = self.grid_tiles[x][y]
                    tile.highlight(TileHighlightState.ATTACK_RANGE)
                    self.highlighted_tiles.add((x, y))
    
    def highlight_attack_area(self, center_pos, area_radius):
        """Highlight area effect around target position"""
        for x in range(len(self.grid_tiles)):
            for y in range(len(self.grid_tiles[0])):
                distance = calculate_manhattan_distance(center_pos, (x, y))
                if distance <= area_radius:
                    tile = self.grid_tiles[x][y]
                    if distance == 0:
                        tile.highlight(TileHighlightState.SELECTED)  # Center
                    else:
                        tile.highlight(TileHighlightState.ATTACK_AREA)  # Area
                    self.highlighted_tiles.add((x, y))
```

## Interaction Patterns

### Turn-Based Action Sequence
```python
def handle_unit_turn(self, unit):
    """Handle complete turn sequence for a unit"""
    # 1. Unit selection
    self.select_unit(unit)
    self.highlight_available_actions(unit)
    
    # 2. Action selection
    self.show_action_modal(unit)
    action = self.wait_for_action_selection()
    
    # 3. Target selection (if needed)
    if action.requires_target:
        self.enter_targeting_mode(action)
        target = self.wait_for_target_selection()
        action.set_target(target)
    
    # 4. Confirmation
    if action.requires_confirmation:
        confirmed = self.show_confirmation_modal(action)
        if not confirmed:
            return self.handle_unit_turn(unit)  # Restart turn
    
    # 5. Execution
    result = self.execute_action(action)
    self.show_action_result(result)
    
    # 6. Turn cleanup
    self.clear_highlights()
    self.end_unit_turn(unit)
```

### Context-Sensitive Input Handling
```python
class ContextualInputHandler:
    def handle_key_input(self, key):
        """Handle keyboard input based on current context"""
        # Global shortcuts always available
        if key in self.global_shortcuts:
            return self.global_shortcuts[key]()
        
        # Context-specific handling
        if self.interaction_manager.interaction_mode == InteractionMode.MOVEMENT:
            return self._handle_movement_keys(key)
        elif self.interaction_manager.interaction_mode == InteractionMode.ATTACK:
            return self._handle_attack_keys(key)
        elif self.modal_stack:
            return self._handle_modal_keys(key)
        else:
            return self._handle_normal_keys(key)
    
    def _handle_movement_keys(self, key):
        """Handle keys during movement planning"""
        movement_keys = {
            'w': lambda: self.move_cursor(0, 1),
            'a': lambda: self.move_cursor(-1, 0),
            's': lambda: self.move_cursor(0, -1),
            'd': lambda: self.move_cursor(1, 0),
            'enter': lambda: self.confirm_movement(),
            'escape': lambda: self.cancel_movement()
        }
        
        if key in movement_keys:
            return movement_keys[key]()
        return False
```

### Visual Feedback System
```python
class FeedbackSystem:
    def provide_action_feedback(self, action, result):
        """Provide visual and audio feedback for actions"""
        # Visual effects
        if isinstance(action, AttackAction):
            self.show_damage_numbers(result.targets, result.damage)
            self.show_impact_effects(result.targets)
        elif isinstance(action, MovementAction):
            self.show_movement_trail(action.path)
        
        # Audio feedback
        sound_map = {
            AttackAction: "attack_hit.wav",
            MovementAction: "footstep.wav",
            AbilityAction: "spell_cast.wav"
        }
        
        sound_file = sound_map.get(type(action))
        if sound_file:
            self.play_sound_effect(sound_file)
        
        # UI updates
        self.update_relevant_panels(action, result)
    
    def show_damage_numbers(self, targets, damage_amounts):
        """Display floating damage numbers"""
        for target, damage in zip(targets, damage_amounts):
            damage_text = Text(
                text=str(damage),
                position=target.position + Vector3(0, 0.5, 0),
                color=color.red,
                scale=2
            )
            
            # Animate damage number floating upward
            self.animate_floating_text(damage_text)
```

## Advanced Interaction Features

### Drag and Drop System
```python
class DragDropHandler:
    def __init__(self):
        self.dragging = False
        self.drag_object = None
        self.drag_start_pos = None
    
    def start_drag(self, obj, start_pos):
        """Begin dragging an object"""
        self.dragging = True
        self.drag_object = obj
        self.drag_start_pos = start_pos
        obj.z -= 0.01  # Bring to front
    
    def update_drag(self, current_pos):
        """Update object position during drag"""
        if self.dragging and self.drag_object:
            self.drag_object.position = current_pos
    
    def end_drag(self, end_pos):
        """Complete drag operation"""
        if self.dragging and self.drag_object:
            # Validate drop location
            if self.is_valid_drop_location(end_pos):
                self.execute_drop(self.drag_object, end_pos)
            else:
                # Return to original position
                self.drag_object.position = self.drag_start_pos
        
        self.cleanup_drag()
    
    def cleanup_drag(self):
        """Clean up drag state"""
        if self.drag_object:
            self.drag_object.z += 0.01  # Return to normal layer
        
        self.dragging = False
        self.drag_object = None
        self.drag_start_pos = None
```

### Gesture Recognition
```python
class GestureRecognizer:
    def __init__(self):
        self.gesture_buffer = []
        self.gesture_patterns = self._define_gesture_patterns()
    
    def add_input_point(self, point, timestamp):
        """Add input point to gesture buffer"""
        self.gesture_buffer.append((point, timestamp))
        
        # Keep buffer size manageable
        if len(self.gesture_buffer) > 50:
            self.gesture_buffer.pop(0)
        
        # Check for completed gestures
        self.check_for_gestures()
    
    def check_for_gestures(self):
        """Analyze buffer for recognized gesture patterns"""
        for gesture_name, pattern in self.gesture_patterns.items():
            if self.matches_pattern(self.gesture_buffer, pattern):
                self.execute_gesture(gesture_name)
                self.clear_gesture_buffer()
                break
    
    def _define_gesture_patterns(self):
        """Define recognizable gesture patterns"""
        return {
            'circle_select': CirclePattern(min_radius=50, max_radius=200),
            'line_attack': LinePattern(min_length=100, max_angle_deviation=15),
            'cross_cancel': CrossPattern(min_arm_length=50)
        }
```

## Integration with Game Systems

### Event System Integration
```python
class InteractionEventBridge:
    def __init__(self, event_manager):
        self.event_manager = event_manager
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Set up event handling for interaction events"""
        self.event_manager.subscribe('unit_selected', self.on_unit_selected)
        self.event_manager.subscribe('action_completed', self.on_action_completed)
        self.event_manager.subscribe('turn_ended', self.on_turn_ended)
    
    def on_unit_selected(self, event_data):
        """Handle unit selection events"""
        unit = event_data['unit']
        self.interaction_manager.set_selected_unit(unit)
        self.highlight_available_actions(unit)
    
    def emit_interaction_event(self, event_type, data):
        """Emit events from interaction system"""
        self.event_manager.emit(event_type, data)
```

### UI Panel Integration
```python
def integrate_with_ui_panels(self):
    """Connect interaction system with UI panels"""
    # Panel visibility affects interaction modes
    self.panel_manager.on_panel_opened = self.on_panel_opened
    self.panel_manager.on_panel_closed = self.on_panel_closed
    
    # Interaction events update panels
    self.on_unit_selected = lambda unit: self.panel_manager.update_character_panel(unit)
    self.on_inventory_changed = lambda inv: self.panel_manager.update_inventory_panel(inv)

def on_panel_opened(self, panel_name):
    """Handle panel opening affecting interaction mode"""
    if panel_name in ['inventory', 'character', 'abilities']:
        self.interaction_manager.set_interaction_mode(InteractionMode.MENU)
        self.pause_game_interactions()

def on_panel_closed(self, panel_name):
    """Handle panel closing restoring normal interaction"""
    if not self.panel_manager.has_open_panels():
        self.interaction_manager.set_interaction_mode(InteractionMode.NORMAL)
        self.resume_game_interactions()
```

## Best Practices

### User Experience
- **Immediate Feedback** - Provide instant visual response to all inputs
- **Clear Intent** - Make available actions and their effects obvious
- **Forgiveness** - Allow easy cancellation and undo of actions
- **Consistency** - Use consistent interaction patterns throughout

### Performance
- **Event Throttling** - Limit frequency of input processing
- **Efficient Highlighting** - Optimize visual feedback updates
- **Input Buffering** - Handle rapid input sequences gracefully
- **Memory Management** - Clean up interaction state properly

### Accessibility
- **Keyboard Navigation** - Support full keyboard control
- **Visual Indicators** - Clear visual feedback for all states
- **Audio Cues** - Sound feedback for important actions
- **Customizable Controls** - Allow input remapping

### Error Handling
- **Input Validation** - Check all inputs for validity
- **Graceful Degradation** - Handle missing UI elements
- **Recovery Mechanisms** - Reset interaction state when needed
- **User Communication** - Clear error messages and guidance