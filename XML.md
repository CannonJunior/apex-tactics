# XML Tag Definitions

This document defines all XML tags used in CLAUDE.md files throughout the project for consistency and clarity.

## Standard Tags

### `<system_context>`
**Purpose**: Provides overview and purpose of the system or component
**Usage**: Brief description of what the system does and why it exists
**Example**: `<system_context>Core ECS architecture for managing game entities and components</system_context>`

### `<critical_notes>`
**Purpose**: Must-know information that could affect development or cause issues
**Usage**: Important warnings, limitations, or requirements
**Example**: `<critical_notes>Entity IDs must be unique across the entire game world</critical_notes>`

### `<paved_path>`
**Purpose**: The canonical way to accomplish common tasks
**Usage**: The recommended approach that follows established patterns
**Example**: `<paved_path>Use EntityManager.create_entity() rather than direct Entity construction</paved_path>`

### `<file_map>`
**Purpose**: Where to find things - maps concepts to actual file locations
**Usage**: Points to specific files without adding detail to context window
**Example**: `<file_map>Entity creation: @src/core/ecs/entity.py, Component types: @src/components/</file_map>`

### `<patterns>`
**Purpose**: Common code patterns used in this area
**Usage**: Reusable code structures and conventions
**Example**: `<patterns>All components inherit from BaseComponent and implement update()</patterns>`

### `<example>`
**Purpose**: Concrete examples of usage
**Usage**: Working code snippets or usage examples
**Example**: `<example>entity = EntityManager.create_entity(Transform, Stats)</example>`

### `<workflow>`
**Purpose**: Chain of thought steps for complex processes
**Usage**: Step-by-step procedures for multi-step tasks
**Example**: `<workflow>1. Create entity 2. Add components 3. Register with systems 4. Initialize</workflow>`

### `<common_tasks>`
**Purpose**: Step-by-step guides for frequent operations
**Usage**: Detailed instructions for routine tasks
**Example**: `<common_tasks>Adding new component: 1. Create class 2. Add to registry 3. Update systems</common_tasks>`

### `<hatch>`
**Purpose**: Alternative approaches when the paved path doesn't work
**Usage**: Workarounds, edge cases, or different solutions
**Example**: `<hatch>For performance-critical entities, bypass component system and use direct calls</hatch>`

### `<advanced_pattern>`
**Purpose**: Complex use cases and sophisticated patterns
**Usage**: Advanced techniques for experienced developers
**Example**: `<advanced_pattern>Component pooling for high-frequency entity creation/destruction</advanced_pattern>`

### `<fatal_implications>`
**Purpose**: What happens when things go wrong - serious consequences
**Usage**: Critical failure modes and their impacts
**Example**: `<fatal_implications>Circular component dependencies will cause infinite loops and crash</fatal_implications>`

## Project-Specific Tags

Additional tags may be added as the project develops. All new tags must be documented here.