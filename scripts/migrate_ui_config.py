#!/usr/bin/env python3
"""
UI Configuration Migration Script

Identifies hardcoded UI values in the codebase and suggests replacements
using the master UI configuration system.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


class UIConfigMigrator:
    """Identifies and suggests migrations for hardcoded UI values."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.hardcoded_patterns = {
            'positions': [
                r'position\s*=\s*\(([^)]+)\)',  # position=(x, y, z)
                r'\.position\s*=\s*\(([^)]+)\)', # .position = (x, y, z)
            ],
            'colors': [
                r'color\.(\w+)',  # color.red, color.blue, etc.
                r'color\s*=\s*color\.(\w+)',  # color=color.red
                r'rgba?\(\s*([^)]+)\)',  # rgb(1,0,0) or rgba(1,0,0,1)
            ],
            'scales': [
                r'scale\s*=\s*([\d.]+)',  # scale=0.06
                r'scale\s*=\s*\(([^)]+)\)',  # scale=(0.3, 0.03)
            ],
            'models': [
                r"model\s*=\s*['\"](\w+)['\"]",  # model='cube'
            ],
            'textures': [
                r"texture\s*=\s*['\"]([^'\"]+)['\"]",  # texture='white_cube'
            ]
        }
        self.suggestions = []
    
    def scan_file(self, file_path: Path) -> List[Dict]:
        """Scan a single file for hardcoded UI values."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except (UnicodeDecodeError, FileNotFoundError):
            return findings
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments and imports
            if line.strip().startswith('#') or 'import' in line:
                continue
                
            for category, patterns in self.hardcoded_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        findings.append({
                            'file': str(file_path),
                            'line': line_num,
                            'category': category,
                            'value': match.group(0),
                            'extracted': match.group(1) if match.groups() else match.group(0),
                            'line_content': line.strip(),
                            'suggestion': self._generate_suggestion(category, match.group(0))
                        })
        
        return findings
    
    def _generate_suggestion(self, category: str, value: str) -> str:
        """Generate a suggestion for replacing hardcoded value."""
        suggestions = {
            'positions': "ui_config.get_position_tuple('component.position')",
            'colors': "ui_config.get_color('colors.action_types.ComponentType')",
            'scales': "ui_config.get('component.scale', 1.0)",
            'models': "ui_config.get('models_and_textures.default_models.component', 'cube')",
            'textures': "ui_config.get('models_and_textures.default_textures.component', 'white_cube')"
        }
        return suggestions.get(category, "Use master UI config")
    
    def scan_directory(self, directory: Path) -> List[Dict]:
        """Scan directory for Python files with hardcoded UI values."""
        all_findings = []
        
        # Focus on UI-related directories
        ui_directories = [
            'src/ui',
            'src/game/utils/ui',
            'src/game/controllers',
            'src/ui/panels',
            'src/ui/battlefield',
            'src/ui/visual'
        ]
        
        for ui_dir in ui_directories:
            full_path = self.project_root / ui_dir
            if full_path.exists():
                print(f"Scanning {ui_dir}...")
                for py_file in full_path.rglob('*.py'):
                    findings = self.scan_file(py_file)
                    all_findings.extend(findings)
        
        return all_findings
    
    def generate_report(self, findings: List[Dict]) -> str:
        """Generate a migration report."""
        report = [
            "# UI Configuration Migration Report",
            "",
            f"Found {len(findings)} hardcoded UI values that should be migrated to master config.",
            "",
            "## Summary by Category",
            ""
        ]
        
        # Categorize findings
        by_category = {}
        for finding in findings:
            category = finding['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(finding)
        
        for category, items in by_category.items():
            report.append(f"- **{category.title()}**: {len(items)} instances")
        
        report.extend(["", "## Detailed Findings", ""])
        
        # Group by file
        by_file = {}
        for finding in findings:
            file_path = finding['file']
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(finding)
        
        for file_path, file_findings in by_file.items():
            rel_path = Path(file_path).relative_to(self.project_root)
            report.append(f"### {rel_path}")
            report.append("")
            
            for finding in file_findings:
                report.append(f"**Line {finding['line']} ({finding['category']})**")
                report.append(f"```python")
                report.append(f"# Current (hardcoded)")
                report.append(f"{finding['line_content']}")
                report.append(f"")
                report.append(f"# Suggested replacement")
                report.append(f"# {finding['suggestion']}")
                report.append(f"```")
                report.append("")
        
        return "\n".join(report)
    
    def generate_config_additions(self, findings: List[Dict]) -> str:
        """Generate suggested additions to master UI config."""
        additions = [
            "# Suggested additions to master_ui_config.json",
            "",
            "Based on the scan, consider adding these sections to your master config:",
            ""
        ]
        
        # Extract common patterns
        position_values = []
        color_values = []
        scale_values = []
        
        for finding in findings:
            if finding['category'] == 'positions':
                position_values.append(finding['extracted'])
            elif finding['category'] == 'colors':
                color_values.append(finding['extracted'])
            elif finding['category'] == 'scales':
                scale_values.append(finding['extracted'])
        
        if position_values:
            additions.extend([
                "## Common Positions Found",
                "```json",
                '"common_positions": {'
            ])
            for i, pos in enumerate(set(position_values[:5])):  # Show top 5
                additions.append(f'  "position_{i+1}": {{"x": ?, "y": ?, "z": ?}}, // From: {pos}')
            additions.extend(["}```", ""])
        
        if color_values:
            additions.extend([
                "## Common Colors Found", 
                "```json",
                '"additional_colors": {'
            ])
            for color in set(color_values[:5]):
                additions.append(f'  "{color}": "#??????", // color.{color}')
            additions.extend(["}```", ""])
        
        return "\n".join(additions)


def main():
    """Run the UI configuration migration scanner."""
    project_root = Path(__file__).parent.parent
    
    print("🔍 Scanning for hardcoded UI values...")
    migrator = UIConfigMigrator(str(project_root))
    findings = migrator.scan_directory(project_root)
    
    print(f"Found {len(findings)} hardcoded UI values")
    
    if findings:
        # Generate and save report
        report = migrator.generate_report(findings)
        report_path = project_root / "ui_migration_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Migration report saved to: {report_path}")
        
        # Generate config suggestions
        config_suggestions = migrator.generate_config_additions(findings)
        suggestions_path = project_root / "ui_config_suggestions.md"
        
        with open(suggestions_path, 'w', encoding='utf-8') as f:
            f.write(config_suggestions)
        
        print(f"💡 Config suggestions saved to: {suggestions_path}")
        
        # Show summary
        print("\n📊 Summary by category:")
        by_category = {}
        for finding in findings:
            category = finding['category']
            by_category[category] = by_category.get(category, 0) + 1
        
        for category, count in sorted(by_category.items()):
            print(f"  {category.title()}: {count} instances")
        
        print(f"\n🎯 Next steps:")
        print(f"1. Review the migration report: {report_path}")
        print(f"2. Add missing config to master_ui_config.json")
        print(f"3. Update code to use ui_config_manager")
        print(f"4. Test UI positioning and appearance")
        
    else:
        print("✅ No hardcoded UI values found!")


if __name__ == "__main__":
    main()