# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a tactical RPG 3D engine implementation using Python and Ursina, designed for extreme complexity while maintaining Unity portability. The system features advanced stat mechanics, sophisticated equipment tiers, AI-driven combat through MCP tools, and real-time visual feedback systems.

## Architecture

The engine implements a **hybrid ECS architecture** optimized for Unity portability:

- **Component System**: Uses modular components (Transform, Stats, Equipment, Movement, Combat)
- **System Manager**: Event-driven messaging between independent game systems
- **MCP Integration**: FastMCP server for AI agent control and tactical decision-making
- **Portable Design**: Clear abstraction layers separating game logic from rendering

## Core Systems

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

## File System Structure

The project follows a comprehensive organization structure detailed in `File-System-Structure.md`:

- **Source Code** (`src/`): Modular ECS architecture with clear component/system separation
- **Assets** (`assets/`): Organized by system (characters, equipment, environments) with tier-based equipment structure
- **Data** (`data/`): JSON configuration files for all game content, supporting data-driven design
- **Character Organization**: Separate folders for heroes, enemies, NPCs with class-based subdivision
- **Equipment Organization**: Five-tier structure (BASE→ENHANCED→ENCHANTED→SUPERPOWERED→METAPOWERED)
- **Battleground Organization**: Organized by environment type (plains, forests, mountains, dungeons, cities)
- **Story Content**: Chapter-based organization with dialogue trees and cutscene data

## Asset Management System

The project implements a comprehensive asset management system detailed in `Asset-Management-Systems.md`:

- **Dependency Tracking**: Automatic propagation of updates when assets change
- **Version Control**: Semantic versioning with compatibility checking between asset versions
- **Streaming System**: Dynamic asset loading based on player position and performance metrics
- **LOD Management**: Automatic quality adjustment based on distance, hardware capabilities, and performance
- **Multi-Platform Support**: Asset variants optimized for Ursina, Unity, iOS, and console platforms
- **Localization**: Full internationalization support with 10+ languages and regional settings
- **Performance Monitoring**: Real-time tracking of asset loading times and memory usage
- **Unity Integration**: Seamless export system for Unity portability

## Runtime Organization

The project includes advanced runtime optimization detailed in `Runtime-Organization.md`:

- **Memory Management**: Four-tier memory pools (resident, streaming, temporary, procedural) with smart allocation
- **Resident Systems**: UI elements and core systems stay permanently loaded for instant access
- **Environmental Streaming**: Large environmental assets stream in/out based on player position and camera frustum
- **Dependency Resolution**: Comprehensive dependency graph system prevents crashes from missing dependencies
- **Procedural Generation**: Runtime asset variation and level generation with intelligent caching
- **Crash Prevention**: Fallback strategies, asset validation, and graceful degradation for missing dependencies
- **Performance Optimization**: Automatic memory pool optimization and real-time performance monitoring

## Development Commands

Since this is currently a documentation-only repository, no build/test commands are established yet. When implementation begins, expect:

- **Python Environment**: Requires Python with Ursina engine
- **MCP Server**: FastMCP for AI integration
- **Testing**: Comprehensive test suite for combat mechanics
- **Performance**: Target <1ms stat calculations, <2ms pathfinding

## Performance Targets

- Stat Calculations: <1ms for complex character sheets
- Pathfinding: <2ms per query on 10x10 grids with height
- Visual Updates: <5ms for full battlefield refresh  
- AI Decisions: <100ms per unit turn
- Memory Usage: <512MB total for full tactical battle

## Implementation Phases

1. **Foundation** (Weeks 1-3): Core ECS, MCP setup, grid system, stat framework
2. **Combat Systems** (Weeks 4-6): Defense layers, area effects, equipment tiers
3. **AI Integration** (Weeks 7-9): MCP tools, difficulty scaling, leader AI
4. **Visual Systems** (Weeks 10-11): Tile highlighting, inventory interface
5. **Polish** (Weeks 12-13): Testing, optimization, Unity portability validation

## Key Design Principles

- **Unity Portability**: All systems designed for easy Unity conversion
- **Performance First**: Caching, lazy evaluation, optimized pathfinding
- **Modular Architecture**: Independent systems communicating via events
- **MCP Integration**: AI agents control units through comprehensive tool suite
- **Complex Mechanics**: Deep stat interactions without overwhelming complexity