# File System Structure

This document outlines the comprehensive file system organization for the Tactical RPG 3D Engine project, designed to support all game systems while maintaining scalability and Unity portability.

## Root Directory Structure

```
alt-apex-tactics/
├── src/                           # Source code
├── assets/                        # Game content assets
├── data/                          # Game data and configuration
├── tools/                         # Development and build tools
├── tests/                         # Test suites
├── docs/                          # Documentation
├── exports/                       # Unity export packages
└── temp/                          # Temporary files and cache
```

## Source Code Organization (`src/`)

```
src/
├── core/                          # Core engine systems
│   ├── ecs/                       # Entity Component System
│   │   ├── entity.py              # Base entity class
│   │   ├── component.py           # Component base classes
│   │   ├── system.py              # System base classes
│   │   └── world.py               # World/scene management
│   ├── events/                    # Event system
│   │   ├── event_bus.py           # Event dispatcher
│   │   ├── event_types.py         # Event type definitions
│   │   └── listeners.py           # Event listener utilities
│   ├── math/                      # Mathematical utilities
│   │   ├── vector.py              # Vector operations
│   │   ├── grid.py                # Grid mathematics
│   │   └── pathfinding.py         # Pathfinding algorithms
│   └── utils/                     # Core utilities
│       ├── serialization.py       # Save/load utilities
│       ├── logging.py             # Logging system
│       └── performance.py         # Performance monitoring
├── components/                    # Game components
│   ├── stats/                     # Stat system components
│   │   ├── attributes.py          # Nine-attribute system
│   │   ├── derived_stats.py       # Calculated stats
│   │   ├── resources.py           # MP, Rage, Kwan systems
│   │   └── modifiers.py           # Temporary modifiers
│   ├── combat/                    # Combat components
│   │   ├── combat_stats.py        # Combat-specific stats
│   │   ├── abilities.py           # Ability system
│   │   ├── damage.py              # Damage calculation
│   │   └── effects.py             # Status effects
│   ├── equipment/                 # Equipment components
│   │   ├── equipment_manager.py   # Equipment management
│   │   ├── item_stats.py          # Item stat bonuses
│   │   ├── sentience.py           # Sentient item AI
│   │   └── auras.py               # Equipment auras
│   ├── movement/                  # Movement components
│   │   ├── grid_movement.py       # Grid-based movement
│   │   ├── pathfinding.py         # Unit pathfinding
│   │   └── positioning.py         # Position management
│   └── visual/                    # Visual components
│       ├── renderer.py            # Rendering component
│       ├── animation.py           # Animation controller
│       └── effects.py             # Visual effects
├── systems/                       # Game systems
│   ├── stat_system.py             # Stat calculation system
│   ├── combat_system.py           # Combat resolution
│   ├── equipment_system.py        # Equipment management
│   ├── movement_system.py         # Movement processing
│   ├── ai_system.py               # AI decision making
│   ├── visual_system.py           # Visual feedback
│   └── input_system.py            # Input handling
├── ai/                            # AI implementation
│   ├── mcp/                       # MCP server integration
│   │   ├── tactical_server.py     # Main MCP server
│   │   ├── tools/                 # MCP tools
│   │   │   ├── analyze_battle.py  # Battle analysis
│   │   │   ├── execute_action.py  # Action execution
│   │   │   ├── evaluate_position.py # Position evaluation
│   │   │   └── predict_outcome.py # Outcome prediction
│   │   └── handlers/              # Tool handlers
│   ├── difficulty/                # AI difficulty levels
│   │   ├── scripted_ai.py         # Basic scripted AI
│   │   ├── strategic_ai.py        # Strategic AI
│   │   ├── adaptive_ai.py         # Adaptive AI
│   │   └── learning_ai.py         # Learning AI
│   ├── leaders/                   # Leader AI systems
│   │   ├── leader_ai.py           # Leader AI controller
│   │   ├── battle_reset.py        # Battle reset ability
│   │   └── coordination.py        # Unit coordination
│   └── behaviors/                 # AI behavior trees
│       ├── combat_behaviors.py    # Combat behavior trees
│       ├── movement_behaviors.py  # Movement behaviors
│       └── utility_behaviors.py   # Utility behaviors
├── ui/                            # User interface
│   ├── screens/                   # UI screens
│   │   ├── main_menu.py           # Main menu
│   │   ├── battle_ui.py           # Battle interface
│   │   ├── inventory.py           # Inventory interface
│   │   ├── character_sheet.py     # Character stats
│   │   └── settings.py            # Settings screen
│   ├── components/                # UI components
│   │   ├── grid_visualizer.py     # Grid visualization
│   │   ├── stat_display.py        # Stat display widgets
│   │   ├── equipment_slots.py     # Equipment slot UI
│   │   ├── tooltip_system.py      # Tooltip system
│   │   └── modal_dialogs.py       # Modal dialogs
│   └── themes/                    # UI themes and styling
│       ├── default_theme.py       # Default UI theme
│       └── combat_theme.py        # Combat UI theme
├── game/                          # Game-specific logic
│   ├── battle/                    # Battle management
│   │   ├── battle_manager.py      # Battle state management
│   │   ├── turn_manager.py        # Turn order system
│   │   ├── action_queue.py        # Action processing
│   │   └── victory_conditions.py  # Win/lose conditions
│   ├── story/                     # Story progression
│   │   ├── story_manager.py       # Story state management
│   │   ├── dialogue_system.py     # Dialogue processing
│   │   └── cutscene_system.py     # Cutscene management
│   └── progression/               # Character progression
│       ├── experience.py          # Experience system
│       ├── leveling.py            # Level advancement
│       └── unlocks.py             # Feature unlocks
└── main.py                        # Application entry point
```

## Asset Organization (`assets/`)

```
assets/
├── characters/                    # Character assets
│   ├── models/                    # 3D character models
│   │   ├── heroes/                # Player characters
│   │   │   ├── warrior/           # Warrior class models
│   │   │   │   ├── base_warrior.fbx
│   │   │   │   ├── warrior_armor_t1.fbx
│   │   │   │   └── warrior_armor_t5.fbx
│   │   │   ├── mage/              # Mage class models
│   │   │   └── rogue/             # Rogue class models
│   │   ├── enemies/               # Enemy character models
│   │   │   ├── basic/             # Basic enemy types
│   │   │   ├── elite/             # Elite enemies
│   │   │   └── bosses/            # Boss characters
│   │   └── npcs/                  # Non-player characters
│   ├── textures/                  # Character textures
│   │   ├── heroes/                # Hero textures
│   │   ├── enemies/               # Enemy textures
│   │   └── shared/                # Shared texture assets
│   ├── animations/                # Character animations
│   │   ├── combat/                # Combat animations
│   │   │   ├── attacks/           # Attack animations
│   │   │   ├── abilities/         # Ability animations
│   │   │   ├── hit_reactions/     # Damage reactions
│   │   │   └── death/             # Death animations
│   │   ├── movement/              # Movement animations
│   │   │   ├── walk/              # Walking animations
│   │   │   ├── run/               # Running animations
│   │   │   └── idle/              # Idle animations
│   │   └── interactions/          # Interaction animations
│   └── portraits/                 # Character portraits
│       ├── heroes/                # Hero portraits
│       ├── enemies/               # Enemy portraits
│       └── equipment/             # Equipment portraits
├── equipment/                     # Equipment assets
│   ├── models/                    # 3D equipment models
│   │   ├── weapons/               # Weapon models
│   │   │   ├── tier1/             # Base tier weapons
│   │   │   ├── tier2/             # Enhanced weapons
│   │   │   ├── tier3/             # Enchanted weapons
│   │   │   ├── tier4/             # Superpowered weapons
│   │   │   └── tier5/             # Metapowered weapons
│   │   ├── armor/                 # Armor models
│   │   │   ├── light/             # Light armor
│   │   │   ├── medium/            # Medium armor
│   │   │   └── heavy/             # Heavy armor
│   │   └── accessories/           # Accessory models
│   ├── textures/                  # Equipment textures
│   │   ├── weapons/               # Weapon textures
│   │   ├── armor/                 # Armor textures
│   │   └── accessories/           # Accessory textures
│   ├── effects/                   # Equipment visual effects
│   │   ├── enchantments/          # Enchantment effects
│   │   ├── auras/                 # Aura effects
│   │   └── sentience/             # Sentient item effects
│   └── icons/                     # Equipment icons
│       ├── weapons/               # Weapon icons
│       ├── armor/                 # Armor icons
│       └── accessories/           # Accessory icons
├── environments/                  # Environment assets
│   ├── battlegrounds/             # Battle maps
│   │   ├── models/                # Battleground 3D models
│   │   │   ├── plains/            # Plains battlegrounds
│   │   │   ├── forests/           # Forest battlegrounds
│   │   │   ├── mountains/         # Mountain battlegrounds
│   │   │   ├── dungeons/          # Dungeon battlegrounds
│   │   │   └── cities/            # Urban battlegrounds
│   │   ├── textures/              # Environment textures
│   │   │   ├── terrain/           # Terrain textures
│   │   │   ├── structures/        # Building textures
│   │   │   └── props/             # Prop textures
│   │   └── heightmaps/            # Height variation data
│   ├── zones/                     # Game world zones
│   │   ├── overworld/             # Overworld areas
│   │   ├── dungeons/              # Dungeon zones
│   │   └── cities/                # City zones
│   └── props/                     # Environmental props
│       ├── vegetation/            # Trees, grass, etc.
│       ├── structures/            # Buildings, walls
│       └── interactive/           # Interactive objects
├── ui/                            # UI assets
│   ├── textures/                  # UI textures
│   │   ├── buttons/               # Button textures
│   │   ├── panels/                # Panel backgrounds
│   │   ├── borders/               # Border graphics
│   │   └── icons/                 # UI icons
│   ├── fonts/                     # Font assets
│   │   ├── primary/               # Primary game font
│   │   ├── secondary/             # Secondary font
│   │   └── special/               # Special fonts
│   └── layouts/                   # UI layout templates
│       ├── battle_ui/             # Battle interface layouts
│       ├── inventory/             # Inventory layouts
│       └── menus/                 # Menu layouts
├── audio/                         # Audio assets
│   ├── music/                     # Background music
│   │   ├── battle/                # Battle music
│   │   ├── ambient/               # Ambient music
│   │   └── story/                 # Story music
│   ├── sfx/                       # Sound effects
│   │   ├── combat/                # Combat sounds
│   │   │   ├── attacks/           # Attack sounds
│   │   │   ├── abilities/         # Ability sounds
│   │   │   ├── impacts/           # Impact sounds
│   │   │   └── movement/          # Movement sounds
│   │   ├── ui/                    # UI sounds
│   │   │   ├── buttons/           # Button clicks
│   │   │   ├── notifications/     # Notification sounds
│   │   │   └── transitions/       # Screen transitions
│   │   └── environmental/         # Environmental sounds
│   └── voice/                     # Voice acting
│       ├── dialogue/              # Character dialogue
│       ├── battle_cries/          # Combat vocalizations
│       └── narration/             # Story narration
└── shaders/                       # Shader assets
    ├── character/                 # Character shaders
    ├── environment/               # Environment shaders
    ├── ui/                        # UI shaders
    └── effects/                   # Effect shaders
```

## Data Organization (`data/`)

```
data/
├── characters/                    # Character data
│   ├── classes/                   # Character classes
│   │   ├── warrior.json           # Warrior class definition
│   │   ├── mage.json              # Mage class definition
│   │   └── rogue.json             # Rogue class definition
│   ├── heroes/                    # Hero character data
│   │   ├── starting_roster.json   # Starting hero roster
│   │   └── unlockable_heroes.json # Unlockable heroes
│   ├── enemies/                   # Enemy data
│   │   ├── basic_enemies.json     # Basic enemy stats
│   │   ├── elite_enemies.json     # Elite enemy stats
│   │   └── bosses.json            # Boss enemy stats
│   └── npcs/                      # NPC data
│       ├── merchants.json         # Merchant NPCs
│       └── story_characters.json  # Story NPCs
├── equipment/                     # Equipment data
│   ├── weapons/                   # Weapon definitions
│   │   ├── tier1_weapons.json     # Base tier weapons
│   │   ├── tier2_weapons.json     # Enhanced weapons
│   │   ├── tier3_weapons.json     # Enchanted weapons
│   │   ├── tier4_weapons.json     # Superpowered weapons
│   │   └── tier5_weapons.json     # Metapowered weapons
│   ├── armor/                     # Armor definitions
│   │   ├── light_armor.json       # Light armor sets
│   │   ├── medium_armor.json      # Medium armor sets
│   │   └── heavy_armor.json       # Heavy armor sets
│   ├── accessories/               # Accessory definitions
│   │   ├── rings.json             # Ring accessories
│   │   ├── amulets.json           # Amulet accessories
│   │   └── trinkets.json          # Trinket accessories
│   ├── sets/                      # Equipment sets
│   │   ├── warrior_sets.json      # Warrior equipment sets
│   │   ├── mage_sets.json         # Mage equipment sets
│   │   └── rogue_sets.json        # Rogue equipment sets
│   └── sentience/                 # Sentient item data
│       ├── personalities.json     # AI personalities
│       └── behaviors.json         # Sentient behaviors
├── battlegrounds/                 # Battlefield data
│   ├── maps/                      # Battle map definitions
│   │   ├── plains_maps.json       # Plains battlegrounds
│   │   ├── forest_maps.json       # Forest battlegrounds
│   │   ├── mountain_maps.json     # Mountain battlegrounds
│   │   ├── dungeon_maps.json      # Dungeon battlegrounds
│   │   └── city_maps.json         # Urban battlegrounds
│   ├── objectives/                # Battle objectives
│   │   ├── defeat_all.json        # Defeat all enemies
│   │   ├── protect_ally.json      # Protect ally objectives
│   │   ├── capture_point.json     # Capture point objectives
│   │   └── escape.json            # Escape objectives
│   └── hazards/                   # Environmental hazards
│       ├── fire_hazards.json      # Fire environmental effects
│       ├── ice_hazards.json       # Ice environmental effects
│       └── poison_hazards.json    # Poison environmental effects
├── story/                         # Story content
│   ├── chapters/                  # Story chapters
│   │   ├── chapter_01.json        # Chapter 1 content
│   │   ├── chapter_02.json        # Chapter 2 content
│   │   └── chapter_03.json        # Chapter 3 content
│   ├── dialogue/                  # Dialogue trees
│   │   ├── main_story.json        # Main story dialogue
│   │   ├── side_quests.json       # Side quest dialogue
│   │   └── character_interactions.json # Character interactions
│   └── cutscenes/                 # Cutscene data
│       ├── opening.json           # Opening cutscene
│       ├── chapter_transitions.json # Chapter transitions
│       └── ending.json            # Ending cutscene
├── abilities/                     # Ability definitions
│   ├── combat_abilities.json      # Combat abilities
│   ├── support_abilities.json     # Support abilities
│   ├── movement_abilities.json    # Movement abilities
│   └── ultimate_abilities.json    # Ultimate abilities
├── ai/                            # AI configuration
│   ├── difficulty_scaling.json    # AI difficulty parameters
│   ├── behavior_trees.json        # AI behavior definitions
│   ├── tactical_patterns.json     # Tactical AI patterns
│   └── leader_abilities.json      # Leader AI abilities
├── balance/                       # Game balance data
│   ├── stat_curves.json           # Stat progression curves
│   ├── damage_formulas.json       # Damage calculation formulas
│   ├── equipment_scaling.json     # Equipment tier scaling
│   └── ability_costs.json         # Ability resource costs
├── localization/                  # Localization data
│   ├── en/                        # English localization
│   │   ├── ui_text.json           # UI text strings
│   │   ├── dialogue.json          # Dialogue text
│   │   ├── item_descriptions.json # Item descriptions
│   │   └── ability_descriptions.json # Ability descriptions
│   └── templates/                 # Localization templates
└── config/                        # Configuration files
    ├── engine_config.json         # Engine configuration
    ├── graphics_config.json       # Graphics settings
    ├── audio_config.json          # Audio settings
    └── input_config.json          # Input mappings
```

## Key Organizational Principles

### 1. Modular Asset Structure
- Each system (characters, equipment, environments) has dedicated asset folders
- Tier-based organization for equipment (tier1-tier5)
- Separate folders for different content types (models, textures, animations)

### 2. Data-Driven Design
- JSON configuration files for all game data
- Separate data definitions from code implementation
- Localization support built into structure

### 3. Unity Portability
- Asset naming conventions compatible with Unity
- Hierarchical organization that maps to Unity's Project window
- Shader and material organization for Unity conversion

### 4. Scalability
- Room for expansion in each category
- Consistent naming conventions across all systems
- Clear separation between core systems and game-specific content

### 5. Development Efficiency
- Tools folder for build scripts and utilities
- Temporary folder for cache and generated content
- Test organization matching source code structure

This structure supports the complex systems described in the Advanced Implementation Guide while maintaining organization for future expansion and Unity portability.