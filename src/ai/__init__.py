"""
AI Systems

AI implementation including MCP servers, difficulty scaling, and behavior trees.
Enhanced with Week 3 AI Agent Integration.
"""

# Week 3 AI Agent Integration - Simplified imports to avoid missing dependencies
try:
    from .mcp_tools import MCPToolRegistry, ToolResult
    MCP_TOOLS_AVAILABLE = True
except ImportError:
    MCP_TOOLS_AVAILABLE = False

from .unit_ai_controller import UnitAIController, AIPersonality, AISkillLevel
from .simple_mcp_tools import SimpleMCPToolRegistry, ToolResult as SimpleToolResult

try:
    from .orchestration_agent import OrchestrationAgent, AIRole
    ORCHESTRATION_AVAILABLE = True
except ImportError:
    ORCHESTRATION_AVAILABLE = False

try:
    from .ai_integration_manager import AIIntegrationManager, AIUnitConfig
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False

try:
    from .low_latency_pipeline import LowLatencyDecisionPipeline, DecisionPriority
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False

__all__ = [
    'UnitAIController', 'AIPersonality', 'AISkillLevel',
    'SimpleMCPToolRegistry', 'SimpleToolResult'
]

# Add optional components if available
if MCP_TOOLS_AVAILABLE:
    __all__.extend(['MCPToolRegistry', 'ToolResult'])
if ORCHESTRATION_AVAILABLE:
    __all__.extend(['OrchestrationAgent', 'AIRole'])
if INTEGRATION_AVAILABLE:
    __all__.extend(['AIIntegrationManager', 'AIUnitConfig'])
if PIPELINE_AVAILABLE:
    __all__.extend(['LowLatencyDecisionPipeline', 'DecisionPriority'])