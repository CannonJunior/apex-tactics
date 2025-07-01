# Portable UI System

<system_context>
Multi-engine UI framework providing abstraction layer for cross-platform development supporting Ursina, Unity, Godot, and other engines.
</system_context>

<critical_notes>
- UI abstractions MUST remain engine-agnostic for portability
- All engine-specific implementations MUST inherit from abstract interfaces
- Event handling should use the portable UIEventBus system
- Colors and positions use normalized values (0.0-1.0) for consistency
- Dataclasses use default_factory for mutable defaults to avoid ValueError
</critical_notes>

<file_map>
Core abstractions: @src/ui/core/ui_abstractions.py
Ursina implementation: @src/ui/ursina/ursina_ui_manager.py
Start screen system: @src/ui/screens/start_screen.py
Demo application: @src/ui/screens/start_screen_demo.py
</file_map>

<paved_path>
1. Define abstract UI interfaces (IUIElement, IUIButton, IUIPanel, etc.)
2. Create engine-specific implementations (UrsinaUIButton, etc.)
3. Implement screen management system with state transitions
4. Build start screen with main menu functionality
5. Add settings management and configuration system
</paved_path>

<patterns>
```python
# Engine-agnostic UI creation
ui_manager = UrsinaUIManager()  # or UnityUIManager(), GodotUIManager()
button = ui_manager.create_button("Click Me", UIVector2(50, 50), UIVector2(20, 8))
button.add_event_handler("click", my_callback)

# Screen management
menu_manager = MainMenuManager(ui_manager)
menu_manager.show_start_screen()

# Portable color and positioning
button.background_color = UIColor.from_hex("#4CAF50")
button.position = UIVector2(50, 50)  # Center of screen
```
</patterns>

<architecture>
The system uses a three-layer architecture:
1. **Abstract Layer**: Engine-agnostic interfaces (IUIElement, IUIButton, etc.)
2. **Implementation Layer**: Engine-specific implementations (UrsinaUIButton, etc.)
3. **Application Layer**: Game screens and UI logic (StartScreen, SettingsScreen)

This allows the same UI code to work across different engines by swapping the implementation layer.
</architecture>

<phase45_implementation>
Phase 4.5 completed the following:

**Portable UI Architecture**:
- Abstract interfaces for all UI components (buttons, panels, text, screens)
- Engine-agnostic color, vector, and event systems
- Flexible theming and styling framework
- Global UI state management with screen stacks

**Ursina Implementation**:
- Complete Ursina-specific UI component implementations
- Proper event handling and visual feedback
- Color conversion and positioning translation
- Memory management and cleanup systems

**Start Screen System**:
- Professional main menu with New Game, Load Game, Settings, Exit
- Settings screen with configurable options (difficulty, graphics, audio)
- Screen transition management with proper state handling
- Game settings persistence framework

**Multi-Panel Framework**:
- Flexible panel layout system with anchoring and sizing
- Event-driven architecture for UI interactions
- Modular screen design for easy extension
- Component abstraction for engine portability
</phase45_implementation>

<portability_features>
- **Engine Independence**: Same UI code works with Ursina, Unity, Godot
- **Normalized Coordinates**: All positions/sizes use 0-100 scale
- **Color Abstraction**: Engine-agnostic color representation
- **Event System**: Unified event handling across engines
- **Component Interface**: Abstract base classes for all UI elements
- **Theme Support**: Configurable styling and appearance
</portability_features>

<workflow>
1. Create UI manager for target engine
2. Define screen layouts using abstract components  
3. Implement event handlers and business logic
4. Use screen manager for transitions and state
5. Apply themes and styling as needed
</workflow>

<demo_usage>
Run the Phase 4.5 UI demonstration with uv:

```bash
# From project root - simple runner
uv run run_ui_demo.py

# Direct demo execution
uv run src/ui/screens/start_screen_demo.py

# Install dependencies if needed
uv add ursina
```

The demo shows:
- Professional start screen with main menu
- Settings screen with configurable options
- Screen transitions and state management
- Portable UI components working with Ursina
</demo_usage>

<fatal_implications>
Breaking the abstraction layer by using engine-specific code in application layer will destroy portability.
</fatal_implications>