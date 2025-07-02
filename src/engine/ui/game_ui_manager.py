"""
Game UI Manager

Real-time UI management system that provides WebSocket-based UI updates
and visual feedback for connected players.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

import structlog

from ...core.events import EventBus, GameEvent, EventType
from ...core.ecs import ECSManager, EntityID
from ..components.stats_component import StatsComponent
from ..components.position_component import PositionComponent
from ..components.team_component import TeamComponent
from ..components.equipment_component import EquipmentComponent
from ..components.status_effects_component import StatusEffectsComponent

logger = structlog.get_logger()


class UIEventType(str, Enum):
    """UI-specific event types"""
    UNIT_SELECTED = "unit_selected"
    UNIT_DESELECTED = "unit_deselected"
    TILE_HIGHLIGHTED = "tile_highlighted"
    TILE_UNHIGHLIGHTED = "tile_unhighlighted"
    ACTION_AVAILABLE = "action_available"
    ACTION_UNAVAILABLE = "action_unavailable"
    DAMAGE_DEALT = "damage_dealt"
    HEALING_APPLIED = "healing_applied"
    STATUS_EFFECT_APPLIED = "status_effect_applied"
    STATUS_EFFECT_REMOVED = "status_effect_removed"
    BATTLEFIELD_UPDATED = "battlefield_updated"
    TURN_INDICATOR_UPDATED = "turn_indicator_updated"


class HighlightType(str, Enum):
    """Tile highlight types for UI feedback"""
    MOVEMENT = "movement"
    ATTACK_RANGE = "attack_range"
    EFFECT_AREA = "effect_area"
    DANGER_ZONE = "danger_zone"
    SELECTION = "selection"
    INVALID = "invalid"
    PATH = "path"


@dataclass
class UIHighlight:
    """UI tile highlight configuration"""
    tile_x: int
    tile_y: int
    highlight_type: HighlightType
    color: str
    intensity: float = 1.0
    pulse: bool = False
    duration: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FloatingText:
    """Floating text configuration for UI effects"""
    x: float
    y: float
    z: float
    text: str
    color: str
    size: str = "medium"
    animation: str = "float_up"
    duration: float = 2.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UIState:
    """Current UI state for a session"""
    selected_unit: Optional[EntityID] = None
    highlighted_tiles: Dict[str, UIHighlight] = field(default_factory=dict)
    floating_texts: List[FloatingText] = field(default_factory=list)
    available_actions: List[Dict[str, Any]] = field(default_factory=list)
    turn_order: List[str] = field(default_factory=list)
    current_player: Optional[str] = None
    battlefield_size: tuple = (10, 10)
    camera_position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 5, "z": 5})


class GameUIManager:
    """Manages real-time UI updates and visual feedback"""
    
    def __init__(self, ecs: ECSManager, event_bus: EventBus):
        self.ecs = ecs
        self.event_bus = event_bus
        
        # UI state per session
        self.session_ui_states: Dict[str, UIState] = {}
        
        # WebSocket message callback
        self.websocket_callback: Optional[callable] = None
        
        # Performance tracking
        self.ui_updates_sent = 0
        self.last_cleanup_time = datetime.now()
        
        # Subscribe to game events
        self._subscribe_to_events()
        
        logger.info("Game UI Manager initialized")
    
    def _subscribe_to_events(self):
        """Subscribe to relevant game events"""
        self.event_bus.subscribe(EventType.UNIT_MOVED, self._on_unit_moved)
        self.event_bus.subscribe(EventType.UNIT_ATTACKED, self._on_unit_attacked)
        self.event_bus.subscribe(EventType.UNIT_DIED, self._on_unit_died)
        self.event_bus.subscribe(EventType.DAMAGE_DEALT, self._on_damage_dealt)
        self.event_bus.subscribe(EventType.HEALING_APPLIED, self._on_healing_applied)
        self.event_bus.subscribe(EventType.STATUS_EFFECT_APPLIED, self._on_status_effect_applied)
        self.event_bus.subscribe(EventType.STATUS_EFFECT_REMOVED, self._on_status_effect_removed)
        self.event_bus.subscribe(EventType.TURN_START, self._on_turn_start)
        self.event_bus.subscribe(EventType.TURN_END, self._on_turn_end)
        self.event_bus.subscribe(EventType.GAME_START, self._on_game_start)
        self.event_bus.subscribe(EventType.GAME_END, self._on_game_end)
    
    def set_websocket_callback(self, callback: callable):
        """Set callback for sending WebSocket messages"""
        self.websocket_callback = callback
    
    async def initialize_session(self, session_id: str, battlefield_size: tuple = (10, 10)):
        """Initialize UI state for a new session"""
        self.session_ui_states[session_id] = UIState(
            battlefield_size=battlefield_size
        )
        
        logger.info("UI state initialized for session", session_id=session_id)
    
    async def cleanup_session(self, session_id: str):
        """Clean up UI state for a session"""
        if session_id in self.session_ui_states:
            del self.session_ui_states[session_id]
            logger.info("UI state cleaned up for session", session_id=session_id)
    
    async def select_unit(self, session_id: str, entity_id: EntityID, player_id: str):
        """Select a unit and update UI highlights"""
        if session_id not in self.session_ui_states:
            return
        
        ui_state = self.session_ui_states[session_id]
        
        # Clear previous selection
        if ui_state.selected_unit:
            await self._clear_selection_highlights(session_id)
        
        ui_state.selected_unit = entity_id
        
        # Update unit highlights
        await self._update_unit_highlights(session_id, entity_id)
        
        # Update available actions
        await self._update_available_actions(session_id, entity_id)
        
        # Send UI update
        await self._send_ui_update(session_id, UIEventType.UNIT_SELECTED, {
            "unit_id": str(entity_id),
            "player_id": player_id,
            "unit_data": await self._get_unit_ui_data(entity_id)
        })
    
    async def deselect_unit(self, session_id: str):
        """Deselect current unit"""
        if session_id not in self.session_ui_states:
            return
        
        ui_state = self.session_ui_states[session_id]
        
        if ui_state.selected_unit:
            selected_unit = ui_state.selected_unit
            ui_state.selected_unit = None
            
            # Clear highlights
            await self._clear_selection_highlights(session_id)
            
            # Clear available actions
            ui_state.available_actions.clear()
            
            # Send UI update
            await self._send_ui_update(session_id, UIEventType.UNIT_DESELECTED, {
                "unit_id": str(selected_unit)
            })
    
    async def highlight_tiles(self, session_id: str, tiles: List[Dict[str, Any]], 
                            highlight_type: HighlightType, duration: Optional[float] = None):
        """Highlight multiple tiles"""
        if session_id not in self.session_ui_states:
            return
        
        ui_state = self.session_ui_states[session_id]
        
        for tile_data in tiles:
            tile_key = f"{tile_data['x']}_{tile_data['y']}"
            
            highlight = UIHighlight(
                tile_x=tile_data['x'],
                tile_y=tile_data['y'],
                highlight_type=highlight_type,
                color=self._get_highlight_color(highlight_type),
                intensity=tile_data.get('intensity', 1.0),
                pulse=tile_data.get('pulse', False),
                duration=duration
            )
            
            ui_state.highlighted_tiles[tile_key] = highlight
        
        # Send UI update
        await self._send_ui_update(session_id, UIEventType.TILE_HIGHLIGHTED, {
            "tiles": tiles,
            "highlight_type": highlight_type.value,
            "duration": duration
        })
    
    async def clear_highlights(self, session_id: str, highlight_type: Optional[HighlightType] = None):
        """Clear tile highlights"""
        if session_id not in self.session_ui_states:
            return
        
        ui_state = self.session_ui_states[session_id]
        
        if highlight_type is None:
            # Clear all highlights
            cleared_tiles = list(ui_state.highlighted_tiles.keys())
            ui_state.highlighted_tiles.clear()
        else:
            # Clear specific highlight type
            cleared_tiles = []
            tiles_to_remove = []
            
            for tile_key, highlight in ui_state.highlighted_tiles.items():
                if highlight.highlight_type == highlight_type:
                    cleared_tiles.append(tile_key)
                    tiles_to_remove.append(tile_key)
            
            for tile_key in tiles_to_remove:
                del ui_state.highlighted_tiles[tile_key]
        
        if cleared_tiles:
            await self._send_ui_update(session_id, UIEventType.TILE_UNHIGHLIGHTED, {
                "tiles": cleared_tiles,
                "highlight_type": highlight_type.value if highlight_type else "all"
            })
    
    async def show_floating_text(self, session_id: str, x: float, y: float, z: float, 
                                text: str, color: str, animation: str = "float_up", 
                                duration: float = 2.0):
        """Show floating text effect"""
        if session_id not in self.session_ui_states:
            return
        
        ui_state = self.session_ui_states[session_id]
        
        floating_text = FloatingText(
            x=x, y=y, z=z,
            text=text,
            color=color,
            animation=animation,
            duration=duration
        )
        
        ui_state.floating_texts.append(floating_text)
        
        # Send UI update
        await self._send_ui_update(session_id, "floating_text", {
            "x": x, "y": y, "z": z,
            "text": text,
            "color": color,
            "animation": animation,
            "duration": duration
        })
        
        # Schedule cleanup
        asyncio.create_task(self._cleanup_floating_text(session_id, floating_text, duration))
    
    async def update_turn_indicator(self, session_id: str, current_player: str, 
                                  turn_order: List[str], time_remaining: float):
        """Update turn indicator UI"""
        if session_id not in self.session_ui_states:
            return
        
        ui_state = self.session_ui_states[session_id]
        ui_state.current_player = current_player
        ui_state.turn_order = turn_order
        
        await self._send_ui_update(session_id, UIEventType.TURN_INDICATOR_UPDATED, {
            "current_player": current_player,
            "turn_order": turn_order,
            "time_remaining": time_remaining
        })
    
    async def update_battlefield_view(self, session_id: str, camera_position: Dict[str, float] = None):
        """Update battlefield view and camera position"""
        if session_id not in self.session_ui_states:
            return
        
        ui_state = self.session_ui_states[session_id]
        
        if camera_position:
            ui_state.camera_position = camera_position
        
        # Get current battlefield state
        battlefield_data = await self._get_battlefield_ui_data(session_id)
        
        await self._send_ui_update(session_id, UIEventType.BATTLEFIELD_UPDATED, {
            "battlefield": battlefield_data,
            "camera_position": ui_state.camera_position
        })
    
    # Event handlers
    async def _on_unit_moved(self, event: GameEvent):
        """Handle unit movement event"""
        session_id = event.session_id
        unit_id = event.data.get("unit_id")
        from_pos = event.data.get("from_position", {})
        to_pos = event.data.get("to_position", {})
        
        # Show movement trail
        await self.highlight_tiles(session_id, [
            {"x": from_pos.get("x", 0), "y": from_pos.get("y", 0), "pulse": True}
        ], HighlightType.PATH, duration=1.0)
        
        # Update battlefield view
        await self.update_battlefield_view(session_id)
    
    async def _on_unit_attacked(self, event: GameEvent):
        """Handle unit attack event"""
        session_id = event.session_id
        attacker_id = event.data.get("attacker_id")
        target_id = event.data.get("target_id")
        
        # Get positions for visual effects
        if attacker_id and target_id:
            attacker_pos = await self._get_unit_position(EntityID(attacker_id))
            target_pos = await self._get_unit_position(EntityID(target_id))
            
            if attacker_pos and target_pos:
                # Show attack effect
                await self.show_floating_text(
                    session_id, 
                    target_pos.x, target_pos.y + 1, target_pos.z,
                    "⚔️", "#FF4444", "shake", 1.5
                )
    
    async def _on_unit_died(self, event: GameEvent):
        """Handle unit death event"""
        session_id = event.session_id
        unit_id = event.data.get("unit_id")
        
        if unit_id:
            position = await self._get_unit_position(EntityID(unit_id))
            if position:
                await self.show_floating_text(
                    session_id,
                    position.x, position.y + 1, position.z,
                    "💀", "#888888", "fade_out", 3.0
                )
        
        # Update battlefield view
        await self.update_battlefield_view(session_id)
    
    async def _on_damage_dealt(self, event: GameEvent):
        """Handle damage dealt event"""
        session_id = event.session_id
        target_id = event.data.get("target_id")
        damage = event.data.get("damage", 0)
        damage_type = event.data.get("damage_type", "physical")
        
        if target_id:
            position = await self._get_unit_position(EntityID(target_id))
            if position:
                color = "#FF0000" if damage_type == "physical" else "#FF00FF" if damage_type == "magical" else "#FFAA00"
                await self.show_floating_text(
                    session_id,
                    position.x + 0.3, position.y + 1.2, position.z,
                    f"-{damage}", color, "float_up", 2.0
                )
    
    async def _on_healing_applied(self, event: GameEvent):
        """Handle healing applied event"""
        session_id = event.session_id
        target_id = event.data.get("target_id")
        healing = event.data.get("healing", 0)
        
        if target_id:
            position = await self._get_unit_position(EntityID(target_id))
            if position:
                await self.show_floating_text(
                    session_id,
                    position.x - 0.3, position.y + 1.2, position.z,
                    f"+{healing}", "#00FF00", "float_up", 2.0
                )
    
    async def _on_status_effect_applied(self, event: GameEvent):
        """Handle status effect applied event"""
        session_id = event.session_id
        target_id = event.data.get("target_id")
        effect_name = event.data.get("effect_name", "")
        
        if target_id:
            position = await self._get_unit_position(EntityID(target_id))
            if position:
                effect_icon = self._get_status_effect_icon(effect_name)
                await self.show_floating_text(
                    session_id,
                    position.x, position.y + 1.5, position.z,
                    effect_icon, "#FFFF00", "pulse", 2.5
                )
    
    async def _on_status_effect_removed(self, event: GameEvent):
        """Handle status effect removed event"""
        session_id = event.session_id
        target_id = event.data.get("target_id")
        effect_name = event.data.get("effect_name", "")
        
        if target_id:
            position = await self._get_unit_position(EntityID(target_id))
            if position:
                await self.show_floating_text(
                    session_id,
                    position.x, position.y + 1.5, position.z,
                    "✨", "#AAAAAA", "fade_out", 1.5
                )
    
    async def _on_turn_start(self, event: GameEvent):
        """Handle turn start event"""
        session_id = event.session_id
        current_player = event.data.get("current_player")
        turn_number = event.data.get("turn_number", 1)
        time_limit = event.data.get("time_limit", 30.0)
        
        # Update turn indicator
        turn_order = []  # This would come from game state
        await self.update_turn_indicator(session_id, current_player, turn_order, time_limit)
    
    async def _on_turn_end(self, event: GameEvent):
        """Handle turn end event"""
        session_id = event.session_id
        
        # Clear selection and highlights
        await self.deselect_unit(session_id)
        await self.clear_highlights(session_id)
    
    async def _on_game_start(self, event: GameEvent):
        """Handle game start event"""
        session_id = event.session_id
        battlefield_size = event.data.get("battlefield_size", (10, 10))
        
        await self.initialize_session(session_id, battlefield_size)
        await self.update_battlefield_view(session_id)
    
    async def _on_game_end(self, event: GameEvent):
        """Handle game end event"""
        session_id = event.session_id
        winner = event.data.get("winner")
        
        # Show game end effect
        await self.show_floating_text(
            session_id, 0, 2, 0,
            f"Game Over - Winner: {winner}" if winner else "Game Over - Draw",
            "#FFD700", "pulse", 5.0
        )
    
    # Helper methods
    async def _get_unit_position(self, entity_id: EntityID):
        """Get unit position from ECS"""
        position_component = self.ecs.get_component(entity_id, PositionComponent)
        return position_component if position_component else None
    
    async def _get_unit_ui_data(self, entity_id: EntityID) -> Dict[str, Any]:
        """Get comprehensive UI data for a unit"""
        stats = self.ecs.get_component(entity_id, StatsComponent)
        position = self.ecs.get_component(entity_id, PositionComponent)
        team = self.ecs.get_component(entity_id, TeamComponent)
        equipment = self.ecs.get_component(entity_id, EquipmentComponent)
        status_effects = self.ecs.get_component(entity_id, StatusEffectsComponent)
        
        unit_data = {
            "unit_id": str(entity_id),
            "position": {
                "x": position.x if position else 0,
                "y": position.y if position else 0,
                "z": position.z if position else 0
            },
            "team": team.team if team else "neutral",
            "can_move": position.can_move if position else False,
            "has_moved": position.has_moved if position else False
        }
        
        if stats:
            unit_data["stats"] = {
                "hp": {"current": stats.current_hp, "max": stats.max_hp},
                "mp": {"current": stats.current_mp, "max": stats.max_mp},
                "alive": stats.alive
            }
        
        if equipment:
            equipment.calculate_bonuses()
            unit_data["equipment"] = {
                "attack_bonus": equipment.total_attack_bonus,
                "defense_bonus": equipment.total_defense_bonus
            }
        
        if status_effects:
            unit_data["status_effects"] = status_effects.get_effect_summary()
        
        return unit_data
    
    async def _get_battlefield_ui_data(self, session_id: str) -> Dict[str, Any]:
        """Get battlefield data for UI"""
        if session_id not in self.session_ui_states:
            return {}
        
        ui_state = self.session_ui_states[session_id]
        
        # Get all units on battlefield
        units = []
        entities_with_position = self.ecs.get_entities_with_components([PositionComponent])
        
        for entity_id in entities_with_position:
            unit_data = await self._get_unit_ui_data(entity_id)
            units.append(unit_data)
        
        return {
            "size": ui_state.battlefield_size,
            "units": units,
            "highlights": [
                {
                    "x": highlight.tile_x,
                    "y": highlight.tile_y,
                    "type": highlight.highlight_type.value,
                    "color": highlight.color,
                    "intensity": highlight.intensity,
                    "pulse": highlight.pulse
                }
                for highlight in ui_state.highlighted_tiles.values()
            ]
        }
    
    async def _update_unit_highlights(self, session_id: str, entity_id: EntityID):
        """Update highlights for selected unit"""
        position = await self._get_unit_position(entity_id)
        if not position:
            return
        
        # Highlight unit position
        await self.highlight_tiles(session_id, [
            {"x": position.x, "y": position.y, "intensity": 1.2, "pulse": True}
        ], HighlightType.SELECTION)
        
        # Show movement range (simplified)
        movement_tiles = []
        if position.can_move:
            movement_speed = getattr(position, 'movement_speed', 3)
            for dx in range(-movement_speed, movement_speed + 1):
                for dy in range(-movement_speed, movement_speed + 1):
                    if abs(dx) + abs(dy) <= movement_speed and (dx != 0 or dy != 0):
                        movement_tiles.append({
                            "x": position.x + dx,
                            "y": position.y + dy,
                            "intensity": 0.7
                        })
        
        if movement_tiles:
            await self.highlight_tiles(session_id, movement_tiles, HighlightType.MOVEMENT)
    
    async def _clear_selection_highlights(self, session_id: str):
        """Clear highlights related to unit selection"""
        await self.clear_highlights(session_id, HighlightType.SELECTION)
        await self.clear_highlights(session_id, HighlightType.MOVEMENT)
        await self.clear_highlights(session_id, HighlightType.ATTACK_RANGE)
    
    async def _update_available_actions(self, session_id: str, entity_id: EntityID):
        """Update available actions for selected unit"""
        if session_id not in self.session_ui_states:
            return
        
        ui_state = self.session_ui_states[session_id]
        
        # Get unit components
        position = self.ecs.get_component(entity_id, PositionComponent)
        stats = self.ecs.get_component(entity_id, StatsComponent)
        status_effects = self.ecs.get_component(entity_id, StatusEffectsComponent)
        
        actions = []
        
        if stats and stats.alive:
            # Check if unit can act
            can_act = True
            if status_effects:
                can_act = status_effects.can_act()
            
            if can_act:
                # Movement action
                if position and position.can_move and not position.has_moved:
                    actions.append({
                        "type": "move",
                        "name": "Move",
                        "available": True,
                        "description": "Move to a new position"
                    })
                
                # Attack action
                actions.append({
                    "type": "attack",
                    "name": "Attack", 
                    "available": True,
                    "description": "Attack an enemy unit"
                })
                
                # Wait action (always available)
                actions.append({
                    "type": "wait",
                    "name": "Wait",
                    "available": True,
                    "description": "End turn without action"
                })
        
        ui_state.available_actions = actions
        
        await self._send_ui_update(session_id, UIEventType.ACTION_AVAILABLE, {
            "unit_id": str(entity_id),
            "actions": actions
        })
    
    def _get_highlight_color(self, highlight_type: HighlightType) -> str:
        """Get color for highlight type"""
        colors = {
            HighlightType.MOVEMENT: "#00FF00",      # Green
            HighlightType.ATTACK_RANGE: "#FF0000",  # Red
            HighlightType.EFFECT_AREA: "#FFFF00",   # Yellow
            HighlightType.DANGER_ZONE: "#FF8800",   # Orange
            HighlightType.SELECTION: "#FFFFFF",     # White
            HighlightType.INVALID: "#8800AA",       # Purple
            HighlightType.PATH: "#0088FF"           # Blue
        }
        return colors.get(highlight_type, "#FFFFFF")
    
    def _get_status_effect_icon(self, effect_name: str) -> str:
        """Get icon for status effect"""
        icons = {
            "poison": "☠️",
            "burn": "🔥", 
            "bleed": "🩸",
            "regeneration": "💚",
            "blessed": "✨",
            "stunned": "😵",
            "slowed": "🐌",
            "hasted": "💨",
            "attack_boost": "💪",
            "defense_boost": "🛡️"
        }
        return icons.get(effect_name, "❓")
    
    async def _send_ui_update(self, session_id: str, event_type: str, data: Dict[str, Any]):
        """Send UI update via WebSocket"""
        if not self.websocket_callback:
            return
        
        message = {
            "type": "ui_update",
            "event_type": event_type,
            "session_id": session_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self.websocket_callback(session_id, message)
            self.ui_updates_sent += 1
        except Exception as e:
            logger.error("Failed to send UI update", 
                        session_id=session_id,
                        event_type=event_type,
                        error=str(e))
    
    async def _cleanup_floating_text(self, session_id: str, floating_text: FloatingText, duration: float):
        """Clean up floating text after duration"""
        await asyncio.sleep(duration)
        
        if session_id in self.session_ui_states:
            ui_state = self.session_ui_states[session_id]
            if floating_text in ui_state.floating_texts:
                ui_state.floating_texts.remove(floating_text)
    
    async def update(self, delta_time: float):
        """Update UI manager (called from game loop)"""
        current_time = datetime.now()
        
        # Clean up expired highlights and effects periodically
        if (current_time - self.last_cleanup_time).total_seconds() > 5.0:
            await self._cleanup_expired_effects()
            self.last_cleanup_time = current_time
    
    async def _cleanup_expired_effects(self):
        """Clean up expired UI effects"""
        current_time = datetime.now()
        
        for session_id, ui_state in self.session_ui_states.items():
            # Clean up expired highlights
            expired_highlights = []
            for tile_key, highlight in ui_state.highlighted_tiles.items():
                if (highlight.duration and 
                    (current_time - highlight.created_at).total_seconds() > highlight.duration):
                    expired_highlights.append(tile_key)
            
            for tile_key in expired_highlights:
                del ui_state.highlighted_tiles[tile_key]
            
            # Clean up expired floating texts
            ui_state.floating_texts = [
                text for text in ui_state.floating_texts
                if (current_time - text.created_at).total_seconds() < text.duration
            ]
    
    def get_ui_stats(self) -> Dict[str, Any]:
        """Get UI manager statistics"""
        total_highlights = sum(
            len(ui_state.highlighted_tiles) 
            for ui_state in self.session_ui_states.values()
        )
        
        total_floating_texts = sum(
            len(ui_state.floating_texts)
            for ui_state in self.session_ui_states.values()
        )
        
        return {
            "active_sessions": len(self.session_ui_states),
            "ui_updates_sent": self.ui_updates_sent,
            "total_highlights": total_highlights,
            "total_floating_texts": total_floating_texts
        }
    
    async def get_session_ui_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current UI state for a session"""
        if session_id not in self.session_ui_states:
            return None
        
        ui_state = self.session_ui_states[session_id]
        
        return {
            "selected_unit": str(ui_state.selected_unit) if ui_state.selected_unit else None,
            "highlighted_tiles": len(ui_state.highlighted_tiles),
            "floating_texts": len(ui_state.floating_texts),
            "available_actions": len(ui_state.available_actions),
            "current_player": ui_state.current_player,
            "camera_position": ui_state.camera_position
        }