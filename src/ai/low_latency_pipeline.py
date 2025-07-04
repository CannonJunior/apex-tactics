"""
Low-Latency AI Decision Pipeline

Optimized pipeline for fast AI decision making while maintaining tactical quality.
Implements caching, prediction, and parallel processing to achieve <100ms decision times.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from collections import defaultdict, deque
import asyncio

from ai.mcp_tools import MCPToolRegistry, ToolResult
from ai.unit_ai_controller import ActionDecision, AIPersonality, AISkillLevel


class DecisionPriority(Enum):
    """Priority levels for AI decisions."""
    CRITICAL = 0    # Must complete within 50ms
    HIGH = 1        # Must complete within 100ms  
    NORMAL = 2      # Must complete within 200ms
    LOW = 3         # Can take up to 500ms


@dataclass
class CachedDecision:
    """Cached AI decision with metadata."""
    decision: ActionDecision
    context_hash: str
    timestamp: float
    confidence: float
    hit_count: int = 0
    
    def is_valid(self, max_age_seconds: float = 5.0) -> bool:
        """Check if cached decision is still valid."""
        return (time.time() - self.timestamp) < max_age_seconds


@dataclass
class PipelineMetrics:
    """Performance metrics for the decision pipeline."""
    total_decisions: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_decision_time_ms: float = 0.0
    timeout_count: int = 0
    parallel_efficiency: float = 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0


class LowLatencyDecisionPipeline:
    """
    Optimized AI decision pipeline for tactical RPG combat.
    
    Features:
    - Decision caching with context hashing
    - Parallel decision processing
    - Predictive pre-computation
    - Timeout-based fallback strategies
    - Performance monitoring and optimization
    """
    
    def __init__(self, tool_registry: MCPToolRegistry, max_workers: int = 4):
        self.tool_registry = tool_registry
        
        # Performance configuration
        self.max_workers = max_workers
        self.target_decision_time_ms = 100.0
        self.cache_max_size = 1000
        self.cache_max_age = 5.0
        
        # Decision caching
        self.decision_cache: Dict[str, CachedDecision] = {}
        self.context_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_lock = threading.RLock()
        
        # Parallel processing
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AI_Decision")
        self.pending_decisions: Dict[str, Future] = {}
        
        # Predictive processing
        self.prediction_queue = deque(maxlen=50)
        self.precomputed_decisions: Dict[str, ActionDecision] = {}
        
        # Performance tracking
        self.metrics = PipelineMetrics()
        self.decision_times = deque(maxlen=100)
        
        # Fallback strategies
        self.fallback_decisions = {
            'attack': ActionDecision(
                action_id='basic_attack',
                target_positions=[{'x': 0, 'y': 0}],
                priority='NORMAL',
                confidence=0.3,
                reasoning='Fallback: Basic attack',
                expected_outcome='Deal basic damage'
            )
        }
    
    def make_decision(self, unit_id: str, context: Dict[str, Any], 
                     priority: DecisionPriority = DecisionPriority.NORMAL,
                     timeout_ms: Optional[float] = None) -> Optional[ActionDecision]:
        """
        Make an AI decision with low-latency optimizations.
        
        Args:
            unit_id: ID of unit making decision
            context: Decision context data
            priority: Priority level for this decision
            timeout_ms: Override timeout (defaults based on priority)
            
        Returns:
            ActionDecision or None if decision failed
        """
        start_time = time.time()
        
        # Determine timeout based on priority
        if timeout_ms is None:
            timeout_ms = self._get_timeout_for_priority(priority)
        
        try:
            # Step 1: Check cache for recent similar decision
            cached_decision = self._check_decision_cache(unit_id, context)
            if cached_decision:
                self._update_metrics(start_time, cache_hit=True)
                print(f"🚀 Cache hit for {unit_id} decision ({(time.time() - start_time) * 1000:.1f}ms)")
                return cached_decision.decision
            
            # Step 2: Try to get precomputed decision
            precomputed = self._get_precomputed_decision(unit_id, context)
            if precomputed:
                self._update_metrics(start_time, cache_hit=False)
                print(f"⚡ Precomputed decision for {unit_id} ({(time.time() - start_time) * 1000:.1f}ms)")
                return precomputed
            
            # Step 3: Compute decision with timeout
            decision = self._compute_decision_with_timeout(unit_id, context, timeout_ms)
            
            if decision:
                # Cache the decision
                self._cache_decision(unit_id, context, decision)
                
                # Start predictive computation for future decisions
                self._queue_predictive_computation(unit_id, context)
            
            self._update_metrics(start_time, cache_hit=False)
            return decision
            
        except Exception as e:
            print(f"❌ Decision pipeline error for {unit_id}: {e}")
            self._update_metrics(start_time, cache_hit=False, timeout=True)
            return self._get_fallback_decision(context)
    
    def make_parallel_decisions(self, unit_contexts: List[Tuple[str, Dict[str, Any]]], 
                              priority: DecisionPriority = DecisionPriority.NORMAL) -> Dict[str, Optional[ActionDecision]]:
        """
        Make decisions for multiple units in parallel.
        
        Args:
            unit_contexts: List of (unit_id, context) tuples
            priority: Priority level for all decisions
            
        Returns:
            Dictionary mapping unit_id to ActionDecision
        """
        if not unit_contexts:
            return {}
        
        start_time = time.time()
        timeout_ms = self._get_timeout_for_priority(priority)
        
        # Submit all decision tasks
        future_to_unit = {}
        for unit_id, context in unit_contexts:
            future = self.executor.submit(self.make_decision, unit_id, context, priority, timeout_ms)
            future_to_unit[future] = unit_id
        
        # Collect results with timeout
        decisions = {}
        completed_count = 0
        
        for future in as_completed(future_to_unit, timeout=timeout_ms/1000):
            unit_id = future_to_unit[future]
            try:
                decision = future.result()
                decisions[unit_id] = decision
                completed_count += 1
            except Exception as e:
                print(f"❌ Parallel decision failed for {unit_id}: {e}")
                decisions[unit_id] = self._get_fallback_decision({})
        
        # Handle any remaining futures that didn't complete
        for future in future_to_unit:
            if not future.done():
                future.cancel()
                unit_id = future_to_unit[future]
                if unit_id not in decisions:
                    decisions[unit_id] = self._get_fallback_decision({})
        
        parallel_time = (time.time() - start_time) * 1000
        efficiency = completed_count / len(unit_contexts) if unit_contexts else 0
        
        self.metrics.parallel_efficiency = efficiency
        print(f"⚡ Parallel decisions completed: {completed_count}/{len(unit_contexts)} units in {parallel_time:.1f}ms")
        
        return decisions
    
    def precompute_decisions(self, unit_contexts: List[Tuple[str, Dict[str, Any]]]):
        """
        Precompute decisions during idle time for faster future access.
        
        Args:
            unit_contexts: List of (unit_id, context) tuples to precompute
        """
        for unit_id, context in unit_contexts:
            context_hash = self._hash_context(context)
            
            # Skip if already precomputed
            if context_hash in self.precomputed_decisions:
                continue
            
            # Queue for background computation
            self.prediction_queue.append((unit_id, context, context_hash))
        
        # Process prediction queue in background
        self._process_prediction_queue()
    
    def _check_decision_cache(self, unit_id: str, context: Dict[str, Any]) -> Optional[CachedDecision]:
        """Check cache for similar recent decision."""
        context_hash = self._hash_context(context)
        cache_key = f"{unit_id}_{context_hash}"
        
        with self.cache_lock:
            cached = self.decision_cache.get(cache_key)
            if cached and cached.is_valid(self.cache_max_age):
                cached.hit_count += 1
                return cached
            elif cached:
                # Remove expired entry
                del self.decision_cache[cache_key]
        
        return None
    
    def _get_precomputed_decision(self, unit_id: str, context: Dict[str, Any]) -> Optional[ActionDecision]:
        """Get precomputed decision if available."""
        context_hash = self._hash_context(context)
        return self.precomputed_decisions.get(context_hash)
    
    def _compute_decision_with_timeout(self, unit_id: str, context: Dict[str, Any], 
                                     timeout_ms: float) -> Optional[ActionDecision]:
        """Compute decision with timeout protection."""
        try:
            # Create a simplified unit controller for this decision
            from .unit_ai_controller import UnitAIController
            
            controller = UnitAIController(
                unit_id=unit_id,
                tool_registry=self.tool_registry,
                personality=AIPersonality.BALANCED,
                skill_level=AISkillLevel.STRATEGIC
            )
            
            # Submit decision task with timeout
            future = self.executor.submit(controller.make_decision, None, timeout_ms)
            decision = future.result(timeout=timeout_ms/1000)
            
            return decision
            
        except Exception as e:
            print(f"⚠️ Decision computation failed for {unit_id}: {e}")
            return None
    
    def _cache_decision(self, unit_id: str, context: Dict[str, Any], decision: ActionDecision):
        """Cache a decision for future use."""
        context_hash = self._hash_context(context)
        cache_key = f"{unit_id}_{context_hash}"
        
        cached_decision = CachedDecision(
            decision=decision,
            context_hash=context_hash,
            timestamp=time.time(),
            confidence=decision.confidence
        )
        
        with self.cache_lock:
            # Add to cache
            self.decision_cache[cache_key] = cached_decision
            
            # Enforce cache size limit
            if len(self.decision_cache) > self.cache_max_size:
                # Remove oldest entries
                oldest_keys = sorted(
                    self.decision_cache.keys(),
                    key=lambda k: self.decision_cache[k].timestamp
                )
                for key in oldest_keys[:len(self.decision_cache) - self.cache_max_size]:
                    del self.decision_cache[key]
    
    def _queue_predictive_computation(self, unit_id: str, context: Dict[str, Any]):
        """Queue predictive computation for future decisions."""
        # Predict likely next contexts (simplified)
        predicted_contexts = self._predict_future_contexts(unit_id, context)
        
        for predicted_context in predicted_contexts:
            context_hash = self._hash_context(predicted_context)
            self.prediction_queue.append((unit_id, predicted_context, context_hash))
    
    def _predict_future_contexts(self, unit_id: str, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predict likely future decision contexts."""
        # Simplified prediction - in full implementation would use more sophisticated logic
        predicted = []
        
        # Predict context after taking damage
        if 'unit_details' in current_context:
            unit_details = current_context['unit_details'].copy()
            if 'stats' in unit_details:
                stats = unit_details['stats'].copy()
                stats['hp'] = max(0, stats['hp'] - 20)  # Predict taking damage
                
                predicted_context = current_context.copy()
                predicted_context['unit_details'] = unit_details
                predicted.append(predicted_context)
        
        return predicted[:3]  # Limit predictions
    
    def _process_prediction_queue(self):
        """Process prediction queue in background."""
        if not self.prediction_queue:
            return
        
        # Process a few items from queue
        for _ in range(min(3, len(self.prediction_queue))):
            if not self.prediction_queue:
                break
            
            unit_id, context, context_hash = self.prediction_queue.popleft()
            
            # Skip if already computed
            if context_hash in self.precomputed_decisions:
                continue
            
            # Compute decision in background
            try:
                decision = self._compute_decision_with_timeout(unit_id, context, 200.0)
                if decision:
                    self.precomputed_decisions[context_hash] = decision
                    
                    # Limit precomputed cache size
                    if len(self.precomputed_decisions) > 100:
                        # Remove oldest (simplified)
                        oldest_key = next(iter(self.precomputed_decisions))
                        del self.precomputed_decisions[oldest_key]
            
            except Exception as e:
                print(f"⚠️ Predictive computation failed: {e}")
    
    def _get_fallback_decision(self, context: Dict[str, Any]) -> ActionDecision:
        """Get fallback decision when normal processing fails."""
        # Use simple fallback strategy
        return self.fallback_decisions['attack']
    
    def _hash_context(self, context: Dict[str, Any]) -> str:
        """Create hash of decision context for caching."""
        # Simplified context hashing - in full implementation would be more sophisticated
        key_parts = []
        
        if 'unit_details' in context and 'stats' in context['unit_details']:
            stats = context['unit_details']['stats']
            key_parts.append(f"hp_{stats.get('hp', 0)}")
            key_parts.append(f"mp_{stats.get('mp', 0)}")
        
        if 'battlefield_state' in context and 'units' in context['battlefield_state']:
            units = context['battlefield_state']['units']
            alive_enemies = len([u for u in units if u.get('team') == 'player' and u.get('alive')])
            key_parts.append(f"enemies_{alive_enemies}")
        
        return "_".join(key_parts)
    
    def _get_timeout_for_priority(self, priority: DecisionPriority) -> float:
        """Get timeout in milliseconds for given priority level."""
        timeouts = {
            DecisionPriority.CRITICAL: 50.0,
            DecisionPriority.HIGH: 100.0,
            DecisionPriority.NORMAL: 200.0,
            DecisionPriority.LOW: 500.0
        }
        return timeouts.get(priority, 200.0)
    
    def _update_metrics(self, start_time: float, cache_hit: bool = False, timeout: bool = False):
        """Update pipeline performance metrics."""
        decision_time = (time.time() - start_time) * 1000
        self.decision_times.append(decision_time)
        
        self.metrics.total_decisions += 1
        
        if cache_hit:
            self.metrics.cache_hits += 1
        else:
            self.metrics.cache_misses += 1
        
        if timeout:
            self.metrics.timeout_count += 1
        
        # Update average decision time
        if self.decision_times:
            self.metrics.average_decision_time_ms = sum(self.decision_times) / len(self.decision_times)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            'metrics': {
                'total_decisions': self.metrics.total_decisions,
                'cache_hit_rate': self.metrics.cache_hit_rate,
                'average_decision_time_ms': self.metrics.average_decision_time_ms,
                'timeout_rate': (self.metrics.timeout_count / max(1, self.metrics.total_decisions)) * 100,
                'parallel_efficiency': self.metrics.parallel_efficiency * 100
            },
            'cache_status': {
                'cache_size': len(self.decision_cache),
                'precomputed_decisions': len(self.precomputed_decisions),
                'prediction_queue_size': len(self.prediction_queue)
            },
            'performance_target': {
                'target_time_ms': self.target_decision_time_ms,
                'meeting_target': self.metrics.average_decision_time_ms <= self.target_decision_time_ms
            }
        }
    
    def optimize_performance(self):
        """Optimize pipeline performance based on metrics."""
        report = self.get_performance_report()
        
        # Adjust cache size if hit rate is low
        if report['metrics']['cache_hit_rate'] < 20:
            self.cache_max_size = min(2000, self.cache_max_size * 1.5)
            print(f"📈 Increased cache size to {self.cache_max_size}")
        
        # Adjust timeouts if too many timeouts
        if report['metrics']['timeout_rate'] > 10:
            self.target_decision_time_ms *= 1.2
            print(f"⏱️ Increased target decision time to {self.target_decision_time_ms}ms")
        
        # Clear old precomputed decisions if cache is full
        if len(self.precomputed_decisions) > 80:
            # Keep only the 50 most recent
            keys_to_remove = list(self.precomputed_decisions.keys())[50:]
            for key in keys_to_remove:
                del self.precomputed_decisions[key]
            print(f"🧹 Cleaned precomputed cache: {len(keys_to_remove)} entries removed")
    
    def shutdown(self):
        """Shutdown the decision pipeline."""
        self.executor.shutdown(wait=True)
        self.decision_cache.clear()
        self.precomputed_decisions.clear()
        self.prediction_queue.clear()
        print("🔄 Low-latency decision pipeline shut down")