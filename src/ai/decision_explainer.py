"""
AI Decision Explanation System

Provides detailed explanations of AI decision-making processes,
making AI reasoning transparent and educational for players.
"""

import json
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

import structlog
from pydantic import BaseModel

from .models import (
    AIDecisionRequest, AIDecisionResponse, GameAction, BattlefieldState
)
from .personalities import AIPersonality, PersonalityType
from .tactical_ai import TacticalSituation, TacticalPattern

logger = structlog.get_logger()


class ExplanationLevel(str, Enum):
    """Levels of explanation detail"""
    BRIEF = "brief"
    DETAILED = "detailed"
    TECHNICAL = "technical"
    EDUCATIONAL = "educational"


class ReasoningType(str, Enum):
    """Types of reasoning used in decisions"""
    TACTICAL = "tactical"
    STRATEGIC = "strategic"
    PERSONALITY = "personality"
    LEARNED = "learned"
    DEFENSIVE = "defensive"
    OPPORTUNISTIC = "opportunistic"


@dataclass
class DecisionFactor:
    """Individual factor influencing a decision"""
    factor_type: ReasoningType
    description: str
    weight: float
    confidence: float
    supporting_data: Dict[str, Any]


class DecisionExplanation(BaseModel):
    """Complete explanation of an AI decision"""
    decision_id: str
    session_id: str
    unit_id: str
    timestamp: datetime
    
    # Core decision info
    chosen_action: Dict[str, Any]
    alternative_actions: List[Dict[str, Any]]
    final_confidence: float
    
    # Explanation components
    primary_reasoning: str
    decision_factors: List[Dict[str, Any]]
    personality_influence: Dict[str, Any]
    tactical_analysis: Dict[str, Any]
    learning_insights: Dict[str, Any]
    
    # Contextual information
    battlefield_assessment: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    expected_outcomes: Dict[str, Any]
    
    # Educational content
    tactical_concepts: List[str]
    learning_opportunities: List[str]
    player_tips: List[str]


class DecisionExplainer:
    """Main AI decision explanation system"""
    
    def __init__(self):
        self.explanation_cache: Dict[str, DecisionExplanation] = {}
        self.concept_library = self._initialize_concept_library()
        self.explanation_templates = self._load_explanation_templates()
        
    def _initialize_concept_library(self) -> Dict[str, Dict[str, Any]]:
        """Initialize library of tactical concepts for educational explanations"""
        return {
            "flanking": {
                "definition": "Attacking enemy units from the side or rear for tactical advantage",
                "benefits": ["Reduced enemy defense", "Higher damage potential", "Disrupts enemy formation"],
                "when_to_use": "When enemy units are positioned in a line or focused forward",
                "difficulty": "intermediate"
            },
            "focus_fire": {
                "definition": "Concentrating multiple units' attacks on a single target",
                "benefits": ["Eliminates threats quickly", "Reduces enemy action economy", "Creates momentum"],
                "when_to_use": "Against high-value or dangerous enemy units",
                "difficulty": "basic"
            },
            "positioning": {
                "definition": "Strategic placement of units to control battlefield areas",
                "benefits": ["Controls movement", "Protects allies", "Threatens objectives"],
                "when_to_use": "Throughout the battle for tactical advantage",
                "difficulty": "intermediate"
            },
            "resource_management": {
                "definition": "Careful use of limited resources like MP, abilities, and unit health",
                "benefits": ["Sustained combat effectiveness", "Emergency reserves", "Long-term viability"],
                "when_to_use": "Continuously, especially in longer battles",
                "difficulty": "advanced"
            },
            "tempo": {
                "definition": "The pace and initiative of battle actions",
                "benefits": ["Dictates battle flow", "Pressures opponent", "Creates opportunities"],
                "when_to_use": "When you have the advantage or need to disrupt enemy plans",
                "difficulty": "advanced"
            },
            "threat_assessment": {
                "definition": "Evaluating and prioritizing enemy units by danger level",
                "benefits": ["Efficient target selection", "Risk mitigation", "Resource allocation"],
                "when_to_use": "Before every major decision",
                "difficulty": "intermediate"
            }
        }
    
    def _load_explanation_templates(self) -> Dict[str, str]:
        """Load templates for different types of explanations"""
        return {
            "move": "Moving {unit} to {position} to {primary_reason}. This {tactical_benefit} while {risk_consideration}.",
            "attack": "Attacking {target} with {unit} because {primary_reason}. Expected {damage_range} damage with {success_chance}% hit chance.",
            "defend": "Having {unit} defend to {defensive_reason}. This provides {defensive_benefit} against {threat_type}.",
            "ability": "Using {ability} with {unit} to {ability_purpose}. This {strategic_impact} and {tactical_outcome}.",
            "wait": "Keeping {unit} in position because {wait_reason}. This maintains {tactical_advantage} until {condition_met}."
        }
    
    async def explain_decision(
        self, 
        decision_request: AIDecisionRequest,
        decision_response: AIDecisionResponse,
        battlefield_state: BattlefieldState,
        personality: AIPersonality,
        tactical_situation: TacticalSituation,
        explanation_level: ExplanationLevel = ExplanationLevel.DETAILED
    ) -> DecisionExplanation:
        """Generate comprehensive explanation of AI decision"""
        
        decision_id = f"decision_{int(time.time() * 1000)}"
        
        # Analyze the decision components
        decision_factors = await self._analyze_decision_factors(
            decision_request, decision_response, tactical_situation, personality
        )
        
        # Generate personality influence explanation
        personality_influence = self._explain_personality_influence(
            personality, decision_response.recommended_action, decision_factors
        )
        
        # Create tactical analysis explanation
        tactical_analysis = self._explain_tactical_analysis(
            tactical_situation, decision_response.recommended_action
        )
        
        # Generate battlefield assessment
        battlefield_assessment = self._explain_battlefield_assessment(
            battlefield_state, tactical_situation
        )
        
        # Create risk assessment
        risk_assessment = self._explain_risk_assessment(
            decision_response, tactical_situation
        )
        
        # Generate expected outcomes
        expected_outcomes = self._explain_expected_outcomes(
            decision_response, tactical_situation
        )
        
        # Create educational content
        tactical_concepts = self._identify_relevant_concepts(decision_response.recommended_action)
        learning_opportunities = self._generate_learning_opportunities(decision_factors)
        player_tips = self._generate_player_tips(decision_response, tactical_situation)
        
        # Generate primary reasoning text
        primary_reasoning = self._generate_primary_reasoning(
            decision_response.recommended_action, decision_factors, explanation_level
        )
        
        explanation = DecisionExplanation(
            decision_id=decision_id,
            session_id=decision_request.session_id,
            unit_id=decision_request.unit_id,
            timestamp=datetime.now(),
            chosen_action=decision_response.recommended_action.dict(),
            alternative_actions=[action.dict() for action in decision_response.alternative_actions],
            final_confidence=decision_response.confidence,
            primary_reasoning=primary_reasoning,
            decision_factors=[factor.__dict__ for factor in decision_factors],
            personality_influence=personality_influence,
            tactical_analysis=tactical_analysis,
            learning_insights={},  # Will be populated by learning system
            battlefield_assessment=battlefield_assessment,
            risk_assessment=risk_assessment,
            expected_outcomes=expected_outcomes,
            tactical_concepts=tactical_concepts,
            learning_opportunities=learning_opportunities,
            player_tips=player_tips
        )
        
        # Cache the explanation
        self.explanation_cache[decision_id] = explanation
        
        logger.info("Decision explanation generated",
                   decision_id=decision_id,
                   unit_id=decision_request.unit_id,
                   action_type=decision_response.recommended_action.action_type,
                   factors_count=len(decision_factors))
        
        return explanation
    
    async def _analyze_decision_factors(
        self,
        request: AIDecisionRequest,
        response: AIDecisionResponse,
        tactical_situation: TacticalSituation,
        personality: AIPersonality
    ) -> List[DecisionFactor]:
        """Analyze all factors that influenced the decision"""
        factors = []
        
        # Tactical factors
        if hasattr(tactical_situation, 'threat_map'):
            threat_level = self._calculate_position_threat(
                response.recommended_action, tactical_situation.threat_map
            )
            factors.append(DecisionFactor(
                factor_type=ReasoningType.TACTICAL,
                description=f"Threat level assessment: {threat_level:.1f}/10",
                weight=0.3,
                confidence=0.8,
                supporting_data={"threat_level": threat_level}
            ))
        
        # Personality factors
        personality_weight = self._calculate_personality_influence(personality, response.recommended_action)
        if personality_weight > 0.1:
            factors.append(DecisionFactor(
                factor_type=ReasoningType.PERSONALITY,
                description=f"{personality.personality_type.value} personality influence",
                weight=personality_weight,
                confidence=0.7,
                supporting_data={"personality_type": personality.personality_type.value}
            ))
        
        # Opportunity factors
        opportunity_score = self._calculate_opportunity_score(response.recommended_action, tactical_situation)
        if opportunity_score > 0.2:
            factors.append(DecisionFactor(
                factor_type=ReasoningType.OPPORTUNISTIC,
                description=f"Tactical opportunity identified",
                weight=opportunity_score,
                confidence=0.6,
                supporting_data={"opportunity_score": opportunity_score}
            ))
        
        # Defensive factors
        defensive_value = self._calculate_defensive_value(response.recommended_action, tactical_situation)
        if defensive_value > 0.1:
            factors.append(DecisionFactor(
                factor_type=ReasoningType.DEFENSIVE,
                description=f"Defensive positioning consideration",
                weight=defensive_value,
                confidence=0.8,
                supporting_data={"defensive_value": defensive_value}
            ))
        
        return factors
    
    def _explain_personality_influence(
        self, 
        personality: AIPersonality, 
        action: GameAction, 
        factors: List[DecisionFactor]
    ) -> Dict[str, Any]:
        """Explain how personality influenced the decision"""
        
        personality_traits = {}
        if hasattr(personality, 'traits'):
            personality_traits = {
                "aggression": personality.traits.aggression,
                "risk_tolerance": personality.traits.risk_tolerance,
                "patience": personality.traits.patience
            }
        
        influence_explanation = ""
        if personality.personality_type == PersonalityType.AGGRESSIVE:
            influence_explanation = "Aggressive personality favors direct confrontation and offensive actions"
        elif personality.personality_type == PersonalityType.DEFENSIVE:
            influence_explanation = "Defensive personality prioritizes unit preservation and careful positioning"
        elif personality.personality_type == PersonalityType.TACTICAL:
            influence_explanation = "Tactical personality emphasizes optimal positioning and battlefield control"
        elif personality.personality_type == PersonalityType.ADAPTIVE:
            influence_explanation = "Adaptive personality adjusts strategy based on current battlefield conditions"
        
        return {
            "personality_type": personality.personality_type.value,
            "traits": personality_traits,
            "influence_description": influence_explanation,
            "decision_alignment": self._calculate_personality_alignment(personality, action)
        }
    
    def _explain_tactical_analysis(self, tactical_situation: TacticalSituation, action: GameAction) -> Dict[str, Any]:
        """Explain the tactical analysis behind the decision"""
        analysis = {
            "battlefield_control": self._assess_battlefield_control(tactical_situation),
            "unit_positioning": self._assess_unit_positioning(tactical_situation),
            "threat_level": self._assess_current_threats(tactical_situation),
            "opportunities": self._identify_tactical_opportunities(tactical_situation, action)
        }
        
        return analysis
    
    def _explain_battlefield_assessment(self, battlefield_state: BattlefieldState, tactical_situation: TacticalSituation) -> Dict[str, Any]:
        """Explain current battlefield situation"""
        ally_count = len(tactical_situation.allies) if hasattr(tactical_situation, 'allies') else 0
        enemy_count = len(tactical_situation.enemies) if hasattr(tactical_situation, 'enemies') else 0
        
        return {
            "unit_balance": {
                "allies": ally_count,
                "enemies": enemy_count,
                "advantage": "allied" if ally_count > enemy_count else "enemy" if enemy_count > ally_count else "balanced"
            },
            "battlefield_phase": self._determine_battle_phase(tactical_situation),
            "key_positions": self._identify_key_positions(battlefield_state),
            "momentum": getattr(tactical_situation, 'momentum', 0.5)
        }
    
    def _explain_risk_assessment(self, response: AIDecisionResponse, tactical_situation: TacticalSituation) -> Dict[str, Any]:
        """Explain risk assessment for the chosen action"""
        action = response.recommended_action
        
        risk_factors = []
        if action.action_type == "attack":
            risk_factors.append("Potential counterattack exposure")
            risk_factors.append("Missing the attack")
        elif action.action_type == "move":
            risk_factors.append("Moving into enemy threat range")
            risk_factors.append("Leaving defensive position")
        
        return {
            "risk_level": self._calculate_action_risk(action, tactical_situation),
            "risk_factors": risk_factors,
            "mitigation_strategies": self._suggest_risk_mitigation(action),
            "acceptable_risk": response.confidence > 0.6
        }
    
    def _explain_expected_outcomes(self, response: AIDecisionResponse, tactical_situation: TacticalSituation) -> Dict[str, Any]:
        """Explain expected outcomes of the chosen action"""
        action = response.recommended_action
        
        outcomes = {
            "primary_outcome": self._describe_primary_outcome(action),
            "success_probability": response.confidence,
            "secondary_effects": self._identify_secondary_effects(action, tactical_situation),
            "long_term_impact": self._assess_long_term_impact(action, tactical_situation)
        }
        
        return outcomes
    
    def _generate_primary_reasoning(self, action: GameAction, factors: List[DecisionFactor], level: ExplanationLevel) -> str:
        """Generate human-readable primary reasoning text"""
        
        if not factors:
            return f"Performing {action.action_type} action based on current battlefield conditions."
        
        # Find the highest-weight factor
        primary_factor = max(factors, key=lambda f: f.weight)
        
        reasoning_templates = {
            ReasoningType.TACTICAL: f"Tactical analysis suggests {action.action_type} to exploit battlefield advantage",
            ReasoningType.PERSONALITY: f"AI personality drives {action.action_type} as preferred approach",
            ReasoningType.OPPORTUNISTIC: f"Identified opportunity warrants {action.action_type} for maximum impact",
            ReasoningType.DEFENSIVE: f"Defensive considerations require {action.action_type} to maintain position"
        }
        
        base_reasoning = reasoning_templates.get(primary_factor.factor_type, f"Choosing {action.action_type} action")
        
        if level == ExplanationLevel.BRIEF:
            return base_reasoning
        elif level == ExplanationLevel.DETAILED:
            return f"{base_reasoning}. {primary_factor.description} (confidence: {primary_factor.confidence:.1%})"
        else:  # Technical or Educational
            factor_details = ", ".join([f"{f.factor_type.value}: {f.weight:.2f}" for f in factors[:3]])
            return f"{base_reasoning}. Primary factors: {factor_details}. Overall confidence: {primary_factor.confidence:.1%}"
    
    def _identify_relevant_concepts(self, action: GameAction) -> List[str]:
        """Identify tactical concepts relevant to this decision"""
        concepts = []
        
        if action.action_type == "attack":
            concepts.extend(["focus_fire", "threat_assessment"])
        elif action.action_type == "move":
            concepts.extend(["positioning", "flanking"])
        elif action.action_type == "defend":
            concepts.extend(["positioning", "resource_management"])
        
        # Add advanced concepts based on action details
        if hasattr(action, 'target_position'):
            concepts.append("tactical_positioning")
        
        return concepts
    
    def _generate_learning_opportunities(self, factors: List[DecisionFactor]) -> List[str]:
        """Generate learning opportunities for the player"""
        opportunities = []
        
        for factor in factors:
            if factor.factor_type == ReasoningType.TACTICAL:
                opportunities.append("Study tactical positioning principles")
            elif factor.factor_type == ReasoningType.OPPORTUNISTIC:
                opportunities.append("Learn to identify battlefield opportunities")
            elif factor.confidence < 0.5:
                opportunities.append("Practice recognizing similar situations")
        
        return opportunities
    
    def _generate_player_tips(self, response: AIDecisionResponse, tactical_situation: TacticalSituation) -> List[str]:
        """Generate helpful tips for the player"""
        tips = []
        action = response.recommended_action
        
        if action.action_type == "attack":
            tips.append("Consider positioning before attacking to maximize damage")
            tips.append("Look for opportunities to attack with multiple units")
        elif action.action_type == "move":
            tips.append("Moving can expose you to enemy attacks - weigh the risks")
            tips.append("Good positioning is often more valuable than immediate action")
        
        # Add situational tips
        if hasattr(tactical_situation, 'enemies') and len(tactical_situation.enemies) > 2:
            tips.append("Against multiple enemies, focus fire on the biggest threat first")
        
        return tips
    
    # Helper methods for calculations
    def _calculate_position_threat(self, action: GameAction, threat_map: Dict[Tuple[int, int], float]) -> float:
        """Calculate threat level for action position"""
        if hasattr(action, 'target_position'):
            pos = (action.target_position.x, action.target_position.y)
            return threat_map.get(pos, 0.0)
        return 0.0
    
    def _calculate_personality_influence(self, personality: AIPersonality, action: GameAction) -> float:
        """Calculate how much personality influenced this decision"""
        # Simplified calculation - in practice this would be more sophisticated
        if personality.personality_type == PersonalityType.AGGRESSIVE and action.action_type == "attack":
            return 0.8
        elif personality.personality_type == PersonalityType.DEFENSIVE and action.action_type == "defend":
            return 0.7
        return 0.3
    
    def _calculate_opportunity_score(self, action: GameAction, tactical_situation: TacticalSituation) -> float:
        """Calculate opportunity score for this action"""
        # Simplified - would involve complex tactical analysis
        return 0.5
    
    def _calculate_defensive_value(self, action: GameAction, tactical_situation: TacticalSituation) -> float:
        """Calculate defensive value of this action"""
        if action.action_type in ["defend", "move"]:
            return 0.6
        return 0.2
    
    def _calculate_personality_alignment(self, personality: AIPersonality, action: GameAction) -> float:
        """Calculate how well action aligns with personality"""
        return 0.7  # Simplified
    
    def _assess_battlefield_control(self, tactical_situation: TacticalSituation) -> str:
        """Assess current battlefield control"""
        return "balanced"  # Simplified
    
    def _assess_unit_positioning(self, tactical_situation: TacticalSituation) -> str:
        """Assess unit positioning quality"""
        return "adequate"  # Simplified
    
    def _assess_current_threats(self, tactical_situation: TacticalSituation) -> str:
        """Assess current threat level"""
        return "moderate"  # Simplified
    
    def _identify_tactical_opportunities(self, tactical_situation: TacticalSituation, action: GameAction) -> List[str]:
        """Identify current tactical opportunities"""
        return ["flanking opportunity", "weak enemy position"]  # Simplified
    
    def _determine_battle_phase(self, tactical_situation: TacticalSituation) -> str:
        """Determine current phase of battle"""
        return "mid_game"  # Simplified
    
    def _identify_key_positions(self, battlefield_state: BattlefieldState) -> List[str]:
        """Identify key battlefield positions"""
        return ["center", "high_ground"]  # Simplified
    
    def _calculate_action_risk(self, action: GameAction, tactical_situation: TacticalSituation) -> str:
        """Calculate risk level of action"""
        return "moderate"  # Simplified
    
    def _suggest_risk_mitigation(self, action: GameAction) -> List[str]:
        """Suggest ways to mitigate risks"""
        return ["Position allies for support", "Have escape route ready"]
    
    def _describe_primary_outcome(self, action: GameAction) -> str:
        """Describe expected primary outcome"""
        if action.action_type == "attack":
            return "Damage enemy unit"
        elif action.action_type == "move":
            return "Improve tactical position"
        return "Maintain current advantage"
    
    def _identify_secondary_effects(self, action: GameAction, tactical_situation: TacticalSituation) -> List[str]:
        """Identify secondary effects of action"""
        return ["Changes battlefield dynamics", "May trigger enemy response"]
    
    def _assess_long_term_impact(self, action: GameAction, tactical_situation: TacticalSituation) -> str:
        """Assess long-term impact of action"""
        return "Positive tactical development"
    
    def get_explanation(self, decision_id: str) -> Optional[DecisionExplanation]:
        """Retrieve cached explanation by ID"""
        return self.explanation_cache.get(decision_id)
    
    def get_concept_details(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """Get details about a tactical concept"""
        return self.concept_library.get(concept_name)
    
    def clear_old_explanations(self, max_age_hours: int = 24):
        """Clear old explanations from cache"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = [
            decision_id for decision_id, explanation in self.explanation_cache.items()
            if explanation.timestamp < cutoff_time
        ]
        
        for decision_id in to_remove:
            del self.explanation_cache[decision_id]
        
        logger.info("Cleared old explanations", count=len(to_remove))
    
    def get_explanation_stats(self) -> Dict[str, Any]:
        """Get statistics about explanations"""
        total_explanations = len(self.explanation_cache)
        
        # Analyze explanation patterns
        action_types = {}
        avg_confidence = 0.0
        
        for explanation in self.explanation_cache.values():
            action_type = explanation.chosen_action.get("action_type", "unknown")
            action_types[action_type] = action_types.get(action_type, 0) + 1
            avg_confidence += explanation.final_confidence
        
        if total_explanations > 0:
            avg_confidence /= total_explanations
        
        return {
            "total_explanations": total_explanations,
            "action_type_distribution": action_types,
            "average_confidence": avg_confidence,
            "concepts_available": len(self.concept_library)
        }