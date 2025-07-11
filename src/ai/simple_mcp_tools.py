"""
Simple MCP Tools for AI Agent Integration

Simplified version that works directly with the game controller without requiring
the full action management system. This allows AI agents to control units using
only MCP tools.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Standardized result format for MCP tools."""
    success: bool
    data: Any = None
    error_message: str = ""
    execution_time_ms: float = 0.0


class SimpleMCPToolRegistry:
    """Simplified MCP tool registry that works with the game controller."""
    
    def __init__(self, game_controller):
        """Initialize with game controller reference."""
        self.game_controller = game_controller
        self.tools = {
            'get_game_state': self._get_game_state,
            'get_unit_details': self._get_unit_details,
            'get_available_actions': self._get_available_actions,
            'move_unit': self._move_unit,
            'attack_unit': self._attack_unit,
            'cast_spell': self._cast_spell,
            'execute_hotkey_talent': self._execute_hotkey_talent,
            'end_turn': self._end_turn,
            'calculate_threat_assessment': self._calculate_threat_assessment,
            'get_battlefield_state': self._get_battlefield_state,
            'get_tactical_analysis': self._get_tactical_analysis
        }
    
    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool with given parameters."""
        try:
            if tool_name not in self.tools:
                return ToolResult(
                    success=False,
                    error_message=f"Tool '{tool_name}' not found"
                )
            
            tool_func = self.tools[tool_name]
            result = tool_func(**kwargs)
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                error_message=f"Tool execution failed: {str(e)}"
            )
    
    def _get_game_state(self) -> ToolResult:
        """Get current game state."""
        try:
            units_data = []
            for unit in self.game_controller.units:
                units_data.append({
                    'name': unit.name,
                    'x': unit.x,
                    'y': unit.y,
                    'hp': unit.hp,
                    'max_hp': unit.max_hp,
                    'ap': getattr(unit, 'ap', 0),
                    'max_ap': getattr(unit, 'max_ap', 0),
                    'is_enemy': getattr(unit, 'is_enemy_unit', False),
                    'alive': unit.alive
                })
            
            # Handle missing turn_manager gracefully
            current_turn = 0
            if hasattr(self.game_controller, 'turn_manager') and self.game_controller.turn_manager:
                current_turn = self.game_controller.turn_manager.current_turn
            
            return ToolResult(
                success=True,
                data={
                    'units': units_data,
                    'grid_width': self.game_controller.grid.width,
                    'grid_height': self.game_controller.grid.height,
                    'current_turn': current_turn
                }
            )
        except Exception as e:
            return ToolResult(success=False, error_message=f"Game state error: {str(e)}")
    
    def _get_unit_details(self, unit_id: str) -> ToolResult:
        """Get detailed information about a specific unit."""
        try:
            # Find unit by ID (name for now)
            unit = self._find_unit_by_id(unit_id)
            if not unit:
                return ToolResult(success=False, error_message=f"Unit '{unit_id}' not found")
            
            return ToolResult(
                success=True,
                data={
                    'name': unit.name,
                    'x': unit.x,
                    'y': unit.y,
                    'hp': unit.hp,
                    'max_hp': unit.max_hp,
                    'ap': getattr(unit, 'ap', 0),
                    'max_ap': getattr(unit, 'max_ap', 0),
                    'is_enemy': getattr(unit, 'is_enemy_unit', False),
                    'alive': unit.alive,
                    'attack_range': unit.attack_range,
                    'physical_attack': unit.physical_attack,
                    'magical_attack': unit.magical_attack,
                    'physical_defense': unit.physical_defense,
                    'magical_defense': unit.magical_defense,
                    'equipped_weapon': getattr(unit, 'equipped_weapon', None),
                    'equipment': {
                        'weapon': getattr(unit.equipped_weapon, 'name', None) if getattr(unit, 'equipped_weapon', None) else None,
                        'armor': getattr(unit.equipped_armor, 'name', None) if getattr(unit, 'equipped_armor', None) else None,
                        'accessory': getattr(unit.equipped_accessory, 'name', None) if getattr(unit, 'equipped_accessory', None) else None
                    }
                }
            )
        except Exception as e:
            return ToolResult(success=False, error_message=str(e))
    
    def _get_available_actions(self, unit_id: str) -> ToolResult:
        """Get available actions for a unit, including hotkey talents."""
        try:
            unit = self._find_unit_by_id(unit_id)
            if not unit:
                return ToolResult(success=False, error_message=f"Unit '{unit_id}' not found")
            
            current_ap = getattr(unit, 'ap', 0)
            actions = []
            
            # Check if unit can move
            if current_ap >= 1 and unit.current_move_points > 0:
                actions.append({
                    'type': 'move',
                    'ap_cost': 1,
                    'description': 'Move to adjacent tile'
                })
            
            # Check if unit can attack
            if current_ap >= 1:
                actions.append({
                    'type': 'attack',
                    'ap_cost': 1,
                    'description': 'Attack enemy unit'
                })
            
            # Check if unit can cast spell
            if current_ap >= 2:
                actions.append({
                    'type': 'ability',
                    'ap_cost': 2,
                    'description': 'Cast spell or use ability'
                })
            
            # Add hotkey talents as available actions
            hotkey_actions = self._get_hotkey_actions(unit)
            actions.extend(hotkey_actions)
            
            return ToolResult(
                success=True,
                data={'actions': actions}
            )
        except Exception as e:
            return ToolResult(success=False, error_message=str(e))
    
    def _get_hotkey_actions(self, unit):
        """Get hotkey talents as available actions for a unit."""
        hotkey_actions = []
        
        try:
            # Check if unit has character instance with hotkey abilities
            if hasattr(unit, 'character_instance_id'):
                character = self.get_character_by_id(unit.character_instance_id)
                
                if character and hasattr(character, 'hotkey_abilities'):
                    # Get hotkey abilities
                    hotkey_abilities = character.hotkey_abilities
                    
                    if isinstance(hotkey_abilities, list):
                        for slot_index, ability_data in enumerate(hotkey_abilities):
                            if ability_data is not None:
                                # Extract AP cost from ability data
                                ap_cost = 1  # Default AP cost
                                if 'cost' in ability_data:
                                    cost_data = ability_data['cost']
                                    if isinstance(cost_data, dict):
                                        ap_cost = cost_data.get('ap', 1)
                                elif 'ap_cost' in ability_data:
                                    ap_cost = ability_data.get('ap_cost', 1)
                                
                                # Create talent action using the actual talent name/ID as the type
                                talent_name = ability_data.get('name', 'Unknown Ability')
                                talent_id = ability_data.get('talent_id', f'talent_{slot_index + 1}')
                                
                                # Use talent_id as the action type for MCP tool identification
                                hotkey_action = {
                                    'type': talent_id,  # Use talent_id as action type
                                    'slot_index': slot_index,
                                    'ap_cost': ap_cost,
                                    'description': f"{talent_name} (Hotkey {slot_index + 1})",
                                    'talent_id': talent_id,
                                    'ability_name': talent_name,
                                    'action_type': ability_data.get('action_type', 'Unknown')
                                }
                                hotkey_actions.append(hotkey_action)
                                
        except Exception as e:
            print(f"⚠️ Error getting hotkey actions: {e}")
        
        return hotkey_actions
    
    def _execute_hotkey_talent(self, unit_id: str, slot_index: int, target_x: int = None, target_y: int = None) -> ToolResult:
        """Execute a specific hotkey talent."""
        try:
            unit = self._find_unit_by_id(unit_id)
            if not unit:
                return ToolResult(success=False, error_message=f"Unit '{unit_id}' not found")
            
            # Get the hotkey ability data
            if hasattr(unit, 'character_instance_id'):
                character = self.get_character_by_id(unit.character_instance_id)
                
                if character and hasattr(character, 'hotkey_abilities'):
                    hotkey_abilities = character.hotkey_abilities
                    
                    if isinstance(hotkey_abilities, list) and slot_index < len(hotkey_abilities):
                        ability_data = hotkey_abilities[slot_index]
                        
                        if ability_data is not None:
                            # Check AP cost
                            ap_cost = ability_data.get('ap_cost', 1)
                            if unit.ap < ap_cost:
                                return ToolResult(success=False, error_message=f"Insufficient AP for talent: {unit.ap}/{ap_cost}")
                            
                            # Execute the talent (simplified implementation)
                            talent_name = ability_data.get('name', 'Unknown Talent')
                            
                            # For now, simulate talent execution
                            # In a full implementation, this would call the actual talent execution system
                            if target_x is not None and target_y is not None:
                                # Target-based talent
                                target_unit = self.game_controller.grid.get_unit_at(target_x, target_y)
                                if target_unit:
                                    # Simple damage/healing simulation
                                    action_type = ability_data.get('action_type', 'attack')
                                    if action_type.lower() == 'attack':
                                        damage = getattr(unit, 'magical_attack', 10)
                                        target_unit.take_damage(damage, 'magical')
                                        unit.ap -= ap_cost
                                        
                                        return ToolResult(
                                            success=True,
                                            data={
                                                'caster': unit.name,
                                                'talent_name': talent_name,
                                                'target': target_unit.name,
                                                'damage': damage,
                                                'target_hp_remaining': target_unit.hp,
                                                'caster_ap_remaining': unit.ap
                                            }
                                        )
                                    else:
                                        # Non-attack talent (healing, buff, etc.)
                                        unit.ap -= ap_cost
                                        return ToolResult(
                                            success=True,
                                            data={
                                                'caster': unit.name,
                                                'talent_name': talent_name,
                                                'effect': f"Used {talent_name}",
                                                'caster_ap_remaining': unit.ap
                                            }
                                        )
                                else:
                                    return ToolResult(success=False, error_message="No target at specified position")
                            else:
                                # Self-targeted or instant talent
                                unit.ap -= ap_cost
                                return ToolResult(
                                    success=True,
                                    data={
                                        'caster': unit.name,
                                        'talent_name': talent_name,
                                        'effect': f"Used {talent_name}",
                                        'caster_ap_remaining': unit.ap
                                    }
                                )
                        else:
                            return ToolResult(success=False, error_message=f"No talent in hotkey slot {slot_index + 1}")
                    else:
                        return ToolResult(success=False, error_message=f"Invalid hotkey slot {slot_index + 1}")
                else:
                    return ToolResult(success=False, error_message="Unit has no hotkey abilities")
            else:
                return ToolResult(success=False, error_message="Unit has no character instance")
                
        except Exception as e:
            return ToolResult(success=False, error_message=f"Hotkey talent execution failed: {str(e)}")
    
    def _move_unit(self, unit_id: str, target_x: int, target_y: int) -> ToolResult:
        """Move a unit to target position."""
        try:
            unit = self._find_unit_by_id(unit_id)
            if not unit:
                return ToolResult(success=False, error_message=f"Unit '{unit_id}' not found")
            
            # Check if target position is valid
            if not self.game_controller.grid.is_valid(target_x, target_y):
                return ToolResult(success=False, error_message="Invalid target position")
            
            # Check if position is occupied
            if self.game_controller.grid.get_unit_at(target_x, target_y):
                return ToolResult(success=False, error_message="Target position is occupied")
            
            # Check if unit can move there
            if not unit.can_move_to(target_x, target_y, self.game_controller.grid):
                return ToolResult(success=False, error_message="Unit cannot move to target position")
            
            # Move the unit
            old_x, old_y = unit.x, unit.y
            print(f"🤖 AI Movement: {unit.name} from ({old_x}, {old_y}) to ({target_x}, {target_y})")
            
            self.game_controller.grid.remove_unit(unit)
            unit.x, unit.y = target_x, target_y
            self.game_controller.grid.add_unit(unit)
            
            # Update visual position to match data model
            self.game_controller.update_unit_visual_position(unit)
            
            # Also update TacticalGrid positions if available
            if hasattr(self.game_controller, 'tactical_grid') and self.game_controller.tactical_grid:
                from core.math.vector import Vector2Int
                old_pos = Vector2Int(old_x, old_y)
                new_pos = Vector2Int(target_x, target_y)
                self.game_controller.tactical_grid.free_cell(old_pos)
                unit_id = f"{unit.name}_{target_x}_{target_y}"
                self.game_controller.tactical_grid.occupy_cell(new_pos, unit_id)
            
            # Consume AP and movement points
            unit.ap -= 1
            distance = abs(target_x - old_x) + abs(target_y - old_y)
            unit.current_move_points -= distance
            
            return ToolResult(
                success=True,
                data={
                    'unit_moved': unit.name,
                    'from': {'x': old_x, 'y': old_y},
                    'to': {'x': target_x, 'y': target_y},
                    'ap_remaining': unit.ap,
                    'move_points_remaining': unit.current_move_points
                }
            )
        except Exception as e:
            return ToolResult(success=False, error_message=str(e))
    
    def _attack_unit(self, attacker_id: str, target_x: int, target_y: int) -> ToolResult:
        """Attack a unit at target position."""
        try:
            attacker = self._find_unit_by_id(attacker_id)
            if not attacker:
                return ToolResult(success=False, error_message=f"Attacker '{attacker_id}' not found")
            
            # Find target unit
            target = self.game_controller.grid.get_unit_at(target_x, target_y)
            if not target:
                return ToolResult(success=False, error_message="No unit at target position")
            
            # Check if target is in range
            distance = abs(target_x - attacker.x) + abs(target_y - attacker.y)
            if distance > attacker.attack_range:
                return ToolResult(success=False, error_message="Target out of attack range")
            
            # Check if attacker has enough AP
            if attacker.ap < 1:
                return ToolResult(success=False, error_message="Insufficient AP for attack")
            
            # Perform attack
            damage = attacker.physical_attack
            target.take_damage(damage, "physical")
            attacker.ap -= 1
            
            return ToolResult(
                success=True,
                data={
                    'attacker': attacker.name,
                    'target': target.name,
                    'damage_dealt': damage,
                    'target_hp_remaining': target.hp,
                    'target_alive': target.alive,
                    'attacker_ap_remaining': attacker.ap
                }
            )
        except Exception as e:
            return ToolResult(success=False, error_message=str(e))
    
    def _cast_spell(self, caster_id: str, target_x: int, target_y: int) -> ToolResult:
        """Cast a spell at target position."""
        try:
            caster = self._find_unit_by_id(caster_id)
            if not caster:
                return ToolResult(success=False, error_message=f"Caster '{caster_id}' not found")
            
            # Check if caster has enough AP
            if caster.ap < 2:
                return ToolResult(success=False, error_message="Insufficient AP for spell")
            
            # Check if target is in range
            distance = abs(target_x - caster.x) + abs(target_y - caster.y)
            if distance > caster.magic_range:
                return ToolResult(success=False, error_message="Target out of magic range")
            
            # Find target unit
            target = self.game_controller.grid.get_unit_at(target_x, target_y)
            if not target:
                return ToolResult(success=False, error_message="No unit at target position")
            
            # Cast spell (simple magical attack)
            damage = caster.magical_attack
            target.take_damage(damage, "magical")
            caster.ap -= 2
            
            return ToolResult(
                success=True,
                data={
                    'caster': caster.name,
                    'target': target.name,
                    'spell_damage': damage,
                    'target_hp_remaining': target.hp,
                    'target_alive': target.alive,
                    'caster_ap_remaining': caster.ap
                }
            )
        except Exception as e:
            return ToolResult(success=False, error_message=str(e))
    
    def _end_turn(self, unit_id: str) -> ToolResult:
        """End the current unit's turn."""
        try:
            unit = self._find_unit_by_id(unit_id)
            if not unit:
                return ToolResult(success=False, error_message=f"Unit '{unit_id}' not found")
            
            # Check if it's actually this unit's turn
            current_unit = self.game_controller.turn_manager.current_unit()
            if current_unit != unit:
                return ToolResult(success=False, error_message="Not this unit's turn")
            
            # End the turn
            self.game_controller.end_current_turn()
            
            return ToolResult(
                success=True,
                data={'message': f"{unit.name}'s turn ended"}
            )
        except Exception as e:
            return ToolResult(success=False, error_message=str(e))
    
    def _calculate_threat_assessment(self, unit_id: str) -> ToolResult:
        """Calculate threat assessment for a unit."""
        try:
            unit = self._find_unit_by_id(unit_id)
            if not unit:
                return ToolResult(success=False, error_message=f"Unit '{unit_id}' not found")
            
            threats = []
            for other_unit in self.game_controller.units:
                if other_unit != unit and other_unit.alive:
                    # Check if this is an enemy unit
                    is_enemy = (getattr(unit, 'is_enemy_unit', False) != getattr(other_unit, 'is_enemy_unit', False))
                    
                    if is_enemy:
                        distance = abs(other_unit.x - unit.x) + abs(other_unit.y - unit.y)
                        threat_level = other_unit.physical_attack / max(1, distance)
                        can_attack = distance <= other_unit.attack_range
                        
                        # Debug coordinate and range calculations
                        print(f"🔍 AI Range Debug: {other_unit.name} -> {unit.name}")
                        print(f"   {other_unit.name} position: ({other_unit.x}, {other_unit.y})")
                        print(f"   {unit.name} position: ({unit.x}, {unit.y})")
                        print(f"   Distance: {distance} (Manhattan)")
                        print(f"   {other_unit.name} attack_range: {other_unit.attack_range}")
                        print(f"   Can attack: {can_attack}")
                        
                        threats.append({
                            'unit_name': other_unit.name,
                            'distance': distance,
                            'threat_level': threat_level,
                            'can_attack_me': can_attack,
                            'position': {'x': other_unit.x, 'y': other_unit.y}
                        })
            
            return ToolResult(
                success=True,
                data={'threats': threats}
            )
        except Exception as e:
            return ToolResult(success=False, error_message=str(e))
    
    def _get_battlefield_state(self) -> ToolResult:
        """Get comprehensive battlefield state with tactical analysis."""
        try:
            # Get basic game state
            basic_state = self._get_game_state()
            if not basic_state.success:
                return basic_state
            
            battlefield_data = basic_state.data.copy()
            
            # Add detailed grid occupancy information
            battlefield_data['grid_occupancy'] = self._analyze_grid_occupancy()
            
            # Add tactical analysis for each unit
            battlefield_data['tactical_analysis'] = self._analyze_tactical_situation()
            
            return ToolResult(success=True, data=battlefield_data)
        except Exception as e:
            return ToolResult(success=False, error_message=str(e))
    
    def _analyze_grid_occupancy(self) -> Dict[str, Any]:
        """Analyze which grid tiles are occupied and by whom."""
        occupancy = {
            'occupied_tiles': {},
            'free_tiles': [],
            'unit_positions': {}
        }
        
        try:
            # Map all occupied positions
            for unit in self.game_controller.units:
                if unit.alive:
                    position = (unit.x, unit.y)
                    occupancy['occupied_tiles'][f"{unit.x},{unit.y}"] = {
                        'unit_name': unit.name,
                        'is_enemy': getattr(unit, 'is_enemy_unit', False),
                        'hp': unit.hp,
                        'max_hp': unit.max_hp,
                        'ap': getattr(unit, 'ap', 0)
                    }
                    occupancy['unit_positions'][unit.name] = {'x': unit.x, 'y': unit.y}
            
            # Find all free tiles
            for x in range(self.game_controller.grid.width):
                for y in range(self.game_controller.grid.height):
                    if f"{x},{y}" not in occupancy['occupied_tiles']:
                        occupancy['free_tiles'].append({'x': x, 'y': y})
            
            return occupancy
        except Exception as e:
            print(f"⚠️ Error analyzing grid occupancy: {e}")
            return occupancy
    
    def _analyze_tactical_situation(self) -> Dict[str, Any]:
        """Analyze tactical situation for all units."""
        tactical_analysis = {}
        
        try:
            for unit in self.game_controller.units:
                if unit.alive:
                    unit_analysis = self._analyze_unit_tactical_options(unit)
                    tactical_analysis[unit.name] = unit_analysis
            
            return tactical_analysis
        except Exception as e:
            print(f"⚠️ Error analyzing tactical situation: {e}")
            return tactical_analysis
    
    def _analyze_unit_tactical_options(self, unit) -> Dict[str, Any]:
        """Analyze tactical options for a specific unit."""
        analysis = {
            'position': {'x': unit.x, 'y': unit.y},
            'movement_options': [],
            'attack_targets': [],
            'ability_targets': [],
            'talent_effects': {},
            'threats': [],
            'opportunities': []
        }
        
        try:
            # Analyze movement options
            analysis['movement_options'] = self._get_movement_options(unit)
            
            # Analyze attack targets
            analysis['attack_targets'] = self._get_attack_targets(unit)
            
            # Analyze ability targets
            analysis['ability_targets'] = self._get_ability_targets(unit)
            
            # Analyze talent effects
            analysis['talent_effects'] = self._analyze_talent_effects(unit)
            
            # Analyze threats to this unit
            analysis['threats'] = self._analyze_threats_to_unit(unit)
            
            # Analyze tactical opportunities
            analysis['opportunities'] = self._analyze_tactical_opportunities(unit)
            
            return analysis
        except Exception as e:
            print(f"⚠️ Error analyzing unit {unit.name}: {e}")
            return analysis
    
    def _get_movement_options(self, unit) -> List[Dict[str, Any]]:
        """Get all possible movement positions for a unit."""
        movement_options = []
        
        try:
            current_move_points = getattr(unit, 'current_move_points', 3)
            
            # Check all positions within movement range
            for dx in range(-current_move_points, current_move_points + 1):
                for dy in range(-current_move_points, current_move_points + 1):
                    # Use Manhattan distance for tactical RPG movement
                    distance = abs(dx) + abs(dy)
                    if distance <= current_move_points and distance > 0:
                        target_x = unit.x + dx
                        target_y = unit.y + dy
                        
                        # Check if position is valid and unoccupied
                        if (self.game_controller.grid.is_valid(target_x, target_y) and 
                            not self.game_controller.grid.get_unit_at(target_x, target_y)):
                            
                            movement_options.append({
                                'x': target_x,
                                'y': target_y,
                                'distance': distance,
                                'strategic_value': self._evaluate_position_value(unit, target_x, target_y)
                            })
            
            return movement_options
        except Exception as e:
            print(f"⚠️ Error getting movement options: {e}")
            return movement_options
    
    def _get_attack_targets(self, unit) -> List[Dict[str, Any]]:
        """Get all units that can be attacked from current position."""
        attack_targets = []
        
        try:
            attack_range = getattr(unit, 'attack_range', 1)
            
            for other_unit in self.game_controller.units:
                if (other_unit != unit and other_unit.alive and 
                    getattr(unit, 'is_enemy_unit', False) != getattr(other_unit, 'is_enemy_unit', False)):
                    
                    distance = abs(other_unit.x - unit.x) + abs(other_unit.y - unit.y)
                    if distance <= attack_range:
                        attack_targets.append({
                            'unit_name': other_unit.name,
                            'position': {'x': other_unit.x, 'y': other_unit.y},
                            'distance': distance,
                            'hp': other_unit.hp,
                            'max_hp': other_unit.max_hp,
                            'estimated_damage': getattr(unit, 'physical_attack', 10),
                            'priority': self._calculate_target_priority(unit, other_unit)
                        })
            
            return attack_targets
        except Exception as e:
            print(f"⚠️ Error getting attack targets: {e}")
            return attack_targets
    
    def _get_ability_targets(self, unit) -> List[Dict[str, Any]]:
        """Get all units that can be targeted with abilities."""
        ability_targets = []
        
        try:
            magic_range = getattr(unit, 'magic_range', 2)
            
            for other_unit in self.game_controller.units:
                if other_unit != unit and other_unit.alive:
                    distance = abs(other_unit.x - unit.x) + abs(other_unit.y - unit.y)
                    if distance <= magic_range:
                        # Determine if this is an enemy or ally target
                        is_enemy = (getattr(unit, 'is_enemy_unit', False) != getattr(other_unit, 'is_enemy_unit', False))
                        
                        ability_targets.append({
                            'unit_name': other_unit.name,
                            'position': {'x': other_unit.x, 'y': other_unit.y},
                            'distance': distance,
                            'hp': other_unit.hp,
                            'max_hp': other_unit.max_hp,
                            'is_enemy': is_enemy,
                            'estimated_damage': getattr(unit, 'magical_attack', 8) if is_enemy else 0,
                            'estimated_healing': 15 if not is_enemy else 0,  # Rough healing estimate
                            'priority': self._calculate_ability_target_priority(unit, other_unit, is_enemy)
                        })
            
            return ability_targets
        except Exception as e:
            print(f"⚠️ Error getting ability targets: {e}")
            return ability_targets
    
    def _analyze_talent_effects(self, unit) -> Dict[str, Any]:
        """Analyze what effects each talent can have on the battlefield."""
        talent_effects = {}
        
        try:
            # Get available talents for this unit
            if hasattr(unit, 'character_instance_id'):
                character = self.get_character_by_id(unit.character_instance_id)
                
                if character and hasattr(character, 'hotkey_abilities'):
                    hotkey_abilities = character.hotkey_abilities
                    
                    if isinstance(hotkey_abilities, list):
                        for slot_index, ability_data in enumerate(hotkey_abilities):
                            if ability_data is not None:
                                talent_id = ability_data.get('talent_id', f'talent_{slot_index + 1}')
                                talent_name = ability_data.get('name', 'Unknown Talent')
                                
                                # Analyze what this talent can affect
                                talent_analysis = self._analyze_talent_range_and_targets(unit, ability_data)
                                
                                talent_effects[talent_id] = {
                                    'name': talent_name,
                                    'slot_index': slot_index,
                                    'ap_cost': ability_data.get('cost', {}).get('ap', 1),
                                    'mp_cost': ability_data.get('cost', {}).get('mp', 0),
                                    'action_type': ability_data.get('action_type', 'unknown'),
                                    'targets': talent_analysis
                                }
            
            return talent_effects
        except Exception as e:
            print(f"⚠️ Error analyzing talent effects: {e}")
            return talent_effects
    
    def _analyze_talent_range_and_targets(self, unit, ability_data) -> List[Dict[str, Any]]:
        """Analyze what targets a talent can affect."""
        targets = []
        
        try:
            # Get talent range (default to magic range if not specified)
            talent_range = ability_data.get('range', getattr(unit, 'magic_range', 2))
            action_type = ability_data.get('action_type', 'attack').lower()
            
            for other_unit in self.game_controller.units:
                if other_unit != unit and other_unit.alive:
                    distance = abs(other_unit.x - unit.x) + abs(other_unit.y - unit.y)
                    
                    if distance <= talent_range:
                        is_enemy = (getattr(unit, 'is_enemy_unit', False) != getattr(other_unit, 'is_enemy_unit', False))
                        
                        # Determine if this talent would be effective on this target
                        effective = False
                        estimated_effect = 0
                        
                        if action_type == 'attack' and is_enemy:
                            effective = True
                            estimated_effect = getattr(unit, 'magical_attack', 8)
                        elif action_type == 'heal' and not is_enemy and other_unit.hp < other_unit.max_hp:
                            effective = True
                            estimated_effect = min(15, other_unit.max_hp - other_unit.hp)
                        elif action_type == 'buff' and not is_enemy:
                            effective = True
                            estimated_effect = 5  # Rough buff value
                        elif action_type == 'debuff' and is_enemy:
                            effective = True
                            estimated_effect = 3  # Rough debuff value
                        
                        if effective:
                            targets.append({
                                'unit_name': other_unit.name,
                                'position': {'x': other_unit.x, 'y': other_unit.y},
                                'distance': distance,
                                'is_enemy': is_enemy,
                                'estimated_effect': estimated_effect,
                                'current_hp': other_unit.hp,
                                'max_hp': other_unit.max_hp,
                                'effectiveness_score': self._calculate_talent_effectiveness(unit, other_unit, ability_data)
                            })
            
            return targets
        except Exception as e:
            print(f"⚠️ Error analyzing talent range: {e}")
            return targets
    
    def _analyze_threats_to_unit(self, unit) -> List[Dict[str, Any]]:
        """Analyze threats that can affect this unit."""
        threats = []
        
        try:
            for other_unit in self.game_controller.units:
                if (other_unit != unit and other_unit.alive and 
                    getattr(unit, 'is_enemy_unit', False) != getattr(other_unit, 'is_enemy_unit', False)):
                    
                    # Check if other unit can attack this unit
                    attack_range = getattr(other_unit, 'attack_range', 1)
                    magic_range = getattr(other_unit, 'magic_range', 2)
                    distance = abs(other_unit.x - unit.x) + abs(other_unit.y - unit.y)
                    
                    threat_level = 0
                    can_attack = distance <= attack_range
                    can_cast = distance <= magic_range
                    
                    if can_attack:
                        threat_level += getattr(other_unit, 'physical_attack', 10)
                    if can_cast:
                        threat_level += getattr(other_unit, 'magical_attack', 8)
                    
                    if threat_level > 0:
                        threats.append({
                            'unit_name': other_unit.name,
                            'position': {'x': other_unit.x, 'y': other_unit.y},
                            'distance': distance,
                            'threat_level': threat_level,
                            'can_attack': can_attack,
                            'can_cast': can_cast,
                            'estimated_damage': threat_level,
                            'priority': threat_level / max(1, distance)  # Closer threats are more dangerous
                        })
            
            # Sort threats by priority (highest first)
            threats.sort(key=lambda x: x['priority'], reverse=True)
            return threats
        except Exception as e:
            print(f"⚠️ Error analyzing threats: {e}")
            return threats
    
    def _analyze_tactical_opportunities(self, unit) -> List[Dict[str, Any]]:
        """Analyze tactical opportunities available to this unit."""
        opportunities = []
        
        try:
            # Look for low-health enemies that can be finished off
            for other_unit in self.game_controller.units:
                if (other_unit != unit and other_unit.alive and 
                    getattr(unit, 'is_enemy_unit', False) != getattr(other_unit, 'is_enemy_unit', False)):
                    
                    distance = abs(other_unit.x - unit.x) + abs(other_unit.y - unit.y)
                    
                    # Check if unit can be killed
                    can_kill_with_attack = (distance <= getattr(unit, 'attack_range', 1) and 
                                          other_unit.hp <= getattr(unit, 'physical_attack', 10))
                    can_kill_with_ability = (distance <= getattr(unit, 'magic_range', 2) and 
                                           other_unit.hp <= getattr(unit, 'magical_attack', 8))
                    
                    if can_kill_with_attack:
                        opportunities.append({
                            'type': 'kill_opportunity',
                            'target': other_unit.name,
                            'position': {'x': other_unit.x, 'y': other_unit.y},
                            'action': 'attack',
                            'priority': 10,  # High priority for kills
                            'description': f"Can kill {other_unit.name} with attack"
                        })
                    
                    if can_kill_with_ability:
                        opportunities.append({
                            'type': 'kill_opportunity',
                            'target': other_unit.name,
                            'position': {'x': other_unit.x, 'y': other_unit.y},
                            'action': 'ability',
                            'priority': 10,
                            'description': f"Can kill {other_unit.name} with ability"
                        })
            
            # Look for healing opportunities
            for other_unit in self.game_controller.units:
                if (other_unit != unit and other_unit.alive and 
                    getattr(unit, 'is_enemy_unit', False) == getattr(other_unit, 'is_enemy_unit', False) and
                    other_unit.hp < other_unit.max_hp * 0.5):  # Less than 50% HP
                    
                    distance = abs(other_unit.x - unit.x) + abs(other_unit.y - unit.y)
                    if distance <= getattr(unit, 'magic_range', 2):
                        opportunities.append({
                            'type': 'healing_opportunity',
                            'target': other_unit.name,
                            'position': {'x': other_unit.x, 'y': other_unit.y},
                            'action': 'heal',
                            'priority': 7,  # Medium-high priority for healing
                            'description': f"Can heal {other_unit.name} ({other_unit.hp}/{other_unit.max_hp} HP)"
                        })
            
            # Sort opportunities by priority
            opportunities.sort(key=lambda x: x['priority'], reverse=True)
            return opportunities
        except Exception as e:
            print(f"⚠️ Error analyzing opportunities: {e}")
            return opportunities
    
    def _evaluate_position_value(self, unit, x: int, y: int) -> float:
        """Evaluate the strategic value of a position."""
        try:
            value = 0.0
            
            # Distance to enemies (closer can be better for attack, farther for safety)
            enemy_distances = []
            for other_unit in self.game_controller.units:
                if (other_unit != unit and other_unit.alive and 
                    getattr(unit, 'is_enemy_unit', False) != getattr(other_unit, 'is_enemy_unit', False)):
                    distance = abs(other_unit.x - x) + abs(other_unit.y - y)
                    enemy_distances.append(distance)
            
            if enemy_distances:
                avg_enemy_distance = sum(enemy_distances) / len(enemy_distances)
                min_enemy_distance = min(enemy_distances)
                
                # Prefer positions within attack range but not too close
                if min_enemy_distance <= getattr(unit, 'attack_range', 1):
                    value += 3.0  # Can attack from here
                elif min_enemy_distance <= getattr(unit, 'magic_range', 2):
                    value += 2.0  # Can cast from here
                
                # Avoid being too close to multiple enemies
                enemies_in_range = sum(1 for d in enemy_distances if d <= 2)
                if enemies_in_range > 1:
                    value -= enemies_in_range * 0.5
            
            # Prefer center positions (more tactical options)
            center_x = self.game_controller.grid.width // 2
            center_y = self.game_controller.grid.height // 2
            distance_to_center = abs(x - center_x) + abs(y - center_y)
            max_distance = center_x + center_y
            value += (max_distance - distance_to_center) * 0.1
            
            return value
        except Exception as e:
            return 0.0
    
    def _calculate_target_priority(self, attacker, target) -> float:
        """Calculate target priority for attacks."""
        try:
            priority = 0.0
            
            # Prefer low-health targets
            hp_percentage = target.hp / target.max_hp
            priority += (1.0 - hp_percentage) * 5.0
            
            # Prefer closer targets
            distance = abs(target.x - attacker.x) + abs(target.y - attacker.y)
            priority += max(0, 5 - distance)
            
            # Prefer targets that can be killed
            estimated_damage = getattr(attacker, 'physical_attack', 10)
            if target.hp <= estimated_damage:
                priority += 10.0  # High priority for kills
            
            return priority
        except Exception as e:
            return 0.0
    
    def _calculate_ability_target_priority(self, caster, target, is_enemy: bool) -> float:
        """Calculate target priority for abilities."""
        try:
            priority = 0.0
            
            if is_enemy:
                # Enemy target - prefer low health for kills
                hp_percentage = target.hp / target.max_hp
                priority += (1.0 - hp_percentage) * 3.0
                
                estimated_damage = getattr(caster, 'magical_attack', 8)
                if target.hp <= estimated_damage:
                    priority += 8.0  # High priority for magical kills
            else:
                # Ally target - prefer low health for healing
                hp_percentage = target.hp / target.max_hp
                if hp_percentage < 0.5:  # Only heal if below 50%
                    priority += (1.0 - hp_percentage) * 4.0
            
            # Prefer closer targets
            distance = abs(target.x - caster.x) + abs(target.y - caster.y)
            priority += max(0, 3 - distance)
            
            return priority
        except Exception as e:
            return 0.0
    
    def _calculate_talent_effectiveness(self, caster, target, ability_data) -> float:
        """Calculate how effective a talent would be on a target."""
        try:
            effectiveness = 0.0
            action_type = ability_data.get('action_type', 'attack').lower()
            
            if action_type == 'attack':
                # More effective against low-health enemies
                hp_percentage = target.hp / target.max_hp
                effectiveness = (1.0 - hp_percentage) * 3.0
                
                # Bonus if it can kill
                estimated_damage = getattr(caster, 'magical_attack', 8)
                if target.hp <= estimated_damage:
                    effectiveness += 5.0
            
            elif action_type == 'heal':
                # More effective on low-health allies
                hp_percentage = target.hp / target.max_hp
                if hp_percentage < 0.8:  # Only effective if not near full health
                    effectiveness = (1.0 - hp_percentage) * 4.0
            
            elif action_type == 'buff':
                # More effective on healthy allies
                hp_percentage = target.hp / target.max_hp
                effectiveness = hp_percentage * 2.0
            
            elif action_type == 'debuff':
                # More effective on healthy enemies
                hp_percentage = target.hp / target.max_hp
                effectiveness = hp_percentage * 2.0
            
            return effectiveness
        except Exception as e:
            return 0.0
    
    def _get_tactical_analysis(self, unit_id: str) -> ToolResult:
        """Get comprehensive tactical analysis for a unit with move-action combinations."""
        try:
            unit = self._find_unit_by_id(unit_id)
            if not unit:
                return ToolResult(success=False, error_message=f"Unit '{unit_id}' not found")
            
            # Get enemy units
            enemy_units = self._get_enemy_units(unit)
            
            # Calculate all possible move-action combinations
            move_action_combinations = self._calculate_move_action_combinations(unit, enemy_units)
            
            # Find the optimal combination
            optimal_combination = self._find_optimal_combination(move_action_combinations)
            
            return ToolResult(
                success=True,
                data={
                    'unit_id': unit_id,
                    'unit_position': {'x': unit.x, 'y': unit.y},
                    'current_ap': getattr(unit, 'ap', 0),
                    'enemy_units': enemy_units,
                    'move_action_combinations': move_action_combinations,
                    'optimal_combination': optimal_combination
                }
            )
            
        except Exception as e:
            return ToolResult(success=False, error_message=f"Tactical analysis failed: {str(e)}")
    
    def _get_enemy_units(self, unit) -> List[Dict[str, Any]]:
        """Get list of enemy units with their positions."""
        enemy_units = []
        
        try:
            for other_unit in self.game_controller.units:
                if (other_unit != unit and other_unit.alive and 
                    getattr(unit, 'is_enemy_unit', False) != getattr(other_unit, 'is_enemy_unit', False)):
                    
                    enemy_units.append({
                        'name': other_unit.name,
                        'position': {'x': other_unit.x, 'y': other_unit.y},
                        'hp': other_unit.hp,
                        'max_hp': other_unit.max_hp,
                        'physical_defense': getattr(other_unit, 'physical_defense', 0),
                        'magical_defense': getattr(other_unit, 'magical_defense', 0)
                    })
        except Exception as e:
            print(f"⚠️ Error getting enemy units: {e}")
        
        return enemy_units
    
    def _calculate_move_action_combinations(self, unit, enemy_units) -> List[Dict[str, Any]]:
        """Calculate all possible move-action combinations and their damage potential."""
        combinations = []
        
        try:
            current_ap = getattr(unit, 'ap', 0)
            current_move_points = getattr(unit, 'current_move_points', 3)
            
            # Get all possible move positions (including current position)
            move_positions = self._get_all_move_positions(unit, current_move_points)
            move_positions.append({'x': unit.x, 'y': unit.y, 'distance': 0})  # Include staying put
            
            # For each move position, calculate possible actions
            for move_pos in move_positions:
                move_distance = move_pos['distance']
                move_ap_cost = move_distance  # Assume 1 AP per move
                
                # Skip if we can't afford the move
                if move_ap_cost > current_ap:
                    continue
                
                ap_after_move = current_ap - move_ap_cost
                
                # Calculate damage potential from this position
                damage_options = self._calculate_damage_from_position(
                    unit, move_pos, enemy_units, ap_after_move
                )
                
                # Create combination entry
                best_action = max(damage_options, key=lambda x: x['total_damage']) if damage_options else None
                
                # Debug: Uncomment for talent debugging
                # if best_action and len(damage_options) > 1:
                #     talent_options_in_list = [opt for opt in damage_options if opt.get('action_type') == 'talent']
                #     if talent_options_in_list:
                #         print(f"🔍 Best action selected: {best_action.get('action_type')} (talent options available: {len(talent_options_in_list)})")
                #         print(f"🔍 Damage comparison - Best: {best_action.get('total_damage')}, Talents: {[opt.get('total_damage') for opt in talent_options_in_list]}")
                
                combination = {
                    'move_to': move_pos,
                    'move_ap_cost': move_ap_cost,
                    'ap_after_move': ap_after_move,
                    'damage_options': damage_options,
                    'max_damage': max([opt['total_damage'] for opt in damage_options] + [0]),
                    'best_action': best_action
                }
                
                combinations.append(combination)
            
            # Sort by maximum damage potential
            combinations.sort(key=lambda x: x['max_damage'], reverse=True)
            
        except Exception as e:
            print(f"⚠️ Error calculating move-action combinations: {e}")
        
        return combinations
    
    def _get_all_move_positions(self, unit, move_points) -> List[Dict[str, Any]]:
        """Get all valid move positions within movement range."""
        positions = []
        
        try:
            # Check all positions within movement range
            for dx in range(-move_points, move_points + 1):
                for dy in range(-move_points, move_points + 1):
                    distance = abs(dx) + abs(dy)  # Manhattan distance
                    if distance <= move_points and distance > 0:
                        target_x = unit.x + dx
                        target_y = unit.y + dy
                        
                        # Check if position is valid and unoccupied
                        if (self.game_controller.grid.is_valid(target_x, target_y) and 
                            not self.game_controller.grid.get_unit_at(target_x, target_y)):
                            
                            positions.append({
                                'x': target_x,
                                'y': target_y,
                                'distance': distance
                            })
        
        except Exception as e:
            print(f"⚠️ Error getting move positions: {e}")
        
        return positions
    
    def _calculate_damage_from_position(self, unit, position, enemy_units, available_ap) -> List[Dict[str, Any]]:
        """Calculate damage potential from a specific position."""
        damage_options = []
        
        try:
            unit_x, unit_y = position['x'], position['y']
            
            # Get unit's combat stats
            attack_range = getattr(unit, 'attack_range', 1)
            magic_range = getattr(unit, 'magic_range', 2)
            physical_attack = getattr(unit, 'physical_attack', 10)
            magical_attack = getattr(unit, 'magical_attack', 8)
            
            # Check each enemy unit
            for enemy in enemy_units:
                enemy_x, enemy_y = enemy['position']['x'], enemy['position']['y']
                distance = abs(enemy_x - unit_x) + abs(enemy_y - unit_y)
                
                # Attack option
                if distance <= attack_range and available_ap >= 1:
                    attack_damage = max(1, physical_attack - enemy['physical_defense'])
                    damage_options.append({
                        'action_type': 'attack',
                        'target': enemy['name'],
                        'target_position': enemy['position'],
                        'ap_cost': 1,
                        'damage': attack_damage,
                        'total_damage': attack_damage,
                        'can_kill': attack_damage >= enemy['hp']
                    })
                
                # Get talent options first
                talent_options = self._get_talent_damage_options(unit, enemy, distance, available_ap)
                has_combat_talents = len(talent_options) > 0
                
                # Debug talent detection (comment out when not needed)
                # if has_combat_talents:
                #     print(f"🔍 {unit.name} has {len(talent_options)} combat talents vs {enemy['name']}")
                # else:
                #     print(f"🔍 {unit.name} has NO combat talents vs {enemy['name']}, creating generic ability")
                
                # Magic ability option (only if no combat talents are available)
                if distance <= magic_range and available_ap >= 2 and not has_combat_talents:
                    magic_damage = max(1, magical_attack - enemy['magical_defense'])
                    damage_options.append({
                        'action_type': 'ability',
                        'target': enemy['name'],
                        'target_position': enemy['position'],
                        'ap_cost': 2,
                        'damage': magic_damage,
                        'total_damage': magic_damage,
                        'can_kill': magic_damage >= enemy['hp']
                    })
                
                # Add talent options
                damage_options.extend(talent_options)
            
            # Sort by total damage
            damage_options.sort(key=lambda x: x['total_damage'], reverse=True)
            
        except Exception as e:
            print(f"⚠️ Error calculating damage from position: {e}")
        
        return damage_options
    
    def _get_talent_damage_options(self, unit, enemy, distance, available_ap) -> List[Dict[str, Any]]:
        """Get talent damage options for a specific enemy."""
        talent_options = []
        
        try:
            if hasattr(unit, 'character_instance_id'):
                character = self.get_character_by_id(unit.character_instance_id)
                
                if character and hasattr(character, 'hotkey_abilities'):
                    hotkey_abilities = character.hotkey_abilities
                    
                    if isinstance(hotkey_abilities, list):
                        for slot_index, ability_data in enumerate(hotkey_abilities):
                            if ability_data is not None:
                                talent_id = ability_data.get('talent_id', f'talent_{slot_index + 1}')
                                talent_name = ability_data.get('name', 'Unknown Talent')
                                
                                # Get talent costs - handle both old and new format
                                cost_data = ability_data.get('cost', {})
                                ap_cost = cost_data.get('ap_cost', cost_data.get('ap', 1))
                                
                                # Get talent range (default to magic range)
                                talent_range = ability_data.get('range', getattr(unit, 'magic_range', 2))
                                
                                # Check if we can afford this talent
                                if ap_cost > available_ap:
                                    continue
                                
                                # Check if enemy is in range
                                if distance > talent_range:
                                    continue
                                
                                action_type = ability_data.get('action_type', 'attack').lower()
                                
                                # Only create damage options for offensive talents
                                # Combat talents typically have these action types or damage effects
                                is_combat_talent = (
                                    action_type in ['attack', 'ability', 'spell', 'magic', 'combat'] or
                                    'damage' in str(ability_data.get('effects', {})).lower() or
                                    'attack' in talent_name.lower() or
                                    'strike' in talent_name.lower() or
                                    'blast' in talent_name.lower() or
                                    'bolt' in talent_name.lower()
                                )
                                
                                if is_combat_talent:
                                    # Calculate talent damage - use the higher of physical or magical attack
                                    physical_damage = max(1, getattr(unit, 'physical_attack', 10) - enemy['physical_defense'])
                                    magical_damage = max(1, getattr(unit, 'magical_attack', 8) - enemy['magical_defense'])
                                    base_talent_damage = max(physical_damage, magical_damage)
                                    
                                    # Boost talent damage significantly to make them competitive with basic attacks
                                    talent_damage = int(base_talent_damage * 1.5)  # 50% bonus for talents
                                    
                                    talent_option = {
                                        'action_type': 'talent',
                                        'talent_id': talent_id,
                                        'talent_name': talent_name,
                                        'slot_index': slot_index,
                                        'target': enemy['name'],
                                        'target_position': enemy['position'],
                                        'ap_cost': ap_cost,
                                        'damage': talent_damage,
                                        'total_damage': talent_damage,
                                        'can_kill': talent_damage >= enemy['hp']
                                    }
                                    talent_options.append(talent_option)
        
        except Exception as e:
            print(f"⚠️ Error getting talent options: {e}")
        
        return talent_options
    
    def _find_optimal_combination(self, combinations) -> Dict[str, Any]:
        """Find the optimal move-action combination."""
        if not combinations:
            return None
        
        # Find combination with highest damage potential
        best_combination = max(combinations, key=lambda x: x['max_damage'])
        
        return {
            'move_to': best_combination['move_to'],
            'action': best_combination['best_action'],
            'total_damage': best_combination['max_damage'],
            'ap_required': best_combination['move_ap_cost'] + (best_combination['best_action']['ap_cost'] if best_combination['best_action'] else 0)
        }
    
    def _find_unit_by_id(self, unit_id: str):
        """Find unit by ID (using name for now)."""
        # Extract unit name from ID (format: "Name_12345")
        unit_name = unit_id.split('_')[0]
        for unit in self.game_controller.units:
            if unit.name == unit_name:
                return unit
        return None
    
    def get_character_by_id(self, character_instance_id: str):
        """Get character instance by ID from character state manager."""
        try:
            if hasattr(self.game_controller, 'character_state_manager'):
                return self.game_controller.character_state_manager.get_character_instance(character_instance_id)
            return None
        except Exception as e:
            print(f"⚠️ Error getting character by ID: {e}")
            return None