# Math Utilities

<system_context>
Mathematical operations for 3D vectors, grid coordinates, pathfinding, and tactical calculations.
</system_context>

<critical_notes>
- All vector operations must be immutable
- Grid coordinates use integer positions only
- Pathfinding must complete within 2ms for 10x10 grids
- Height variations affect movement costs
</critical_notes>

<file_map>
Vector operations: @src/core/math/vector.py
Grid mathematics: @src/core/math/grid.py
Pathfinding algorithms: @src/core/math/pathfinding.py
</file_map>

<paved_path>
1. Implement Vector3 and Vector2Int classes
2. Create grid coordinate conversion functions
3. Build A* pathfinding with height support
4. Add tactical geometry calculations
</paved_path>

<patterns>
```python
# Vector operations
new_pos = position + velocity * delta_time

# Grid conversions
grid_pos = world_to_grid(world_position)
world_pos = grid_to_world(grid_position)
```
</patterns>

<performance_target>
Pathfinding: <2ms per query on 10x10 grids with height variations
</performance_target>