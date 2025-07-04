"""
Unit AI Controller

Individual AI controller for single units. Handles unit-specific decision making,
action planning, and execution within the broader tactical context provided by
the orchestration agent.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import time

from ai.mcp_tools import MCPToolRegistry, ToolResult


class AIPersonality(Enum):
    """AI personality types affecting decision making."""
    AGGRESSIVE = "aggressive"       # Favors offensive actions
    DEFENSIVE = "defensive"         # Prioritizes survival and support
    BALANCED = "balanced"          # Balanced approach
    TACTICAL = "tactical"          # Focuses on optimal positioning
    BERSERKER = "berserker"        # High-risk, high-reward actions


class AISkillLevel(Enum):
    """AI skill levels from design document."""
    SCRIPTED = "scripted"          # Basic scripted behavior
    STRATEGIC = "strategic"        # Simple tactical decisions
    ADAPTIVE = "adaptive"          # Adapts to player patterns
    LEARNING = "learning"          # Learns and improves over time


@dataclass
class DecisionContext:
    """Context information for AI decision making."""
    unit_id: str
    battlefield_state: Dict[str, Any]
    unit_details: Dict[str, Any]
    available_actions: List[Dict[str, Any]]
    threat_assessment: Dict[str, Any]
    battle_plan_assignment: Optional[str] = None
    time_pressure: bool = False
    previous_actions: List[str] = None


@dataclass
class ActionDecision:
    """Represents an AI decision about what action to take."""
    action_id: str
    target_positions: List[Dict[str, int]]
    priority: str
    confidence: float
    reasoning: str
    expected_outcome: str
    alternative_actions: List[str] = None


class UnitAIController:
    """
    AI controller for individual units.
    
    Handles unit-specific tactical decisions within the context of the
    overall battle plan provided by the orchestration agent.
    """
    
    def __init__(self, unit_id: str, tool_registry: MCPToolRegistry,
                 personality: AIPersonality = AIPersonality.BALANCED,
                 skill_level: AISkillLevel = AISkillLevel.STRATEGIC):
        self.unit_id = unit_id
        self.tool_registry = tool_registry
        self.personality = personality
        self.skill_level = skill_level
        
        # Decision history for learning
        self.decision_history: List[ActionDecision] = []
        self.performance_metrics = {
            'decisions_made': 0,
            'successful_actions': 0,
            'average_decision_time_ms': 0.0,
            'damage_dealt': 0,
            'damage_taken': 0,
            'survival_turns': 0
        }
        
        # Personality modifiers
        self.personality_modifiers = self._get_personality_modifiers()
        
        # Learning patterns (for ADAPTIVE and LEARNING skill levels)
        self.learned_patterns = {
            'effective_actions': {},
            'target_preferences': {},
            'positioning_patterns': {},
            'player_behavior': {}
        }
    
    def _get_personality_modifiers(self) -> Dict[str, float]:
        """Get personality-specific decision modifiers."""
        modifiers = {
            AIPersonality.AGGRESSIVE: {
                'attack_preference': 2.0,
                'defense_preference': 0.5,
                'risk_tolerance': 1.5,
                'support_preference': 0.3
            },
            AIPersonality.DEFENSIVE: {
                'attack_preference': 0.7,
                'defense_preference': 2.0,
                'risk_tolerance': 0.3,
                'support_preference': 1.5
            },
            AIPersonality.BALANCED: {
                'attack_preference': 1.0,
                'defense_preference': 1.0,
                'risk_tolerance': 1.0,
                'support_preference': 1.0
            },
            AIPersonality.TACTICAL: {
                'attack_preference': 1.2,
                'defense_preference': 1.3,
                'risk_tolerance': 0.8,
                'support_preference': 1.1
            },
            AIPersonality.BERSERKER: {
                'attack_preference': 3.0,
                'defense_preference': 0.2,
                'risk_tolerance': 2.5,
                'support_preference': 0.1
            }
        }
        
        return modifiers.get(self.personality, modifiers[AIPersonality.BALANCED])
    
    def make_decision(self, assignment: Optional[str] = None,
                     time_limit_ms: float = 100.0) -> Optional[ActionDecision]:
        """
        Make a tactical decision for this unit.
        
        Args:
            assignment: Assignment from battle plan (e.g., "eliminate_player1")
            time_limit_ms: Time limit for decision making
            
        Returns:
            ActionDecision or None if no valid decision possible
        """
        start_time = time.time()
        
        try:
            # Gather decision context
            context = self._gather_decision_context(assignment)
            if not context:
                return None
            
            # Make decision based on skill level
            decision = self._make_skill_based_decision(context, time_limit_ms)
            
            # Record decision
            if decision:
                self.decision_history.append(decision)
                self._update_performance_metrics(time.time() - start_time)
            
            return decision
            
        except Exception as e:
            print(f"❌ AI decision error for {self.unit_id}: {e}")
            return None
    
    def _gather_decision_context(self, assignment: Optional[str]) -> Optional[DecisionContext]:
        """Gather all information needed for decision making."""
        # Get unit details
        unit_result = self.tool_registry.execute_tool('get_unit_details', unit_id=self.unit_id)
        if not unit_result.success:
            return None
        
        # Get battlefield state
        battlefield_result = self.tool_registry.execute_tool('get_battlefield_state')
        if not battlefield_result.success:
            return None
        
        # Get threat assessment
        threat_result = self.tool_registry.execute_tool('calculate_threat_assessment', unit_id=self.unit_id)
        
        context = DecisionContext(
            unit_id=self.unit_id,
            battlefield_state=battlefield_result.data,
            unit_details=unit_result.data,
            available_actions=unit_result.data.get('available_actions', []),
            threat_assessment=threat_result.data if threat_result.success else {},
            battle_plan_assignment=assignment,
            previous_actions=[d.action_id for d in self.decision_history[-3:]]  # Last 3 actions
        )
        
        return context
    
    def _make_skill_based_decision(self, context: DecisionContext, 
                                 time_limit_ms: float) -> Optional[ActionDecision]:
        """Make decision based on AI skill level."""
        if self.skill_level == AISkillLevel.SCRIPTED:
            return self._make_scripted_decision(context)
        elif self.skill_level == AISkillLevel.STRATEGIC:
            return self._make_strategic_decision(context)
        elif self.skill_level == AISkillLevel.ADAPTIVE:
            return self._make_adaptive_decision(context)
        elif self.skill_level == AISkillLevel.LEARNING:
            return self._make_learning_decision(context)
        else:
            return self._make_strategic_decision(context)  # Default
    
    def _make_scripted_decision(self, context: DecisionContext) -> Optional[ActionDecision]:
        """Simple scripted behavior - attack nearest enemy."""
        # Find first attack action
        attack_action = None
        for action in context.available_actions:
            if action['type'] == 'Attack':
                attack_action = action
                break
        
        if not attack_action:
            return None
        
        # Target nearest enemy (simplified)
        target_pos = self._find_nearest_enemy_position(context)
        if not target_pos:
            return None
        
        return ActionDecision(
            action_id=attack_action['id'],
            target_positions=[target_pos],
            priority='NORMAL',
            confidence=0.6,
            reasoning='Scripted: Attack nearest enemy',
            expected_outcome='Deal damage to enemy'
        )
    
    def _make_strategic_decision(self, context: DecisionContext) -> Optional[ActionDecision]:
        """Strategic decision making with basic tactics."""
        # Evaluate all available actions
        action_evaluations = []
        
        for action in context.available_actions:
            evaluation = self._evaluate_action_strategically(action, context)
            action_evaluations.append((action, evaluation))
        
        # Sort by tactical value
        action_evaluations.sort(key=lambda x: x[1]['tactical_value'], reverse=True)
        
        if not action_evaluations:
            return None
        
        best_action, best_eval = action_evaluations[0]
        
        # Apply personality modifiers
        confidence = best_eval['base_confidence'] * self._get_personality_modifier_for_action(best_action)
        
        # Determine target
        target_pos = self._select_strategic_target(best_action, context)
        if not target_pos:
            return None
        
        return ActionDecision(
            action_id=best_action['id'],
            target_positions=[target_pos],
            priority=best_eval['suggested_priority'],
            confidence=min(1.0, confidence),
            reasoning=f"Strategic: {best_eval['reasoning']}",
            expected_outcome=best_eval['expected_outcome'],
            alternative_actions=[ae[0]['id'] for ae in action_evaluations[1:3]]
        )
    
    def _make_adaptive_decision(self, context: DecisionContext) -> Optional[ActionDecision]:
        """Adaptive decision making that learns from patterns."""
        # Start with strategic decision
        strategic_decision = self._make_strategic_decision(context)
        if not strategic_decision:
            return None
        
        # Adapt based on learned patterns
        adapted_decision = self._adapt_decision_based_on_patterns(strategic_decision, context)
        
        # Update learned patterns
        self._update_learned_patterns(context)
        
        return adapted_decision
    
    def _make_learning_decision(self, context: DecisionContext) -> Optional[ActionDecision]:
        """Advanced learning decision making."""
        # Use adaptive decision as base
        decision = self._make_adaptive_decision(context)
        if not decision:
            return None
        
        # Apply advanced learning optimizations
        optimized_decision = self._apply_learning_optimizations(decision, context)
        
        return optimized_decision
    
    def _evaluate_action_strategically(self, action: Dict[str, Any], 
                                     context: DecisionContext) -> Dict[str, Any]:
        """Evaluate an action's strategic value."""
        base_value = 1.0
        reasoning = []
        
        action_type = action.get('type', 'Unknown')
        
        # Base tactical value by type
        type_values = {
            'Attack': 1.5,
            'Magic': 2.0,
            'Spirit': 1.8,
            'Move': 0.8,
            'Inventory': 1.2
        }
        base_value = type_values.get(action_type, 1.0)
        
        # Modify based on unit health
        unit_hp_percent = context.unit_details['stats']['hp'] / context.unit_details['stats']['max_hp']
        if unit_hp_percent < 0.3:
            # Low health - prefer healing or defensive actions
            if 'heal' in action['name'].lower() or action_type == 'Spirit':
                base_value *= 2.0
                reasoning.append("Low health - prioritize healing")
            elif action_type == 'Attack':
                base_value *= 0.5
                reasoning.append("Low health - avoid risky attacks")
        
        # Modify based on resources
        unit_mp_percent = context.unit_details['stats']['mp'] / max(context.unit_details['stats']['max_mp'], 1)
        mp_cost = action.get('costs', {}).get('mp_cost', 0)
        if mp_cost > 0 and unit_mp_percent < 0.3:
            base_value *= 0.3
            reasoning.append("Low MP - avoid expensive spells")
        
        # Battle plan assignment modifier
        if context.battle_plan_assignment:
            if context.battle_plan_assignment.startswith('eliminate_') and action_type in ['Attack', 'Magic']:
                base_value *= 1.5
                reasoning.append("Supports elimination assignment")
            elif context.battle_plan_assignment == 'support_allies' and action_type in ['Spirit', 'Inventory']:
                base_value *= 1.3
                reasoning.append("Supports ally support assignment")
        
        # Determine priority
        if base_value > 2.5:
            priority = 'HIGH'
        elif base_value > 1.5:
            priority = 'NORMAL'
        else:
            priority = 'LOW'
        
        return {
            'tactical_value': base_value,
            'base_confidence': min(0.9, base_value / 3.0),
            'reasoning': '; '.join(reasoning) or 'Basic tactical evaluation',
            'expected_outcome': f'Execute {action["name"]} with value {base_value:.1f}',
            'suggested_priority': priority
        }
    
    def _get_personality_modifier_for_action(self, action: Dict[str, Any]) -> float:
        """Get personality modifier for a specific action."""
        action_type = action.get('type', 'Unknown')
        modifiers = self.personality_modifiers
        
        if action_type in ['Attack', 'Magic']:
            return modifiers.get('attack_preference', 1.0)
        elif action_type == 'Spirit' or 'heal' in action.get('name', '').lower():
            return modifiers.get('support_preference', 1.0)
        elif action_type == 'Move':
            return modifiers.get('defense_preference', 1.0)
        else:
            return 1.0
    
    def _select_strategic_target(self, action: Dict[str, Any], 
                               context: DecisionContext) -> Optional[Dict[str, int]]:
        """Select target position for an action."""
        action_type = action.get('type', 'Unknown')
        
        if action_type in ['Attack', 'Magic']:
            # Target enemy units
            return self._find_best_enemy_target(context)
        elif action_type == 'Spirit' or 'heal' in action.get('name', '').lower():
            # Target self or allies
            return self._find_best_ally_target(context)
        else:
            # Default to self position
            return {
                'x': context.unit_details['position']['x'],
                'y': context.unit_details['position']['y']
            }
    
    def _find_nearest_enemy_position(self, context: DecisionContext) -> Optional[Dict[str, int]]:
        """Find position of nearest enemy unit."""
        my_pos = context.unit_details['position']
        enemy_units = [u for u in context.battlefield_state['units'] if u['team'] == 'player']
        
        if not enemy_units:
            return None
        
        nearest_enemy = min(enemy_units, 
                          key=lambda u: abs(u['position']['x'] - my_pos['x']) + 
                                       abs(u['position']['y'] - my_pos['y']))
        
        return nearest_enemy['position']
    
    def _find_best_enemy_target(self, context: DecisionContext) -> Optional[Dict[str, int]]:
        """Find best enemy target based on threat and opportunity."""
        enemy_units = [u for u in context.battlefield_state['units'] 
                      if u['team'] == 'player' and u['alive']]
        
        if not enemy_units:
            return None
        
        # Evaluate each enemy
        target_scores = []
        for enemy in enemy_units:
            score = 0.0
            
            # Prefer low health enemies (easier kills)
            hp_percent = enemy['hp'] / enemy['max_hp']
            if hp_percent < 0.3:
                score += 3.0
            elif hp_percent < 0.6:
                score += 1.5
            
            # Prefer high-threat enemies (from battle plan)
            if context.battle_plan_assignment and context.battle_plan_assignment.startswith('eliminate_'):
                target_id = context.battle_plan_assignment.replace('eliminate_', '')
                if enemy['id'] == target_id:
                    score += 2.0
            
            # Distance consideration (prefer closer targets)
            my_pos = context.unit_details['position']
            distance = abs(enemy['position']['x'] - my_pos['x']) + abs(enemy['position']['y'] - my_pos['y'])
            score += max(0, 5 - distance) * 0.2
            
            target_scores.append((enemy, score))
        
        # Select best target
        if target_scores:
            best_enemy = max(target_scores, key=lambda x: x[1])[0]
            return best_enemy['position']
        
        return None
    
    def _find_best_ally_target(self, context: DecisionContext) -> Optional[Dict[str, int]]:
        """Find best ally target for support actions."""
        ally_units = [u for u in context.battlefield_state['units'] 
                     if u['team'] == 'enemy' and u['alive'] and u['id'] != self.unit_id]
        
        # Include self as potential target
        self_unit = next((u for u in context.battlefield_state['units'] if u['id'] == self.unit_id), None)
        if self_unit:
            ally_units.append(self_unit)
        
        if not ally_units:
            return None
        
        # Prefer most damaged allies
        best_ally = min(ally_units, key=lambda u: u['hp'] / u['max_hp'])
        return best_ally['position']
    
    def _adapt_decision_based_on_patterns(self, decision: ActionDecision, 
                                        context: DecisionContext) -> ActionDecision:
        """Adapt decision based on learned patterns."""
        # For now, return original decision
        # In full implementation, this would analyze learned patterns
        # and modify the decision accordingly
        return decision
    
    def _update_learned_patterns(self, context: DecisionContext):
        """Update learned behavior patterns."""
        # Placeholder for pattern learning
        # Would track effective actions, successful strategies, etc.
        pass
    
    def _apply_learning_optimizations(self, decision: ActionDecision, 
                                    context: DecisionContext) -> ActionDecision:
        """Apply advanced learning optimizations."""
        # Placeholder for advanced learning
        # Would use more sophisticated ML techniques
        return decision
    
    def _update_performance_metrics(self, decision_time: float):
        """Update performance tracking metrics."""
        self.performance_metrics['decisions_made'] += 1
        decision_time_ms = decision_time * 1000
        
        # Update average decision time
        current_avg = self.performance_metrics['average_decision_time_ms']
        total_decisions = self.performance_metrics['decisions_made']
        
        new_avg = ((current_avg * (total_decisions - 1)) + decision_time_ms) / total_decisions
        self.performance_metrics['average_decision_time_ms'] = new_avg
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for this AI controller."""
        success_rate = 0.0
        if self.performance_metrics['decisions_made'] > 0:
            success_rate = self.performance_metrics['successful_actions'] / self.performance_metrics['decisions_made']
        
        return {
            'unit_id': self.unit_id,
            'personality': self.personality.value,
            'skill_level': self.skill_level.value,
            'decisions_made': self.performance_metrics['decisions_made'],
            'success_rate': success_rate,
            'average_decision_time_ms': self.performance_metrics['average_decision_time_ms'],
            'recent_actions': [d.action_id for d in self.decision_history[-5:]],
            'damage_dealt': self.performance_metrics['damage_dealt'],
            'survival_turns': self.performance_metrics['survival_turns']
        }