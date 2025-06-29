"""
Pathfinding Algorithms for Tactical Grid

Implements A* pathfinding optimized for <2ms queries on 10x10 grids.
Supports height variations and movement costs.
"""

import heapq
import time
from typing import List, Dict, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field

from .vector import Vector2Int
from .grid import TacticalGrid
from core.utils.object_pool import get_pathnode_pool

@dataclass
class PathNode:
    """Node for pathfinding algorithms"""
    position: Vector2Int
    g_cost: float = 0.0  # Cost from start
    h_cost: float = 0.0  # Heuristic cost to goal
    parent: Optional['PathNode'] = None
    
    @property
    def f_cost(self) -> float:
        """Total cost (g + h)"""
        return self.g_cost + self.h_cost
    
    def __lt__(self, other: 'PathNode') -> bool:
        """For heapq comparison"""
        return self.f_cost < other.f_cost

class PathfindingResult:
    """Result of pathfinding query"""
    
    def __init__(self, path: List[Vector2Int], cost: float, 
                 search_time: float, nodes_explored: int):
        self.path = path
        self.cost = cost
        self.search_time = search_time
        self.nodes_explored = nodes_explored
        self.success = len(path) > 0
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for debugging"""
        return {
            'success': self.success,
            'path_length': len(self.path),
            'total_cost': self.cost,
            'search_time_ms': self.search_time * 1000,
            'nodes_explored': self.nodes_explored,
            'path': [pos.to_dict() for pos in self.path]
        }

class AStarPathfinder:
    """
    A* pathfinding implementation optimized for tactical grids.
    
    Optimized for performance with caching and early termination.
    Target: <2ms per query on 10x10 grids with height variations.
    """
    
    def __init__(self, grid: TacticalGrid):
        self.grid = grid
        # Use LRU cache for better cache performance
        from core.utils.lru_cache import LRUCache
        self.path_cache = LRUCache(max_size=1000)
        self.max_search_nodes = 500  # Limit for performance
        self.node_pool = get_pathnode_pool()  # Object pool for PathNode instances
    
    def find_path(self, start: Vector2Int, goal: Vector2Int,
                  movement_cost_func: Optional[Callable[[Vector2Int, Vector2Int], float]] = None,
                  max_cost: float = float('inf')) -> PathfindingResult:
        """
        Find path from start to goal using A* algorithm.
        
        Args:
            start: Starting position
            goal: Goal position
            movement_cost_func: Optional custom movement cost function
            max_cost: Maximum allowed path cost
            
        Returns:
            PathfindingResult with path and performance data
        """
        search_start_time = time.perf_counter()
        
        # Check cache first
        cache_key = (start, goal)
        cached_result = self.path_cache.get(cache_key)
        if cached_result is not None:
            # Update search time for cached result
            cached_result.search_time = time.perf_counter() - search_start_time
            return cached_result
        
        # Validate start and goal
        if not self._is_valid_position(start) or not self._is_valid_position(goal):
            return PathfindingResult([], 0.0, time.perf_counter() - search_start_time, 0)
        
        # If start == goal, return single-node path
        if start == goal:
            result = PathfindingResult([start], 0.0, time.perf_counter() - search_start_time, 1)
            self._cache_result(cache_key, result)
            return result
        
        # Use custom cost function or default grid costs
        cost_func = movement_cost_func or self.grid.get_movement_cost
        
        # A* algorithm
        open_set = []
        closed_set: Set[Vector2Int] = set()
        nodes: Dict[Vector2Int, PathNode] = {}
        used_nodes: List[PathNode] = []  # Track nodes for cleanup
        
        # Initialize start node using object pool
        start_node = self.node_pool.get_node(start, 0.0, self._heuristic(start, goal))
        nodes[start] = start_node
        used_nodes.append(start_node)
        heapq.heappush(open_set, start_node)
        
        nodes_explored = 0
        
        while open_set and nodes_explored < self.max_search_nodes:
            current_node = heapq.heappop(open_set)
            current_pos = current_node.position
            
            # Check if we reached the goal
            if current_pos == goal:
                path = self._reconstruct_path(current_node)
                search_time = time.perf_counter() - search_start_time
                result = PathfindingResult(path, current_node.g_cost, search_time, nodes_explored)
                self._cache_result(cache_key, result)
                
                # Return used nodes to pool for reuse
                self.node_pool.return_nodes(used_nodes)
                
                return result
            
            closed_set.add(current_pos)
            nodes_explored += 1
            
            # Explore neighbors
            for neighbor_pos in self.grid.get_neighbors(current_pos):
                if neighbor_pos in closed_set:
                    continue
                
                # Calculate movement cost
                movement_cost = cost_func(current_pos, neighbor_pos)
                if movement_cost == float('inf'):
                    continue  # Impassable
                
                tentative_g_cost = current_node.g_cost + movement_cost
                
                # Skip if cost exceeds maximum
                if tentative_g_cost > max_cost:
                    continue
                
                # Check if this is a better path to the neighbor
                if neighbor_pos not in nodes:
                    neighbor_node = self.node_pool.get_node(
                        neighbor_pos,
                        tentative_g_cost,
                        self._heuristic(neighbor_pos, goal),
                        current_node
                    )
                    nodes[neighbor_pos] = neighbor_node
                    used_nodes.append(neighbor_node)
                    heapq.heappush(open_set, neighbor_node)
                    
                elif tentative_g_cost < nodes[neighbor_pos].g_cost:
                    neighbor_node = nodes[neighbor_pos]
                    neighbor_node.g_cost = tentative_g_cost
                    neighbor_node.parent = current_node
                    # Re-add to open set (heapq doesn't support decrease-key)
                    heapq.heappush(open_set, neighbor_node)
        
        # No path found
        search_time = time.perf_counter() - search_start_time
        result = PathfindingResult([], 0.0, search_time, nodes_explored)
        self._cache_result(cache_key, result)
        
        # Return used nodes to pool for reuse
        self.node_pool.return_nodes(used_nodes)
        
        return result
    
    def find_reachable_positions(self, start: Vector2Int, max_movement: float) -> List[Vector2Int]:
        """
        Find all positions reachable within movement points.
        
        Args:
            start: Starting position
            max_movement: Maximum movement points available
            
        Returns:
            List of reachable positions
        """
        if not self._is_valid_position(start):
            return []
        
        reachable = []
        visited: Set[Vector2Int] = set()
        queue = [(start, 0.0)]  # (position, cost_to_reach)
        
        while queue:
            current_pos, current_cost = queue.pop(0)
            
            if current_pos in visited:
                continue
            
            visited.add(current_pos)
            reachable.append(current_pos)
            
            # Explore neighbors
            for neighbor_pos in self.grid.get_neighbors(current_pos):
                if neighbor_pos in visited:
                    continue
                
                movement_cost = self.grid.get_movement_cost(current_pos, neighbor_pos)
                if movement_cost == float('inf'):
                    continue
                
                total_cost = current_cost + movement_cost
                if total_cost <= max_movement:
                    queue.append((neighbor_pos, total_cost))
        
        return reachable
    
    def _heuristic(self, pos: Vector2Int, goal: Vector2Int) -> float:
        """
        Heuristic function for A* (Manhattan distance with height consideration).
        
        Args:
            pos: Current position
            goal: Goal position
            
        Returns:
            Estimated cost to goal
        """
        # Manhattan distance as base
        manhattan_dist = pos.manhattan_distance_to(goal)
        
        # Add height difference consideration
        pos_cell = self.grid.get_cell(pos)
        goal_cell = self.grid.get_cell(goal)
        
        if pos_cell and goal_cell:
            height_diff = abs(pos_cell.height - goal_cell.height)
            height_cost = height_diff * 0.5  # Conservative height cost estimate
            return float(manhattan_dist) + height_cost
        
        return float(manhattan_dist)
    
    def _reconstruct_path(self, goal_node: PathNode) -> List[Vector2Int]:
        """Reconstruct path from goal node back to start"""
        path = []
        current = goal_node
        
        while current is not None:
            path.append(current.position)
            current = current.parent
        
        path.reverse()
        return path
    
    def _is_valid_position(self, pos: Vector2Int) -> bool:
        """Check if position is valid and pathable"""
        cell = self.grid.get_cell(pos)
        return cell is not None and cell.passable
    
    def _cache_result(self, cache_key: Tuple[Vector2Int, Vector2Int], 
                     result: PathfindingResult):
        """Cache pathfinding result using LRU cache"""
        self.path_cache.put(cache_key, result)
    
    def clear_cache(self):
        """Clear pathfinding cache"""
        self.path_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get pathfinding cache performance statistics"""
        cache_stats = self.path_cache.get_stats()
        pool_stats = self.node_pool.get_stats()
        
        return {
            'cache': cache_stats,
            'node_pool': pool_stats,
            'total_memory_savings': pool_stats.get('memory_savings', 0)
        }
    

class JumpPointSearch:
    """
    Jump Point Search pathfinding (JPS) for improved performance.
    
    More advanced pathfinding algorithm that can be 10-40x faster than A*
    on uniform grids. Planned for future optimization.
    """
    
    def __init__(self, grid: TacticalGrid):
        self.grid = grid
        # TODO: Implement JPS for Phase 2 optimization
    
    def find_path(self, start: Vector2Int, goal: Vector2Int) -> PathfindingResult:
        """Find path using Jump Point Search"""
        # Placeholder - fall back to A* for now
        pathfinder = AStarPathfinder(self.grid)
        return pathfinder.find_path(start, goal)

# Utility functions for pathfinding

def smooth_path(path: List[Vector2Int], grid: TacticalGrid) -> List[Vector2Int]:
    """
    Smooth path by removing unnecessary waypoints.
    
    Args:
        path: Original path
        grid: Grid for line-of-sight checks
        
    Returns:
        Smoothed path
    """
    if len(path) <= 2:
        return path
    
    smoothed = [path[0]]
    current_index = 0
    
    while current_index < len(path) - 1:
        # Look for the furthest point we can reach directly
        furthest_index = current_index + 1
        
        for i in range(current_index + 2, len(path)):
            if grid.get_line_of_sight(path[current_index], path[i]):
                furthest_index = i
            else:
                break
        
        smoothed.append(path[furthest_index])
        current_index = furthest_index
    
    return smoothed

def calculate_path_cost(path: List[Vector2Int], grid: TacticalGrid) -> float:
    """
    Calculate total cost of a path.
    
    Args:
        path: Path to calculate cost for
        grid: Grid for movement costs
        
    Returns:
        Total path cost
    """
    if len(path) < 2:
        return 0.0
    
    total_cost = 0.0
    for i in range(len(path) - 1):
        cost = grid.get_movement_cost(path[i], path[i + 1])
        if cost == float('inf'):
            return float('inf')  # Invalid path
        total_cost += cost
    
    return total_cost