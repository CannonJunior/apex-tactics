# Comprehensive Dependency Analysis for Apex Tactics

## Executive Summary

**Total Project Files**: 240 Python files (excluding virtual environment)  
**Used Files**: 73 (30.4%)  
**Unused Files**: 167 (69.6%)  

The analysis shows that approximately 70% of the codebase consists of unused files that are candidates for removal. The project has four main entry points with overlapping dependency trees.

## Main Entry Points and Dependencies

### 1. apex-tactics.py (Main Standalone Client)
- **Total Dependencies**: 62 files
- **Direct Imports**: 7 files
  - `src/game/controllers/tactical_rpg_controller.py`
  - `src/ui/panels/control_panel.py`
  - `src/ui/panels/character_panel.py`
  - `src/ui/panels/inventory_panel.py`
  - `src/ui/panels/party_panel.py`
  - `src/ui/panels/talent_panel.py`
  - `src/ui/panels/upgrade_panel.py`

### 2. apex-tactics-websocket-client.py (WebSocket Client)
- **Total Dependencies**: 63 files
- **Direct Imports**: 8 files (includes WebSocket client)
  - Same as apex-tactics.py plus:
  - `src/client/websocket_game_client.py`

### 3. apex-tactics-enhanced.py (Enhanced Version)
- **Total Dependencies**: 67 files
- **Direct Imports**: 12 files (includes AI integration)
  - Same as apex-tactics.py plus:
  - `src/ai/ai_integration_manager.py`
  - `src/game/config/feature_flags.py`
  - `src/integration/controller_bridge.py`
  - `src/ui/queue_management.py`
  - `src/ui/ui_integration.py`

### 4. run_game_engine.py (Headless Engine)
- **Total Dependencies**: 3 files
- **Direct Imports**: 2 files
  - `src/engine/game_engine.py`
  - `src/engine/integrations/websocket_handler.py`

## Dependency Tree Structure

The main dependency chain flows through:
1. **TacticalRPG Controller** (core game logic) - imported by 56 files
2. **UI Config Manager** (configuration) - imported by 21 files
3. **Math/Vector utilities** - imported by 19 files
4. **ECS components** - imported by 15+ files

## Unused Files by Category

### High-Confidence Removal Candidates (Safe to Remove)

#### Tests (17 files)
- `docker/test-services.py`
- `src/ai/test_ai_behaviors.py`
- `src/ai/test_ollama_logging.py`
- `test_ap_validation.py`
- `test_hotkey_mcp.py`
- `test_reactpy.py`
- `tests/integration/*` (10 files)
- `tests/test_*` (3 files)

#### Demos (1 file)
- `src/demos/__init__.py`

#### Scripts (4 files)
- `scripts/launch_mcp_gateway.py`
- `scripts/migrate_ui_config.py`
- `scripts/run_game_with_mcp.py`
- `scripts/run_tests.py`

### Medium-Confidence Removal Candidates

#### Unused AI Components (24 files)
- `src/ai/adaptive_difficulty.py`
- `src/ai/agents/mcp_tactical_agent.py`
- `src/ai/decision_explainer.py`
- `src/ai/difficulty/difficulty_manager.py`
- `src/ai/leaders/leader_ai.py`
- `src/ai/learning_system.py`
- `src/ai/low_latency_pipeline.py`
- `src/ai/mcp/tactical_server.py`
- And 16 more AI-related files

#### Unused Engine Components (14 files)
- `src/engine/battlefield.py`
- `src/engine/components/*` (6 files)
- `src/engine/game_state.py`
- `src/engine/integrations/ai_integration.py`
- `src/engine/mcp/gateway_server.py`
- `src/engine/systems/combat_system.py`
- And 4 more engine files

#### Unused Core Components (17 files)
- `src/core/ecs.py` (old ECS implementation)
- `src/core/events.py` and related event files
- `src/core/game_loop.py`
- `src/core/assets/talent_manager.py`
- And 13 more core files

### Uncertain Files (May Be Dynamically Loaded)

These files might be loaded at runtime through configuration or factory patterns:

#### Asset Managers and Factories
- `src/ai/managers/ai_agent_manager.py` - might be loaded by AI integration
- `src/components/equipment/equipment_manager.py` - might be loaded by equipment system
- `src/core/assets/talent_manager.py` - might be loaded by talent system
- `src/engine/ui/game_ui_manager.py` - might be loaded by UI system
- `src/game/battle/battle_manager.py` - might be loaded by battle system
- `src/game/factories/unit_factory.py` - might be loaded by unit creation
- `src/game/managers/base_manager.py` - base class for managers

#### API and WebSocket Components
- `src/api/websocket_manager.py` - might be used by WebSocket system
- `src/api/game_engine.py` - alternative game engine implementation

## Dynamic Loading Analysis

### Confirmed Dynamic Loading Patterns

1. **Configuration Files**: The `ConfigManager` loads JSON files dynamically:
   - `assets/data/gameplay/*.json`
   - `assets/data/ui/*.json`
   - `assets/data/units/*.json`
   - `assets/data/characters/*.json`

2. **Asset Loading**: The `AssetLoader` loads assets from:
   - `assets/data/items/`
   - `assets/data/abilities/`
   - `assets/data/zones/`
   - `assets/textures/`
   - `assets/audio/`

3. **Formula Evaluation**: `ConfigManager.get_formula_result()` uses `eval()` which could potentially execute dynamic code

### No Python Module Loading Found
- No evidence of `importlib.import_module()` or `__import__()` for loading Python files
- No plugin system or dynamic class loading
- No evidence of factory patterns loading Python modules at runtime

## Recommendations

### Immediate Safe Removals (22 files)
Remove all test files, demos, and scripts:
```bash
rm -rf tests/
rm -rf docker/test-services.py
rm src/demos/__init__.py
rm scripts/launch_mcp_gateway.py
rm scripts/migrate_ui_config.py
rm scripts/run_game_with_mcp.py
rm scripts/run_tests.py
rm test_*.py
rm src/ai/test_*.py
```

### Medium-Risk Removals (Recommend Testing)

1. **Unused AI Components**: Remove if AI features are not being used
2. **Alternative Engine Implementation**: Remove `src/engine/` if using legacy controller
3. **Old ECS System**: Remove `src/core/ecs.py` if using newer ECS in `src/core/ecs/`
4. **Event System**: Remove `src/core/events.py` if using newer event system

### Keep for Safety (Uncertain Files)

Retain these files until you can confirm they're not dynamically loaded:
- All manager classes
- All factory classes  
- API components
- WebSocket components

### Verification Steps

Before removing uncertain files:
1. Search for string references to class names in configuration files
2. Check if any JSON files reference Python class paths
3. Test all game modes to ensure no runtime errors
4. Check if any MCP tools reference these classes

## File Categories Summary

| Category | Count | Action |
|----------|-------|---------|
| **USED** | 73 | Keep (30.4%) |
| **Safe to Remove** | 22 | Remove immediately |
| **Medium Risk** | 55 | Remove after testing |
| **Uncertain** | 90 | Investigate before removing |

This analysis provides a data-driven approach to cleaning up the codebase while minimizing the risk of breaking functionality.