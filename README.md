# Apex Tactics - 3D Tactical RPG Engine

A tactical RPG 3D engine implementation using Python and Ursina, designed for extreme complexity while maintaining Unity portability. The system features advanced stat mechanics, sophisticated equipment tiers, AI-driven combat through MCP tools, and real-time visual feedback systems.

## Architecture Overview

The engine implements a **hybrid client-server WebSocket architecture** with the following components:

- **Headless Game Engine** (`run_game_engine.py`): FastAPI server with WebSocket support
- **Ursina Frontend Client** (`apex-tactics-websocket-client.py`): 3D visualization and UI
- **Legacy Standalone Client** (`apex-tactics.py`): Original monolithic implementation
- **Component System**: Modular ECS with Transform, Stats, Equipment, Movement, Combat
- **MCP Integration**: FastMCP server for AI agent control and tactical decision-making

## Quick Start

### Option 1: WebSocket Client-Server (Recommended)

1. **Start the headless game engine:**
   ```bash
   uv run python run_game_engine.py
   ```
   This starts a FastAPI server with WebSocket support on `localhost:8002`

2. **Start the Ursina frontend client:**
   ```bash
   uv run python apex-tactics-websocket-client.py
   ```
   This connects to the headless engine and provides 3D visualization

### Option 2: Standalone Client (Legacy)

```bash
uv run python apex-tactics.py
```
Runs the original monolithic implementation with full UI and game logic.

## Controls

### UI Panels
- **T** - Toggle Talent Panel
- **I** - Toggle Inventory Panel  
- **P** - Toggle Party Panel
- **U** - Toggle Upgrade Panel
- **C** - Toggle Character Panel

### Camera Controls
- **WASD** - Move camera / Unit movement (when unit selected)
- **Arrow Keys** - Camera movement
- **Mouse** - Camera rotation and interaction
- **1-9** - Camera presets

### Game Controls
- **M** - Movement mode
- **A** - Attack mode
- **ESC** - Cancel current action
- **Click** - Select units/tiles
- **Enter** - Confirm movement path

## System Components

### Stat System
- **Nine-Attribute Foundation**: strength, fortitude, finesse, wisdom, wonder, worthy, faith, spirit, speed
- **Derived Stats**: Complex formulas calculating HP, MP, and attack/defense values
- **Three Resources**: MP (regenerating), Rage (building/decaying), Kwan (location-based)
- **Temporary Modifiers**: Advanced buff/debuff mechanics with stacking rules

### Equipment System
- **Five Tiers**: BASE (1.0x) → ENHANCED (1.4x) → ENCHANTED (2.0x) → SUPERPOWERED (3.0x) → METAPOWERED (4.5x)
- **Sentient Items**: Metapowered equipment with independent AI decision-making
- **Ability Scaling**: Additional ability slots per tier (1-4 slots)

### Combat System
- **Multi-Layered Defense**: Physical, Magical, and Spiritual defense types
- **Hybrid Damage Formula**: Prevents zero damage while maintaining tactical depth
- **Area Effects**: Complex area damage with friendly fire considerations
- **Armor Penetration**: Defense reduction mechanics

### AI System
- **Four Difficulty Levels**: Scripted → Strategic → Adaptive → Learning
- **Pattern Recognition**: Adaptive AI tracks and counters player strategies
- **Leader Mechanics**: Battle reset, enemy prediction, strategic coordination
- **MCP Tool Integration**: Comprehensive tactical analysis and action execution

## WebSocket API

The headless engine exposes the following WebSocket endpoints:

- `ws://localhost:8002/ws` - Main game WebSocket connection
- `/api/session` - Session management (create, start, join)
- `/api/health` - Health check endpoint

See `src/api/` for detailed API documentation.

## Development

### Requirements
- Python 3.12+
- Ursina engine
- FastAPI + WebSockets
- FastMCP (for AI integration)

### Project Structure
```
src/
├── api/           # WebSocket API endpoints
├── client/        # WebSocket client components  
├── core/          # ECS architecture (components, systems)
├── engine/        # Game engine core
├── game/          # Game controllers and logic
├── mcp/           # MCP server integration
├── ui/            # Ursina UI panels and components
└── ...
```

### Performance Targets
- Stat Calculations: <1ms for complex character sheets
- Pathfinding: <2ms per query on 10x10 grids with height
- Visual Updates: <5ms for full battlefield refresh  
- AI Decisions: <100ms per unit turn
- Memory Usage: <512MB total for full tactical battle

## TODO

### UI Improvements
1. Create a top Menu panel with "END TURN" and dropdown options
2. Update bottom panel with character turn order icons
3. Add targeted unit panel on the right
4. Enhance inventory panel with equipment hot-keys
5. Expand talent panel with spell hot-key assignment
6. Create spiritual panel for auras, stances, and transformations

### WebSocket Enhancements
1. Real-time multiplayer support
2. Spectator mode
3. Game state persistence
4. Reconnection handling

### AI Integration
1. Enhanced MCP tool suite
2. Difficulty scaling algorithms
3. Player behavior analysis
4. Dynamic encounter generation