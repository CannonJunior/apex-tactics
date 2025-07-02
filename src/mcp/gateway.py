"""
MCP Gateway Service

FastMCP gateway service that provides Model Context Protocol tools for AI agents
to interact with the Apex Tactics game engine.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog
import uvicorn
import httpx

from fastmcp import FastMCP
from fastmcp.tools import Tool

from .tools import (
    MoveUnitTool, AttackUnitTool, GetGameStateTool, 
    AnalyzeBattlefieldTool, GetAvailableActionsTool,
    EndTurnTool, UseItemTool, CastSpellTool
)
from .models import MCPRequest, MCPResponse, ToolCallResult
from .game_client import GameEngineClient

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global instances
game_client: Optional[GameEngineClient] = None
mcp_server: Optional[FastMCP] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global game_client, mcp_server
    
    logger.info("Starting MCP Gateway Service")
    
    # Initialize game engine client
    game_engine_url = "http://game-engine:8000"  # Default docker-compose URL
    game_client = GameEngineClient(game_engine_url)
    
    # Initialize FastMCP server
    mcp_server = FastMCP("Apex Tactics MCP Gateway")
    
    # Register MCP tools
    await _register_mcp_tools()
    
    logger.info("MCP Gateway Service started", tools_count=len(mcp_server.tools))
    
    yield
    
    # Cleanup
    logger.info("Shutting down MCP Gateway Service")
    if game_client:
        await game_client.close()

# Create FastAPI application
app = FastAPI(
    title="Apex Tactics MCP Gateway",
    description="Model Context Protocol gateway for AI agent integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def _register_mcp_tools():
    """Register all MCP tools with the FastMCP server"""
    global mcp_server, game_client
    
    if not mcp_server or not game_client:
        raise RuntimeError("MCP server or game client not initialized")
    
    # Initialize tools with game client
    tools = [
        MoveUnitTool(game_client),
        AttackUnitTool(game_client),
        GetGameStateTool(game_client),
        AnalyzeBattlefieldTool(game_client),
        GetAvailableActionsTool(game_client),
        EndTurnTool(game_client),
        UseItemTool(game_client),
        CastSpellTool(game_client),
    ]
    
    # Register each tool
    for tool in tools:
        mcp_server.add_tool(tool)
        logger.info("Registered MCP tool", tool_name=tool.name)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "service": "mcp-gateway",
        "version": "1.0.0",
        "mcp_tools": len(mcp_server.tools) if mcp_server else 0
    }

# MCP tool execution endpoints
@app.post("/mcp/call-tool", response_model=MCPResponse)
async def call_mcp_tool(request: MCPRequest) -> MCPResponse:
    """Execute an MCP tool call"""
    global mcp_server
    
    if not mcp_server:
        raise HTTPException(status_code=500, detail="MCP server not initialized")
    
    try:
        logger.info("MCP tool call", tool_name=request.tool_name, 
                   session_id=request.session_id)
        
        # Execute the tool
        result = await mcp_server.call_tool(request.tool_name, request.parameters)
        
        return MCPResponse(
            success=True,
            result=result,
            tool_name=request.tool_name,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error("MCP tool execution failed", 
                    tool_name=request.tool_name, error=str(e))
        
        return MCPResponse(
            success=False,
            error=str(e),
            tool_name=request.tool_name,
            session_id=request.session_id
        )

@app.get("/mcp/tools")
async def list_mcp_tools():
    """List all available MCP tools"""
    global mcp_server
    
    if not mcp_server:
        return {"tools": []}
    
    tools_info = []
    for tool_name, tool in mcp_server.tools.items():
        tools_info.append({
            "name": tool_name,
            "description": tool.description,
            "parameters": tool.parameters_schema
        })
    
    return {"tools": tools_info}

@app.get("/mcp/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get detailed information about a specific tool"""
    global mcp_server
    
    if not mcp_server or tool_name not in mcp_server.tools:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    tool = mcp_server.tools[tool_name]
    return {
        "name": tool_name,
        "description": tool.description,
        "parameters": tool.parameters_schema,
        "returns": getattr(tool, 'returns_schema', None)
    }

# Game state proxy endpoints
@app.get("/game/sessions/{session_id}/state")
async def get_game_state_proxy(session_id: str):
    """Proxy game state requests to game engine"""
    global game_client
    
    if not game_client:
        raise HTTPException(status_code=500, detail="Game client not initialized")
    
    try:
        state = await game_client.get_game_state(session_id)
        return state
    except Exception as e:
        logger.error("Failed to get game state", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get game state")

@app.post("/game/sessions/{session_id}/analyze")
async def analyze_battlefield(session_id: str, analysis_request: dict):
    """Analyze battlefield for AI decision making"""
    global game_client
    
    if not game_client:
        raise HTTPException(status_code=500, detail="Game client not initialized")
    
    try:
        # Get current game state
        game_state = await game_client.get_game_state(session_id)
        
        # Perform analysis based on request
        analysis_type = analysis_request.get("type", "tactical")
        
        if analysis_type == "tactical":
            analysis = await _perform_tactical_analysis(game_state)
        elif analysis_type == "strategic":
            analysis = await _perform_strategic_analysis(game_state)
        elif analysis_type == "threat":
            analysis = await _perform_threat_analysis(game_state)
        else:
            raise HTTPException(status_code=400, detail="Unknown analysis type")
        
        return {
            "session_id": session_id,
            "analysis_type": analysis_type,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error("Battlefield analysis failed", 
                    session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Analysis failed")

async def _perform_tactical_analysis(game_state: dict) -> dict:
    """Perform tactical analysis of current battlefield state"""
    units = game_state.get("units", [])
    current_unit_index = game_state.get("current_unit_index", 0)
    
    if not units or current_unit_index >= len(units):
        return {"error": "No valid current unit"}
    
    current_unit = units[current_unit_index]
    
    # Analyze possible moves
    possible_moves = []
    for x in range(game_state.get("grid_size", [10, 10])[0]):
        for y in range(game_state.get("grid_size", [10, 10])[1]):
            # Simple distance check (would be more sophisticated in real implementation)
            dx = abs(x - current_unit["position"][0])
            dy = abs(y - current_unit["position"][1])
            if dx + dy <= current_unit.get("move_points", 3):
                possible_moves.append({"x": x, "y": y, "cost": dx + dy})
    
    # Analyze potential targets
    potential_targets = []
    for unit in units:
        if unit["id"] != current_unit["id"] and unit["alive"]:
            dx = abs(unit["position"][0] - current_unit["position"][0])
            dy = abs(unit["position"][1] - current_unit["position"][1])
            distance = dx + dy
            
            potential_targets.append({
                "unit_id": unit["id"],
                "distance": distance,
                "threat_level": _calculate_threat_level(unit, current_unit),
                "vulnerability": _calculate_vulnerability(unit)
            })
    
    return {
        "current_unit": current_unit["id"],
        "possible_moves": possible_moves[:10],  # Limit results
        "potential_targets": sorted(potential_targets, key=lambda x: x["threat_level"], reverse=True)[:5],
        "recommendations": _generate_tactical_recommendations(current_unit, potential_targets)
    }

async def _perform_strategic_analysis(game_state: dict) -> dict:
    """Perform strategic analysis of overall game state"""
    units = game_state.get("units", [])
    
    # Analyze team composition and strengths
    team_analysis = {}
    for unit in units:
        team = "friendly" if unit.get("team") == "player" else "enemy"
        if team not in team_analysis:
            team_analysis[team] = {"units": [], "total_hp": 0, "total_power": 0}
        
        team_analysis[team]["units"].append(unit)
        team_analysis[team]["total_hp"] += unit["hp"]
        team_analysis[team]["total_power"] += _calculate_unit_power(unit)
    
    return {
        "team_analysis": team_analysis,
        "game_phase": _determine_game_phase(game_state),
        "strategic_recommendations": _generate_strategic_recommendations(team_analysis)
    }

async def _perform_threat_analysis(game_state: dict) -> dict:
    """Perform threat analysis for defensive planning"""
    units = game_state.get("units", [])
    current_unit_index = game_state.get("current_unit_index", 0)
    
    if not units or current_unit_index >= len(units):
        return {"error": "No valid current unit"}
    
    current_unit = units[current_unit_index]
    
    # Identify immediate threats
    immediate_threats = []
    for unit in units:
        if unit["id"] != current_unit["id"] and unit["alive"]:
            threat_score = _calculate_threat_score(unit, current_unit)
            if threat_score > 0.3:  # Threshold for significant threat
                immediate_threats.append({
                    "unit_id": unit["id"],
                    "threat_score": threat_score,
                    "can_attack_current": _can_unit_attack(unit, current_unit),
                    "distance": abs(unit["position"][0] - current_unit["position"][0]) + 
                               abs(unit["position"][1] - current_unit["position"][1])
                })
    
    return {
        "immediate_threats": sorted(immediate_threats, key=lambda x: x["threat_score"], reverse=True),
        "defensive_recommendations": _generate_defensive_recommendations(current_unit, immediate_threats)
    }

def _calculate_threat_level(unit: dict, target: dict) -> float:
    """Calculate threat level of a unit against a target"""
    # Simple calculation based on attack power vs defense
    attack_power = unit.get("physical_attack", 10) + unit.get("magical_attack", 10)
    target_defense = target.get("physical_defense", 5) + target.get("magical_defense", 5)
    
    return min(attack_power / max(target_defense, 1), 3.0)

def _calculate_vulnerability(unit: dict) -> float:
    """Calculate how vulnerable a unit is"""
    current_hp = unit.get("hp", 100)
    max_hp = unit.get("max_hp", 100)
    defense_total = unit.get("physical_defense", 5) + unit.get("magical_defense", 5)
    
    hp_ratio = current_hp / max_hp
    vulnerability = (1.0 - hp_ratio) + (1.0 / max(defense_total, 1))
    
    return min(vulnerability, 2.0)

def _calculate_unit_power(unit: dict) -> float:
    """Calculate overall power level of a unit"""
    attack_power = unit.get("physical_attack", 10) + unit.get("magical_attack", 10)
    hp_factor = unit.get("hp", 100) / 100
    
    return attack_power * hp_factor

def _calculate_threat_score(threat_unit: dict, target_unit: dict) -> float:
    """Calculate threat score of one unit against another"""
    attack_power = threat_unit.get("physical_attack", 10)
    target_hp = target_unit.get("hp", 100)
    distance = abs(threat_unit["position"][0] - target_unit["position"][0]) + \
               abs(threat_unit["position"][1] - target_unit["position"][1])
    
    # Higher threat for more powerful units that are closer
    threat_score = (attack_power / max(target_hp, 1)) * (1.0 / max(distance, 1))
    
    return min(threat_score, 1.0)

def _can_unit_attack(attacker: dict, target: dict) -> bool:
    """Check if attacker can attack target from current position"""
    distance = abs(attacker["position"][0] - target["position"][0]) + \
               abs(attacker["position"][1] - target["position"][1])
    
    attack_range = attacker.get("attack_range", 1)
    return distance <= attack_range

def _determine_game_phase(game_state: dict) -> str:
    """Determine current phase of the game"""
    turn_number = game_state.get("turn_number", 1)
    units = game_state.get("units", [])
    alive_units = [u for u in units if u["alive"]]
    
    if turn_number <= 3:
        return "opening"
    elif len(alive_units) <= len(units) * 0.6:
        return "endgame"
    else:
        return "midgame"

def _generate_tactical_recommendations(current_unit: dict, targets: list) -> list:
    """Generate tactical recommendations for current unit"""
    recommendations = []
    
    if not targets:
        recommendations.append("No immediate targets available. Focus on positioning.")
    else:
        best_target = targets[0]
        recommendations.append(f"Consider attacking {best_target['unit_id']} (highest threat)")
        
        vulnerable_target = min(targets, key=lambda x: x["vulnerability"]) if targets else None
        if vulnerable_target and vulnerable_target != best_target:
            recommendations.append(f"Alternative: target {vulnerable_target['unit_id']} (most vulnerable)")
    
    if current_unit.get("hp", 100) < current_unit.get("max_hp", 100) * 0.3:
        recommendations.append("Consider defensive positioning - unit has low HP")
    
    return recommendations

def _generate_strategic_recommendations(team_analysis: dict) -> list:
    """Generate strategic recommendations based on team analysis"""
    recommendations = []
    
    friendly_power = team_analysis.get("friendly", {}).get("total_power", 0)
    enemy_power = team_analysis.get("enemy", {}).get("total_power", 0)
    
    if friendly_power > enemy_power * 1.2:
        recommendations.append("Favorable position - consider aggressive tactics")
    elif enemy_power > friendly_power * 1.2:
        recommendations.append("Defensive position - focus on survival and positioning")
    else:
        recommendations.append("Balanced engagement - tactical positioning crucial")
    
    return recommendations

def _generate_defensive_recommendations(current_unit: dict, threats: list) -> list:
    """Generate defensive recommendations"""
    recommendations = []
    
    if not threats:
        recommendations.append("No immediate threats detected")
        return recommendations
    
    highest_threat = threats[0]
    recommendations.append(f"Priority threat: {highest_threat['unit_id']}")
    
    if highest_threat["can_attack_current"]:
        recommendations.append("Move out of threat range or prepare for incoming attack")
    
    if len(threats) > 2:
        recommendations.append("Multiple threats detected - consider group tactics")
    
    return recommendations

# Background task for health monitoring
@app.post("/monitoring/health-check")
async def trigger_health_check(background_tasks: BackgroundTasks):
    """Trigger health check of connected services"""
    background_tasks.add_task(_perform_health_checks)
    return {"message": "Health check initiated"}

async def _perform_health_checks():
    """Perform health checks on connected services"""
    global game_client
    
    if game_client:
        try:
            await game_client.health_check()
            logger.info("Game engine health check passed")
        except Exception as e:
            logger.error("Game engine health check failed", error=str(e))

# Development endpoints
@app.post("/dev/test-tool/{tool_name}")
async def test_mcp_tool(tool_name: str, parameters: dict):
    """Development endpoint to test MCP tools"""
    global mcp_server
    
    if not mcp_server or tool_name not in mcp_server.tools:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    try:
        result = await mcp_server.call_tool(tool_name, parameters)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "src.mcp.gateway:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_config=None
    )