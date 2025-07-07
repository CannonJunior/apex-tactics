"""
AI Agent Manager

Manages AI agents for different units, handling agent creation, configuration,
and assignment based on unit characteristics and difficulty settings.
"""

from typing import Dict, Optional, Any
from ..agents.mcp_tactical_agent import MCPTacticalAgent
from ..mcp_tools import MCPToolRegistry


class AIAgentManager:
    """Manages AI agents for tactical combat units"""
    
    def __init__(self, mcp_tools: MCPToolRegistry):
        """
        Initialize AI agent manager.
        
        Args:
            mcp_tools: MCP tool registry for AI agents to use
        """
        self.mcp_tools = mcp_tools
        self.agents: Dict[str, MCPTacticalAgent] = {}  # unit_id -> agent
        self.default_difficulty = "STRATEGIC"
        self.difficulty_overrides: Dict[str, str] = {}  # unit_id -> difficulty
        
        print("🎯 AI Agent Manager initialized")
    
    def get_agent_for_unit(self, unit) -> Optional[MCPTacticalAgent]:
        """
        Get or create AI agent for specific unit.
        
        Args:
            unit: Game unit that needs AI control
            
        Returns:
            MCPTacticalAgent instance for the unit
        """
        unit_id = str(getattr(unit, 'id', unit.name))
        
        # Return existing agent if available
        if unit_id in self.agents:
            return self.agents[unit_id]
        
        # Create new agent
        difficulty = self._determine_difficulty_for_unit(unit)
        agent = MCPTacticalAgent(self.mcp_tools, difficulty)
        
        # Store agent for reuse
        self.agents[unit_id] = agent
        
        print(f"🤖 Created {difficulty} AI agent for {unit.name}")
        return agent
    
    def _determine_difficulty_for_unit(self, unit) -> str:
        """
        Determine appropriate AI difficulty for a unit.
        
        Args:
            unit: Game unit to analyze
            
        Returns:
            Difficulty level string
        """
        unit_id = str(getattr(unit, 'id', unit.name))
        
        # Check for unit-specific override
        if unit_id in self.difficulty_overrides:
            return self.difficulty_overrides[unit_id]
        
        # Check if unit has specified AI difficulty
        if hasattr(unit, 'ai_difficulty'):
            return unit.ai_difficulty
        
        # Check team component for leadership role
        team_comp = getattr(unit, 'team_component', None)
        if team_comp:
            if team_comp.team_role == "leader":
                return "ADAPTIVE"  # Leaders get higher difficulty
            elif team_comp.command_level > 0:
                return "STRATEGIC"  # Officers get medium difficulty
        
        # Check unit level or type for difficulty scaling
        if hasattr(unit, 'level'):
            if unit.level >= 10:
                return "ADAPTIVE"
            elif unit.level >= 5:
                return "STRATEGIC"
            else:
                return "SCRIPTED"
        
        # Default difficulty
        return self.default_difficulty
    
    def set_global_difficulty(self, difficulty: str):
        """
        Set default difficulty for all new agents.
        
        Args:
            difficulty: New default difficulty level
        """
        valid_difficulties = ["SCRIPTED", "STRATEGIC", "ADAPTIVE", "LEARNING"]
        if difficulty in valid_difficulties:
            self.default_difficulty = difficulty
            print(f"🎯 Global AI difficulty set to {difficulty}")
        else:
            print(f"❌ Invalid difficulty: {difficulty}. Valid options: {valid_difficulties}")
    
    def set_unit_difficulty(self, unit_id: str, difficulty: str):
        """
        Set specific difficulty for a unit.
        
        Args:
            unit_id: ID of unit to configure
            difficulty: Difficulty level for this unit
        """
        valid_difficulties = ["SCRIPTED", "STRATEGIC", "ADAPTIVE", "LEARNING"]
        if difficulty in valid_difficulties:
            self.difficulty_overrides[unit_id] = difficulty
            
            # Update existing agent if present
            if unit_id in self.agents:
                self.agents[unit_id].difficulty = difficulty
                self.agents[unit_id]._configure_difficulty()
                
            print(f"🎯 Unit {unit_id} AI difficulty set to {difficulty}")
        else:
            print(f"❌ Invalid difficulty: {difficulty}. Valid options: {valid_difficulties}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all managed agents.
        
        Returns:
            Dictionary with agent status information
        """
        return {
            'total_agents': len(self.agents),
            'default_difficulty': self.default_difficulty,
            'agents': {
                unit_id: {
                    'difficulty': agent.difficulty,
                    'move_preference': agent.move_preference,
                    'aggression_level': agent.aggression_level
                }
                for unit_id, agent in self.agents.items()
            },
            'difficulty_overrides': self.difficulty_overrides.copy()
        }
    
    def clear_agents(self):
        """Clear all cached agents (useful for new battles)"""
        self.agents.clear()
        print("🧹 Cleared all AI agents")
    
    def remove_agent(self, unit_id: str):
        """
        Remove specific agent.
        
        Args:
            unit_id: ID of unit whose agent to remove
        """
        if unit_id in self.agents:
            del self.agents[unit_id]
            print(f"🗑️ Removed AI agent for unit {unit_id}")
    
    def update_agent_parameters(self, unit_id: str, parameters: Dict[str, float]):
        """
        Update specific agent's parameters.
        
        Args:
            unit_id: ID of unit whose agent to update
            parameters: Dictionary of parameter updates
        """
        if unit_id in self.agents:
            agent = self.agents[unit_id]
            
            for param, value in parameters.items():
                if hasattr(agent, param):
                    setattr(agent, param, value)
                    print(f"🔧 Updated {unit_id} agent {param} to {value}")
                else:
                    print(f"⚠️ Unknown parameter {param} for agent {unit_id}")
        else:
            print(f"⚠️ No agent found for unit {unit_id}")
    
    def get_recommended_difficulty(self, player_performance: Optional[Dict[str, float]] = None) -> str:
        """
        Get recommended difficulty based on player performance.
        
        Args:
            player_performance: Optional performance metrics
            
        Returns:
            Recommended difficulty level
        """
        if not player_performance:
            return self.default_difficulty
        
        # Simple performance-based difficulty recommendation
        win_rate = player_performance.get('win_rate', 0.5)
        efficiency = player_performance.get('efficiency', 0.5)
        
        overall_performance = (win_rate + efficiency) / 2
        
        if overall_performance > 0.8:
            return "LEARNING"
        elif overall_performance > 0.65:
            return "ADAPTIVE"
        elif overall_performance > 0.4:
            return "STRATEGIC"
        else:
            return "SCRIPTED"