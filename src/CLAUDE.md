# Source Code Directory

<system_context>
Main source code directory containing all game engine implementation files organized by system type.
</system_context>

<critical_notes>
- All Python files must use absolute imports from src root
- Follow PEP 8 naming conventions strictly
- Each system should be self-contained with minimal cross-dependencies
</critical_notes>

<file_map>
Core systems: @src/core/
Game components: @src/components/
Game systems: @src/systems/
AI implementation: @src/ai/
User interface: @src/ui/
Game logic: @src/game/
</file_map>

<paved_path>
1. Implement core infrastructure first (ECS, events, math utilities)
2. Build components and systems on top of core
3. Add game-specific logic and AI
4. Implement UI last
</paved_path>

<patterns>
- All modules should have __init__.py files
- Use dependency injection for system connections
- Implement interfaces for Unity portability
- Follow component composition over inheritance
</patterns>

<workflow>
Development order: core → components → systems → ai → game → ui
</workflow>