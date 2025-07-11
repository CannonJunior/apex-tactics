# UI Configuration Migration Report

Found 804 hardcoded UI values that should be migrated to master config.

## Summary by Category

- **Models**: 75 instances
- **Scales**: 140 instances
- **Positions**: 130 instances
- **Colors**: 450 instances
- **Textures**: 9 instances

## Detailed Findings

### src/ui/action_prediction.py

**Line 477 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 479 (scales)**
```python
# Current (hardcoded)
scale=(3, 2, 0.05),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 480 (positions)**
```python
# Current (hardcoded)
position=(0, -6, 0)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 487 (positions)**
```python
# Current (hardcoded)
position=(0, 0.8, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 488 (scales)**
```python
# Current (hardcoded)
scale=1.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 526 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 528 (scales)**
```python
# Current (hardcoded)
scale=(2.5, 0.25, 0.02),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 529 (positions)**
```python
# Current (hardcoded)
position=(0, y_pos, -0.02)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 536 (positions)**
```python
# Current (hardcoded)
position=(-1, 0, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 537 (scales)**
```python
# Current (hardcoded)
scale=1.0,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 550 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 552 (scales)**
```python
# Current (hardcoded)
scale=(0.2, 0.8, 0.05),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 553 (positions)**
```python
# Current (hardcoded)
position=(1, 0, -0.02)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

### src/ui/queue_management.py

**Line 163 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 165 (scales)**
```python
# Current (hardcoded)
scale=(12, 1.5, 0.1),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 166 (positions)**
```python
# Current (hardcoded)
position=(0, 8, 0)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 173 (positions)**
```python
# Current (hardcoded)
position=(-5.5, 0.6, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 174 (scales)**
```python
# Current (hardcoded)
scale=2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 195 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 197 (scales)**
```python
# Current (hardcoded)
scale=(slot_width, 0.8, 0.05),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 198 (positions)**
```python
# Current (hardcoded)
position=(start_x + i * (slot_width + 0.1), -0.2, -0.05)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 205 (positions)**
```python
# Current (hardcoded)
position=(0, -0.5, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 206 (scales)**
```python
# Current (hardcoded)
scale=1.5,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 269 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 271 (scales)**
```python
# Current (hardcoded)
scale=(0.7, 0.6, 0.1),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 272 (positions)**
```python
# Current (hardcoded)
position=(0, 0.1, -0.1)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 280 (positions)**
```python
# Current (hardcoded)
position=(0, 0.4, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 281 (scales)**
```python
# Current (hardcoded)
scale=1.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 289 (positions)**
```python
# Current (hardcoded)
position=(0, -0.4, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 290 (scales)**
```python
# Current (hardcoded)
scale=1.0,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 299 (positions)**
```python
# Current (hardcoded)
position=(0.25, 0.25, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 300 (scales)**
```python
# Current (hardcoded)
scale=0.8,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 364 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 366 (scales)**
```python
# Current (hardcoded)
scale=(4, 6, 0.1),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 367 (positions)**
```python
# Current (hardcoded)
position=(6, 2, 0)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 374 (positions)**
```python
# Current (hardcoded)
position=(0, 2.5, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 375 (scales)**
```python
# Current (hardcoded)
scale=1.5,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 383 (scales)**
```python
# Current (hardcoded)
scale=(1.5, 0.4),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 384 (positions)**
```python
# Current (hardcoded)
position=(0, -2.5, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 422 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 424 (scales)**
```python
# Current (hardcoded)
scale=(3.5, 0.6, 0.05),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 425 (positions)**
```python
# Current (hardcoded)
position=(0, y_pos, -0.05)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 434 (positions)**
```python
# Current (hardcoded)
position=(-1.2, 0.1, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 435 (scales)**
```python
# Current (hardcoded)
scale=1.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 443 (positions)**
```python
# Current (hardcoded)
position=(-1.2, -0.2, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 444 (scales)**
```python
# Current (hardcoded)
scale=0.9,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 458 (positions)**
```python
# Current (hardcoded)
position=(1.2, 0, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 459 (scales)**
```python
# Current (hardcoded)
scale=1.0,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 467 (scales)**
```python
# Current (hardcoded)
scale=(0.3, 0.3),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 468 (positions)**
```python
# Current (hardcoded)
position=(1.5, 0, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 558 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 560 (scales)**
```python
# Current (hardcoded)
scale=(5, 4, 0.1),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 561 (positions)**
```python
# Current (hardcoded)
position=(-6, 2, 0)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 568 (positions)**
```python
# Current (hardcoded)
position=(0, 1.7, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 569 (scales)**
```python
# Current (hardcoded)
scale=1.5,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 577 (positions)**
```python
# Current (hardcoded)
position=(-2, 1.2, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 578 (scales)**
```python
# Current (hardcoded)
scale=1.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 585 (positions)**
```python
# Current (hardcoded)
position=(-2, 0.8, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 586 (scales)**
```python
# Current (hardcoded)
scale=1.0,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 594 (positions)**
```python
# Current (hardcoded)
position=(-2, 0.2, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 595 (scales)**
```python
# Current (hardcoded)
scale=1.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

### src/ui/screens/practice_battle.py

**Line 181 (positions)**
```python
# Current (hardcoded)
camera.position = (x, y, z)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 181 (positions)**
```python
# Current (hardcoded)
camera.position = (x, y, z)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 188 (positions)**
```python
# Current (hardcoded)
camera.position = (self.camera_target.x, 12, self.camera_target.z)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 188 (positions)**
```python
# Current (hardcoded)
camera.position = (self.camera_target.x, 12, self.camera_target.z)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 262 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 263 (colors)**
```python
# Current (hardcoded)
color=color.gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 263 (colors)**
```python
# Current (hardcoded)
color=color.gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 264 (scales)**
```python
# Current (hardcoded)
scale=(0.9, 0.1, 0.9),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 265 (positions)**
```python
# Current (hardcoded)
position=(x, 0, y),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 270 (colors)**
```python
# Current (hardcoded)
self.default_color = color.gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 270 (colors)**
```python
# Current (hardcoded)
self.default_color = color.gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 273 (colors)**
```python
# Current (hardcoded)
def highlight(self, highlight_color=color.orange):

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 273 (colors)**
```python
# Current (hardcoded)
def highlight(self, highlight_color=color.orange):

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 284 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 286 (scales)**
```python
# Current (hardcoded)
scale=(0.8, 1.5, 0.8),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 287 (positions)**
```python
# Current (hardcoded)
position=(unit.x, 0.8, unit.y),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 294 (colors)**
```python
# Current (hardcoded)
UnitType.HEROMANCER: color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 295 (colors)**
```python
# Current (hardcoded)
UnitType.UBERMENSCH: color.orange,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 296 (colors)**
```python
# Current (hardcoded)
UnitType.SOUL_LINKED: color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 297 (colors)**
```python
# Current (hardcoded)
UnitType.REALM_WALKER: color.magenta,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 298 (colors)**
```python
# Current (hardcoded)
UnitType.WARGI: color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 299 (colors)**
```python
# Current (hardcoded)
UnitType.MAGI: color.blue

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 301 (colors)**
```python
# Current (hardcoded)
return unit_colors.get(unit.type, color.white)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 304 (positions)**
```python
# Current (hardcoded)
self.position = (self.unit.x, 0.8, self.unit.y)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 304 (positions)**
```python
# Current (hardcoded)
self.position = (self.unit.x, 0.8, self.unit.y)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 356 (models)**
```python
# Current (hardcoded)
model='plane',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 357 (textures)**
```python
# Current (hardcoded)
texture='white_cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_textures.component', 'white_cube')
```

**Line 358 (colors)**
```python
# Current (hardcoded)
color=color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 358 (colors)**
```python
# Current (hardcoded)
color=color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 359 (scales)**
```python
# Current (hardcoded)
scale=(20, 1, 20),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 360 (positions)**
```python
# Current (hardcoded)
position=(4, -0.1, 4)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 365 (colors)**
```python
# Current (hardcoded)
AmbientLight(color=color.rgba(100, 100, 100, 100))

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 365 (colors)**
```python
# Current (hardcoded)
AmbientLight(color=color.rgba(100, 100, 100, 100))

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 365 (colors)**
```python
# Current (hardcoded)
AmbientLight(color=color.rgba(100, 100, 100, 100))

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 410 (colors)**
```python
# Current (hardcoded)
Text('Practice Battle Tutorial', color=color.white, scale=1.2),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 410 (colors)**
```python
# Current (hardcoded)
Text('Practice Battle Tutorial', color=color.white, scale=1.2),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 410 (scales)**
```python
# Current (hardcoded)
Text('Practice Battle Tutorial', color=color.white, scale=1.2),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 412 (colors)**
```python
# Current (hardcoded)
Text('Player 1 Turn', color=color.blue),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 412 (colors)**
```python
# Current (hardcoded)
Text('Player 1 Turn', color=color.blue),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 415 (colors)**
```python
# Current (hardcoded)
Text('Controls:', color=color.yellow),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 415 (colors)**
```python
# Current (hardcoded)
Text('Controls:', color=color.yellow),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 427 (scales)**
```python
# Current (hardcoded)
self.info_panel.scale = 0.8

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 448 (colors)**
```python
# Current (hardcoded)
tile.highlight(color.yellow)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 463 (colors)**
```python
# Current (hardcoded)
tile.highlight(color.blue)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 500 (colors)**
```python
# Current (hardcoded)
self.grid_tiles[x][y].highlight(color.green)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 515 (colors)**
```python
# Current (hardcoded)
Text(f'Turn {self.turn_count} - Player {self.current_player}', color=color.blue, scale=1.2),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 515 (colors)**
```python
# Current (hardcoded)
Text(f'Turn {self.turn_count} - Player {self.current_player}', color=color.blue, scale=1.2),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 515 (scales)**
```python
# Current (hardcoded)
Text(f'Turn {self.turn_count} - Player {self.current_player}', color=color.blue, scale=1.2),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 517 (colors)**
```python
# Current (hardcoded)
Text(f'Selected: {unit.name}', color=color.white, scale=1.1),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 517 (colors)**
```python
# Current (hardcoded)
Text(f'Selected: {unit.name}', color=color.white, scale=1.1),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 517 (scales)**
```python
# Current (hardcoded)
Text(f'Selected: {unit.name}', color=color.white, scale=1.1),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 518 (colors)**
```python
# Current (hardcoded)
Text(f'Type: {unit.type.value.title()}', color=color.light_gray),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 518 (colors)**
```python
# Current (hardcoded)
Text(f'Type: {unit.type.value.title()}', color=color.light_gray),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 521 (colors)**
```python
# Current (hardcoded)
Text('Stats:', color=color.yellow),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 521 (colors)**
```python
# Current (hardcoded)
Text('Stats:', color=color.yellow),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 526 (colors)**
```python
# Current (hardcoded)
Text('Attributes:', color=color.orange),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 526 (colors)**
```python
# Current (hardcoded)
Text('Attributes:', color=color.orange),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 531 (colors)**
```python
# Current (hardcoded)
Text('Combat:', color=color.red),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 531 (colors)**
```python
# Current (hardcoded)
Text('Combat:', color=color.red),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/screens/start_screen_demo.py

**Line 50 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 50 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 51 (scales)**
```python
# Current (hardcoded)
scale=2

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 57 (colors)**
```python
# Current (hardcoded)
color=color.light_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 57 (colors)**
```python
# Current (hardcoded)
color=color.light_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 63 (colors)**
```python
# Current (hardcoded)
color=color.gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 63 (colors)**
```python
# Current (hardcoded)
color=color.gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 69 (colors)**
```python
# Current (hardcoded)
color=color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 69 (colors)**
```python
# Current (hardcoded)
color=color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 70 (scales)**
```python
# Current (hardcoded)
scale=(2, 1)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 76 (colors)**
```python
# Current (hardcoded)
color=color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 76 (colors)**
```python
# Current (hardcoded)
color=color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 77 (scales)**
```python
# Current (hardcoded)
scale=(2, 1)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 83 (colors)**
```python
# Current (hardcoded)
color=color.violet,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 83 (colors)**
```python
# Current (hardcoded)
color=color.violet,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 84 (scales)**
```python
# Current (hardcoded)
scale=(2, 1)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 90 (colors)**
```python
# Current (hardcoded)
color=color.orange,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 90 (colors)**
```python
# Current (hardcoded)
color=color.orange,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 91 (scales)**
```python
# Current (hardcoded)
scale=(2, 1)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 97 (colors)**
```python
# Current (hardcoded)
color=color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 97 (colors)**
```python
# Current (hardcoded)
color=color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 98 (scales)**
```python
# Current (hardcoded)
scale=(2, 1)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 105 (colors)**
```python
# Current (hardcoded)
color=color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 105 (colors)**
```python
# Current (hardcoded)
color=color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 106 (scales)**
```python
# Current (hardcoded)
scale=0.8

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 192 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 192 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 193 (scales)**
```python
# Current (hardcoded)
scale=1.5

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 200 (colors)**
```python
# Current (hardcoded)
color=color.azure,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 200 (colors)**
```python
# Current (hardcoded)
color=color.azure,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 201 (scales)**
```python
# Current (hardcoded)
scale=(1.5, 1)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 209 (colors)**
```python
# Current (hardcoded)
color=color.azure,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 209 (colors)**
```python
# Current (hardcoded)
color=color.azure,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 210 (scales)**
```python
# Current (hardcoded)
scale=(1.5, 1)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 220 (colors)**
```python
# Current (hardcoded)
color=color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 220 (colors)**
```python
# Current (hardcoded)
color=color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 221 (scales)**
```python
# Current (hardcoded)
scale=(1.5, 1)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 227 (colors)**
```python
# Current (hardcoded)
color=color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 227 (colors)**
```python
# Current (hardcoded)
color=color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 228 (scales)**
```python
# Current (hardcoded)
scale=(1.5, 1)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 306 (positions)**
```python
# Current (hardcoded)
camera.position = (0, 0, -5)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 306 (positions)**
```python
# Current (hardcoded)
camera.position = (0, 0, -5)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 333 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 334 (colors)**
```python
# Current (hardcoded)
color=color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 334 (colors)**
```python
# Current (hardcoded)
color=color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 335 (scales)**
```python
# Current (hardcoded)
scale=(20, 10, 1),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 336 (positions)**
```python
# Current (hardcoded)
position=(0, 0, 5)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 341 (colors)**
```python
# Current (hardcoded)
AmbientLight(color=color.rgba(100, 100, 100, 100))

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 341 (colors)**
```python
# Current (hardcoded)
AmbientLight(color=color.rgba(100, 100, 100, 100))

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 341 (colors)**
```python
# Current (hardcoded)
AmbientLight(color=color.rgba(100, 100, 100, 100))

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/core/ui_style_manager.py

**Line 151 (colors)**
```python
# Current (hardcoded)
return color.Color(r, g, b, a)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/camera/camera_controller.py

**Line 28 (positions)**
```python
# Current (hardcoded)
camera.position = (x, y, z)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 28 (positions)**
```python
# Current (hardcoded)
camera.position = (x, y, z)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 35 (positions)**
```python
# Current (hardcoded)
camera.position = (self.camera_target.x, 12, self.camera_target.z)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 35 (positions)**
```python
# Current (hardcoded)
camera.position = (self.camera_target.x, 12, self.camera_target.z)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

### src/ui/visual/grid_utilities.py

**Line 35 (colors)**
```python
# Current (hardcoded)
line_color = color.Color(0.4, 0.4, 0.4, 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 35 (colors)**
```python
# Current (hardcoded)
line_color = color.Color(0.4, 0.4, 0.4, 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 42 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 44 (scales)**
```python
# Current (hardcoded)
scale=(0.02, 0.01, grid_size),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 45 (positions)**
```python
# Current (hardcoded)
position=(x, 0, grid_size / 2)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 52 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 54 (scales)**
```python
# Current (hardcoded)
scale=(grid_size, 0.01, 0.02),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 55 (positions)**
```python
# Current (hardcoded)
position=(grid_size / 2, 0, z)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 80 (colors)**
```python
# Current (hardcoded)
ground_color = color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 80 (colors)**
```python
# Current (hardcoded)
ground_color = color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 83 (models)**
```python
# Current (hardcoded)
model='plane',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 84 (textures)**
```python
# Current (hardcoded)
texture='white_cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_textures.component', 'white_cube')
```

**Line 86 (scales)**
```python
# Current (hardcoded)
scale=(size[0], 1, size[1]),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 35 (colors)**
```python
# Current (hardcoded)
line_color = color.Color(0.4, 0.4, 0.4, 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 35 (colors)**
```python
# Current (hardcoded)
line_color = color.Color(0.4, 0.4, 0.4, 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 42 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 44 (scales)**
```python
# Current (hardcoded)
scale=(0.02, 0.01, grid_size),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 45 (positions)**
```python
# Current (hardcoded)
position=(x, 0, grid_size / 2)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 52 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 54 (scales)**
```python
# Current (hardcoded)
scale=(grid_size, 0.01, 0.02),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 55 (positions)**
```python
# Current (hardcoded)
position=(grid_size / 2, 0, z)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 80 (colors)**
```python
# Current (hardcoded)
ground_color = color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 80 (colors)**
```python
# Current (hardcoded)
ground_color = color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 83 (models)**
```python
# Current (hardcoded)
model='plane',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 84 (textures)**
```python
# Current (hardcoded)
texture='white_cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_textures.component', 'white_cube')
```

**Line 86 (scales)**
```python
# Current (hardcoded)
scale=(size[0], 1, size[1]),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

### src/ui/visual/combat_animator.py

**Line 237 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 238 (scales)**
```python
# Current (hardcoded)
scale=0.1,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 240 (colors)**
```python
# Current (hardcoded)
color=color.yellow

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 240 (colors)**
```python
# Current (hardcoded)
color=color.yellow

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 272 (colors)**
```python
# Current (hardcoded)
self._create_spell_effect(caster.position, color.blue, duration * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 301 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.red

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 301 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.red

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 333 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.green

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 333 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.green

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 360 (colors)**
```python
# Current (hardcoded)
self._create_spell_effect(visual_entity.position, color.purple, animation_event.duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 371 (colors)**
```python
# Current (hardcoded)
Func(visual_entity.animate_color, color.Color(0.5, 0.5, 0.5, 0.3), animation_event.duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 386 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.gold

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 386 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.gold

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 397 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 398 (scales)**
```python
# Current (hardcoded)
scale=0.3,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 400 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.8, 0.7, 0.6, 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 400 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.8, 0.7, 0.6, 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 407 (colors)**
```python
# Current (hardcoded)
dust_effect.animate_color(color.Color(0.8, 0.7, 0.6, 0), duration=1.0)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 420 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 421 (scales)**
```python
# Current (hardcoded)
scale=0.5,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 423 (colors)**
```python
# Current (hardcoded)
color=color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 423 (colors)**
```python
# Current (hardcoded)
color=color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 430 (colors)**
```python
# Current (hardcoded)
impact.animate_color(color.Color(1, 1, 1, 0), duration=0.2)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 440 (colors)**
```python
# Current (hardcoded)
def _create_spell_effect(self, position: Vec3, effect_color: color.Color, duration: float):

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 443 (models)**
```python
# Current (hardcoded)
model='sphere',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 444 (scales)**
```python
# Current (hardcoded)
scale=0.3,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 453 (colors)**
```python
# Current (hardcoded)
spell_effect.animate_color(color.Color(effect_color.r, effect_color.g, effect_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 453 (colors)**
```python
# Current (hardcoded)
spell_effect.animate_color(color.Color(effect_color.r, effect_color.g, effect_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 453 (colors)**
```python
# Current (hardcoded)
spell_effect.animate_color(color.Color(effect_color.r, effect_color.g, effect_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 453 (colors)**
```python
# Current (hardcoded)
spell_effect.animate_color(color.Color(effect_color.r, effect_color.g, effect_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 467 (models)**
```python
# Current (hardcoded)
model='sphere',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 468 (scales)**
```python
# Current (hardcoded)
scale=0.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 470 (colors)**
```python
# Current (hardcoded)
color=color.green

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 470 (colors)**
```python
# Current (hardcoded)
color=color.green

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 477 (colors)**
```python
# Current (hardcoded)
heal_effect.animate_color(color.Color(0, 1, 0, 0), duration=duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 491 (colors)**
```python
# Current (hardcoded)
damage_color = color.red if damage_type == 'physical' else color.blue

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 491 (colors)**
```python
# Current (hardcoded)
damage_color = color.red if damage_type == 'physical' else color.blue

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 491 (colors)**
```python
# Current (hardcoded)
damage_color = color.red if damage_type == 'physical' else color.blue

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 494 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 495 (scales)**
```python
# Current (hardcoded)
scale=0.1,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 504 (colors)**
```python
# Current (hardcoded)
damage_indicator.animate_color(color.Color(damage_color.r, damage_color.g, damage_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 504 (colors)**
```python
# Current (hardcoded)
damage_indicator.animate_color(color.Color(damage_color.r, damage_color.g, damage_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 504 (colors)**
```python
# Current (hardcoded)
damage_indicator.animate_color(color.Color(damage_color.r, damage_color.g, damage_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 504 (colors)**
```python
# Current (hardcoded)
damage_indicator.animate_color(color.Color(damage_color.r, damage_color.g, damage_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 518 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 519 (scales)**
```python
# Current (hardcoded)
scale=0.1,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 521 (colors)**
```python
# Current (hardcoded)
color=color.lime

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 521 (colors)**
```python
# Current (hardcoded)
color=color.lime

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 528 (colors)**
```python
# Current (hardcoded)
heal_indicator.animate_color(color.Color(0, 1, 0.5, 0), duration=1.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 541 (models)**
```python
# Current (hardcoded)
model='sphere',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 542 (scales)**
```python
# Current (hardcoded)
scale=0.5,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 544 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.2, 0.2, 0.2, 0.8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 544 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.2, 0.2, 0.2, 0.8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 551 (colors)**
```python
# Current (hardcoded)
death_effect.animate_color(color.Color(0.2, 0.2, 0.2, 0), duration=2.0)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 564 (models)**
```python
# Current (hardcoded)
model='sphere',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 565 (scales)**
```python
# Current (hardcoded)
scale=0.1,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 567 (colors)**
```python
# Current (hardcoded)
color=color.gold

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 567 (colors)**
```python
# Current (hardcoded)
color=color.gold

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 574 (colors)**
```python
# Current (hardcoded)
level_effect.animate_color(color.Color(1, 0.8, 0, 0), duration=duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 587 (models)**
```python
# Current (hardcoded)
model='sphere',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 588 (scales)**
```python
# Current (hardcoded)
scale=0.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 590 (colors)**
```python
# Current (hardcoded)
color=color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 590 (colors)**
```python
# Current (hardcoded)
color=color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 597 (colors)**
```python
# Current (hardcoded)
explosion.animate_color(color.Color(1, 0.5, 0, 0), duration=duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 614 (colors)**
```python
# Current (hardcoded)
self._create_spell_effect(effect_pos, color.purple, duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 237 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 238 (scales)**
```python
# Current (hardcoded)
scale=0.1,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 240 (colors)**
```python
# Current (hardcoded)
color=color.yellow

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 240 (colors)**
```python
# Current (hardcoded)
color=color.yellow

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 272 (colors)**
```python
# Current (hardcoded)
self._create_spell_effect(caster.position, color.blue, duration * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 301 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.red

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 301 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.red

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 333 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.green

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 333 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.green

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 360 (colors)**
```python
# Current (hardcoded)
self._create_spell_effect(visual_entity.position, color.purple, animation_event.duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 371 (colors)**
```python
# Current (hardcoded)
Func(visual_entity.animate_color, color.Color(0.5, 0.5, 0.5, 0.3), animation_event.duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 386 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.gold

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 386 (colors)**
```python
# Current (hardcoded)
visual_entity.color = color.gold

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 397 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 398 (scales)**
```python
# Current (hardcoded)
scale=0.3,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 400 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.8, 0.7, 0.6, 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 400 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.8, 0.7, 0.6, 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 407 (colors)**
```python
# Current (hardcoded)
dust_effect.animate_color(color.Color(0.8, 0.7, 0.6, 0), duration=1.0)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 420 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 421 (scales)**
```python
# Current (hardcoded)
scale=0.5,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 423 (colors)**
```python
# Current (hardcoded)
color=color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 423 (colors)**
```python
# Current (hardcoded)
color=color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 430 (colors)**
```python
# Current (hardcoded)
impact.animate_color(color.Color(1, 1, 1, 0), duration=0.2)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 440 (colors)**
```python
# Current (hardcoded)
def _create_spell_effect(self, position: Vec3, effect_color: color.Color, duration: float):

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 443 (models)**
```python
# Current (hardcoded)
model='sphere',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 444 (scales)**
```python
# Current (hardcoded)
scale=0.3,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 453 (colors)**
```python
# Current (hardcoded)
spell_effect.animate_color(color.Color(effect_color.r, effect_color.g, effect_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 453 (colors)**
```python
# Current (hardcoded)
spell_effect.animate_color(color.Color(effect_color.r, effect_color.g, effect_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 453 (colors)**
```python
# Current (hardcoded)
spell_effect.animate_color(color.Color(effect_color.r, effect_color.g, effect_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 453 (colors)**
```python
# Current (hardcoded)
spell_effect.animate_color(color.Color(effect_color.r, effect_color.g, effect_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 467 (models)**
```python
# Current (hardcoded)
model='sphere',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 468 (scales)**
```python
# Current (hardcoded)
scale=0.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 470 (colors)**
```python
# Current (hardcoded)
color=color.green

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 470 (colors)**
```python
# Current (hardcoded)
color=color.green

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 477 (colors)**
```python
# Current (hardcoded)
heal_effect.animate_color(color.Color(0, 1, 0, 0), duration=duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 491 (colors)**
```python
# Current (hardcoded)
damage_color = color.red if damage_type == 'physical' else color.blue

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 491 (colors)**
```python
# Current (hardcoded)
damage_color = color.red if damage_type == 'physical' else color.blue

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 491 (colors)**
```python
# Current (hardcoded)
damage_color = color.red if damage_type == 'physical' else color.blue

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 494 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 495 (scales)**
```python
# Current (hardcoded)
scale=0.1,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 504 (colors)**
```python
# Current (hardcoded)
damage_indicator.animate_color(color.Color(damage_color.r, damage_color.g, damage_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 504 (colors)**
```python
# Current (hardcoded)
damage_indicator.animate_color(color.Color(damage_color.r, damage_color.g, damage_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 504 (colors)**
```python
# Current (hardcoded)
damage_indicator.animate_color(color.Color(damage_color.r, damage_color.g, damage_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 504 (colors)**
```python
# Current (hardcoded)
damage_indicator.animate_color(color.Color(damage_color.r, damage_color.g, damage_color.b, 0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 518 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 519 (scales)**
```python
# Current (hardcoded)
scale=0.1,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 521 (colors)**
```python
# Current (hardcoded)
color=color.lime

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 521 (colors)**
```python
# Current (hardcoded)
color=color.lime

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 528 (colors)**
```python
# Current (hardcoded)
heal_indicator.animate_color(color.Color(0, 1, 0.5, 0), duration=1.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 541 (models)**
```python
# Current (hardcoded)
model='sphere',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 542 (scales)**
```python
# Current (hardcoded)
scale=0.5,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 544 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.2, 0.2, 0.2, 0.8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 544 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.2, 0.2, 0.2, 0.8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 551 (colors)**
```python
# Current (hardcoded)
death_effect.animate_color(color.Color(0.2, 0.2, 0.2, 0), duration=2.0)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 564 (models)**
```python
# Current (hardcoded)
model='sphere',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 565 (scales)**
```python
# Current (hardcoded)
scale=0.1,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 567 (colors)**
```python
# Current (hardcoded)
color=color.gold

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 567 (colors)**
```python
# Current (hardcoded)
color=color.gold

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 574 (colors)**
```python
# Current (hardcoded)
level_effect.animate_color(color.Color(1, 0.8, 0, 0), duration=duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 587 (models)**
```python
# Current (hardcoded)
model='sphere',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 588 (scales)**
```python
# Current (hardcoded)
scale=0.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 590 (colors)**
```python
# Current (hardcoded)
color=color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 590 (colors)**
```python
# Current (hardcoded)
color=color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 597 (colors)**
```python
# Current (hardcoded)
explosion.animate_color(color.Color(1, 0.5, 0, 0), duration=duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 614 (colors)**
```python
# Current (hardcoded)
self._create_spell_effect(effect_pos, color.purple, duration)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/visual/tile_highlighter.py

**Line 247 (colors)**
```python
# Current (hardcoded)
new_color = color.Color(

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 247 (colors)**
```python
# Current (hardcoded)
new_color = color.Color(

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 248 (colors)**
```python
# Current (hardcoded)
current_color.r,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 249 (colors)**
```python
# Current (hardcoded)
current_color.g,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 250 (colors)**
```python
# Current (hardcoded)
current_color.b,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 255 (colors)**
```python
# Current (hardcoded)
def _convert_color(self, rgba_tuple: Tuple[float, float, float, float]) -> color.Color:

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 258 (colors)**
```python
# Current (hardcoded)
return color.Color(r, g, b, a)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 293 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 294 (scales)**
```python
# Current (hardcoded)
scale=0.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 296 (colors)**
```python
# Current (hardcoded)
color=color.yellow,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 296 (colors)**
```python
# Current (hardcoded)
color=color.yellow,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 331 (colors)**
```python
# Current (hardcoded)
effect.color = color.Color(

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 331 (colors)**
```python
# Current (hardcoded)
effect.color = color.Color(

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 332 (colors)**
```python
# Current (hardcoded)
effect.color.r,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 333 (colors)**
```python
# Current (hardcoded)
effect.color.g,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 334 (colors)**
```python
# Current (hardcoded)
effect.color.b,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 247 (colors)**
```python
# Current (hardcoded)
new_color = color.Color(

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 247 (colors)**
```python
# Current (hardcoded)
new_color = color.Color(

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 248 (colors)**
```python
# Current (hardcoded)
current_color.r,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 249 (colors)**
```python
# Current (hardcoded)
current_color.g,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 250 (colors)**
```python
# Current (hardcoded)
current_color.b,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 255 (colors)**
```python
# Current (hardcoded)
def _convert_color(self, rgba_tuple: Tuple[float, float, float, float]) -> color.Color:

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 258 (colors)**
```python
# Current (hardcoded)
return color.Color(r, g, b, a)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 293 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 294 (scales)**
```python
# Current (hardcoded)
scale=0.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 296 (colors)**
```python
# Current (hardcoded)
color=color.yellow,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 296 (colors)**
```python
# Current (hardcoded)
color=color.yellow,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 331 (colors)**
```python
# Current (hardcoded)
effect.color = color.Color(

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 331 (colors)**
```python
# Current (hardcoded)
effect.color = color.Color(

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 332 (colors)**
```python
# Current (hardcoded)
effect.color.r,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 333 (colors)**
```python
# Current (hardcoded)
effect.color.g,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 334 (colors)**
```python
# Current (hardcoded)
effect.color.b,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/visual/unit_renderer.py

**Line 47 (positions)**
```python
# Current (hardcoded)
position=(unit.x + 0.5, 1.0, unit.y + 0.5)  # Center units on grid tiles

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 68 (colors)**
```python
# Current (hardcoded)
self.color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 68 (colors)**
```python
# Current (hardcoded)
self.color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 81 (positions)**
```python
# Current (hardcoded)
self.position = (x + 0.5, 1.0, y + 0.5)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 81 (positions)**
```python
# Current (hardcoded)
self.position = (x + 0.5, 1.0, y + 0.5)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 97 (colors)**
```python
# Current (hardcoded)
self.color = color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 97 (colors)**
```python
# Current (hardcoded)
self.color = color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 100 (colors)**
```python
# Current (hardcoded)
self.color = color.dark_red

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 100 (colors)**
```python
# Current (hardcoded)
self.color = color.dark_red

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 47 (positions)**
```python
# Current (hardcoded)
position=(unit.x + 0.5, 1.0, unit.y + 0.5)  # Center units on grid tiles

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 68 (colors)**
```python
# Current (hardcoded)
self.color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 68 (colors)**
```python
# Current (hardcoded)
self.color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 81 (positions)**
```python
# Current (hardcoded)
self.position = (x + 0.5, 1.0, y + 0.5)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 81 (positions)**
```python
# Current (hardcoded)
self.position = (x + 0.5, 1.0, y + 0.5)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 97 (colors)**
```python
# Current (hardcoded)
self.color = color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 97 (colors)**
```python
# Current (hardcoded)
self.color = color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 100 (colors)**
```python
# Current (hardcoded)
self.color = color.dark_red

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 100 (colors)**
```python
# Current (hardcoded)
self.color = color.dark_red

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/panels/control_panel.py

**Line 77 (colors)**
```python
# Current (hardcoded)
color=color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 77 (colors)**
```python
# Current (hardcoded)
color=color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 185 (positions)**
```python
# Current (hardcoded)
position=(icon_x, icon_y, 0)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 201 (positions)**
```python
# Current (hardcoded)
position=(icon_x, icon_y + name_text_offset, 0),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 225 (colors)**
```python
# Current (hardcoded)
return color.yellow

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 233 (colors)**
```python
# Current (hardcoded)
return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 233 (colors)**
```python
# Current (hardcoded)
return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 233 (colors)**
```python
# Current (hardcoded)
return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 233 (colors)**
```python
# Current (hardcoded)
return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 233 (colors)**
```python
# Current (hardcoded)
return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 300 (colors)**
```python
# Current (hardcoded)
icon.color = color.yellow  # Current turn

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 300 (colors)**
```python
# Current (hardcoded)
icon.color = color.yellow  # Current turn

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 302 (colors)**
```python
# Current (hardcoded)
icon.color = color.white   # Selected

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 302 (colors)**
```python
# Current (hardcoded)
icon.color = color.white   # Selected

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 77 (colors)**
```python
# Current (hardcoded)
color=color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 77 (colors)**
```python
# Current (hardcoded)
color=color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 185 (positions)**
```python
# Current (hardcoded)
position=(icon_x, icon_y, 0)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 201 (positions)**
```python
# Current (hardcoded)
position=(icon_x, icon_y + name_text_offset, 0),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 225 (colors)**
```python
# Current (hardcoded)
return color.yellow

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 233 (colors)**
```python
# Current (hardcoded)
return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 233 (colors)**
```python
# Current (hardcoded)
return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 233 (colors)**
```python
# Current (hardcoded)
return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 233 (colors)**
```python
# Current (hardcoded)
return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 233 (colors)**
```python
# Current (hardcoded)
return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 300 (colors)**
```python
# Current (hardcoded)
icon.color = color.yellow  # Current turn

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 300 (colors)**
```python
# Current (hardcoded)
icon.color = color.yellow  # Current turn

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 302 (colors)**
```python
# Current (hardcoded)
icon.color = color.white   # Selected

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 302 (colors)**
```python
# Current (hardcoded)
icon.color = color.white   # Selected

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/panels/inventory_panel.py

**Line 52 (models)**
```python
# Current (hardcoded)
model='quad',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 73 (colors)**
```python
# Current (hardcoded)
self.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 73 (colors)**
```python
# Current (hardcoded)
self.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 106 (colors)**
```python
# Current (hardcoded)
return color.white  # Fallback color

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 125 (models)**
```python
# Current (hardcoded)
model='quad',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 127 (scales)**
```python
# Current (hardcoded)
scale=(1 + border_width * 2, 1 + border_width * 2),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 251 (textures)**
```python
# Current (hardcoded)
texture='white_cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_textures.component', 'white_cube')
```

**Line 252 (scales)**
```python
# Current (hardcoded)
texture_scale=(width, height),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 253 (scales)**
```python
# Current (hardcoded)
scale=(width*.08, height*.08),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 255 (positions)**
```python
# Current (hardcoded)
position=(-.2, .2),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 256 (colors)**
```python
# Current (hardcoded)
color=color.hsv(0, 0, .1, .9),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 256 (colors)**
```python
# Current (hardcoded)
color=color.hsv(0, 0, .1, .9),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 400 (scales)**
```python
# Current (hardcoded)
self.info_panel.scale = (0.3, 0.4)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 401 (positions)**
```python
# Current (hardcoded)
self.info_panel.position = (0.3, 0.2)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 401 (positions)**
```python
# Current (hardcoded)
self.info_panel.position = (0.3, 0.2)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 411 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 411 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 411 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 412 (scales)**
```python
# Current (hardcoded)
scale=(0.08, 0.03),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 413 (positions)**
```python
# Current (hardcoded)
position=(-0.4 + i * 0.09, 0.45),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 426 (colors)**
```python
# Current (hardcoded)
color=color.lime.tint(-.25),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 426 (colors)**
```python
# Current (hardcoded)
color=color.lime.tint(-.25),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 427 (scales)**
```python
# Current (hardcoded)
scale=(0.08, 0.04),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 428 (positions)**
```python
# Current (hardcoded)
position=(0.3, 0.0),  # Below the info panel

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 438 (colors)**
```python
# Current (hardcoded)
color=color.orange.tint(-.25),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 438 (colors)**
```python
# Current (hardcoded)
color=color.orange.tint(-.25),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 439 (scales)**
```python
# Current (hardcoded)
scale=(0.08, 0.04),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 440 (positions)**
```python
# Current (hardcoded)
position=(0.4, 0.0),  # Next to the Add Item button

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 530 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tabs[i] == tab_name else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 530 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tabs[i] == tab_name else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 530 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tabs[i] == tab_name else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 560 (scales)**
```python
# Current (hardcoded)
self.info_panel.scale = (0.3, 0.4)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 561 (positions)**
```python
# Current (hardcoded)
self.info_panel.position = (0.3, 0.2)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 561 (positions)**
```python
# Current (hardcoded)
self.info_panel.position = (0.3, 0.2)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 52 (models)**
```python
# Current (hardcoded)
model='quad',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 73 (colors)**
```python
# Current (hardcoded)
self.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 73 (colors)**
```python
# Current (hardcoded)
self.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 106 (colors)**
```python
# Current (hardcoded)
return color.white  # Fallback color

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 125 (models)**
```python
# Current (hardcoded)
model='quad',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 127 (scales)**
```python
# Current (hardcoded)
scale=(1 + border_width * 2, 1 + border_width * 2),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 251 (textures)**
```python
# Current (hardcoded)
texture='white_cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_textures.component', 'white_cube')
```

**Line 252 (scales)**
```python
# Current (hardcoded)
texture_scale=(width, height),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 253 (scales)**
```python
# Current (hardcoded)
scale=(width*.08, height*.08),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 255 (positions)**
```python
# Current (hardcoded)
position=(-.2, .2),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 256 (colors)**
```python
# Current (hardcoded)
color=color.hsv(0, 0, .1, .9),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 256 (colors)**
```python
# Current (hardcoded)
color=color.hsv(0, 0, .1, .9),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 400 (scales)**
```python
# Current (hardcoded)
self.info_panel.scale = (0.3, 0.4)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 401 (positions)**
```python
# Current (hardcoded)
self.info_panel.position = (0.3, 0.2)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 401 (positions)**
```python
# Current (hardcoded)
self.info_panel.position = (0.3, 0.2)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 411 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 411 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 411 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 412 (scales)**
```python
# Current (hardcoded)
scale=(0.08, 0.03),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 413 (positions)**
```python
# Current (hardcoded)
position=(-0.4 + i * 0.09, 0.45),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 426 (colors)**
```python
# Current (hardcoded)
color=color.lime.tint(-.25),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 426 (colors)**
```python
# Current (hardcoded)
color=color.lime.tint(-.25),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 427 (scales)**
```python
# Current (hardcoded)
scale=(0.08, 0.04),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 428 (positions)**
```python
# Current (hardcoded)
position=(0.3, 0.0),  # Below the info panel

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 438 (colors)**
```python
# Current (hardcoded)
color=color.orange.tint(-.25),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 438 (colors)**
```python
# Current (hardcoded)
color=color.orange.tint(-.25),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 439 (scales)**
```python
# Current (hardcoded)
scale=(0.08, 0.04),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 440 (positions)**
```python
# Current (hardcoded)
position=(0.4, 0.0),  # Next to the Add Item button

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 530 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tabs[i] == tab_name else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 530 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tabs[i] == tab_name else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 530 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tabs[i] == tab_name else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 560 (scales)**
```python
# Current (hardcoded)
self.info_panel.scale = (0.3, 0.4)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 561 (positions)**
```python
# Current (hardcoded)
self.info_panel.position = (0.3, 0.2)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 561 (positions)**
```python
# Current (hardcoded)
self.info_panel.position = (0.3, 0.2)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

### src/ui/panels/talent_panel.py

**Line 41 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 42 (textures)**
```python
# Current (hardcoded)
texture='white_cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_textures.component', 'white_cube')
```

**Line 51 (colors)**
```python
# Current (hardcoded)
self.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 51 (colors)**
```python
# Current (hardcoded)
self.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 82 (colors)**
```python
# Current (hardcoded)
'Attack': color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 83 (colors)**
```python
# Current (hardcoded)
'Magic': color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 84 (colors)**
```python
# Current (hardcoded)
'Spirit': color.yellow,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 85 (colors)**
```python
# Current (hardcoded)
'Move': color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 86 (colors)**
```python
# Current (hardcoded)
'Inventory': color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 88 (colors)**
```python
# Current (hardcoded)
return color_map.get(action_type, color.white)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 282 (scales)**
```python
# Current (hardcoded)
icon_scale = 0.06

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 287 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 288 (textures)**
```python
# Current (hardcoded)
texture='white_cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_textures.component', 'white_cube')
```

**Line 291 (positions)**
```python
# Current (hardcoded)
position=(0, 0, -0.01)  # Slightly in front of slot

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 300 (colors)**
```python
# Current (hardcoded)
slot_icon.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 300 (colors)**
```python
# Current (hardcoded)
slot_icon.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 458 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 458 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 458 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 459 (scales)**
```python
# Current (hardcoded)
scale=(0.2, 0.4),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 461 (positions)**
```python
# Current (hardcoded)
position=(x_offset, y_offset, 0),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 515 (positions)**
```python
# Current (hardcoded)
position=(x, y, 0)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 522 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tab_name == self.current_tab else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 522 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tab_name == self.current_tab else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 522 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tab_name == self.current_tab else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 41 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 42 (textures)**
```python
# Current (hardcoded)
texture='white_cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_textures.component', 'white_cube')
```

**Line 51 (colors)**
```python
# Current (hardcoded)
self.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 51 (colors)**
```python
# Current (hardcoded)
self.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 82 (colors)**
```python
# Current (hardcoded)
'Attack': color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 83 (colors)**
```python
# Current (hardcoded)
'Magic': color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 84 (colors)**
```python
# Current (hardcoded)
'Spirit': color.yellow,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 85 (colors)**
```python
# Current (hardcoded)
'Move': color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 86 (colors)**
```python
# Current (hardcoded)
'Inventory': color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 88 (colors)**
```python
# Current (hardcoded)
return color_map.get(action_type, color.white)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 282 (scales)**
```python
# Current (hardcoded)
icon_scale = 0.06

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 287 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 288 (textures)**
```python
# Current (hardcoded)
texture='white_cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_textures.component', 'white_cube')
```

**Line 291 (positions)**
```python
# Current (hardcoded)
position=(0, 0, -0.01)  # Slightly in front of slot

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 300 (colors)**
```python
# Current (hardcoded)
slot_icon.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 300 (colors)**
```python
# Current (hardcoded)
slot_icon.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 458 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 458 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 458 (colors)**
```python
# Current (hardcoded)
color=color.azure if tab == self.current_tab else color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 459 (scales)**
```python
# Current (hardcoded)
scale=(0.2, 0.4),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 461 (positions)**
```python
# Current (hardcoded)
position=(x_offset, y_offset, 0),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 515 (positions)**
```python
# Current (hardcoded)
position=(x, y, 0)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 522 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tab_name == self.current_tab else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 522 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tab_name == self.current_tab else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 522 (colors)**
```python
# Current (hardcoded)
btn.color = color.azure if tab_name == self.current_tab else color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/panels/base_panel.py

**Line 81 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 83 (scales)**
```python
# Current (hardcoded)
scale=(self.config.width, self.config.height, 0.01),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 97 (positions)**
```python
# Current (hardcoded)
position=(0, self.config.height/2 - 0.05, -0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 98 (scales)**
```python
# Current (hardcoded)
scale=1.5,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 99 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 99 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 174 (colors)**
```python
# Current (hardcoded)
text_color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 174 (colors)**
```python
# Current (hardcoded)
text_color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 204 (colors)**
```python
# Current (hardcoded)
button_color = color.gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 204 (colors)**
```python
# Current (hardcoded)
button_color = color.gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 81 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 83 (scales)**
```python
# Current (hardcoded)
scale=(self.config.width, self.config.height, 0.01),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 97 (positions)**
```python
# Current (hardcoded)
position=(0, self.config.height/2 - 0.05, -0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 98 (scales)**
```python
# Current (hardcoded)
scale=1.5,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 99 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 99 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 174 (colors)**
```python
# Current (hardcoded)
text_color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 174 (colors)**
```python
# Current (hardcoded)
text_color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 204 (colors)**
```python
# Current (hardcoded)
button_color = color.gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 204 (colors)**
```python
# Current (hardcoded)
button_color = color.gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/battlefield/grid_tile.py

**Line 29 (positions)**
```python
# Current (hardcoded)
position=(x + position_offset['x'], position_offset['y'], y + position_offset['z']),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 135 (colors)**
```python
# Current (hardcoded)
def highlight(self, highlight_color=color.yellow):

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 135 (colors)**
```python
# Current (hardcoded)
def highlight(self, highlight_color=color.yellow):

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 29 (positions)**
```python
# Current (hardcoded)
position=(x + position_offset['x'], position_offset['y'], y + position_offset['z']),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 135 (colors)**
```python
# Current (hardcoded)
def highlight(self, highlight_color=color.yellow):

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 135 (colors)**
```python
# Current (hardcoded)
def highlight(self, highlight_color=color.yellow):

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/battlefield/unit_entity.py

**Line 16 (positions)**
```python
# Current (hardcoded)
position=(unit.x + 0.5, 1.0, unit.y + 0.5)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 22 (colors)**
```python
# Current (hardcoded)
self.color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 22 (colors)**
```python
# Current (hardcoded)
self.color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 16 (positions)**
```python
# Current (hardcoded)
position=(unit.x + 0.5, 1.0, unit.y + 0.5)

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 22 (colors)**
```python
# Current (hardcoded)
self.color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 22 (colors)**
```python
# Current (hardcoded)
self.color = color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/ursina/ursina_ui_manager.py

**Line 31 (scales)**
```python
# Current (hardcoded)
scale=(self.size.x / 100, self.size.y / 100),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 32 (positions)**
```python
# Current (hardcoded)
position=(self.position.x / 100 - 0.5, 0.5 - self.position.y / 100),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 50 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 50 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 50 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 50 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 50 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 88 (scales)**
```python
# Current (hardcoded)
self.entity.scale = (self.size.x / 100, self.size.y / 100)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 108 (models)**
```python
# Current (hardcoded)
model='quad',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 110 (scales)**
```python
# Current (hardcoded)
scale=(self.size.x / 100, self.size.y / 100),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 111 (positions)**
```python
# Current (hardcoded)
position=(self.position.x / 100 - 0.5, 0.5 - self.position.y / 100),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 122 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 122 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 122 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 122 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 122 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 133 (models)**
```python
# Current (hardcoded)
model='quad',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 161 (scales)**
```python
# Current (hardcoded)
self.entity.scale = (self.size.x / 100, self.size.y / 100)

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 193 (positions)**
```python
# Current (hardcoded)
position=(self.position.x / 100 - 0.5, 0.5 - self.position.y / 100),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 201 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 201 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 201 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 201 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 201 (colors)**
```python
# Current (hardcoded)
return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/interaction/interactive_tile.py

**Line 60 (colors)**
```python
# Current (hardcoded)
TileState.NORMAL: color.light_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 61 (colors)**
```python
# Current (hardcoded)
TileState.HIGHLIGHTED: color.yellow,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 62 (colors)**
```python
# Current (hardcoded)
TileState.SELECTED: color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 63 (colors)**
```python
# Current (hardcoded)
TileState.MOVEMENT_RANGE: color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 64 (colors)**
```python
# Current (hardcoded)
TileState.ATTACK_RANGE: color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 65 (colors)**
```python
# Current (hardcoded)
TileState.EFFECT_AREA: color.orange,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 66 (colors)**
```python
# Current (hardcoded)
TileState.INVALID: color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 67 (colors)**
```python
# Current (hardcoded)
TileState.HOVERED: color.blue

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 79 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 81 (scales)**
```python
# Current (hardcoded)
scale=(self.tile_size * 0.95, 0.1, self.tile_size * 0.95),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 82 (positions)**
```python
# Current (hardcoded)
position=(self.world_pos.x, self.world_pos.y, self.world_pos.z),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

### src/ui/interaction/action_modal.py

**Line 74 (colors)**
```python
# Current (hardcoded)
'background': color.black33,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 75 (colors)**
```python
# Current (hardcoded)
'modal_bg': color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 76 (colors)**
```python
# Current (hardcoded)
'modal_border': color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 77 (colors)**
```python
# Current (hardcoded)
'button_normal': color.azure,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 78 (colors)**
```python
# Current (hardcoded)
'button_hover': color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 79 (colors)**
```python
# Current (hardcoded)
'button_disabled': color.gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 80 (colors)**
```python
# Current (hardcoded)
'text': color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 81 (colors)**
```python
# Current (hardcoded)
'title': color.yellow

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 91 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 93 (scales)**
```python
# Current (hardcoded)
scale=(2, 1, 2),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 94 (positions)**
```python
# Current (hardcoded)
position=(0, 0, -0.1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 100 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 102 (scales)**
```python
# Current (hardcoded)
scale=(self.modal_width, self.modal_height, 0.01),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 103 (positions)**
```python
# Current (hardcoded)
position=(0, 0, 0),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 111 (positions)**
```python
# Current (hardcoded)
position=(0, self.modal_height/2 - 0.1, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 112 (scales)**
```python
# Current (hardcoded)
scale=1.5,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 134 (scales)**
```python
# Current (hardcoded)
scale=(self.modal_width - 0.1, self.button_height),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 135 (positions)**
```python
# Current (hardcoded)
position=(0, button_y, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 153 (colors)**
```python
# Current (hardcoded)
color=color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 153 (colors)**
```python
# Current (hardcoded)
color=color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 154 (scales)**
```python
# Current (hardcoded)
scale=(self.modal_width - 0.1, self.button_height),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 155 (positions)**
```python
# Current (hardcoded)
position=(0, cancel_button_y, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 159 (colors)**
```python
# Current (hardcoded)
cancel_button.on_mouse_enter = lambda: setattr(cancel_button, 'color', color.dark_gray)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 160 (colors)**
```python
# Current (hardcoded)
cancel_button.on_mouse_exit = lambda: setattr(cancel_button, 'color', color.red)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/ui/interface/combat_interface.py

**Line 52 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 53 (scales)**
```python
# Current (hardcoded)
scale=(0.3, 0.2, 0.01),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 54 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.1, 0.1, 0.15, 0.9),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 54 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.1, 0.1, 0.15, 0.9),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 55 (positions)**
```python
# Current (hardcoded)
position=(-0.6, 0.3, 0),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 62 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 63 (scales)**
```python
# Current (hardcoded)
scale=(0.25, 0.4, 0.01),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 64 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.1, 0.1, 0.15, 0.9),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 64 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.1, 0.1, 0.15, 0.9),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 65 (positions)**
```python
# Current (hardcoded)
position=(0.6, 0.1, 0),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 87 (positions)**
```python
# Current (hardcoded)
position=(x_pos, button_y, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 88 (scales)**
```python
# Current (hardcoded)
scale=0.08,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 89 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.3, 0.3, 0.35, 1.0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 89 (colors)**
```python
# Current (hardcoded)
color=color.Color(0.3, 0.3, 0.35, 1.0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 90 (colors)**
```python
# Current (hardcoded)
text_color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 90 (colors)**
```python
# Current (hardcoded)
text_color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 137 (positions)**
```python
# Current (hardcoded)
position=(0, 0.07, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 138 (scales)**
```python
# Current (hardcoded)
scale=1.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 139 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 139 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 150 (positions)**
```python
# Current (hardcoded)
position=(0, 0.03, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 151 (scales)**
```python
# Current (hardcoded)
scale=0.8,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 152 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 152 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 158 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 159 (scales)**
```python
# Current (hardcoded)
scale=(0.2, 0.02, 0.001),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 160 (colors)**
```python
# Current (hardcoded)
color=color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 160 (colors)**
```python
# Current (hardcoded)
color=color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 161 (positions)**
```python
# Current (hardcoded)
position=(0, -0.01, 0.001),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 166 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 167 (scales)**
```python
# Current (hardcoded)
scale=(0.2 * hp_ratio, 0.02, 0.001),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 168 (colors)**
```python
# Current (hardcoded)
color=color.red if hp_ratio < 0.3 else color.yellow if hp_ratio < 0.7 else color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 168 (colors)**
```python
# Current (hardcoded)
color=color.red if hp_ratio < 0.3 else color.yellow if hp_ratio < 0.7 else color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 168 (colors)**
```python
# Current (hardcoded)
color=color.red if hp_ratio < 0.3 else color.yellow if hp_ratio < 0.7 else color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 168 (colors)**
```python
# Current (hardcoded)
color=color.red if hp_ratio < 0.3 else color.yellow if hp_ratio < 0.7 else color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 169 (positions)**
```python
# Current (hardcoded)
position=((-0.2 + 0.2 * hp_ratio) / 2, -0.01, 0.002),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 179 (positions)**
```python
# Current (hardcoded)
position=(0, -0.05, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 180 (scales)**
```python
# Current (hardcoded)
scale=0.8,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 181 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 181 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 186 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 187 (scales)**
```python
# Current (hardcoded)
scale=(0.2, 0.02, 0.001),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 188 (colors)**
```python
# Current (hardcoded)
color=color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 188 (colors)**
```python
# Current (hardcoded)
color=color.dark_gray,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 189 (positions)**
```python
# Current (hardcoded)
position=(0, -0.09, 0.001),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 194 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 195 (scales)**
```python
# Current (hardcoded)
scale=(0.2 * mp_ratio, 0.02, 0.001),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 196 (colors)**
```python
# Current (hardcoded)
color=color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 196 (colors)**
```python
# Current (hardcoded)
color=color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 197 (positions)**
```python
# Current (hardcoded)
position=((-0.2 + 0.2 * mp_ratio) / 2, -0.09, 0.002),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 206 (colors)**
```python
# Current (hardcoded)
button.color = color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 206 (colors)**
```python
# Current (hardcoded)
button.color = color.dark_gray

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 234 (colors)**
```python
# Current (hardcoded)
button.color = color.Color(0.3, 0.3, 0.35, 1.0)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 234 (colors)**
```python
# Current (hardcoded)
button.color = color.Color(0.3, 0.3, 0.35, 1.0)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 237 (colors)**
```python
# Current (hardcoded)
button.color = color.Color(0.15, 0.15, 0.15, 1.0)  # Darker gray for insufficient AP

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 237 (colors)**
```python
# Current (hardcoded)
button.color = color.Color(0.15, 0.15, 0.15, 1.0)  # Darker gray for insufficient AP

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 283 (positions)**
```python
# Current (hardcoded)
position=(0, 0.15, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 284 (scales)**
```python
# Current (hardcoded)
scale=1.0,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 285 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 285 (colors)**
```python
# Current (hardcoded)
color=color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 294 (colors)**
```python
# Current (hardcoded)
text_color = color.yellow if unit == self.selected_unit else color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 294 (colors)**
```python
# Current (hardcoded)
text_color = color.yellow if unit == self.selected_unit else color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 294 (colors)**
```python
# Current (hardcoded)
text_color = color.yellow if unit == self.selected_unit else color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 298 (positions)**
```python
# Current (hardcoded)
position=(0, y_pos, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 299 (scales)**
```python
# Current (hardcoded)
scale=0.7,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

### src/ui/interface/inventory_interface.py

**Line 92 (colors)**
```python
# Current (hardcoded)
'background': color.Color(0.1, 0.1, 0.15, 0.95),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 93 (colors)**
```python
# Current (hardcoded)
'panel': color.Color(0.2, 0.2, 0.25, 0.9),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 94 (colors)**
```python
# Current (hardcoded)
'button': color.Color(0.3, 0.3, 0.35, 1.0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 95 (colors)**
```python
# Current (hardcoded)
'button_hover': color.Color(0.4, 0.4, 0.45, 1.0),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 96 (colors)**
```python
# Current (hardcoded)
'text': color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 97 (colors)**
```python
# Current (hardcoded)
'stat_increase': color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 98 (colors)**
```python
# Current (hardcoded)
'stat_decrease': color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 99 (colors)**
```python
# Current (hardcoded)
'equipment_common': color.white,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 100 (colors)**
```python
# Current (hardcoded)
'equipment_enhanced': color.Color(0.0, 1.0, 0.0, 1.0),  # Green

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 101 (colors)**
```python
# Current (hardcoded)
'equipment_enchanted': color.Color(0.0, 0.7, 1.0, 1.0),  # Blue

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 102 (colors)**
```python
# Current (hardcoded)
'equipment_superpowered': color.Color(0.8, 0.0, 1.0, 1.0),  # Purple

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 103 (colors)**
```python
# Current (hardcoded)
'equipment_metapowered': color.Color(1.0, 0.7, 0.0, 1.0)   # Orange/Gold

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 113 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 114 (scales)**
```python
# Current (hardcoded)
scale=(20, 20, 1),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 115 (colors)**
```python
# Current (hardcoded)
color=color.Color(0, 0, 0, 0.3),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 115 (colors)**
```python
# Current (hardcoded)
color=color.Color(0, 0, 0, 0.3),

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 116 (positions)**
```python
# Current (hardcoded)
position=(0, 0, -1),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 123 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 124 (scales)**
```python
# Current (hardcoded)
scale=(self.panel_width, self.panel_height, 0.01),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 126 (positions)**
```python
# Current (hardcoded)
position=(0, 0, 0),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 150 (positions)**
```python
# Current (hardcoded)
position=(0, header_y, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 151 (scales)**
```python
# Current (hardcoded)
scale=2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 172 (positions)**
```python
# Current (hardcoded)
position=(x_pos, button_y, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 173 (scales)**
```python
# Current (hardcoded)
scale=0.08,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 195 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 196 (scales)**
```python
# Current (hardcoded)
scale=(slot_size, slot_size, 0.005),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 198 (positions)**
```python
# Current (hardcoded)
position=(slot_x, slot_y, 0.005),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 230 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 231 (scales)**
```python
# Current (hardcoded)
scale=(slot_size, slot_size, 0.005),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 233 (positions)**
```python
# Current (hardcoded)
position=(slot_x, slot_y, 0.005),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 240 (positions)**
```python
# Current (hardcoded)
position=(slot_x, slot_y - slot_size - 0.02, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 241 (scales)**
```python
# Current (hardcoded)
scale=0.5,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 259 (positions)**
```python
# Current (hardcoded)
position=(stats_x, stats_y + 0.15, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 260 (scales)**
```python
# Current (hardcoded)
scale=1.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 278 (positions)**
```python
# Current (hardcoded)
position=(stats_x, stat_y, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 279 (scales)**
```python
# Current (hardcoded)
scale=0.8,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 295 (positions)**
```python
# Current (hardcoded)
position=(comparison_x, comparison_y + 0.15, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 296 (scales)**
```python
# Current (hardcoded)
scale=1.2,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 304 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 305 (scales)**
```python
# Current (hardcoded)
scale=(0.35, 0.25, 0.005),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 307 (positions)**
```python
# Current (hardcoded)
position=(comparison_x, comparison_y, 0.005),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 317 (positions)**
```python
# Current (hardcoded)
position=(self.panel_width / 2 - 0.05, self.panel_height / 2 - 0.05, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 318 (scales)**
```python
# Current (hardcoded)
scale=0.05,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 319 (colors)**
```python
# Current (hardcoded)
color=color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 319 (colors)**
```python
# Current (hardcoded)
color=color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 342 (positions)**
```python
# Current (hardcoded)
position=(x_pos, button_y, 0.01),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 343 (scales)**
```python
# Current (hardcoded)
scale=0.08,

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

### src/game/utils/ui/hotkeys.py

**Line 111 (positions)**
```python
# Current (hardcoded)
position=(start_pos['x'] + x_offset, start_pos['y'], start_pos['z']),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 124 (positions)**
```python
# Current (hardcoded)
position=(text_pos['x'], text_pos['y'], text_pos['z']),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 150 (colors)**
```python
# Current (hardcoded)
'Attack': color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 151 (colors)**
```python
# Current (hardcoded)
'Magic': color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 152 (colors)**
```python
# Current (hardcoded)
'Spirit': color.yellow,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 153 (colors)**
```python
# Current (hardcoded)
'Move': color.green,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 154 (colors)**
```python
# Current (hardcoded)
'Inventory': color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 156 (colors)**
```python
# Current (hardcoded)
return color_map.get(action_type, color.white)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 386 (colors)**
```python
# Current (hardcoded)
slot.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 386 (colors)**
```python
# Current (hardcoded)
slot.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/game/utils/ui/confirmation.py

**Line 21 (colors)**
```python
# Current (hardcoded)
color=self._get_button_color('attack_confirmation', 'confirm', color.red)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 25 (colors)**
```python
# Current (hardcoded)
color=self._get_button_color('attack_confirmation', 'cancel', color.gray)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 135 (colors)**
```python
# Current (hardcoded)
color=self._get_button_color('magic_confirmation', 'confirm', color.blue)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 139 (colors)**
```python
# Current (hardcoded)
color=self._get_button_color('magic_confirmation', 'cancel', color.gray)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

### src/game/controllers/tactical_rpg_controller.py

**Line 295 (colors)**
```python
# Current (hardcoded)
return color.rgb(color_data[0], color_data[1], color_data[2])

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 295 (colors)**
```python
# Current (hardcoded)
return color.rgb(color_data[0], color_data[1], color_data[2])

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 298 (colors)**
```python
# Current (hardcoded)
return fallback_color or color.white

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 316 (colors)**
```python
# Current (hardcoded)
return color.rgb(color_data[0], color_data[1], color_data[2])

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 316 (colors)**
```python
# Current (hardcoded)
return color.rgb(color_data[0], color_data[1], color_data[2])

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 328 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 331 (positions)**
```python
# Current (hardcoded)
position=(x + position_offset[0], position_offset[1], y + position_offset[2]),

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 494 (positions)**
```python
# Current (hardcoded)
entity.position = (entity.unit.x + 0.5, 1.0, entity.unit.y + 0.5)  # Center on grid tiles

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 494 (positions)**
```python
# Current (hardcoded)
entity.position = (entity.unit.x + 0.5, 1.0, entity.unit.y + 0.5)  # Center on grid tiles

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 546 (colors)**
```python
# Current (hardcoded)
highlight_color = self._get_highlight_style('selection', color.white)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 549 (colors)**
```python
# Current (hardcoded)
highlight_color = self._get_highlight_style('movement', color.green)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 676 (colors)**
```python
# Current (hardcoded)
btn = Button(text=action, color=color.azure)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 676 (colors)**
```python
# Current (hardcoded)
btn = Button(text=action, color=color.azure)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 681 (colors)**
```python
# Current (hardcoded)
cancel_btn = Button(text='Cancel', color=color.red)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 681 (colors)**
```python
# Current (hardcoded)
cancel_btn = Button(text='Cancel', color=color.red)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 852 (colors)**
```python
# Current (hardcoded)
highlight_color = color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 852 (colors)**
```python
# Current (hardcoded)
highlight_color = color.orange

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 855 (colors)**
```python
# Current (hardcoded)
highlight_color = color.yellow

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 855 (colors)**
```python
# Current (hardcoded)
highlight_color = color.yellow

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 859 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 861 (scales)**
```python
# Current (hardcoded)
scale=(0.9, 0.2, 0.9),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 862 (positions)**
```python
# Current (hardcoded)
position=(x + 0.5, 0, y + 0.5),  # Same height as grid tiles

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 885 (colors)**
```python
# Current (hardcoded)
color=self._get_button_color('attack_confirmation', 'confirm', color.red)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 889 (colors)**
```python
# Current (hardcoded)
color=self._get_button_color('attack_confirmation', 'cancel', color.gray)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1059 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 1061 (scales)**
```python
# Current (hardcoded)
scale=(0.9, 0.2, 0.9),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 1062 (positions)**
```python
# Current (hardcoded)
position=(x + 0.5, 0, y + 0.5),  # Same height as grid tiles

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 1085 (colors)**
```python
# Current (hardcoded)
color=self._get_button_color('magic_confirmation', 'confirm', color.blue)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1089 (colors)**
```python
# Current (hardcoded)
color=self._get_button_color('magic_confirmation', 'cancel', color.gray)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1161 (colors)**
```python
# Current (hardcoded)
color=self._get_button_color('movement_confirmation', 'confirm', color.green)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1165 (colors)**
```python
# Current (hardcoded)
color=self._get_button_color('movement_confirmation', 'cancel', color.red)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1343 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 1344 (colors)**
```python
# Current (hardcoded)
color=color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1344 (colors)**
```python
# Current (hardcoded)
color=color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1345 (scales)**
```python
# Current (hardcoded)
scale=(0.9, 0.2, 0.9),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 1346 (positions)**
```python
# Current (hardcoded)
position=(pos[0] + 0.5, 0, pos[1] + 0.5),  # Center on tile, same level as grid

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 1357 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 1358 (colors)**
```python
# Current (hardcoded)
color=color.yellow,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1358 (colors)**
```python
# Current (hardcoded)
color=color.yellow,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1359 (scales)**
```python
# Current (hardcoded)
scale=(0.9, 0.2, 0.9),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 1360 (positions)**
```python
# Current (hardcoded)
position=(self.path_cursor[0] + 0.5, 0, self.path_cursor[1] + 0.5),  # Center on tile, same level as grid

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 1392 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 1393 (colors)**
```python
# Current (hardcoded)
color=color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1393 (colors)**
```python
# Current (hardcoded)
color=color.red,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1394 (scales)**
```python
# Current (hardcoded)
scale=(0.9, 0.2, 0.9),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 1395 (positions)**
```python
# Current (hardcoded)
position=(x + 0.5, 0, y + 0.5),  # Same height as grid tiles

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 1422 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 1423 (colors)**
```python
# Current (hardcoded)
color=color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1423 (colors)**
```python
# Current (hardcoded)
color=color.blue,

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 1424 (scales)**
```python
# Current (hardcoded)
scale=(0.9, 0.2, 0.9),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 1425 (positions)**
```python
# Current (hardcoded)
position=(x + 0.5, 0, y + 0.5),  # Same height as grid tiles

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```

**Line 2196 (colors)**
```python
# Current (hardcoded)
hex_color = hex_color.lstrip('#')

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 2201 (colors)**
```python
# Current (hardcoded)
return color.rgb(r, g, b)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 2201 (colors)**
```python
# Current (hardcoded)
return color.rgb(r, g, b)

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 2203 (colors)**
```python
# Current (hardcoded)
return color.gray  # Fallback color

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 2401 (models)**
```python
# Current (hardcoded)
model='cube',

# Suggested replacement
# ui_config.get('models_and_textures.default_models.component', 'cube')
```

**Line 2402 (colors)**
```python
# Current (hardcoded)
color=color.orange,  # Orange color for targets

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 2402 (colors)**
```python
# Current (hardcoded)
color=color.orange,  # Orange color for targets

# Suggested replacement
# ui_config.get_color('colors.action_types.ComponentType')
```

**Line 2403 (scales)**
```python
# Current (hardcoded)
scale=(0.9, 0.2, 0.9),

# Suggested replacement
# ui_config.get('component.scale', 1.0)
```

**Line 2404 (positions)**
```python
# Current (hardcoded)
position=(target_unit.x + 0.5, 0.1, target_unit.y + 0.5),  # Slightly above ground

# Suggested replacement
# ui_config.get_position_tuple('component.position')
```
