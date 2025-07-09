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

try:
    from ai.mcp_tools import MCPToolRegistry, ToolResult
except ImportError:
    from ai.simple_mcp_tools import SimpleMCPToolRegistry as MCPToolRegistry, ToolResult


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
            print(f"🧠 AI Agent {self.unit_id} making decision...")
            
            # Gather decision context
            context = self._gather_decision_context(assignment)
            if not context:
                print(f"❌ AI Agent {self.unit_id}: Failed to gather decision context")
                return None
            
            print(f"🔍 AI Agent {self.unit_id}: Context gathered - {len(context.available_actions)} actions available")
            print(f"🔍 Available action types: {[action.get('type', 'unknown') for action in context.available_actions]}")
            
            # Make decision based on skill level
            decision = self._make_skill_based_decision(context, time_limit_ms)
            
            if decision:
                print(f"✅ AI Agent {self.unit_id}: Decision made - {decision.action_id}")
            else:
                print(f"❌ AI Agent {self.unit_id}: No valid decision could be made")
            
            # Record decision
            if decision:
                self.decision_history.append(decision)
                self._update_performance_metrics(time.time() - start_time)
            
            return decision
            
        except Exception as e:
            print(f"❌ AI decision error for {self.unit_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _gather_decision_context(self, assignment: Optional[str]) -> Optional[DecisionContext]:
        """Gather all information needed for decision making."""
        print(f"📊 AI Agent {self.unit_id}: Gathering decision context...")
        
        # Get tactical analysis (new comprehensive approach)
        tactical_result = self.tool_registry.execute_tool('get_tactical_analysis', unit_id=self.unit_id)
        if not tactical_result.success:
            print(f"❌ Failed to get tactical analysis: {tactical_result.error_message}")
            return None
        print(f"✅ Tactical analysis retrieved successfully")
        
        tactical_data = tactical_result.data
        
        # Get unit details
        unit_result = self.tool_registry.execute_tool('get_unit_details', unit_id=self.unit_id)
        if not unit_result.success:
            print(f"❌ Failed to get unit details: {unit_result.error_message}")
            return None
        print(f"✅ Unit details retrieved successfully")
        
        # Convert tactical analysis to available actions format
        available_actions = self._convert_tactical_to_actions(tactical_data)
        print(f"✅ Converted tactical analysis to {len(available_actions)} available actions")
        
        # Create simplified battlefield state from tactical data
        battlefield_state = {
            'units': [{'name': enemy['name'], 'position': enemy['position'], 'hp': enemy['hp'], 'max_hp': enemy['max_hp']} 
                     for enemy in tactical_data.get('enemy_units', [])],
            'current_unit_position': tactical_data.get('unit_position', {}),
            'current_ap': tactical_data.get('current_ap', 0),
            'optimal_combination': tactical_data.get('optimal_combination')
        }
        
        context = DecisionContext(
            unit_id=self.unit_id,
            battlefield_state=battlefield_state,
            unit_details=unit_result.data,
            available_actions=available_actions,
            threat_assessment={},  # Not needed with new approach
            battle_plan_assignment=assignment,
            previous_actions=[d.action_id for d in self.decision_history[-3:]]  # Last 3 actions
        )
        
        return context
    
    def _convert_tactical_to_actions(self, tactical_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert tactical analysis to available actions format."""
        actions = []
        
        try:
            move_combinations = tactical_data.get('move_action_combinations', [])
            
            # Convert each move-action combination to an action
            for combination in move_combinations:
                move_to = combination.get('move_to', {})
                best_action = combination.get('best_action')
                
                if best_action:
                    action = {
                        'type': best_action.get('action_type', 'unknown'),
                        'move_to': move_to,
                        'target': best_action.get('target'),
                        'target_position': best_action.get('target_position'),
                        'ap_cost': combination.get('move_ap_cost', 0) + best_action.get('ap_cost', 0),
                        'damage': best_action.get('damage', 0),
                        'can_kill': best_action.get('can_kill', False),
                        'total_damage': best_action.get('total_damage', 0),
                        'description': f"Move to ({move_to.get('x', 0)}, {move_to.get('y', 0)}) and {best_action.get('action_type', 'act')} {best_action.get('target', 'target')} for {best_action.get('damage', 0)} damage"
                    }
                    
                    # Add talent-specific information if it's a talent action
                    if best_action.get('action_type') == 'talent':
                        action['talent_id'] = best_action.get('talent_id')
                        action['talent_name'] = best_action.get('talent_name')
                        action['slot_index'] = best_action.get('slot_index')
                    
                    actions.append(action)
            
            # Sort by total damage (highest first)
            actions.sort(key=lambda x: x.get('total_damage', 0), reverse=True)
            
        except Exception as e:
            print(f"⚠️ Error converting tactical to actions: {e}")
        
        return actions
    
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
            if action['type'].lower() == 'attack':
                attack_action = action
                break
        
        if not attack_action:
            return None
        
        # Target nearest enemy (simplified)
        target_pos = self._find_nearest_enemy_position(context)
        if not target_pos:
            return None
        
        return ActionDecision(
            action_id=attack_action['type'],  # Use 'type' as action_id for our simple system
            target_positions=[target_pos],  # List of target positions
            priority='NORMAL',
            confidence=0.6,
            reasoning='Scripted: Attack nearest enemy',
            expected_outcome='Deal damage to enemy'
        )
    
    def _make_strategic_decision(self, context: DecisionContext) -> Optional[ActionDecision]:
        """Strategic decision making with basic tactics."""
        # With new tactical analysis, actions are pre-evaluated
        if not context.available_actions:
            return None
        
        # Get the best action (first in sorted list)
        best_action = context.available_actions[0]
        
        # Create decision from the pre-calculated action
        move_to = best_action.get('move_to', {})
        target_position = best_action.get('target_position', {})
        
        # Determine action type for execution
        action_type = best_action.get('type', 'unknown')
        if action_type == 'talent':
            action_id = best_action.get('talent_id', 'unknown_talent')
        else:
            action_id = action_type
        
        # Calculate confidence based on damage potential
        damage = best_action.get('damage', 0)
        confidence = min(1.0, max(0.3, damage / 20.0))  # Scale confidence with damage
        
        # Enhance confidence if this can kill
        if best_action.get('can_kill', False):
            confidence = min(1.0, confidence + 0.3)
        
        decision = ActionDecision(
            action_id=action_id,
            target_positions=[target_position] if target_position else [],
            priority='HIGH' if best_action.get('can_kill', False) else 'NORMAL',
            confidence=confidence,
            reasoning=f"Tactical: {best_action.get('description', 'Pre-calculated optimal action')}",
            expected_outcome=f"Deal {damage} damage to {best_action.get('target', 'target')}",
            alternative_actions=[action.get('type', 'unknown') for action in context.available_actions[1:3]]
        )
        
        # Add move information to the decision object
        decision.move_to = move_to
        
        return decision
    
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
        
        action_type = action.get('type', 'unknown').lower()
        
        # Base tactical value by type
        type_values = {
            'attack': 1.5,
            'ability': 2.0,
            'move': 0.8
        }
        base_value = type_values.get(action_type, 1.0)
        
        # Modify based on unit health
        unit_hp = context.unit_details.get('hp', 100)
        unit_max_hp = context.unit_details.get('max_hp', 100)
        unit_hp_percent = unit_hp / max(unit_max_hp, 1)
        if unit_hp_percent < 0.3:
            # Low health - prefer healing or defensive actions
            if 'heal' in action.get('description', '').lower() or action_type == 'ability':
                base_value *= 2.0
                reasoning.append("Low health - prioritize healing")
            elif action_type == 'attack':
                base_value *= 0.5
                reasoning.append("Low health - avoid risky attacks")
        
        # Modify based on resources (AP for now, since MP not in simple structure)
        unit_ap = context.unit_details.get('ap', 0)
        unit_max_ap = context.unit_details.get('max_ap', 1)
        unit_ap_percent = unit_ap / max(unit_max_ap, 1)
        ap_cost = action.get('ap_cost', 1)
        if ap_cost > unit_ap:
            base_value *= 0.1  # Can't afford this action
            reasoning.append("Insufficient AP - action not viable")
        
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
            'expected_outcome': f'Execute {action_type} action with value {base_value:.1f}',
            'suggested_priority': priority
        }
    
    def _get_personality_modifier_for_action(self, action: Dict[str, Any]) -> float:
        """Get personality modifier for a specific action."""
        action_type = action.get('type', 'unknown').lower()
        modifiers = self.personality_modifiers
        
        if action_type in ['attack', 'ability']:
            return modifiers.get('attack_preference', 1.0)
        elif action_type == 'move':
            return modifiers.get('defense_preference', 1.0)
        else:
            return 1.0
    
    def _select_strategic_target(self, action: Dict[str, Any], 
                               context: DecisionContext) -> Optional[Dict[str, int]]:
        """Select target position for an action."""
        action_type = action.get('type', 'unknown').lower()
        
        if action_type in ['attack', 'ability']:
            # Target enemy units
            return self._find_best_enemy_target(context)
        elif action_type == 'move':
            # Find good position to move to
            return self._find_nearest_enemy_position(context)
        else:
            # Default to self position
            return {
                'x': context.unit_details.get('x', 0),
                'y': context.unit_details.get('y', 0)
            }
    
    def _find_nearest_enemy_position(self, context: DecisionContext) -> Optional[Dict[str, int]]:
        """Find position of nearest enemy unit."""
        my_x = context.unit_details.get('x', 0)
        my_y = context.unit_details.get('y', 0)
        # Find enemy units (player units are enemies of AI units)
        enemy_units = [u for u in context.battlefield_state['units'] if not u.get('is_enemy', True)]
        
        if not enemy_units:
            return None
        
        nearest_enemy = min(enemy_units, 
                          key=lambda u: abs(u['x'] - my_x) + abs(u['y'] - my_y))
        
        return {'x': nearest_enemy['x'], 'y': nearest_enemy['y']}
    
    def _find_best_enemy_target(self, context: DecisionContext) -> Optional[Dict[str, int]]:
        """Find best enemy target based on threat and opportunity."""
        enemy_units = [u for u in context.battlefield_state['units'] 
                      if not u.get('is_enemy', True) and u.get('alive', True)]
        
        if not enemy_units:
            return None
        
        # Get unit's current position and ranges
        my_x = context.unit_details.get('x', 0)
        my_y = context.unit_details.get('y', 0)
        attack_range = context.unit_details.get('attack_range', 1)
        magic_range = context.unit_details.get('magic_range', 2)
        
        # Filter enemies by range (prefer those within attack range, then magic range)
        reachable_enemies = []
        for enemy in enemy_units:
            distance = abs(enemy['x'] - my_x) + abs(enemy['y'] - my_y)
            if distance <= attack_range:
                reachable_enemies.append((enemy, distance, 'attack'))
            elif distance <= magic_range:
                reachable_enemies.append((enemy, distance, 'magic'))
        
        if not reachable_enemies:
            # No enemies in range, find closest one for movement
            print(f"🔍 No enemies in range (attack: {attack_range}, magic: {magic_range}), finding closest")
            nearest_enemy = min(enemy_units, 
                              key=lambda u: abs(u['x'] - my_x) + abs(u['y'] - my_y))
            return {'x': nearest_enemy['x'], 'y': nearest_enemy['y']}
        
        # Evaluate reachable enemies
        target_scores = []
        for enemy, distance, range_type in reachable_enemies:
            score = 0.0
            
            # Range type preference (prefer attack range over magic range)
            if range_type == 'attack':
                score += 2.0
            elif range_type == 'magic':
                score += 1.0
            
            # Prefer low health enemies (easier kills)
            hp_percent = enemy['hp'] / max(enemy['max_hp'], 1)
            if hp_percent < 0.3:
                score += 3.0
            elif hp_percent < 0.6:
                score += 1.5
            
            # Distance consideration (prefer closer targets)
            score += max(0, 5 - distance) * 0.2
            
            target_scores.append((enemy, score))
        
        # Select best target
        if target_scores:
            best_enemy = max(target_scores, key=lambda x: x[1])[0]
            print(f"🎯 Selected target: ({best_enemy['x']}, {best_enemy['y']}) - {best_enemy['name']}")
            return {'x': best_enemy['x'], 'y': best_enemy['y']}
        
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
    
    def execute_turn(self, unit, game_state):
        """Execute a complete turn for an AI-controlled unit using only MCP tools."""
        try:
            print(f"🤖 AI Agent {unit.name} starting turn execution...")
            
            # Log available MCP tools for debugging
            print(f"🔧 Available MCP tools: {list(self.tool_registry.tools.keys())}")
            
            # Test basic tool connectivity
            game_state_result = self.tool_registry.execute_tool('get_game_state')
            if game_state_result.success:
                print(f"✅ Game state retrieved: {len(game_state_result.data.get('units', []))} units on battlefield")
            else:
                print(f"❌ Failed to get game state: {game_state_result.error_message}")
            
            unit_details_result = self.tool_registry.execute_tool('get_unit_details', unit_id=self.unit_id)
            if unit_details_result.success:
                unit_data = unit_details_result.data
                print(f"✅ Unit details retrieved: {unit_data.get('name')} at ({unit_data.get('x')}, {unit_data.get('y')}) with {unit_data.get('ap')} AP")
            else:
                print(f"❌ Failed to get unit details: {unit_details_result.error_message}")
            
            available_actions_result = self.tool_registry.execute_tool('get_available_actions', unit_id=self.unit_id)
            if available_actions_result.success:
                actions = available_actions_result.data.get('actions', [])
                print(f"✅ Available actions: {[action.get('type') for action in actions]} ({len(actions)} total)")
            else:
                print(f"❌ Failed to get available actions: {available_actions_result.error_message}")
            
            # Continue making decisions and executing actions until we should end turn
            actions_taken = 0
            failed_actions = 0
            max_actions_per_turn = 10  # Safety limit to prevent infinite loops
            max_failed_actions = 3  # Maximum consecutive failed actions before ending turn
            
            while actions_taken < max_actions_per_turn and failed_actions < max_failed_actions:
                # Make a decision about what to do next
                decision = self.make_decision()
                
                if not decision:
                    print(f"🤖 AI Agent {unit.name}: No valid decisions available, ending turn")
                    break
                
                print(f"🤖 AI Agent {unit.name}: Decided to {decision.action_id}")
                
                # Execute the decided action using MCP tools
                action_result = self._execute_action_via_mcp(decision, unit)
                
                if action_result:
                    actions_taken += 1
                    failed_actions = 0  # Reset failed action counter on success
                    print(f"🤖 AI Agent {unit.name}: Action executed successfully ({actions_taken} actions taken)")
                    
                    # Check if we should end the turn
                    if self._should_end_turn(unit, actions_taken):
                        print(f"🤖 AI Agent {unit.name}: Ending turn (insufficient AP or tactical decision)")
                        break
                else:
                    actions_taken += 1  # Count failed actions too
                    failed_actions += 1  # Increment consecutive failed actions
                    print(f"🤖 AI Agent {unit.name}: Action failed, consuming 1 AP as penalty ({actions_taken} actions taken, {failed_actions} consecutive failures)")
                    
                    # Consume AP for failed action to prevent infinite loops
                    current_ap = getattr(unit, 'ap', 0)
                    if current_ap > 0:
                        unit.ap -= 1
                        print(f"⚡ AI Agent {unit.name}: AP reduced to {unit.ap} due to failed action")
                    
                    # Check if we should end the turn after failed action
                    if self._should_end_turn(unit, actions_taken):
                        print(f"🤖 AI Agent {unit.name}: Ending turn after failed action (insufficient AP)")
                        break
                    
                    # Check if too many consecutive failures
                    if failed_actions >= max_failed_actions:
                        print(f"🤖 AI Agent {unit.name}: Too many consecutive failures ({failed_actions}), ending turn")
                        break
                    
            # End the turn using MCP tools
            self._end_turn_via_mcp(unit)
            
        except Exception as e:
            print(f"❌ AI Agent {unit.name} turn execution failed: {e}")
            # Fallback: end turn via MCP tools
            self._end_turn_via_mcp(unit)
    
    def _execute_action_via_mcp(self, decision: ActionDecision, unit) -> bool:
        """Execute an action using only MCP tools."""
        try:
            action_type = decision.action_id
            print(f"🎮 Executing action: {action_type} for {unit.name}")
            print(f"   Target positions: {decision.target_positions}")
            print(f"   Reasoning: {decision.reasoning}")
            print(f"   Confidence: {decision.confidence}")
            
            # The new tactical analysis provides pre-calculated move-action combinations
            # We need to extract the move and action components from the decision
            
            # Check if we have move information in the context
            move_to = getattr(decision, 'move_to', None)
            if hasattr(decision, 'target_positions') and decision.target_positions:
                target_pos = decision.target_positions[0]
            else:
                target_pos = None
            
            # Execute movement first if needed
            if move_to and (move_to.get('x') != unit.x or move_to.get('y') != unit.y):
                print(f"🚶 Moving to ({move_to['x']}, {move_to['y']}) first")
                move_result = self.tool_registry.execute_tool(
                    'move_unit',
                    unit_id=self.unit_id,
                    target_x=move_to['x'],
                    target_y=move_to['y']
                )
                if not move_result.success:
                    print(f"❌ Movement failed: {move_result.error_message}")
                    return False
                print(f"✅ Movement successful")
            
            # Execute the action
            if action_type == "attack":
                return self._execute_attack_via_mcp(decision, unit)
            elif action_type == "ability":
                return self._execute_ability_via_mcp(decision, unit)
            elif self._is_talent_action(action_type):
                return self._execute_talent_via_mcp(decision, unit)
            elif action_type == "wait":
                print(f"💤 {unit.name} waits (no action taken)")
                return True
            else:
                print(f"⚠️ Unknown action type: {action_type}")
                return False
                
        except Exception as e:
            print(f"❌ MCP action execution failed: {e}")
            return False
    
    def _execute_move_via_mcp(self, decision: ActionDecision, unit) -> bool:
        """Execute movement using MCP move_unit tool."""
        try:
            if not decision.target_positions or len(decision.target_positions) == 0:
                print(f"❌ Move action failed: No target positions provided")
                return False
                
            target_pos = decision.target_positions[0]  # Use first target position
            print(f"🚶 Attempting to move {unit.name} to ({target_pos['x']}, {target_pos['y']})")
            
            result = self.tool_registry.execute_tool(
                'move_unit', 
                unit_id=self.unit_id,
                target_x=target_pos['x'],
                target_y=target_pos['y']
            )
            
            if result.success:
                print(f"✅ Move successful: {result.data}")
            else:
                print(f"❌ Move failed: {result.error_message}")
                
            return result.success
        except Exception as e:
            print(f"❌ MCP move exception: {e}")
            return False
    
    def _execute_attack_via_mcp(self, decision: ActionDecision, unit) -> bool:
        """Execute attack using MCP attack_unit tool."""
        try:
            if not decision.target_positions or len(decision.target_positions) == 0:
                print(f"❌ Attack action failed: No target positions provided")
                return False
                
            target_pos = decision.target_positions[0]  # Use first target position
            print(f"⚔️ Attempting to attack from {unit.name} to ({target_pos['x']}, {target_pos['y']})")
            
            result = self.tool_registry.execute_tool(
                'attack_unit',
                attacker_id=self.unit_id,
                target_x=target_pos['x'],
                target_y=target_pos['y']
            )
            
            if result.success:
                print(f"✅ Attack successful: {result.data}")
            else:
                print(f"❌ Attack failed: {result.error_message}")
                
            return result.success
        except Exception as e:
            print(f"❌ MCP attack exception: {e}")
            return False
    
    def _execute_ability_via_mcp(self, decision: ActionDecision, unit) -> bool:
        """Execute ability using MCP cast_spell tool."""
        try:
            if not decision.target_positions or len(decision.target_positions) == 0:
                print(f"❌ Ability action failed: No target positions provided")
                return False
                
            target_pos = decision.target_positions[0]  # Use first target position
            print(f"✨ Attempting to cast spell from {unit.name} to ({target_pos['x']}, {target_pos['y']})")
            
            result = self.tool_registry.execute_tool(
                'cast_spell',
                caster_id=self.unit_id,
                target_x=target_pos['x'],
                target_y=target_pos['y']
            )
            
            if result.success:
                print(f"✅ Ability successful: {result.data}")
            else:
                print(f"❌ Ability failed: {result.error_message}")
                
            return result.success
        except Exception as e:
            print(f"❌ MCP ability exception: {e}")
            return False
    
    def _is_talent_action(self, action_type: str) -> bool:
        """Check if action type is a talent action."""
        # Check if this is a talent by looking at available actions
        try:
            actions_result = self.tool_registry.execute_tool('get_available_actions', unit_id=self.unit_id)
            if actions_result.success:
                actions = actions_result.data.get('actions', [])
                talent_actions = [action for action in actions if action.get('talent_id') == action_type]
                return len(talent_actions) > 0
        except:
            pass
        return False
    
    def _execute_talent_via_mcp(self, decision: ActionDecision, unit) -> bool:
        """Execute talent using MCP execute_talent tool."""
        try:
            talent_id = decision.action_id
            print(f"🔥 Attempting to use talent '{talent_id}' from {unit.name}")
            
            # Find the slot index for this talent
            actions_result = self.tool_registry.execute_tool('get_available_actions', unit_id=self.unit_id)
            if not actions_result.success:
                print(f"❌ Failed to get available actions: {actions_result.error_message}")
                return False
            
            actions = actions_result.data.get('actions', [])
            talent_action = None
            for action in actions:
                if action.get('talent_id') == talent_id:
                    talent_action = action
                    break
            
            if not talent_action:
                print(f"❌ Talent '{talent_id}' not found in available actions")
                return False
            
            slot_index = talent_action.get('slot_index', 0)
            
            # Check if we have target positions
            if decision.target_positions and len(decision.target_positions) > 0:
                target_pos = decision.target_positions[0]
                print(f"   Targeting ({target_pos['x']}, {target_pos['y']})")
                
                result = self.tool_registry.execute_tool(
                    'execute_hotkey_talent',
                    unit_id=self.unit_id,
                    slot_index=slot_index,
                    target_x=target_pos['x'],
                    target_y=target_pos['y']
                )
            else:
                # Self-targeted or instant talent
                print(f"   Self-targeted talent")
                
                result = self.tool_registry.execute_tool(
                    'execute_hotkey_talent',
                    unit_id=self.unit_id,
                    slot_index=slot_index
                )
            
            if result.success:
                print(f"✅ Talent '{talent_id}' executed successfully: {result.data}")
            else:
                print(f"❌ Talent '{talent_id}' failed: {result.error_message}")
                
            return result.success
        except Exception as e:
            print(f"❌ MCP talent exception: {e}")
            return False
    
    def _should_end_turn(self, unit, actions_taken: int) -> bool:
        """Determine if the AI should end its turn."""
        try:
            # Get current unit state via MCP tools
            unit_result = self.tool_registry.execute_tool('get_unit_details', unit_id=self.unit_id)
            if not unit_result.success:
                return True  # If we can't get unit details, end turn
            
            unit_data = unit_result.data
            current_ap = unit_data.get('ap', 0)
            
            # End turn if no AP left
            if current_ap <= 0:
                return True
            
            # Get available actions via MCP tools
            actions_result = self.tool_registry.execute_tool('get_available_actions', unit_id=self.unit_id)
            if not actions_result.success:
                return True  # If we can't get actions, end turn
            
            available_actions = actions_result.data.get('actions', [])
            
            # End turn if no actions available
            if not available_actions:
                return True
            
            # Tactical decision: end turn if we've taken 3+ actions (conservative play)
            if actions_taken >= 3:
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error checking turn end condition: {e}")
            return True  # Default to ending turn on error
    
    def _end_turn_via_mcp(self, unit):
        """End the turn using MCP end_turn tool."""
        try:
            result = self.tool_registry.execute_tool('end_turn', unit_id=self.unit_id)
            if result.success:
                print(f"🤖 AI Agent {unit.name}: Turn ended successfully via MCP")
            else:
                print(f"⚠️ AI Agent {unit.name}: MCP end_turn failed: {result.error}")
        except Exception as e:
            print(f"❌ MCP end_turn failed: {e}")