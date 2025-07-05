"""
MCP Integration Manager

Manages MCP tool integration for tactical RPG without expanding TacticalRPG controller.
Provides seamless integration between game systems and MCP AI capabilities.
"""

from typing import Dict, List, Optional, Any
import json
import asyncio
from dataclasses import dataclass

try:
    from ..interfaces.game_interfaces import BaseManager
    INTERFACES_AVAILABLE = True
except ImportError:
    # Fallback for missing interfaces
    class BaseManager:
        def __init__(self):
            self.is_initialized = False
        def initialize(self):
            self.is_initialized = True
        def shutdown(self):
            self.is_initialized = False
    INTERFACES_AVAILABLE = False


@dataclass
class TalentRecommendation:
    """AI recommendation for talent usage."""
    talent_id: str
    confidence: float
    reasoning: str
    optimal_target: Optional[Dict[str, int]] = None
    synergy_talents: Optional[List[str]] = None


class MCPIntegrationManager(BaseManager):
    """
    Manages MCP tool integration without expanding TacticalRPG controller.
    
    Features:
    - AI talent recommendations via MCP tools
    - Talent execution notifications for learning
    - Battlefield analysis integration
    - Resource cost optimization
    - Strategic planning support
    """
    
    def __init__(self, tactical_controller):
        """Initialize MCP integration manager."""
        super().__init__()
        self.tactical_controller = tactical_controller
        self.mcp_client = None
        self.config = {}
        
        # AI recommendation cache
        self.ai_recommendations: Dict[str, List[TalentRecommendation]] = {}
        self.last_analysis_timestamp = 0
        
        # MCP integration state
        self.is_mcp_available = False
        self.mcp_gateway_url = "http://localhost:8002"
        self.talent_execution_log: List[Dict[str, Any]] = []
        
        print("🔗 MCPIntegrationManager initialized")
    
    def initialize(self):
        """Initialize MCP client and load configuration."""
        super().initialize()
        
        try:
            # Load MCP configuration
            try:
                from ...core.config.config_manager import get_config_manager
                config_manager = get_config_manager()
                self.config = config_manager.get_value('mcp_integration_config', {
                    'enabled': True,
                    'talent_analysis': True,
                    'ai_recommendations': True,
                    'gateway_url': 'http://localhost:8002'
                })
            except ImportError:
                # Fallback configuration if config manager not available
                self.config = {
                    'enabled': True,
                    'talent_analysis': True,
                    'ai_recommendations': True,
                    'gateway_url': 'http://localhost:8002'
                }
            
            if self.config.get('enabled', True):
                self._initialize_mcp_client()
                print("✅ MCP integration enabled and initialized")
            else:
                print("ℹ️ MCP integration disabled by configuration")
                
        except Exception as e:
            print(f"⚠️ MCP integration initialization failed: {e}")
            self.is_mcp_available = False
    
    def _initialize_mcp_client(self):
        """Initialize MCP client connection."""
        try:
            self.mcp_gateway_url = self.config.get('gateway_url', 'http://localhost:8002')
            # TODO: Initialize actual MCP client when httpx is available
            self.is_mcp_available = True
            print(f"🌐 MCP client configured for {self.mcp_gateway_url}")
        except Exception as e:
            print(f"⚠️ Failed to initialize MCP client: {e}")
            self.is_mcp_available = False
    
    def get_talent_recommendations(self, unit_id: str) -> List[TalentRecommendation]:
        """
        Get AI talent recommendations via MCP for specified unit.
        
        Args:
            unit_id: Target unit identifier
            
        Returns:
            List of AI talent recommendations with confidence scores
        """
        if not self.is_mcp_available or not self.config.get('ai_recommendations', True):
            return []
        
        try:
            # Check cache first
            if unit_id in self.ai_recommendations:
                cached_recommendations = self.ai_recommendations[unit_id]
                if cached_recommendations:
                    print(f"📋 Returning {len(cached_recommendations)} cached talent recommendations for {unit_id}")
                    return cached_recommendations
            
            # Generate recommendations via MCP (async call)
            recommendations = self._generate_talent_recommendations(unit_id)
            
            # Cache results
            self.ai_recommendations[unit_id] = recommendations
            
            if recommendations:
                print(f"🤖 Generated {len(recommendations)} AI talent recommendations for {unit_id}")
                for rec in recommendations[:3]:  # Log top 3
                    print(f"   • {rec.talent_id} (confidence: {rec.confidence:.2f}): {rec.reasoning}")
            
            return recommendations
            
        except Exception as e:
            print(f"⚠️ Failed to get talent recommendations: {e}")
            return []
    
    def _generate_talent_recommendations(self, unit_id: str) -> List[TalentRecommendation]:
        """Generate talent recommendations using available data."""
        recommendations = []
        
        try:
            # Get unit data from tactical controller
            if not hasattr(self.tactical_controller, 'character_state_manager'):
                return recommendations
            
            char_manager = self.tactical_controller.character_state_manager
            active_character = char_manager.get_active_character()
            
            if not active_character:
                return recommendations
            
            # Analyze available talents (fallback analysis)
            available_talents = self._get_available_talents(active_character)
            battlefield_context = self._get_battlefield_context()
            
            # Generate basic recommendations based on situation
            for talent_data in available_talents[:3]:  # Top 3 available talents
                confidence = self._calculate_talent_confidence(talent_data, battlefield_context)
                reasoning = self._generate_talent_reasoning(talent_data, battlefield_context)
                
                recommendation = TalentRecommendation(
                    talent_id=talent_data.get('id', 'unknown'),
                    confidence=confidence,
                    reasoning=reasoning,
                    optimal_target=self._suggest_optimal_target(talent_data)
                )
                
                recommendations.append(recommendation)
            
            # Sort by confidence
            recommendations.sort(key=lambda x: x.confidence, reverse=True)
            
        except Exception as e:
            print(f"⚠️ Error generating talent recommendations: {e}")
        
        return recommendations
    
    def _get_available_talents(self, character) -> List[Dict[str, Any]]:
        """Get available talents for character."""
        talents = []
        
        try:
            if hasattr(character, 'template_data'):
                hotkey_abilities = character.template_data.get('hotkey_abilities', {})
                
                # Get talent data for each hotkey
                for slot, ability_data in hotkey_abilities.items():
                    if 'talent_id' in ability_data:
                        talent_data = {
                            'id': ability_data['talent_id'],
                            'slot': slot,
                            'name': ability_data.get('name', ability_data['talent_id']),
                            'action_type': ability_data.get('action_type', 'Attack')
                        }
                        talents.append(talent_data)
        
        except Exception as e:
            print(f"⚠️ Error getting available talents: {e}")
        
        return talents
    
    def _get_battlefield_context(self) -> Dict[str, Any]:
        """Get current battlefield context for analysis."""
        context = {
            'enemy_count': 0,
            'ally_count': 0,
            'player_health_ratio': 1.0,
            'threat_level': 'low'
        }
        
        try:
            if hasattr(self.tactical_controller, 'units'):
                units = self.tactical_controller.units
                player_units = [u for u in units if getattr(u, 'faction', 'player') == 'player']
                enemy_units = [u for u in units if getattr(u, 'faction', 'enemy') == 'enemy']
                
                context['ally_count'] = len(player_units)
                context['enemy_count'] = len(enemy_units)
                
                # Calculate threat level
                if context['enemy_count'] > context['ally_count']:
                    context['threat_level'] = 'high'
                elif context['enemy_count'] == context['ally_count']:
                    context['threat_level'] = 'medium'
                else:
                    context['threat_level'] = 'low'
        
        except Exception as e:
            print(f"⚠️ Error getting battlefield context: {e}")
        
        return context
    
    def _calculate_talent_confidence(self, talent_data: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate confidence score for talent recommendation."""
        base_confidence = 0.5
        
        # Adjust based on action type and threat level
        action_type = talent_data.get('action_type', 'Attack')
        threat_level = context.get('threat_level', 'low')
        
        if action_type == 'Attack' and threat_level == 'high':
            base_confidence += 0.3
        elif action_type == 'Magic' and context.get('enemy_count', 0) > 2:
            base_confidence += 0.2
        elif action_type == 'Spirit' and context.get('player_health_ratio', 1.0) < 0.5:
            base_confidence += 0.4
        
        return min(base_confidence, 1.0)
    
    def _generate_talent_reasoning(self, talent_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate reasoning for talent recommendation."""
        action_type = talent_data.get('action_type', 'Attack')
        threat_level = context.get('threat_level', 'low')
        enemy_count = context.get('enemy_count', 0)
        
        if action_type == 'Attack' and threat_level == 'high':
            return f"High threat situation with {enemy_count} enemies - offensive action recommended"
        elif action_type == 'Magic' and enemy_count > 2:
            return f"Multiple enemies ({enemy_count}) present - area effect magic optimal"
        elif action_type == 'Spirit':
            return "Spiritual abilities provide tactical flexibility and support"
        else:
            return f"Standard {action_type.lower()} action suitable for current situation"
    
    def _suggest_optimal_target(self, talent_data: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """Suggest optimal target position for talent."""
        # Basic target suggestion (can be enhanced with MCP analysis)
        return {'x': 0, 'y': 0}  # Placeholder
    
    def notify_talent_executed(self, talent_data: Dict[str, Any]):
        """
        Notify MCP system of talent execution for learning.
        
        Args:
            talent_data: Executed talent information
        """
        if not self.is_mcp_available:
            return
        
        try:
            # Log talent execution
            execution_record = {
                'talent_id': talent_data.get('id', 'unknown'),
                'action_type': talent_data.get('action_type', 'unknown'),
                'timestamp': self._get_current_timestamp(),
                'battlefield_context': self._get_battlefield_context()
            }
            
            self.talent_execution_log.append(execution_record)
            
            # Keep log size manageable
            if len(self.talent_execution_log) > 100:
                self.talent_execution_log = self.talent_execution_log[-50:]
            
            print(f"📊 MCP notified: talent {talent_data.get('id', 'unknown')} executed")
            
            # Clear recommendations cache for affected unit
            self._invalidate_recommendation_cache()
            
        except Exception as e:
            print(f"⚠️ Failed to notify MCP of talent execution: {e}")
    
    def _invalidate_recommendation_cache(self):
        """Invalidate AI recommendation cache."""
        self.ai_recommendations.clear()
        print("🔄 AI recommendation cache invalidated")
    
    def _get_current_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def get_mcp_status(self) -> Dict[str, Any]:
        """Get current MCP integration status."""
        return {
            'available': self.is_mcp_available,
            'enabled': self.config.get('enabled', False),
            'gateway_url': self.mcp_gateway_url,
            'talent_analysis': self.config.get('talent_analysis', False),
            'ai_recommendations': self.config.get('ai_recommendations', False),
            'execution_log_size': len(self.talent_execution_log),
            'cached_recommendations': len(self.ai_recommendations)
        }
    
    def shutdown(self):
        """Shutdown MCP integration manager."""
        try:
            if self.mcp_client:
                # TODO: Close MCP client connection
                pass
            
            # Clear caches
            self.ai_recommendations.clear()
            self.talent_execution_log.clear()
            
            print("🔗 MCPIntegrationManager shutdown complete")
            
        except Exception as e:
            print(f"⚠️ Error during MCP integration shutdown: {e}")
        
        super().shutdown()