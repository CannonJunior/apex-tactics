"""
Object Pool Implementation

Provides object pooling for performance optimization by reducing garbage collection pressure.
Particularly useful for frequently created/destroyed objects like PathNode instances.
"""

from typing import TypeVar, Generic, List, Callable, Optional
from threading import Lock

T = TypeVar('T')

class ObjectPool(Generic[T]):
    """
    Generic object pool for recycling objects to reduce GC pressure.
    
    Thread-safe implementation suitable for pathfinding and other performance-critical operations.
    """
    
    def __init__(self, create_func: Callable[[], T], reset_func: Optional[Callable[[T], None]] = None, 
                 max_size: int = 100):
        """
        Initialize object pool.
        
        Args:
            create_func: Function to create new objects when pool is empty
            reset_func: Optional function to reset objects before reuse
            max_size: Maximum number of objects to keep in pool
        """
        self._create_func = create_func
        self._reset_func = reset_func
        self._max_size = max_size
        self._pool: List[T] = []
        self._lock = Lock()
        self._created_count = 0
        self._reused_count = 0
        self._peak_size = 0
    
    def get(self) -> T:
        """
        Get an object from the pool, creating new one if pool is empty.
        
        Returns:
            Object instance ready for use
        """
        with self._lock:
            if self._pool:
                obj = self._pool.pop()
                self._reused_count += 1
                return obj
            else:
                obj = self._create_func()
                self._created_count += 1
                return obj
    
    def put(self, obj: T) -> None:
        """
        Return an object to the pool for reuse.
        
        Args:
            obj: Object to return to pool
        """
        if obj is None:
            return
            
        with self._lock:
            if len(self._pool) < self._max_size:
                # Reset object state if reset function provided
                if self._reset_func:
                    self._reset_func(obj)
                
                self._pool.append(obj)
                self._peak_size = max(self._peak_size, len(self._pool))
    
    def clear(self) -> None:
        """Clear all objects from pool"""
        with self._lock:
            self._pool.clear()
    
    def get_stats(self) -> dict:
        """
        Get pool performance statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        with self._lock:
            total_requests = self._created_count + self._reused_count
            reuse_rate = self._reused_count / total_requests if total_requests > 0 else 0.0
            
            return {
                'current_size': len(self._pool),
                'max_size': self._max_size,
                'peak_size': self._peak_size,
                'created_count': self._created_count,
                'reused_count': self._reused_count,
                'total_requests': total_requests,
                'reuse_rate': reuse_rate,
                'memory_savings': self._reused_count  # Approximate objects saved from GC
            }
    
    def __len__(self) -> int:
        """Get current pool size"""
        with self._lock:
            return len(self._pool)


class PathNodePool:
    """
    Specialized object pool for PathNode instances used in pathfinding.
    
    Optimized for A* pathfinding performance with proper state resetting.
    """
    
    def __init__(self, max_size: int = 500):
        """
        Initialize PathNode pool.
        
        Args:
            max_size: Maximum number of PathNode objects to pool
        """
        # Import here to avoid circular dependency
        from core.math.pathfinding import PathNode
        from core.math.vector import Vector2Int
        
        self._PathNode = PathNode
        self._Vector2Int = Vector2Int
        
        def create_node():
            return PathNode(Vector2Int(0, 0))
        
        def reset_node(node):
            node.position = Vector2Int(0, 0)
            node.g_cost = 0.0
            node.h_cost = 0.0
            node.parent = None
        
        self._pool = ObjectPool[PathNode](create_node, reset_node, max_size)
    
    def get_node(self, position, g_cost: float = 0.0, h_cost: float = 0.0, parent=None):
        """
        Get a PathNode from the pool with specified parameters.
        
        Args:
            position: Grid position for the node
            g_cost: Cost from start
            h_cost: Heuristic cost to goal
            parent: Parent node in path
            
        Returns:
            PathNode instance ready for use
        """
        node = self._pool.get()
        node.position = position
        node.g_cost = g_cost
        node.h_cost = h_cost
        node.parent = parent
        return node
    
    def return_node(self, node) -> None:
        """
        Return a PathNode to the pool for reuse.
        
        Args:
            node: PathNode to return to pool
        """
        self._pool.put(node)
    
    def return_nodes(self, nodes: List) -> None:
        """
        Return multiple PathNodes to the pool for reuse.
        
        Args:
            nodes: List of PathNodes to return to pool
        """
        for node in nodes:
            if node is not None:
                self.return_node(node)
    
    def clear(self) -> None:
        """Clear all nodes from pool"""
        self._pool.clear()
    
    def get_stats(self) -> dict:
        """Get pool performance statistics"""
        return self._pool.get_stats()


# Global PathNode pool instance for use across pathfinding operations
_global_pathnode_pool = None

def get_pathnode_pool() -> PathNodePool:
    """
    Get the global PathNode pool instance.
    
    Returns:
        Global PathNodePool instance
    """
    global _global_pathnode_pool
    if _global_pathnode_pool is None:
        _global_pathnode_pool = PathNodePool(max_size=1000)
    return _global_pathnode_pool