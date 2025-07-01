"""
Start Screen Implementation

Main menu screen with New Game, Load Game, and Settings options.
Uses portable UI framework for multi-engine compatibility.
"""

from typing import Optional, Callable
from ..core.ui_abstractions import *
from ..ursina.ursina_ui_manager import UrsinaUIScreen, UrsinaUIButton, UrsinaUIText, UrsinaUIPanel

class GameSettings:
    """Game settings data structure"""
    
    def __init__(self):
        self.difficulty = "Normal"
        self.music_volume = 0.8
        self.sfx_volume = 0.8
        self.fullscreen = False
        self.graphics_quality = "High"
        self.auto_save = True
        
    def to_dict(self) -> dict:
        """Convert settings to dictionary"""
        return {
            'difficulty': self.difficulty,
            'music_volume': self.music_volume,
            'sfx_volume': self.sfx_volume,
            'fullscreen': self.fullscreen,
            'graphics_quality': self.graphics_quality,
            'auto_save': self.auto_save
        }
    
    def from_dict(self, data: dict) -> None:
        """Load settings from dictionary"""
        self.difficulty = data.get('difficulty', self.difficulty)
        self.music_volume = data.get('music_volume', self.music_volume)
        self.sfx_volume = data.get('sfx_volume', self.sfx_volume)
        self.fullscreen = data.get('fullscreen', self.fullscreen)
        self.graphics_quality = data.get('graphics_quality', self.graphics_quality)
        self.auto_save = data.get('auto_save', self.auto_save)

class StartScreen(UrsinaUIScreen):
    """
    Main menu start screen with game options.
    
    Provides New Game, Load Game, and Settings functionality
    with a clean, professional interface.
    """
    
    def __init__(self, 
                 on_new_game: Optional[Callable] = None,
                 on_load_game: Optional[Callable] = None,
                 on_practice_battle: Optional[Callable] = None,
                 on_settings: Optional[Callable] = None,
                 on_exit: Optional[Callable] = None):
        super().__init__("Apex Tactics")
        
        # Store callbacks
        self.on_new_game = on_new_game
        self.on_load_game = on_load_game
        self.on_practice_battle = on_practice_battle
        self.on_settings = on_settings
        self.on_exit = on_exit
        
        # Settings instance
        self.settings = GameSettings()
        
        # UI elements
        self.main_panel: Optional[IUIPanel] = None
        self.title_label: Optional[IUIText] = None
        self.subtitle_label: Optional[IUIText] = None
        self.new_game_button: Optional[IUIButton] = None
        self.load_game_button: Optional[IUIButton] = None
        self.practice_battle_button: Optional[IUIButton] = None
        self.settings_button: Optional[IUIButton] = None
        self.exit_button: Optional[IUIButton] = None
        self.version_label: Optional[IUIText] = None
        
        # Initialize UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the start screen UI layout - full screen design"""
        # Create full screen background panel
        self.main_panel = UrsinaUIPanel(UIColor.from_hex("#1A1A2E"))  # Dark blue background
        self.main_panel.position = UIVector2(0, 0)
        self.main_panel.size = UIVector2(100, 100)  # Full screen
        self.main_panel.border_color = UIColor.from_hex("#16213E")
        self.main_panel.border_width = 0  # No border for full screen
        self.add_child(self.main_panel)
        
        # Create title - positioned higher and larger
        self.title_label = UrsinaUIText("APEX TACTICS", UIColor.from_hex("#E94560"))
        self.title_label.position = UIVector2(50, 85)  # Higher position
        self.title_label.font_size = 42  # Larger font
        self.add_child(self.title_label)
        
        # Create subtitle - positioned below title
        self.subtitle_label = UrsinaUIText("Tactical RPG Engine", UIColor.from_hex("#0F3460"))
        self.subtitle_label.position = UIVector2(50, 78)  # Below title
        self.subtitle_label.font_size = 18
        self.add_child(self.subtitle_label)
        
        # Button configuration - larger and properly spaced
        button_width = 25
        button_height = 6
        button_x = 50 - button_width / 2  # Center buttons
        button_spacing = 8  # Space between buttons
        
        # Starting Y position for buttons (centered vertically)
        start_y = 60
        
        # New Game button
        self.new_game_button = UrsinaUIButton("NEW GAME", self._handle_new_game)
        self.new_game_button.position = UIVector2(button_x, start_y)
        self.new_game_button.size = UIVector2(button_width, button_height)
        self.new_game_button.background_color = UIColor.from_hex("#4CAF50")  # Green
        self.new_game_button.hover_color = UIColor.from_hex("#66BB6A")
        self.new_game_button.text_color = UIColor.white()
        self.add_child(self.new_game_button)
        
        # Load Game button
        self.load_game_button = UrsinaUIButton("LOAD GAME", self._handle_load_game)
        self.load_game_button.position = UIVector2(button_x, start_y - button_spacing)
        self.load_game_button.size = UIVector2(button_width, button_height)
        self.load_game_button.background_color = UIColor.from_hex("#2196F3")  # Blue
        self.load_game_button.hover_color = UIColor.from_hex("#42A5F5")
        self.load_game_button.text_color = UIColor.white()
        self.add_child(self.load_game_button)
        
        # Practice Battle button (new)
        self.practice_battle_button = UrsinaUIButton("PRACTICE BATTLE", self._handle_practice_battle)
        self.practice_battle_button.position = UIVector2(button_x, start_y - button_spacing * 2)
        self.practice_battle_button.size = UIVector2(button_width, button_height)
        self.practice_battle_button.background_color = UIColor.from_hex("#9C27B0")  # Purple
        self.practice_battle_button.hover_color = UIColor.from_hex("#BA68C8")
        self.practice_battle_button.text_color = UIColor.white()
        self.add_child(self.practice_battle_button)
        
        # Settings button
        self.settings_button = UrsinaUIButton("SETTINGS", self._handle_settings)
        self.settings_button.position = UIVector2(button_x, start_y - button_spacing * 3)
        self.settings_button.size = UIVector2(button_width, button_height)
        self.settings_button.background_color = UIColor.from_hex("#FF9800")  # Orange
        self.settings_button.hover_color = UIColor.from_hex("#FFB74D")
        self.settings_button.text_color = UIColor.white()
        self.add_child(self.settings_button)
        
        # Exit button
        self.exit_button = UrsinaUIButton("EXIT", self._handle_exit)
        self.exit_button.position = UIVector2(button_x, start_y - button_spacing * 4)
        self.exit_button.size = UIVector2(button_width, button_height)
        self.exit_button.background_color = UIColor.from_hex("#F44336")  # Red
        self.exit_button.hover_color = UIColor.from_hex("#EF5350")
        self.exit_button.text_color = UIColor.white()
        self.add_child(self.exit_button)
        
        # Version label - bottom left corner
        self.version_label = UrsinaUIText("v1.0.0 - Phase 4.5", UIColor.from_hex("#707070"))
        self.version_label.position = UIVector2(2, 2)  # Bottom left
        self.version_label.font_size = 10
        self.add_child(self.version_label)
    
    def _handle_new_game(self, button):
        """Handle New Game button click"""
        print("New Game selected")
        if self.on_new_game:
            self.on_new_game()
    
    def _handle_load_game(self, button):
        """Handle Load Game button click"""
        print("Load Game selected")
        if self.on_load_game:
            self.on_load_game()
    
    def _handle_practice_battle(self, button):
        """Handle Practice Battle button click"""
        print("Practice Battle selected")
        if self.on_practice_battle:
            self.on_practice_battle()
    
    def _handle_settings(self, button):
        """Handle Settings button click"""
        print("Settings selected")
        if self.on_settings:
            self.on_settings(self.settings)
    
    def _handle_exit(self, button):
        """Handle Exit button click"""
        print("Exit selected")
        if self.on_exit:
            self.on_exit()
    
    def set_new_game_callback(self, callback: Callable):
        """Set new game callback"""
        self.on_new_game = callback
    
    def set_load_game_callback(self, callback: Callable):
        """Set load game callback"""
        self.on_load_game = callback
    
    def set_practice_battle_callback(self, callback: Callable):
        """Set practice battle callback"""
        self.on_practice_battle = callback
    
    def set_settings_callback(self, callback: Callable):
        """Set settings callback"""
        self.on_settings = callback
    
    def set_exit_callback(self, callback: Callable):
        """Set exit callback"""
        self.on_exit = callback

class SettingsScreen(UrsinaUIScreen):
    """Settings configuration screen"""
    
    def __init__(self, settings: GameSettings, on_back: Optional[Callable] = None):
        super().__init__("Settings")
        self.settings = settings
        self.on_back = on_back
        
        # UI elements
        self.settings_panel: Optional[IUIPanel] = None
        self.back_button: Optional[IUIButton] = None
        self.apply_button: Optional[IUIButton] = None
        
        # Setting controls
        self.difficulty_label: Optional[IUIText] = None
        self.difficulty_button: Optional[IUIButton] = None
        self.music_label: Optional[IUIText] = None
        self.sfx_label: Optional[IUIText] = None
        self.graphics_label: Optional[IUIText] = None
        self.graphics_button: Optional[IUIButton] = None
        
        # Current setting values for cycling
        self.difficulty_options = ["Easy", "Normal", "Hard", "Expert"]
        self.graphics_options = ["Low", "Medium", "High", "Ultra"]
        
        self._create_ui()
    
    def _create_ui(self):
        """Create settings screen UI"""
        # Main settings panel
        self.settings_panel = UrsinaUIPanel(UIColor.gray(0.15))
        self.settings_panel.position = UIVector2(20, 15)
        self.settings_panel.size = UIVector2(60, 70)
        self.settings_panel.border_color = UIColor.gray(0.4)
        self.settings_panel.border_width = 2
        self.add_child(self.settings_panel)
        
        # Difficulty setting
        self.difficulty_label = UrsinaUIText("Difficulty:", UIColor.white())
        self.difficulty_label.position = UIVector2(25, 70)
        self.difficulty_label.font_size = 16
        self.add_child(self.difficulty_label)
        
        self.difficulty_button = UrsinaUIButton(self.settings.difficulty, self._cycle_difficulty)
        self.difficulty_button.position = UIVector2(55, 68)
        self.difficulty_button.size = UIVector2(20, 6)
        self.difficulty_button.background_color = UIColor.from_hex("#607D8B")
        self.difficulty_button.hover_color = UIColor.from_hex("#78909C")
        self.difficulty_button.text_color = UIColor.white()
        self.add_child(self.difficulty_button)
        
        # Graphics quality setting
        self.graphics_label = UrsinaUIText("Graphics:", UIColor.white())
        self.graphics_label.position = UIVector2(25, 60)
        self.graphics_label.font_size = 16
        self.add_child(self.graphics_label)
        
        self.graphics_button = UrsinaUIButton(self.settings.graphics_quality, self._cycle_graphics)
        self.graphics_button.position = UIVector2(55, 58)
        self.graphics_button.size = UIVector2(20, 6)
        self.graphics_button.background_color = UIColor.from_hex("#607D8B")
        self.graphics_button.hover_color = UIColor.from_hex("#78909C")
        self.graphics_button.text_color = UIColor.white()
        self.add_child(self.graphics_button)
        
        # Volume labels (simplified - would normally have sliders)
        self.music_label = UrsinaUIText(f"Music Volume: {int(self.settings.music_volume * 100)}%", UIColor.white())
        self.music_label.position = UIVector2(25, 50)
        self.music_label.font_size = 14
        self.add_child(self.music_label)
        
        self.sfx_label = UrsinaUIText(f"SFX Volume: {int(self.settings.sfx_volume * 100)}%", UIColor.white())
        self.sfx_label.position = UIVector2(25, 45)
        self.sfx_label.font_size = 14
        self.add_child(self.sfx_label)
        
        # Control buttons
        self.apply_button = UrsinaUIButton("APPLY", self._handle_apply)
        self.apply_button.position = UIVector2(35, 30)
        self.apply_button.size = UIVector2(15, 6)
        self.apply_button.background_color = UIColor.from_hex("#4CAF50")
        self.apply_button.hover_color = UIColor.from_hex("#66BB6A")
        self.apply_button.text_color = UIColor.white()
        self.add_child(self.apply_button)
        
        self.back_button = UrsinaUIButton("BACK", self._handle_back)
        self.back_button.position = UIVector2(55, 30)
        self.back_button.size = UIVector2(15, 6)
        self.back_button.background_color = UIColor.from_hex("#757575")
        self.back_button.hover_color = UIColor.from_hex("#9E9E9E")
        self.back_button.text_color = UIColor.white()
        self.add_child(self.back_button)
    
    def _cycle_difficulty(self, button):
        """Cycle through difficulty options"""
        current_index = self.difficulty_options.index(self.settings.difficulty)
        next_index = (current_index + 1) % len(self.difficulty_options)
        self.settings.difficulty = self.difficulty_options[next_index]
        self.difficulty_button.set_text(self.settings.difficulty)
    
    def _cycle_graphics(self, button):
        """Cycle through graphics quality options"""
        current_index = self.graphics_options.index(self.settings.graphics_quality)
        next_index = (current_index + 1) % len(self.graphics_options)
        self.settings.graphics_quality = self.graphics_options[next_index]
        self.graphics_button.set_text(self.settings.graphics_quality)
    
    def _handle_apply(self, button):
        """Handle Apply button click"""
        print(f"Settings applied: {self.settings.to_dict()}")
        # Here you would save settings to file
    
    def _handle_back(self, button):
        """Handle Back button click"""
        if self.on_back:
            self.on_back()

class MainMenuManager:
    """Manager class for main menu system"""
    
    def __init__(self, ui_manager: IUIManager):
        self.ui_manager = ui_manager
        self.start_screen: Optional[StartScreen] = None
        self.settings_screen: Optional[SettingsScreen] = None
        self.current_screen: Optional[IUIScreen] = None
        
        # Game settings
        self.settings = GameSettings()
        
        # Initialize start screen
        self._create_start_screen()
    
    def _create_start_screen(self):
        """Create and configure start screen"""
        self.start_screen = StartScreen(
            on_new_game=self._handle_new_game,
            on_load_game=self._handle_load_game,
            on_practice_battle=self._handle_practice_battle,
            on_settings=self._handle_settings,
            on_exit=self._handle_exit
        )
        self.current_screen = self.start_screen
    
    def _handle_new_game(self):
        """Handle new game request"""
        print("Starting new game...")
        # Here you would transition to game creation/character setup
        
    def _handle_load_game(self):
        """Handle load game request"""
        print("Loading saved game...")
        # Here you would show load game dialog or transition to saved game
    
    def _handle_practice_battle(self):
        """Handle practice battle request"""
        print("Starting practice battle...")
        # Here you would transition to a practice battle mode
        
    def _handle_settings(self, settings: GameSettings):
        """Handle settings request"""
        print("Opening settings...")
        self.settings_screen = SettingsScreen(settings, self._handle_settings_back)
        self._switch_to_screen(self.settings_screen)
    
    def _handle_settings_back(self):
        """Handle back from settings"""
        print("Returning to main menu...")
        self._switch_to_screen(self.start_screen)
    
    def _handle_exit(self):
        """Handle exit request"""
        print("Exiting game...")
        # Here you would perform cleanup and exit
        
    def _switch_to_screen(self, screen: IUIScreen):
        """Switch to a different screen"""
        if self.current_screen:
            self.current_screen.hide()
        
        self.current_screen = screen
        if screen:
            screen.show()
    
    def show_start_screen(self):
        """Show the start screen"""
        self._switch_to_screen(self.start_screen)
    
    def update(self, delta_time: float):
        """Update current screen"""
        if self.current_screen:
            self.current_screen.update(delta_time)
    
    def render(self):
        """Render current screen"""
        if self.current_screen:
            self.current_screen.render()
    
    def cleanup(self):
        """Cleanup menu system"""
        if self.start_screen:
            self.start_screen.destroy()
        if self.settings_screen:
            self.settings_screen.destroy()