"""
AI Orchestration Agent

Coordinates multiple AI sub-agents controlling enemy units. Manages delegation,
tool access, and ensures low-latency game flow while maintaining tactical coherence.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai.mcp_tools import MCPToolRegistry, ToolResult
from ai.unit_ai_controller import UnitAIController
from game.managers.action_manager import ActionManager
from game.config.feature_flags import FeatureFlags


class AIRole(Enum):
    """Roles that AI agents can take in battle."""
    COMMANDER = "commander"          # Overall tactical coordination
    UNIT_CONTROLLER = "unit_controller"  # Individual unit control
    ANALYST = "analyst"             # Battlefield analysis
    SCOUT = "scout"                 # Information gathering


@dataclass
class AIAgent:
    """Represents an AI agent with specific role and capabilities."""
    agent_id: str
    role: AIRole
    assigned_units: Set[str] = field(default_factory=set)
    available_tools: Set[str] = field(default_factory=set)
    is_active: bool = True
    last_action_time: float = 0.0
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize performance metrics."""
        self.performance_metrics = {
            'actions_executed': 0,
            'average_decision_time_ms': 0.0,
            'success_rate': 1.0,
            'tactical_effectiveness': 0.5
        }


@dataclass
class BattlePlan:
    """Represents a coordinated battle plan from the commander."""
    plan_id: str
    objective: str
    unit_assignments: Dict[str, str]  # unit_id -> primary_goal
    priority_targets: List[str]
    formation_strategy: str
    fallback_conditions: List[str]
    estimated_turns: int


class OrchestrationAgent:
    """
    Master AI agent that coordinates all other AI agents.
    
    Responsibilities:
    - Delegate unit control to sub-agents
    - Provide tactical oversight and coordination
    - Manage tool access and permissions
    - Ensure low-latency decision making
    - Maintain battle plan coherence
    """
    
    def __init__(self, action_manager: ActionManager):
        self.action_manager = action_manager
        self.tool_registry = MCPToolRegistry(action_manager)
        
        # Agent management
        self.agents: Dict[str, AIAgent] = {}
        self.commander_agent: Optional[AIAgent] = None
        
        # Battle coordination
        self.current_battle_plan: Optional[BattlePlan] = None
        self.turn_coordination_data: Dict[str, Any] = {}
        
        # Performance monitoring
        self.orchestration_metrics = {
            'total_decisions': 0,
            'average_coordination_time_ms': 0.0,
            'agent_efficiency': {},
            'battle_effectiveness': 0.0
        }
        
        # Concurrency management
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="AI_Agent")
        self.max_decision_time_ms = 100  # Target for low-latency
        
        # Initialize default agents
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Create default AI agents for battle coordination."""
        # Commander agent - overall strategy
        commander = AIAgent(
            agent_id="commander",
            role=AIRole.COMMANDER,
            available_tools={
                'get_battlefield_state', 'get_timeline_preview', 
                'calculate_threat_assessment', 'analyze_action_outcomes'
            }
        )
        self.agents["commander"] = commander
        self.commander_agent = commander
        
        # Analyst agent - battlefield analysis
        analyst = AIAgent(
            agent_id="analyst", 
            role=AIRole.ANALYST,
            available_tools={
                'get_battlefield_state', 'calculate_threat_assessment',
                'analyze_action_outcomes', 'get_timeline_preview'
            }
        )
        self.agents["analyst"] = analyst
        
        print("🤖 Orchestration Agent initialized with commander and analyst")
    
    def register_unit_controller(self, unit_id: str) -> str:
        """
        Register a new unit controller agent for a specific unit.
        
        Args:
            unit_id: ID of unit to control
            
        Returns:
            Agent ID of the created controller
        """
        agent_id = f"unit_controller_{unit_id}"
        
        controller = AIAgent(
            agent_id=agent_id,
            role=AIRole.UNIT_CONTROLLER,
            assigned_units={unit_id},
            available_tools={
                'get_unit_details', 'queue_unit_action', 'cancel_unit_action',
                'analyze_action_outcomes', 'calculate_threat_assessment'
            }
        )
        
        self.agents[agent_id] = controller
        print(f"🎮 Registered unit controller for {unit_id}")
        
        return agent_id
    
    async def coordinate_turn(self, enemy_unit_ids: List[str]) -> Dict[str, Any]:
        """
        Coordinate AI actions for a complete turn.
        
        Args:
            enemy_unit_ids: List of enemy unit IDs to coordinate
            
        Returns:
            Dictionary with coordination results
        """
        start_time = time.time()
        
        try:
            # Phase 1: Battlefield analysis (Commander + Analyst)
            analysis_result = await self._conduct_battlefield_analysis()
            
            # Phase 2: Strategic planning (Commander)
            battle_plan = await self._create_battle_plan(enemy_unit_ids, analysis_result)
            
            # Phase 3: Unit action coordination (Unit Controllers)
            action_results = await self._coordinate_unit_actions(enemy_unit_ids, battle_plan)
            
            # Phase 4: Execution oversight (Commander)
            execution_plan = await self._finalize_execution_plan(action_results)
            
            coordination_time = (time.time() - start_time) * 1000
            
            # Update metrics
            self.orchestration_metrics['total_decisions'] += 1
            self._update_coordination_metrics(coordination_time)
            
            return {
                'success': True,
                'battle_plan': battle_plan.__dict__ if battle_plan else None,
                'unit_actions': action_results,
                'execution_plan': execution_plan,
                'coordination_time_ms': coordination_time,
                'agents_involved': len([a for a in self.agents.values() if a.is_active])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'coordination_time_ms': (time.time() - start_time) * 1000
            }
    
    async def _conduct_battlefield_analysis(self) -> Dict[str, Any]:
        """Conduct comprehensive battlefield analysis."""
        analysis_tasks = []
        
        # Commander gets overall state
        if self.commander_agent:
            task = asyncio.create_task(
                self._execute_agent_tool(
                    self.commander_agent.agent_id,
                    'get_battlefield_state'
                )
            )
            analysis_tasks.append(('battlefield_state', task))
        
        # Analyst calculates threats
        analyst = self.agents.get("analyst")
        if analyst:
            # Get threat assessments for all units
            battlefield_result = await self._execute_agent_tool("analyst", 'get_battlefield_state')
            if battlefield_result.success:
                units = battlefield_result.data.get('units', [])
                for unit in units:
                    if unit['team'] == 'player':  # Assess player threats
                        task = asyncio.create_task(
                            self._execute_agent_tool(
                                analyst.agent_id,
                                'calculate_threat_assessment',
                                unit_id=unit['id']
                            )
                        )
                        analysis_tasks.append(('threat_' + unit['id'], task))
        
        # Collect all analysis results
        analysis_results = {}
        for task_name, task in analysis_tasks:
            try:
                result = await asyncio.wait_for(task, timeout=self.max_decision_time_ms/1000)
                analysis_results[task_name] = result.data if result.success else None
            except asyncio.TimeoutError:
                analysis_results[task_name] = None
                print(f"⚠️ Analysis task {task_name} timed out")
        
        return analysis_results
    
    async def _create_battle_plan(self, unit_ids: List[str], analysis: Dict[str, Any]) -> Optional[BattlePlan]:
        """Create coordinated battle plan based on analysis."""
        if not self.commander_agent or not analysis.get('battlefield_state'):
            return None
        
        battlefield = analysis['battlefield_state']
        units = battlefield.get('units', [])
        
        # Identify priority targets (highest threat players)
        priority_targets = []
        for unit in units:
            if unit['team'] == 'player':
                threat_key = f"threat_{unit['id']}"
                threat_data = analysis.get(threat_key)
                if threat_data and threat_data.get('threat_category') in ['HIGH', 'MEDIUM']:
                    priority_targets.append(unit['id'])
        
        # Assign unit roles
        unit_assignments = {}
        for i, unit_id in enumerate(unit_ids):
            if i < len(priority_targets):
                unit_assignments[unit_id] = f"eliminate_{priority_targets[i]}"
            else:
                unit_assignments[unit_id] = "support_allies"
        
        battle_plan = BattlePlan(
            plan_id=f"plan_{int(time.time())}",
            objective="Eliminate high-threat player units",
            unit_assignments=unit_assignments,
            priority_targets=priority_targets,
            formation_strategy="focused_assault",
            fallback_conditions=["heavy_casualties", "low_resources"],
            estimated_turns=3
        )
        
        self.current_battle_plan = battle_plan
        print(f"📋 Battle plan created: {battle_plan.objective}")
        
        return battle_plan
    
    async def _coordinate_unit_actions(self, unit_ids: List[str], 
                                     battle_plan: Optional[BattlePlan]) -> Dict[str, Any]:
        """Coordinate actions for all AI-controlled units."""
        unit_action_tasks = []
        
        for unit_id in unit_ids:
            # Ensure unit has a controller
            controller_id = f"unit_controller_{unit_id}"
            if controller_id not in self.agents:
                self.register_unit_controller(unit_id)
            
            # Create task for unit action planning
            task = asyncio.create_task(
                self._plan_unit_actions(unit_id, battle_plan)
            )
            unit_action_tasks.append((unit_id, task))
        
        # Collect unit action results
        action_results = {}
        for unit_id, task in unit_action_tasks:
            try:
                result = await asyncio.wait_for(task, timeout=self.max_decision_time_ms/1000)
                action_results[unit_id] = result
            except asyncio.TimeoutError:
                action_results[unit_id] = {'error': 'Decision timeout'}
                print(f"⚠️ Unit {unit_id} action planning timed out")
        
        return action_results
    
    async def _plan_unit_actions(self, unit_id: str, battle_plan: Optional[BattlePlan]) -> Dict[str, Any]:
        """Plan actions for a specific unit based on battle plan."""
        controller_id = f"unit_controller_{unit_id}"
        controller = self.agents.get(controller_id)
        
        if not controller:
            return {'error': 'No controller found'}
        
        # Get unit details
        unit_details_result = await self._execute_agent_tool(
            controller_id, 'get_unit_details', unit_id=unit_id
        )
        
        if not unit_details_result.success:
            return {'error': 'Could not get unit details'}
        
        unit_data = unit_details_result.data
        
        # Determine unit's assignment from battle plan
        assignment = "attack_nearest"  # Default
        if battle_plan and unit_id in battle_plan.unit_assignments:
            assignment = battle_plan.unit_assignments[unit_id]
        
        # Plan actions based on assignment
        planned_actions = []
        
        if assignment.startswith("eliminate_"):
            target_id = assignment.replace("eliminate_", "")
            # Plan attack actions against specific target
            for action in unit_data.get('available_actions', []):
                if action['type'] in ['Attack', 'Magic']:
                    planned_actions.append({
                        'action_id': action['id'],
                        'target_id': target_id,
                        'priority': 'HIGH',
                        'reasoning': f'Eliminate priority target {target_id}'
                    })
                    break  # One action for now
        
        elif assignment == "support_allies":
            # Plan support actions
            for action in unit_data.get('available_actions', []):
                if 'heal' in action['name'].lower() or action['type'] == 'Spirit':
                    planned_actions.append({
                        'action_id': action['id'],
                        'target_id': unit_id,  # Self-support
                        'priority': 'NORMAL',
                        'reasoning': 'Support allies and self'
                    })
                    break
        
        # If no specific actions planned, default to basic attack
        if not planned_actions:
            for action in unit_data.get('available_actions', []):
                if action['type'] == 'Attack':
                    planned_actions.append({
                        'action_id': action['id'],
                        'target_id': 'nearest_enemy',
                        'priority': 'NORMAL',
                        'reasoning': 'Default attack action'
                    })
                    break
        
        return {
            'unit_id': unit_id,
            'assignment': assignment,
            'planned_actions': planned_actions,
            'controller': controller_id
        }
    
    async def _finalize_execution_plan(self, action_results: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize and validate the complete execution plan."""
        execution_plan = {
            'total_units': len(action_results),
            'total_actions': 0,
            'coordination_quality': 'good',
            'estimated_execution_time': 0.0
        }
        
        # Count total actions and estimate execution time
        for unit_id, result in action_results.items():
            if 'planned_actions' in result:
                actions = result['planned_actions']
                execution_plan['total_actions'] += len(actions)
                execution_plan['estimated_execution_time'] += len(actions) * 0.5  # 0.5s per action
        
        # Validate plan coherence (simplified)
        if execution_plan['total_actions'] > 0:
            execution_plan['coordination_quality'] = 'excellent'
        
        return execution_plan
    
    async def _execute_agent_tool(self, agent_id: str, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool on behalf of an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return ToolResult(success=False, error_message=f"Agent {agent_id} not found")
        
        if tool_name not in agent.available_tools:
            return ToolResult(success=False, error_message=f"Tool {tool_name} not available to {agent_id}")
        
        # Execute tool with timeout
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self.tool_registry.execute_tool,
            tool_name,
            **kwargs
        )
        
        # Update agent metrics
        agent.last_action_time = time.time()
        agent.performance_metrics['actions_executed'] += 1
        
        return result
    
    def execute_ai_turn_sync(self, enemy_unit_ids: List[str]) -> Dict[str, Any]:
        """
        Synchronous wrapper for AI turn coordination.
        
        Args:
            enemy_unit_ids: List of enemy unit IDs to coordinate
            
        Returns:
            Coordination results
        """
        if not FeatureFlags.USE_MCP_TOOLS:
            return {'success': False, 'error': 'MCP tools disabled'}
        
        try:
            # Run async coordination in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.coordinate_turn(enemy_unit_ids)
            )
            
            loop.close()
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _update_coordination_metrics(self, coordination_time_ms: float):
        """Update orchestration performance metrics."""
        current_avg = self.orchestration_metrics['average_coordination_time_ms']
        total_decisions = self.orchestration_metrics['total_decisions']
        
        # Calculate new average
        new_avg = ((current_avg * (total_decisions - 1)) + coordination_time_ms) / total_decisions
        self.orchestration_metrics['average_coordination_time_ms'] = new_avg
        
        # Update agent efficiency metrics
        for agent_id, agent in self.agents.items():
            if agent.is_active:
                self.orchestration_metrics['agent_efficiency'][agent_id] = {
                    'actions_executed': agent.performance_metrics['actions_executed'],
                    'average_decision_time': agent.performance_metrics['average_decision_time_ms'],
                    'success_rate': agent.performance_metrics['success_rate']
                }
    
    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current status of AI orchestration."""
        return {
            'total_agents': len(self.agents),
            'active_agents': len([a for a in self.agents.values() if a.is_active]),
            'current_battle_plan': self.current_battle_plan.__dict__ if self.current_battle_plan else None,
            'performance_metrics': self.orchestration_metrics,
            'feature_flags_enabled': FeatureFlags.USE_MCP_TOOLS
        }
    
    def shutdown(self):
        """Shutdown orchestration agent and cleanup resources."""
        self.executor.shutdown(wait=True)
        self.agents.clear()
        self.current_battle_plan = None
        print("🔄 AI Orchestration Agent shut down")