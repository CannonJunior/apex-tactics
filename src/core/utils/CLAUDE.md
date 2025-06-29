# Core Utilities

<system_context>
Essential utilities for serialization, logging, performance monitoring, and system support.
</system_context>

<critical_notes>
- Logging must not impact performance in release builds
- Serialization must support Unity-compatible formats
- Performance monitoring tracks all critical benchmarks
- No external dependencies allowed in core utilities
</critical_notes>

<file_map>
Save/load utilities: @src/core/utils/serialization.py
Logging system: @src/core/utils/logging.py
Performance monitoring: @src/core/utils/performance.py
</file_map>

<paved_path>
1. Implement JSON serialization for game state
2. Create structured logging with performance levels
3. Build performance monitor with frame timing
4. Add utility functions for common operations
</paved_path>

<patterns>
```python
# Performance monitoring
with PerformanceMonitor.measure("stat_calculation"):
    stats = calculate_derived_stats(attributes)

# Logging
Logger.info("Entity created", entity_id=entity.id)
```
</patterns>

<performance_target>
Performance monitoring overhead: <0.1ms per measurement
</performance_target>