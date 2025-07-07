"""
MCP Tactical Agent

AI agent that uses MCP tools to make tactical decisions and control units during battle.
Provides sophisticated decision-making capabilities using the comprehensive MCP toolkit.
"""

import asyncio
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ..mcp_tools import MCPToolRegistry, ToolResult


@dataclass
class TacticalDecision:
    """Represents an AI tactical decision"""
    decision_type: str  # 'move', 'attack', 'ability', 'wait'
    target_position: Optional[Tuple[int, int]] = None
    action_id: Optional[str] = None
    priority: str = "NORMAL"
    confidence: float = 0.5
    reasoning: str = ""


class MCPTacticalAgent:
    """AI agent that uses MCP tools for tactical decision-making"""
    
    def __init__(self, mcp_tools: MCPToolRegistry, difficulty_level: str = "STRATEGIC"):
        """
        Initialize MCP tactical agent.
        
        Args:
            mcp_tools: MCP tool registry for game interaction
            difficulty_level: AI difficulty (SCRIPTED, STRATEGIC, ADAPTIVE, LEARNING)
        """
        self.mcp_tools = mcp_tools
        self.difficulty = difficulty_level
        self.move_preference = 0.6  # Probability of moving when possible
        self.aggression_level = 0.7  # How aggressive the AI is
        self.risk_tolerance = 0.5   # Willingness to take risks
        
        # Adjust parameters based on difficulty
        self._configure_difficulty()
        
        print(f"🤖 MCP Tactical Agent initialized (Difficulty: {difficulty_level})")
    
    def _configure_difficulty(self):
        """Configure AI parameters based on difficulty level"""
        if self.difficulty == "SCRIPTED":
            self.move_preference = 0.8
            self.aggression_level = 0.5
            self.risk_tolerance = 0.3
        elif self.difficulty == "STRATEGIC":
            self.move_preference = 0.6
            self.aggression_level = 0.7
            self.risk_tolerance = 0.5
        elif self.difficulty == "ADAPTIVE":
            self.move_preference = 0.5
            self.aggression_level = 0.8
            self.risk_tolerance = 0.7
        elif self.difficulty == "LEARNING":
            self.move_preference = 0.4
            self.aggression_level = 0.9
            self.risk_tolerance = 0.8
    
    async def execute_turn(self, unit):
        """Execute full AI turn for unit using MCP tools"""
        print(f"🧠 MCP AI planning turn for {unit.name}")
        
        try:
            # 1. Analyze current battlefield situation
            battlefield_analysis = await self._analyze_battlefield(unit)
            
            # 2. Make tactical decisions based on analysis
            decisions = await self._make_tactical_decisions(unit, battlefield_analysis)
            
            # 3. Execute the best decision
            if decisions:
                best_decision = max(decisions, key=lambda d: d.confidence)
                await self._execute_decision(unit, best_decision)
                print(f"✅ {unit.name} executed: {best_decision.reasoning}")
            else:
                print(f"⚠️ No valid decisions found for {unit.name}")
                
        except Exception as e:
            print(f"❌ MCP AI turn failed for {unit.name}: {e}")
            # Fallback to basic decision
            await self._execute_fallback_decision(unit)
    
    async def _analyze_battlefield(self, unit) -> Dict[str, Any]:
        """Analyze battlefield using MCP tools"""
        analysis = {
            'battlefield_state': None,
            'unit_details': None,
            'threat_assessment': None,
            'enemy_units': [],
            'ally_units': []
        }
        
        try:
            # Get complete battlefield state
            battlefield_result = self.mcp_tools.execute_tool('get_battlefield_state')
            if battlefield_result.success:
                analysis['battlefield_state'] = battlefield_result.data
                
                # Categorize units
                for unit_data in battlefield_result.data.get('units', []):
                    if unit_data.get('team') == 'player':
                        analysis['enemy_units'].append(unit_data)
                    elif unit_data.get('team') == 'enemy' and unit_data.get('id') != str(unit.id):
                        analysis['ally_units'].append(unit_data)
            
            # Get detailed unit information
            unit_result = self.mcp_tools.execute_tool('get_unit_details', unit_id=str(unit.id))
            if unit_result.success:
                analysis['unit_details'] = unit_result.data
            
            # Calculate threat assessment
            threat_result = self.mcp_tools.execute_tool('calculate_threat_assessment', unit_id=str(unit.id))
            if threat_result.success:
                analysis['threat_assessment'] = threat_result.data
                
        except Exception as e:
            print(f"⚠️ Battlefield analysis error: {e}")
        
        return analysis
    
    async def _make_tactical_decisions(self, unit, battlefield_analysis: Dict[str, Any]) -> List[TacticalDecision]:
        """Generate tactical decisions using MCP analysis"""
        decisions = []
        
        try:
            # Consider movement
            movement_decision = await self._consider_movement(unit, battlefield_analysis)
            if movement_decision:
                decisions.append(movement_decision)
            
            # Consider attacks and abilities
            combat_decisions = await self._consider_combat_actions(unit, battlefield_analysis)
            decisions.extend(combat_decisions)
            
            # Consider waiting/defensive actions
            if not decisions or random.random() < 0.2:  # 20% chance to consider waiting
                wait_decision = self._consider_waiting(unit, battlefield_analysis)
                if wait_decision:
                    decisions.append(wait_decision)
                    
        except Exception as e:
            print(f"⚠️ Decision making error: {e}")
        
        return decisions
    
    async def _consider_movement(self, unit, battlefield_analysis: Dict[str, Any]) -> Optional[TacticalDecision]:
        """Consider movement options using tactical analysis"""
        # Only move if we have enough AP and it's tactically sound
        unit_details = battlefield_analysis.get('unit_details', {})
        current_ap = unit_details.get('stats', {}).get('ap', 0)
        
        if current_ap <= 1:  # Save AP for attacks
            return None
        
        if random.random() > self.move_preference:
            return None
        
        # Find optimal position based on threats and opportunities
        enemy_units = battlefield_analysis.get('enemy_units', [])
        if not enemy_units:
            return None
        
        # Choose target to approach or retreat from
        current_pos = unit_details.get('position', {'x': unit.x, 'y': unit.y})
        
        # Simple tactical movement: move toward weakest enemy or away from threats
        threat_assessment = battlefield_analysis.get('threat_assessment', {})
        threat_level = threat_assessment.get('threat_category', 'LOW')
        
        if threat_level == 'HIGH':
            # Retreat - move away from nearest enemy
            target_position = self._find_retreat_position(current_pos, enemy_units)
            reasoning = "Retreating from high threat situation"
            confidence = 0.8
        else:
            # Advance - move toward weakest enemy
            target_position = self._find_attack_position(current_pos, enemy_units)
            reasoning = "Advancing to better attack position"
            confidence = 0.6
        
        if target_position and target_position != (current_pos['x'], current_pos['y']):
            return TacticalDecision(
                decision_type='move',
                target_position=target_position,
                confidence=confidence,
                reasoning=reasoning
            )
        
        return None
    
    async def _consider_combat_actions(self, unit, battlefield_analysis: Dict[str, Any]) -> List[TacticalDecision]:
        """Consider attack and ability options"""
        decisions = []
        enemy_units = battlefield_analysis.get('enemy_units', [])
        
        if not enemy_units:
            return decisions
        
        # Get available actions for the unit
        unit_details = battlefield_analysis.get('unit_details', {})
        available_actions = unit_details.get('available_actions', [])
        
        # Analyze each potential action against each enemy
        for action in available_actions:
            action_id = action.get('id', 'basic_attack')
            if action_id in ['move', 'wait']:  # Skip non-combat actions
                continue
            
            for enemy in enemy_units:
                enemy_pos = enemy.get('position', {})
                target_position = (enemy_pos.get('x', 0), enemy_pos.get('y', 0))
                
                # Use MCP analysis to evaluate this action
                try:
                    analysis_result = self.mcp_tools.execute_tool(
                        'analyze_action_outcomes',
                        unit_id=str(unit.id),
                        action_id=action_id,
                        target_positions=[{'x': target_position[0], 'y': target_position[1]}]
                    )
                    
                    if analysis_result.success:
                        tactical_assessment = analysis_result.data.get('tactical_assessment', {})
                        tactical_value = tactical_assessment.get('tactical_value', 0)
                        recommendation = tactical_assessment.get('recommendation', 'AVOID')
                        
                        if recommendation in ['EXECUTE', 'CONSIDER'] and tactical_value > 1.0:
                            confidence = min(tactical_value / 3.0, 0.9)  # Scale confidence
                            
                            decision = TacticalDecision(
                                decision_type='attack',
                                target_position=target_position,
                                action_id=action_id,
                                confidence=confidence,
                                reasoning=f"Attack {enemy.get('name', 'enemy')} with {action_id} (value: {tactical_value:.1f})"
                            )
                            decisions.append(decision)
                            
                except Exception as e:
                    print(f"⚠️ Combat analysis error: {e}")
        
        return decisions
    
    def _consider_waiting(self, unit, battlefield_analysis: Dict[str, Any]) -> Optional[TacticalDecision]:
        """Consider waiting/defensive actions"""
        threat_assessment = battlefield_analysis.get('threat_assessment', {})
        threat_level = threat_assessment.get('threat_category', 'LOW')
        
        # Wait if in a good position and high threat
        if threat_level == 'HIGH':
            return TacticalDecision(
                decision_type='wait',
                confidence=0.4,
                reasoning="Waiting in defensive position due to high threat"
            )
        
        return None
    
    def _find_retreat_position(self, current_pos: Dict[str, int], enemy_units: List[Dict]) -> Optional[Tuple[int, int]]:
        """Find position to retreat to (away from enemies)"""
        if not enemy_units:
            return None
        
        # Simple retreat: move away from nearest enemy
        nearest_enemy = min(enemy_units, 
                          key=lambda e: abs(e['position']['x'] - current_pos['x']) + 
                                       abs(e['position']['y'] - current_pos['y']))
        
        enemy_pos = nearest_enemy['position']
        
        # Move in opposite direction
        dx = current_pos['x'] - enemy_pos['x']
        dy = current_pos['y'] - enemy_pos['y']
        
        # Normalize direction
        if abs(dx) > abs(dy):
            new_x = current_pos['x'] + (1 if dx > 0 else -1)
            new_y = current_pos['y']
        else:
            new_x = current_pos['x']
            new_y = current_pos['y'] + (1 if dy > 0 else -1)
        
        return (new_x, new_y)
    
    def _find_attack_position(self, current_pos: Dict[str, int], enemy_units: List[Dict]) -> Optional[Tuple[int, int]]:
        """Find position to move closer to enemies"""
        if not enemy_units:
            return None
        
        # Move toward weakest enemy (lowest HP)
        target_enemy = min(enemy_units, key=lambda e: e.get('hp', 100))
        enemy_pos = target_enemy['position']
        
        # Move one step closer
        dx = enemy_pos['x'] - current_pos['x']
        dy = enemy_pos['y'] - current_pos['y']
        
        # Normalize direction
        if abs(dx) > abs(dy):
            new_x = current_pos['x'] + (1 if dx > 0 else -1)
            new_y = current_pos['y']
        else:
            new_x = current_pos['x']
            new_y = current_pos['y'] + (1 if dy > 0 else -1)
        
        return (new_x, new_y)
    
    async def _execute_decision(self, unit, decision: TacticalDecision):
        """Execute AI decision using MCP tools"""
        try:
            if decision.decision_type == 'move':
                # Execute movement
                result = self.mcp_tools.execute_tool(
                    'queue_unit_action',
                    unit_id=str(unit.id),
                    action_id='move',
                    target_positions=[{'x': decision.target_position[0], 'y': decision.target_position[1]}],
                    priority=decision.priority
                )
                
            elif decision.decision_type == 'attack':
                # Execute attack/ability
                result = self.mcp_tools.execute_tool(
                    'queue_unit_action',
                    unit_id=str(unit.id),
                    action_id=decision.action_id or 'basic_attack',
                    target_positions=[{'x': decision.target_position[0], 'y': decision.target_position[1]}],
                    priority=decision.priority
                )
                
            elif decision.decision_type == 'wait':
                # Wait/end turn
                result = ToolResult(success=True, data={'action': 'wait'})
                print(f"🤖 {unit.name} waits")
                
            else:
                result = ToolResult(success=False, error_message=f"Unknown decision type: {decision.decision_type}")
            
            if not result.success:
                print(f"❌ Failed to execute {decision.decision_type}: {result.error_message}")
                
        except Exception as e:
            print(f"❌ Decision execution failed: {e}")
    
    async def _execute_fallback_decision(self, unit):
        """Execute basic fallback decision when MCP fails"""
        print(f"🎲 Executing fallback AI for {unit.name}")
        
        # Very simple AI: try to attack if possible, otherwise wait
        if hasattr(unit, 'attack_range') and unit.attack_range > 0:
            # This would need to be implemented in the calling controller
            print(f"🤖 {unit.name} attempts basic attack")
        else:
            print(f"🤖 {unit.name} waits (fallback)")