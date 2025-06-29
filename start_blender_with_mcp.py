#!/usr/bin/env python3
"""
Script to start Blender with the MCP addon pre-installed
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path

def get_blender_addons_path():
    """Get the Blender addons directory path"""
    # For Blender 4.x, the addons are typically in:
    # ~/.config/blender/4.x/scripts/addons/
    
    home = Path.home()
    config_path = home / ".config" / "blender"
    
    # Find the most recent Blender version directory
    if config_path.exists():
        blender_versions = [d for d in config_path.iterdir() if d.is_dir() and d.name.replace('.', '').isdigit()]
        if blender_versions:
            latest_version = max(blender_versions, key=lambda x: tuple(map(int, x.name.split('.'))))
            addons_path = latest_version / "scripts" / "addons"
            return addons_path
    
    return None

def install_addon():
    """Install the Blender MCP addon"""
    addon_source = Path("addon_blender_mcp.py")
    if not addon_source.exists():
        print("Error: addon_blender_mcp.py not found!")
        return False
    
    addons_path = get_blender_addons_path()
    if addons_path is None:
        print("Warning: Could not find Blender addons directory")
        print("You'll need to manually install the addon through Blender's preferences")
        return False
    
    # Create addons directory if it doesn't exist
    addons_path.mkdir(parents=True, exist_ok=True)
    
    # Copy the addon
    addon_dest = addons_path / "blender_mcp_addon.py"
    shutil.copy2(addon_source, addon_dest)
    print(f"Addon installed to: {addon_dest}")
    return True

def start_blender():
    """Start Blender"""
    print("Starting Blender...")
    print("\nTo use the MCP integration:")
    print("1. Go to Edit > Preferences > Add-ons")
    print("2. Search for 'Blender MCP' or enable 'Interface: Blender MCP'")
    print("3. In the 3D viewport, press N to open the sidebar")
    print("4. Click on the 'BlenderMCP' tab")
    print("5. Click 'Connect to Claude'")
    print("\nThen start the MCP server with: uvx blender-mcp")
    
    try:
        subprocess.run(["/snap/bin/blender"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Blender: {e}")
        return False
    except KeyboardInterrupt:
        print("\nBlender closed by user")
        return True
    
    return True

def main():
    print("Blender MCP Setup Script")
    print("========================")
    
    # Install addon
    if install_addon():
        print("✓ Addon installation completed")
    else:
        print("⚠ Addon installation failed - manual installation required")
    
    print("\nStarting Blender...")
    start_blender()

if __name__ == "__main__":
    main()