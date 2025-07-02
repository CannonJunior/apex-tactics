"""
Team Component

Manages team affiliation, relationships, and team-based mechanics
for tactical gameplay and AI coordination.
"""

from typing import Dict, Any, Set, Optional
from dataclasses import dataclass, field

from ...core.ecs import Component


@dataclass
class TeamComponent(Component):
    """Component for team membership and relationships"""
    
    team: str = "neutral"
    player_controlled: bool = False
    ai_controlled: bool = True
    
    # Team relationships
    allied_teams: Set[str] = field(default_factory=set)
    enemy_teams: Set[str] = field(default_factory=set)
    neutral_teams: Set[str] = field(default_factory=set)
    
    # Team role and hierarchy
    team_role: str = "soldier"  # soldier, leader, support, specialist
    command_level: int = 0  # Higher level can command lower level units
    leader_id: Optional[str] = None  # ID of team leader
    
    # Team bonuses and effects
    receives_team_bonuses: bool = True
    provides_team_bonuses: bool = False
    team_bonus_range: int = 2  # Range for team bonus effects
    
    # Combat coordination
    can_coordinate_attacks: bool = True
    preferred_formation: str = "loose"  # loose, tight, line, wedge
    formation_position: int = 0  # Position within formation
    
    def is_ally(self, other_team: str) -> bool:
        """Check if another team is an ally"""
        return other_team in self.allied_teams or other_team == self.team
    
    def is_enemy(self, other_team: str) -> bool:
        """Check if another team is an enemy"""
        return other_team in self.enemy_teams
    
    def is_neutral(self, other_team: str) -> bool:
        """Check if another team is neutral"""
        return other_team in self.neutral_teams or (
            not self.is_ally(other_team) and not self.is_enemy(other_team)
        )
    
    def add_ally(self, team_name: str):
        """Add allied team"""
        self.allied_teams.add(team_name)
        self.enemy_teams.discard(team_name)  # Remove from enemies if present
        self.neutral_teams.discard(team_name)  # Remove from neutral if present
    
    def add_enemy(self, team_name: str):
        """Add enemy team"""
        self.enemy_teams.add(team_name)
        self.allied_teams.discard(team_name)  # Remove from allies if present
        self.neutral_teams.discard(team_name)  # Remove from neutral if present
    
    def set_neutral(self, team_name: str):
        """Set team as neutral"""
        self.neutral_teams.add(team_name)
        self.allied_teams.discard(team_name)
        self.enemy_teams.discard(team_name)
    
    def can_target(self, other_team: str, friendly_fire: bool = False) -> bool:
        """Check if can target units from another team"""
        if self.is_enemy(other_team):
            return True
        
        if friendly_fire and (self.is_ally(other_team) or other_team == self.team):
            return True
        
        return False
    
    def can_coordinate_with(self, other_team_component: 'TeamComponent') -> bool:
        """Check if can coordinate with another unit"""
        if not self.can_coordinate_attacks:
            return False
        
        return self.is_ally(other_team_component.team)
    
    def can_command(self, other_team_component: 'TeamComponent') -> bool:
        """Check if can command another unit"""
        if not self.is_ally(other_team_component.team):
            return False
        
        return self.command_level > other_team_component.command_level
    
    def is_leader(self) -> bool:
        """Check if this unit is a team leader"""
        return self.team_role == "leader" or self.command_level > 0
    
    def has_leader(self) -> bool:
        """Check if this unit has a designated leader"""
        return self.leader_id is not None
    
    def set_leader(self, leader_id: str):
        """Set team leader"""
        self.leader_id = leader_id
        
        # If setting self as leader, update role
        if leader_id == str(self.entity_id):
            self.team_role = "leader"
            self.command_level = max(1, self.command_level)
    
    def get_relationship(self, other_team: str) -> str:
        """Get relationship type with another team"""
        if self.is_ally(other_team):
            return "ally"
        elif self.is_enemy(other_team):
            return "enemy"
        else:
            return "neutral"
    
    def promote_to_leader(self):
        """Promote unit to leader role"""
        self.team_role = "leader"
        self.command_level = max(1, self.command_level)
        self.provides_team_bonuses = True
        self.can_coordinate_attacks = True
    
    def demote_from_leader(self):
        """Demote unit from leader role"""
        if self.team_role == "leader":
            self.team_role = "soldier"
        self.command_level = 0
        self.provides_team_bonuses = False
    
    def get_team_bonus_effectiveness(self) -> float:
        """Get effectiveness of team bonuses provided"""
        if not self.provides_team_bonuses:
            return 0.0
        
        if self.team_role == "leader":
            return 1.0
        elif self.team_role == "support":
            return 0.7
        else:
            return 0.3
    
    def should_receive_bonus_from(self, provider_team_component: 'TeamComponent') -> bool:
        """Check if should receive team bonus from another unit"""
        if not self.receives_team_bonuses:
            return False
        
        if not provider_team_component.provides_team_bonuses:
            return False
        
        return self.is_ally(provider_team_component.team)
    
    def get_formation_priority(self) -> int:
        """Get priority for formation positioning"""
        role_priorities = {
            "leader": 10,
            "support": 5,
            "specialist": 7,
            "soldier": 3
        }
        
        base_priority = role_priorities.get(self.team_role, 1)
        return base_priority + self.command_level
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary"""
        return {
            "team": self.team,
            "player_controlled": self.player_controlled,
            "ai_controlled": self.ai_controlled,
            "allied_teams": list(self.allied_teams),
            "enemy_teams": list(self.enemy_teams),
            "neutral_teams": list(self.neutral_teams),
            "team_role": self.team_role,
            "command_level": self.command_level,
            "leader_id": self.leader_id,
            "receives_team_bonuses": self.receives_team_bonuses,
            "provides_team_bonuses": self.provides_team_bonuses,
            "team_bonus_range": self.team_bonus_range,
            "can_coordinate_attacks": self.can_coordinate_attacks,
            "preferred_formation": self.preferred_formation,
            "formation_position": self.formation_position
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Deserialize component from dictionary"""
        self.team = data.get("team", "neutral")
        self.player_controlled = data.get("player_controlled", False)
        self.ai_controlled = data.get("ai_controlled", True)
        self.allied_teams = set(data.get("allied_teams", []))
        self.enemy_teams = set(data.get("enemy_teams", []))
        self.neutral_teams = set(data.get("neutral_teams", []))
        self.team_role = data.get("team_role", "soldier")
        self.command_level = data.get("command_level", 0)
        self.leader_id = data.get("leader_id")
        self.receives_team_bonuses = data.get("receives_team_bonuses", True)
        self.provides_team_bonuses = data.get("provides_team_bonuses", False)
        self.team_bonus_range = data.get("team_bonus_range", 2)
        self.can_coordinate_attacks = data.get("can_coordinate_attacks", True)
        self.preferred_formation = data.get("preferred_formation", "loose")
        self.formation_position = data.get("formation_position", 0)