#!/usr/bin/env uv run
"""
Start Screen Demo

New implementation based on the ControlPanel class from apex-tactics.py.
Uses Ursina's native WindowPanel for proper UI display.

Run with: uv run src/ui/screens/start_screen_demo.py
"""

import sys
import os

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from ursina import *
    from ursina.prefabs.window_panel import WindowPanel
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False
    print("Ursina not available - demo cannot run")
    print("Install with: uv add ursina")

class StartScreen:
    """
    Start screen implementation based on apex-tactics ControlPanel design.
    Uses Ursina's native WindowPanel for consistent UI appearance.
    """
    
    def __init__(self, on_new_game=None, on_load_game=None, on_practice_battle=None, 
                 on_settings=None, on_exit=None):
        self.on_new_game = on_new_game
        self.on_load_game = on_load_game
        self.on_practice_battle = on_practice_battle
        self.on_settings = on_settings
        self.on_exit = on_exit
        
        # Create UI elements
        self._create_ui()
    
    def _create_ui(self):
        """Create the start screen UI using WindowPanel and master UI config"""
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Title configuration from master UI config
            title_config = ui_config.get('ui_screens.start_screen.title', {})
            title_text = title_config.get('text', 'APEX TACTICS')
            title_color = ui_config.get_color('ui_screens.start_screen.title.color', '#FFFFFF')
            title_scale = title_config.get('scale', 2)
            
            # Subtitle configuration from master UI config
            subtitle_config = ui_config.get('ui_screens.start_screen.subtitle', {})
            subtitle_text = subtitle_config.get('text', 'Tactical RPG Engine - Phase 4.5 Demo')
            subtitle_color = ui_config.get_color('ui_screens.start_screen.subtitle.color', '#D3D3D3')
            
            # Description configuration from master UI config
            description_config = ui_config.get('ui_screens.start_screen.description', {})
            description_text = description_config.get('text', 'A comprehensive tactical RPG system with portable UI framework')
            description_color = ui_config.get_color('ui_screens.start_screen.description.color', '#808080')
        except ImportError:
            # Fallback values if master UI config not available
            title_text = 'APEX TACTICS'
            title_color = color.white
            title_scale = 2
            subtitle_text = 'Tactical RPG Engine - Phase 4.5 Demo'
            subtitle_color = color.light_gray
            description_text = 'A comprehensive tactical RPG system with portable UI framework'
            description_color = color.gray
        
        # Title text
        self.title_text = Text(
            title_text,
            color=title_color,
            scale=title_scale
        )
        
        # Subtitle text
        self.subtitle_text = Text(
            subtitle_text,
            color=subtitle_color
        )
        
        # Description text
        self.description_text = Text(
            description_text,
            color=description_color
        )
        
        # Menu buttons configuration from master UI config
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            buttons_config = ui_config.get('ui_screens.start_screen.menu_buttons', {})
            button_scale = buttons_config.get('scale', (2, 1))
            
            # Individual button configurations
            new_game_config = buttons_config.get('new_game', {})
            load_game_config = buttons_config.get('load_game', {})
            practice_battle_config = buttons_config.get('practice_battle', {})
            settings_config = buttons_config.get('settings', {})
            exit_config = buttons_config.get('exit', {})
        except ImportError:
            # Fallback values
            button_scale = (2, 1)
            new_game_config = {'text': 'NEW GAME', 'color': '#00FF00'}
            load_game_config = {'text': 'LOAD GAME', 'color': '#0000FF'}
            practice_battle_config = {'text': 'PRACTICE BATTLE', 'color': '#8A2BE2'}
            settings_config = {'text': 'SETTINGS', 'color': '#FFA500'}
            exit_config = {'text': 'EXIT', 'color': '#FF0000'}
        
        # Create menu buttons using master UI config
        self.new_game_btn = Button(
            text=new_game_config.get('text', 'NEW GAME'),
            color=ui_config.get_color('ui_screens.start_screen.menu_buttons.new_game.color', '#00FF00') if 'ui_config' in locals() else color.green,
            scale=button_scale
        )
        self.new_game_btn.on_click = self._handle_new_game
        
        self.load_game_btn = Button(
            text=load_game_config.get('text', 'LOAD GAME'),
            color=ui_config.get_color('ui_screens.start_screen.menu_buttons.load_game.color', '#0000FF') if 'ui_config' in locals() else color.blue,
            scale=button_scale
        )
        self.load_game_btn.on_click = self._handle_load_game
        
        self.practice_battle_btn = Button(
            text=practice_battle_config.get('text', 'PRACTICE BATTLE'),
            color=ui_config.get_color('ui_screens.start_screen.menu_buttons.practice_battle.color', '#8A2BE2') if 'ui_config' in locals() else color.violet,
            scale=button_scale
        )
        self.practice_battle_btn.on_click = self._handle_practice_battle
        
        self.settings_btn = Button(
            text=settings_config.get('text', 'SETTINGS'),
            color=ui_config.get_color('ui_screens.start_screen.menu_buttons.settings.color', '#FFA500') if 'ui_config' in locals() else color.orange,
            scale=button_scale
        )
        self.settings_btn.on_click = self._handle_settings
        
        self.exit_btn = Button(
            text=exit_config.get('text', 'EXIT'),
            color=ui_config.get_color('ui_screens.start_screen.menu_buttons.exit.color', '#FF0000') if 'ui_config' in locals() else color.red,
            scale=button_scale
        )
        self.exit_btn.on_click = self._handle_exit
        
        # Version info and panel configuration from master UI config
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Version configuration from master UI config
            version_config = ui_config.get('ui_screens.start_screen.version', {})
            version_text = version_config.get('text', 'Version 1.0.0 - Phase 4.5')
            version_color = ui_config.get_color('ui_screens.start_screen.version.color', '#2F2F2F')
            version_scale = version_config.get('scale', 0.8)
            
            # Panel configuration from master UI config
            panel_config = ui_config.get('ui_screens.start_screen.panel', {})
            panel_title = panel_config.get('title', 'Apex Tactics - Main Menu')
            panel_popup = panel_config.get('popup', False)
            panel_x = panel_config.get('x_position', 0)
            panel_y = panel_config.get('y_position', 0)
            
            # Panel content configuration from master UI config
            content_config = ui_config.get('ui_screens.start_screen.panel.content', {})
            spacer_text = content_config.get('spacer_text', '')
            instruction_text = content_config.get('instruction_text', 'Select an option:')
        except ImportError:
            # Fallback values
            version_text = 'Version 1.0.0 - Phase 4.5'
            version_color = color.dark_gray
            version_scale = 0.8
            panel_title = 'Apex Tactics - Main Menu'
            panel_popup = False
            panel_x = 0
            panel_y = 0
            spacer_text = ''
            instruction_text = 'Select an option:'
        
        # Version info
        self.version_text = Text(
            version_text,
            color=version_color,
            scale=version_scale
        )
        
        # Create main window panel with all content
        self.panel = WindowPanel(
            title=panel_title,
            content=(
                self.title_text,
                self.subtitle_text,
                self.description_text,
                Text(spacer_text),  # Spacer
                Text(instruction_text),
                self.new_game_btn,
                self.load_game_btn,
                self.practice_battle_btn,
                self.settings_btn,
                self.exit_btn,
                Text(spacer_text),  # Spacer
                self.version_text
            ),
            popup=panel_popup
        )
        
        # Center the panel on screen
        self.panel.x = panel_x
        self.panel.y = panel_y
        
        # Layout the content within the panel
        self.panel.layout()
    
    def _handle_new_game(self):
        """Handle New Game button click"""
        print("NEW GAME selected")
        print("Starting character creation and campaign setup...")
        if self.on_new_game:
            self.on_new_game()
    
    def _handle_load_game(self):
        """Handle Load Game button click"""
        print("LOAD GAME selected")
        print("Opening saved game selection...")
        if self.on_load_game:
            self.on_load_game()
    
    def _handle_practice_battle(self):
        """Handle Practice Battle button click"""
        print("PRACTICE BATTLE selected")
        print("Loading tutorial combat scenario...")
        if self.on_practice_battle:
            self.on_practice_battle()
    
    def _handle_settings(self):
        """Handle Settings button click"""
        print("SETTINGS selected")
        print("Opening game configuration...")
        if self.on_settings:
            self.on_settings()
    
    def _handle_exit(self):
        """Handle Exit button click"""
        print("EXIT selected")
        print("Closing application...")
        if self.on_exit:
            self.on_exit()
        else:
            application.quit()
    
    def destroy(self):
        """Clean up the start screen"""
        if hasattr(self, 'panel') and self.panel:
            destroy(self.panel)

class SettingsScreen:
    """Settings screen using WindowPanel design"""
    
    def __init__(self, on_back=None):
        self.on_back = on_back
        self.current_difficulty = "Normal"
        self.current_graphics = "High"
        self._create_ui()
    
    def _create_ui(self):
        """Create settings UI using master UI config"""
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Settings title configuration from master UI config
            settings_config = ui_config.get('ui_screens.settings_screen', {})
            title_config = settings_config.get('title', {})
            title_text = title_config.get('text', 'Game Settings')
            title_color = ui_config.get_color('ui_screens.settings_screen.title.color', '#FFFFFF')
            title_scale = title_config.get('scale', 1.5)
        except ImportError:
            # Fallback values
            title_text = 'Game Settings'
            title_color = color.white
            title_scale = 1.5
        
        # Settings info
        self.settings_title = Text(
            title_text,
            color=title_color,
            scale=title_scale
        )
        
        # Settings options configuration from master UI config
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Settings options configuration
            options_config = ui_config.get('ui_screens.settings_screen.options', {})
            button_scale = options_config.get('button_scale', (1.5, 1))
            button_color = ui_config.get_color('ui_screens.settings_screen.options.button_color', '#F0FFFF')
            
            # Option text templates
            difficulty_template = options_config.get('difficulty_template', 'Difficulty: {value}')
            graphics_template = options_config.get('graphics_template', 'Graphics Quality: {value}')
            audio_text = options_config.get('audio_text', 'Audio: Music 80%, SFX 90%')
            
            # Button text configuration
            difficulty_btn_text = options_config.get('difficulty_button_text', 'Change Difficulty')
            graphics_btn_text = options_config.get('graphics_button_text', 'Change Graphics')
        except ImportError:
            # Fallback values
            button_scale = (1.5, 1)
            button_color = color.azure
            difficulty_template = 'Difficulty: {value}'
            graphics_template = 'Graphics Quality: {value}'
            audio_text = 'Audio: Music 80%, SFX 90%'
            difficulty_btn_text = 'Change Difficulty'
            graphics_btn_text = 'Change Graphics'
        
        # Difficulty setting
        self.difficulty_text = Text(difficulty_template.format(value=self.current_difficulty))
        self.difficulty_btn = Button(
            text=difficulty_btn_text,
            color=button_color,
            scale=button_scale
        )
        self.difficulty_btn.on_click = self._cycle_difficulty
        
        # Graphics setting
        self.graphics_text = Text(graphics_template.format(value=self.current_graphics))
        self.graphics_btn = Button(
            text=graphics_btn_text,
            color=button_color,
            scale=button_scale
        )
        self.graphics_btn.on_click = self._cycle_graphics
        
        # Audio settings (placeholder)
        self.audio_text = Text(audio_text)
        
        # Control buttons configuration from master UI config
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Control buttons configuration
            controls_config = ui_config.get('ui_screens.settings_screen.controls', {})
            control_button_scale = controls_config.get('button_scale', (1.5, 1))
            
            apply_config = controls_config.get('apply_button', {})
            apply_text = apply_config.get('text', 'APPLY SETTINGS')
            apply_color = ui_config.get_color('ui_screens.settings_screen.controls.apply_button.color', '#00FF00')
            
            back_config = controls_config.get('back_button', {})
            back_text = back_config.get('text', 'BACK TO MENU')
            back_color = ui_config.get_color('ui_screens.settings_screen.controls.back_button.color', '#FF0000')
            
            # Panel configuration
            panel_config = ui_config.get('ui_screens.settings_screen.panel', {})
            panel_title = panel_config.get('title', 'Settings Configuration')
            panel_popup = panel_config.get('popup', False)
            panel_x = panel_config.get('x_position', 0)
            panel_y = panel_config.get('y_position', 0)
            spacer_text = panel_config.get('spacer_text', '')
        except ImportError:
            # Fallback values
            control_button_scale = (1.5, 1)
            apply_text = 'APPLY SETTINGS'
            apply_color = color.green
            back_text = 'BACK TO MENU'
            back_color = color.red
            panel_title = 'Settings Configuration'
            panel_popup = False
            panel_x = 0
            panel_y = 0
            spacer_text = ''
        
        # Control buttons
        self.apply_btn = Button(
            text=apply_text,
            color=apply_color,
            scale=control_button_scale
        )
        self.apply_btn.on_click = self._apply_settings
        
        self.back_btn = Button(
            text=back_text,
            color=back_color,
            scale=control_button_scale
        )
        self.back_btn.on_click = self._handle_back
        
        # Create settings panel
        self.panel = WindowPanel(
            title=panel_title,
            content=(
                self.settings_title,
                Text(spacer_text),  # Spacer
                self.difficulty_text,
                self.difficulty_btn,
                Text(spacer_text),  # Spacer
                self.graphics_text,
                self.graphics_btn,
                Text(spacer_text),  # Spacer
                self.audio_text,
                Text(spacer_text),  # Spacer
                self.apply_btn,
                self.back_btn
            ),
            popup=panel_popup
        )
        
        # Center the panel
        self.panel.x = panel_x
        self.panel.y = panel_y
        self.panel.layout()
    
    def _cycle_difficulty(self):
        """Cycle through difficulty options"""
        difficulties = ["Easy", "Normal", "Hard", "Expert"]
        current_index = difficulties.index(self.current_difficulty)
        self.current_difficulty = difficulties[(current_index + 1) % len(difficulties)]
        self.difficulty_text.text = f'Difficulty: {self.current_difficulty}'
        self.panel.layout()
    
    def _cycle_graphics(self):
        """Cycle through graphics options"""
        graphics_options = ["Low", "Medium", "High", "Ultra"]
        current_index = graphics_options.index(self.current_graphics)
        self.current_graphics = graphics_options[(current_index + 1) % len(graphics_options)]
        self.graphics_text.text = f'Graphics Quality: {self.current_graphics}'
        self.panel.layout()
    
    def _apply_settings(self):
        """Apply current settings"""
        print(f"Settings applied: Difficulty={self.current_difficulty}, Graphics={self.current_graphics}")
    
    def _handle_back(self):
        """Handle back to main menu"""
        if self.on_back:
            self.on_back()
    
    def destroy(self):
        """Clean up settings screen"""
        if hasattr(self, 'panel') and self.panel:
            destroy(self.panel)

class StartScreenDemo:
    """Main demo application"""
    
    def __init__(self):
        if not URSINA_AVAILABLE:
            print("Ursina is required for this demo")
            return
        
        # Initialize Ursina app
        self.app = Ursina()
        
        # Set up window and camera
        window.title = "Apex Tactics - Start Screen Demo"
        window.borderless = False
        window.fullscreen = False
        window.exit_button.visible = False
        
        # Set up camera for UI
        camera.orthographic = False
        camera.position = (0, 0, -5)
        camera.rotation = (0, 0, 0)
        
        # Create background
        self._create_background()
        
        # Screen management
        self.current_screen = None
        self.start_screen = None
        self.settings_screen = None
        self.practice_battle = None
        
        # Show start screen
        self._show_start_screen()
        
        # Set up input handling
        def input(key):
            if key == 'escape':
                self._handle_exit()
        
        # Run the application
        self.app.run()
    
    def _create_background(self):
        """Create a simple background using master UI config"""
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Background configuration from master UI config
            bg_config = ui_config.get('ui_screens.start_screen_demo.background', {})
            bg_model = bg_config.get('model', 'cube')
            bg_color = ui_config.get_color('ui_screens.start_screen_demo.background.color', '#2F2F2F')
            bg_scale = bg_config.get('scale', (20, 10, 1))
            bg_position = bg_config.get('position', (0, 0, 5))
            
            # Lighting configuration from master UI config
            lighting_config = ui_config.get('ui_screens.start_screen_demo.lighting', {})
            directional_config = lighting_config.get('directional_light', {})
            dir_position = directional_config.get('position', (0, 2, -1))
            dir_rotation = directional_config.get('rotation', (45, -45, 0))
            
            ambient_config = lighting_config.get('ambient_light', {})
            ambient_color = ui_config.get_color_rgba('ui_screens.start_screen_demo.lighting.ambient_light.color', (100, 100, 100, 100))
        except ImportError:
            # Fallback values
            bg_model = 'cube'
            bg_color = color.dark_gray
            bg_scale = (20, 10, 1)
            bg_position = (0, 0, 5)
            dir_position = (0, 2, -1)
            dir_rotation = (45, -45, 0)
            ambient_color = (100, 100, 100, 100)
        
        # Background plane
        self.background = Entity(
            model=bg_model,
            color=bg_color,
            scale=bg_scale,
            position=bg_position
        )
        
        # Add some lighting
        DirectionalLight(x=dir_position[0], y=dir_position[1], z=dir_position[2], rotation=dir_rotation)
        AmbientLight(color=color.rgba(*ambient_color))
    
    def _show_start_screen(self):
        """Show the main start screen"""
        if self.current_screen:
            self.current_screen.destroy()
        
        self.start_screen = StartScreen(
            on_new_game=self._handle_new_game,
            on_load_game=self._handle_load_game,
            on_practice_battle=self._handle_practice_battle,
            on_settings=self._handle_settings,
            on_exit=self._handle_exit
        )
        self.current_screen = self.start_screen
    
    def _show_settings_screen(self):
        """Show the settings screen"""
        if self.current_screen:
            self.current_screen.destroy()
        
        self.settings_screen = SettingsScreen(
            on_back=self._show_start_screen
        )
        self.current_screen = self.settings_screen
    
    def _handle_new_game(self):
        """Handle new game request"""
        print("Demo: New Game functionality would be implemented here")
        print("This would transition to character creation and campaign setup")
    
    def _handle_load_game(self):
        """Handle load game request"""
        print("Demo: Load Game functionality would be implemented here")
        print("This would show a file browser for saved games")
    
    def _handle_practice_battle(self):
        """Handle practice battle request"""
        print("Demo: Starting Practice Battle...")
        # Import and start practice battle
        try:
            from src.ui.screens.practice_battle import PracticeBattle
            
            # Hide current screen
            if self.current_screen:
                self.current_screen.destroy()
                self.current_screen = None
            
            # Destroy background to clean up
            if hasattr(self, 'background'):
                destroy(self.background)
            
            # Start practice battle
            self.practice_battle = PracticeBattle(on_exit=self._return_from_battle)
            
            # Override input to go to practice battle
            def battle_input(key):
                if hasattr(self, 'practice_battle') and self.practice_battle:
                    self.practice_battle.handle_input(key)
                else:
                    # Fallback to menu
                    if key == 'escape':
                        self._handle_exit()
            
            # Override update to go to practice battle  
            def battle_update():
                if hasattr(self, 'practice_battle') and self.practice_battle:
                    self.practice_battle.update()
            
            # Replace the app's input and update functions
            self.app._input = battle_input  
            self.app._update = battle_update
            
        except ImportError as e:
            print(f"Could not start practice battle: {e}")
            print("Practice battle requires the practice_battle module")
        except Exception as e:
            print(f"Error starting practice battle: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_settings(self):
        """Handle settings request"""
        print("Demo: Opening settings screen")
        self._show_settings_screen()
    
    def _handle_exit(self):
        """Handle exit request"""
        print("Demo: Exiting application")
        application.quit()
    
    def _return_from_battle(self):
        """Return from practice battle to main menu"""
        print("Demo: Returning from practice battle")
        
        # Clean up battle
        if hasattr(self, 'practice_battle'):
            self.practice_battle = None
            del self.practice_battle
        
        # Restore background
        self._create_background()
        
        # Restore main menu
        self._show_start_screen()
        
        # Restore original input handling
        def menu_input(key):
            if key == 'escape':
                self._handle_exit()
        
        # Restore empty update
        def menu_update():
            pass
        
        # Restore the app's input and update functions
        self.app._input = menu_input
        self.app._update = menu_update
    
    def cleanup(self):
        """Cleanup demo resources"""
        if self.current_screen:
            self.current_screen.destroy()

def run_demo():
    """Run the start screen demo"""
    print("Starting Apex Tactics Start Screen Demo")
    print("=" * 50)
    print("Features:")
    print("- WindowPanel-based UI (like apex-tactics ControlPanel)")
    print("- NEW GAME - Character creation and campaign")
    print("- LOAD GAME - Saved game management")
    print("- PRACTICE BATTLE - Tutorial combat")
    print("- SETTINGS - Game configuration")
    print("- EXIT - Close application")
    print()
    print("Controls:")
    print("- Click buttons to navigate")
    print("- ESC to exit")
    print("- All buttons provide console feedback")
    print()
    
    if not URSINA_AVAILABLE:
        print("Cannot run demo without Ursina. Install with:")
        print("uv add ursina")
        return
    
    try:
        demo = StartScreenDemo()
    except Exception as e:
        print(f"Demo failed to start: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Demo finished")

if __name__ == "__main__":
    run_demo()