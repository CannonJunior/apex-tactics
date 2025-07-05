"""
Talent-Specific MCP Tools

Provides MCP tools for talent execution, analysis, and AI decision-making.
Integrates with existing MCP gateway and tactical game systems.
"""

from typing import Dict, List, Any, Optional
import json
import asyncio

try:
    from fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️ FastMCP not available - talent MCP tools will be disabled")

try:
    from .models import (
        ActionRequest, ActionResponse, AnalysisRequest, AnalysisResponse,
        ErrorResponse, GameStateResponse
    )
    from ..game.controllers.tactical_rpg_controller import TacticalRPG
    from ..core.assets.data_manager import get_data_manager
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    print("⚠️ MCP models not available - using fallback implementations")


# Initialize MCP instance for talent tools
if MCP_AVAILABLE:
    mcp = FastMCP("TalentTools")
else:
    class MockMCP:
        def tool(self, func):
            return func
        def resource(self, name):
            def decorator(func):
                return func
            return decorator
    mcp = MockMCP()


@mcp.tool
async def execute_talent_mcp(
    talent_id: str,
    target_x: int,
    target_y: int,
    unit_id: Optional[str] = None,
    session_id: str = "default"
) -> Dict[str, Any]:
    """
    Execute a talent via MCP interface.
    
    Args:
        talent_id: Unique identifier for the talent (e.g., "basic_strike", "fireball")
        target_x: Target X coordinate on the battlefield grid
        target_y: Target Y coordinate on the battlefield grid  
        unit_id: Optional unit identifier (uses active unit if not specified)
        session_id: Game session identifier
        
    Returns:
        Execution result with success status, effects applied, and resource costs
    """
    try:
        # Validate inputs
        if not talent_id:
            return _create_error_response("INVALID_TALENT_ID", "Talent ID is required")
        
        if not isinstance(target_x, int) or not isinstance(target_y, int):
            return _create_error_response("INVALID_COORDINATES", "Target coordinates must be integers")
        
        # Get talent data
        talent_data = await _get_talent_data(talent_id)
        if not talent_data:
            return _create_error_response("TALENT_NOT_FOUND", f"Talent '{talent_id}' not found")
        
        # Validate talent availability
        availability_check = await _check_talent_availability(talent_id, unit_id)
        if not availability_check['available']:
            return _create_error_response("TALENT_NOT_AVAILABLE", availability_check['reason'])
        
        # Validate target position
        target_validation = await _validate_target_position(talent_data, target_x, target_y)
        if not target_validation['valid']:
            return _create_error_response("INVALID_TARGET", target_validation['reason'])
        
        # Execute talent
        execution_result = await _execute_talent_action(talent_data, target_x, target_y, unit_id)
        
        return {
            "success": True,
            "talent_id": talent_id,
            "target_position": {"x": target_x, "y": target_y},
            "damage_dealt": execution_result.get('damage_dealt', 0),
            "healing_applied": execution_result.get('healing_applied', 0),
            "effects_applied": execution_result.get('effects_applied', []),
            "resource_costs": execution_result.get('resource_costs', {}),
            "targets_affected": execution_result.get('targets_affected', []),
            "execution_time": execution_result.get('execution_time', 0)
        }
        
    except Exception as e:
        return _create_error_response("EXECUTION_ERROR", f"Failed to execute talent: {str(e)}")


@mcp.tool
async def get_available_talents_mcp(
    unit_id: Optional[str] = None,
    include_cooldowns: bool = True,
    include_costs: bool = True
) -> Dict[str, Any]:
    """
    Get available talents for specified unit.
    
    Args:
        unit_id: Target unit identifier (uses active unit if not specified)
        include_cooldowns: Whether to include cooldown information
        include_costs: Whether to include resource cost information
        
    Returns:
        List of available talents with detailed information
    """
    try:
        # Get unit data
        unit_data = await _get_unit_data(unit_id)
        if not unit_data:
            return _create_error_response("UNIT_NOT_FOUND", "Unit not found or not active")
        
        # Get available talents
        available_talents = []
        hotkey_abilities = unit_data.get('hotkey_abilities', {})
        
        for slot, ability_data in hotkey_abilities.items():
            if 'talent_id' in ability_data:
                talent_id = ability_data['talent_id']
                talent_info = await _get_detailed_talent_info(
                    talent_id, 
                    include_cooldowns,
                    include_costs
                )
                
                if talent_info:
                    talent_info['hotkey_slot'] = slot
                    available_talents.append(talent_info)
        
        return {
            "success": True,
            "unit_id": unit_id or "active",
            "talent_count": len(available_talents),
            "available_talents": available_talents,
            "unit_resources": await _get_unit_resources(unit_id)
        }
        
    except Exception as e:
        return _create_error_response("QUERY_ERROR", f"Failed to get available talents: {str(e)}")


@mcp.tool
async def analyze_talent_effectiveness_mcp(
    talent_id: str,
    target_position: Dict[str, int],
    scenario_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze talent effectiveness at target position.
    
    Args:
        talent_id: Talent to analyze
        target_position: Target position with 'x' and 'y' coordinates
        scenario_context: Optional battlefield context for analysis
        
    Returns:
        Effectiveness analysis with damage predictions, tactical value, and recommendations
    """
    try:
        # Validate inputs
        if not target_position or 'x' not in target_position or 'y' not in target_position:
            return _create_error_response("INVALID_TARGET", "Target position must include 'x' and 'y' coordinates")
        
        # Get talent data
        talent_data = await _get_talent_data(talent_id)
        if not talent_data:
            return _create_error_response("TALENT_NOT_FOUND", f"Talent '{talent_id}' not found")
        
        # Analyze effectiveness
        target_x = target_position['x']
        target_y = target_position['y']
        
        effectiveness_analysis = await _analyze_talent_at_position(
            talent_data, 
            target_x, 
            target_y,
            scenario_context or {}
        )
        
        return {
            "success": True,
            "talent_id": talent_id,
            "target_position": target_position,
            "effectiveness_score": effectiveness_analysis['score'],
            "predicted_damage": effectiveness_analysis['predicted_damage'],
            "targets_in_range": effectiveness_analysis['targets_in_range'],
            "tactical_advantages": effectiveness_analysis['advantages'],
            "potential_risks": effectiveness_analysis['risks'],
            "alternative_positions": effectiveness_analysis['alternatives'],
            "recommendation": effectiveness_analysis['recommendation']
        }
        
    except Exception as e:
        return _create_error_response("ANALYSIS_ERROR", f"Failed to analyze talent effectiveness: {str(e)}")


@mcp.tool
async def get_talent_synergies_mcp(
    primary_talent_id: str,
    available_talents: Optional[List[str]] = None,
    turns_ahead: int = 3
) -> Dict[str, Any]:
    """
    Analyze talent synergies and combinations.
    
    Args:
        primary_talent_id: Primary talent to find synergies for
        available_talents: List of available talent IDs (auto-detected if not provided)
        turns_ahead: Number of turns to plan ahead for synergy analysis
        
    Returns:
        Synergy analysis with optimal combinations and timing
    """
    try:
        # Get talent data
        primary_talent = await _get_talent_data(primary_talent_id)
        if not primary_talent:
            return _create_error_response("TALENT_NOT_FOUND", f"Primary talent '{primary_talent_id}' not found")
        
        # Get available talents if not provided
        if available_talents is None:
            available_response = await get_available_talents_mcp()
            if available_response.get('success'):
                available_talents = [t['id'] for t in available_response['available_talents']]
            else:
                available_talents = []
        
        # Analyze synergies
        synergy_analysis = await _analyze_talent_synergies(
            primary_talent,
            available_talents,
            turns_ahead
        )
        
        return {
            "success": True,
            "primary_talent": primary_talent_id,
            "synergy_combinations": synergy_analysis['combinations'],
            "optimal_sequence": synergy_analysis['optimal_sequence'],
            "resource_efficiency": synergy_analysis['resource_efficiency'],
            "timing_recommendations": synergy_analysis['timing'],
            "strategic_value": synergy_analysis['strategic_value']
        }
        
    except Exception as e:
        return _create_error_response("SYNERGY_ERROR", f"Failed to analyze talent synergies: {str(e)}")


# Helper functions for talent operations

async def _get_talent_data(talent_id: str) -> Optional[Dict[str, Any]]:
    """Get talent data from asset system."""
    try:
        data_manager = get_data_manager()
        all_talents = data_manager.get_all_talents()
        
        for talent in all_talents:
            if talent.id == talent_id:
                return {
                    'id': talent.id,
                    'name': talent.name,
                    'action_type': talent.action_type,
                    'level': talent.level,
                    'tier': talent.tier,
                    'description': talent.description,
                    'effects': talent.effects,
                    'cost': talent.cost,
                    'requirements': talent.requirements
                }
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error getting talent data: {e}")
        return None


async def _check_talent_availability(talent_id: str, unit_id: Optional[str]) -> Dict[str, Any]:
    """Check if talent is available for use."""
    # Placeholder implementation
    return {
        'available': True,
        'reason': 'Talent is available for use'
    }


async def _validate_target_position(talent_data: Dict[str, Any], target_x: int, target_y: int) -> Dict[str, Any]:
    """Validate target position for talent."""
    # Basic validation - can be enhanced with range checking
    if target_x < 0 or target_y < 0:
        return {
            'valid': False,
            'reason': 'Target coordinates must be non-negative'
        }
    
    return {
        'valid': True,
        'reason': 'Target position is valid'
    }


async def _execute_talent_action(talent_data: Dict[str, Any], target_x: int, target_y: int, unit_id: Optional[str]) -> Dict[str, Any]:
    """Execute talent action."""
    # Placeholder implementation - would integrate with actual game systems
    return {
        'damage_dealt': talent_data.get('effects', {}).get('base_damage', 0),
        'healing_applied': talent_data.get('effects', {}).get('healing_amount', 0),
        'effects_applied': ['talent_executed'],
        'resource_costs': talent_data.get('cost', {}),
        'targets_affected': [{'x': target_x, 'y': target_y}],
        'execution_time': 0.1
    }


async def _get_unit_data(unit_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Get unit data."""
    # Placeholder implementation
    return {
        'id': unit_id or 'active_unit',
        'hotkey_abilities': {
            '1': {'talent_id': 'basic_strike'},
            '2': {'talent_id': 'power_attack'}
        }
    }


async def _get_detailed_talent_info(talent_id: str, include_cooldowns: bool, include_costs: bool) -> Optional[Dict[str, Any]]:
    """Get detailed talent information."""
    talent_data = await _get_talent_data(talent_id)
    if not talent_data:
        return None
    
    info = talent_data.copy()
    
    if include_cooldowns:
        info['cooldown_remaining'] = 0  # Placeholder
    
    if include_costs:
        info['can_afford'] = True  # Placeholder
    
    return info


async def _get_unit_resources(unit_id: Optional[str]) -> Dict[str, Any]:
    """Get unit resource information."""
    return {
        'mp': 100,
        'max_mp': 100,
        'rage': 0,
        'max_rage': 100,
        'kwan': 50,
        'max_kwan': 100
    }


async def _analyze_talent_at_position(talent_data: Dict[str, Any], target_x: int, target_y: int, context: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze talent effectiveness at position."""
    # Placeholder analysis
    base_score = 0.7
    
    # Adjust score based on talent type
    action_type = talent_data.get('action_type', 'Attack')
    if action_type == 'Attack':
        base_score += 0.1
    elif action_type == 'Magic':
        base_score += 0.2
    
    return {
        'score': base_score,
        'predicted_damage': talent_data.get('effects', {}).get('base_damage', 0),
        'targets_in_range': 1,
        'advantages': ['Good positioning', 'Effective range'],
        'risks': ['Potential counter-attack'],
        'alternatives': [{'x': target_x + 1, 'y': target_y}, {'x': target_x, 'y': target_y + 1}],
        'recommendation': 'Recommended for current tactical situation'
    }


async def _analyze_talent_synergies(primary_talent: Dict[str, Any], available_talents: List[str], turns_ahead: int) -> Dict[str, Any]:
    """Analyze talent synergies."""
    return {
        'combinations': [
            {
                'talents': [primary_talent['id'], 'power_attack'],
                'synergy_score': 0.8,
                'description': 'Attack combination for high damage'
            }
        ],
        'optimal_sequence': [primary_talent['id'], 'power_attack'],
        'resource_efficiency': 0.75,
        'timing': {'turn_1': primary_talent['id'], 'turn_2': 'power_attack'},
        'strategic_value': 'High damage output combination'
    }


def _create_error_response(error_code: str, message: str) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "success": False,
        "error_code": error_code,
        "error_message": message,
        "timestamp": _get_current_timestamp()
    }


def _get_current_timestamp() -> float:
    """Get current timestamp."""
    import time
    return time.time()


# Register tools with MCP if available
if MCP_AVAILABLE:
    print("✅ Talent MCP tools registered successfully")
else:
    print("ℹ️ Talent MCP tools defined but not registered (FastMCP not available)")