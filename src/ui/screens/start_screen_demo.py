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
        """Create the start screen UI using WindowPanel"""
        # Title text
        self.title_text = Text(
            'APEX TACTICS',
            color=color.white,
            scale=2
        )
        
        # Subtitle text
        self.subtitle_text = Text(
            'Tactical RPG Engine - Phase 4.5 Demo',
            color=color.light_gray
        )
        
        # Description text
        self.description_text = Text(
            'A comprehensive tactical RPG system with portable UI framework',
            color=color.gray
        )
        
        # Create menu buttons
        self.new_game_btn = Button(
            text='NEW GAME',
            color=color.green,
            scale=(2, 1)
        )
        self.new_game_btn.on_click = self._handle_new_game
        
        self.load_game_btn = Button(
            text='LOAD GAME', 
            color=color.blue,
            scale=(2, 1)
        )
        self.load_game_btn.on_click = self._handle_load_game
        
        self.practice_battle_btn = Button(
            text='PRACTICE BATTLE',
            color=color.violet,
            scale=(2, 1)
        )
        self.practice_battle_btn.on_click = self._handle_practice_battle
        
        self.settings_btn = Button(
            text='SETTINGS',
            color=color.orange,
            scale=(2, 1)
        )
        self.settings_btn.on_click = self._handle_settings
        
        self.exit_btn = Button(
            text='EXIT',
            color=color.red,
            scale=(2, 1)
        )
        self.exit_btn.on_click = self._handle_exit
        
        # Version info
        self.version_text = Text(
            'Version 1.0.0 - Phase 4.5',
            color=color.dark_gray,
            scale=0.8
        )
        
        # Create main window panel with all content
        self.panel = WindowPanel(
            title='Apex Tactics - Main Menu',
            content=(
                self.title_text,
                self.subtitle_text,
                self.description_text,
                Text(''),  # Spacer
                Text('Select an option:'),
                self.new_game_btn,
                self.load_game_btn,
                self.practice_battle_btn,
                self.settings_btn,
                self.exit_btn,
                Text(''),  # Spacer
                self.version_text
            ),
            popup=False
        )
        
        # Center the panel on screen
        self.panel.x = 0
        self.panel.y = 0
        
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
        """Create settings UI"""
        # Settings info
        self.settings_title = Text(
            'Game Settings',
            color=color.white,
            scale=1.5
        )
        
        # Difficulty setting
        self.difficulty_text = Text(f'Difficulty: {self.current_difficulty}')
        self.difficulty_btn = Button(
            text='Change Difficulty',
            color=color.azure,
            scale=(1.5, 1)
        )
        self.difficulty_btn.on_click = self._cycle_difficulty
        
        # Graphics setting
        self.graphics_text = Text(f'Graphics Quality: {self.current_graphics}')
        self.graphics_btn = Button(
            text='Change Graphics',
            color=color.azure,
            scale=(1.5, 1)
        )
        self.graphics_btn.on_click = self._cycle_graphics
        
        # Audio settings (placeholder)
        self.audio_text = Text('Audio: Music 80%, SFX 90%')
        
        # Control buttons
        self.apply_btn = Button(
            text='APPLY SETTINGS',
            color=color.green,
            scale=(1.5, 1)
        )
        self.apply_btn.on_click = self._apply_settings
        
        self.back_btn = Button(
            text='BACK TO MENU',
            color=color.red,
            scale=(1.5, 1)
        )
        self.back_btn.on_click = self._handle_back
        
        # Create settings panel
        self.panel = WindowPanel(
            title='Settings Configuration',
            content=(
                self.settings_title,
                Text(''),  # Spacer
                self.difficulty_text,
                self.difficulty_btn,
                Text(''),  # Spacer
                self.graphics_text,
                self.graphics_btn,
                Text(''),  # Spacer
                self.audio_text,
                Text(''),  # Spacer
                self.apply_btn,
                self.back_btn
            ),
            popup=False
        )
        
        # Center the panel
        self.panel.x = 0
        self.panel.y = 0
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
        """Create a simple background"""
        # Background plane
        self.background = Entity(
            model='cube',
            color=color.dark_gray,
            scale=(20, 10, 1),
            position=(0, 0, 5)
        )
        
        # Add some lighting
        DirectionalLight(y=2, z=-1, rotation=(45, -45, 0))
        AmbientLight(color=color.rgba(100, 100, 100, 100))
    
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