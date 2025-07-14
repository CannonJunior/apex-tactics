#!/usr/bin/env python3
"""
Project-focused dependency analyzer for Apex Tactics.
Excludes virtual environment files.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import defaultdict, deque

class ProjectDependencyAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.all_files = set()
        self.dependencies = defaultdict(set)
        self.reverse_dependencies = defaultdict(set)
        self.entry_points = set()
        self.scan_project()
    
    def scan_project(self):
        """Scan only project Python files (exclude .venv)."""
        for py_file in self.project_root.rglob("*.py"):
            # Skip virtual environment
            if ".venv" in py_file.parts:
                continue
            
            relative_path = py_file.relative_to(self.project_root)
            self.all_files.add(str(relative_path))
    
    def parse_imports(self, file_path: Path) -> Set[str]:
        """Parse imports from a Python file."""
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all import statements
            import_patterns = [
                r'^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import\s+',
                r'^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
            ]
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                
                for pattern in import_patterns:
                    match = re.match(pattern, line)
                    if match:
                        module_name = match.group(1)
                        
                        # Convert module path to file path
                        module_parts = module_name.split('.')
                        
                        # Try different possible paths
                        possible_paths = [
                            '/'.join(module_parts) + '.py',
                            'src/' + '/'.join(module_parts) + '.py',
                            '/'.join(module_parts) + '/__init__.py',
                            'src/' + '/'.join(module_parts) + '/__init__.py',
                        ]
                        
                        for possible_path in possible_paths:
                            if possible_path in self.all_files:
                                imports.add(possible_path)
                                break
        
        except Exception as e:
            # Skip files that can't be read
            pass
        
        return imports
    
    def build_dependency_graph(self):
        """Build the complete dependency graph."""
        for file_str in self.all_files:
            file_path = self.project_root / file_str
            if file_path.exists():
                imports = self.parse_imports(file_path)
                self.dependencies[file_str] = imports
                
                # Build reverse dependencies
                for imported_file in imports:
                    self.reverse_dependencies[imported_file].add(file_str)
    
    def find_entry_points(self):
        """Find all entry points."""
        entry_points = set()
        
        # Known main entry points
        known_entries = [
            'apex-tactics.py',
            'apex-tactics-websocket-client.py', 
            'apex-tactics-enhanced.py',
            'run_game_engine.py',
            'main.py'
        ]
        
        for entry in known_entries:
            if entry in self.all_files:
                entry_points.add(entry)
        
        # Find files with __main__ blocks
        for file_str in self.all_files:
            file_path = self.project_root / file_str
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'if __name__ == "__main__"' in content:
                        entry_points.add(file_str)
            except:
                continue
        
        self.entry_points = entry_points
        return entry_points
    
    def get_all_dependencies(self, start_file: str) -> Set[str]:
        """Get all transitive dependencies of a file."""
        visited = set()
        queue = deque([start_file])
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            
            visited.add(current)
            
            # Add direct dependencies
            for dep in self.dependencies.get(current, set()):
                if dep not in visited:
                    queue.append(dep)
        
        return visited
    
    def analyze_usage(self):
        """Analyze which files are used by entry points."""
        used_files = set()
        
        # Get all dependencies from main entry points
        main_entries = [
            'apex-tactics.py',
            'apex-tactics-websocket-client.py', 
            'apex-tactics-enhanced.py',
            'run_game_engine.py'
        ]
        
        for entry_point in main_entries:
            if entry_point in self.all_files:
                deps = self.get_all_dependencies(entry_point)
                used_files.update(deps)
        
        # Find unused files
        unused_files = self.all_files - used_files
        
        return {
            'used': used_files,
            'unused': unused_files,
            'total': len(self.all_files),
            'used_count': len(used_files),
            'unused_count': len(unused_files)
        }
    
    def categorize_files(self, files: Set[str]) -> Dict[str, List[str]]:
        """Categorize files by type/location."""
        categories = defaultdict(list)
        
        for file in files:
            if '/test' in file or file.startswith('test_'):
                categories['tests'].append(file)
            elif '/scripts/' in file:
                categories['scripts'].append(file)
            elif '/demos/' in file:
                categories['demos'].append(file)
            elif file.startswith('src/'):
                if '/ui/' in file:
                    categories['ui'].append(file)
                elif '/game/' in file:
                    categories['game'].append(file)
                elif '/core/' in file:
                    categories['core'].append(file)
                elif '/ai/' in file:
                    categories['ai'].append(file)
                elif '/engine/' in file:
                    categories['engine'].append(file)
                elif '/components/' in file:
                    categories['components'].append(file)
                else:
                    categories['src_other'].append(file)
            else:
                categories['root'].append(file)
        
        return categories
    
    def generate_report(self):
        """Generate comprehensive dependency report."""
        self.build_dependency_graph()
        entry_points = self.find_entry_points()
        usage = self.analyze_usage()
        
        report = []
        report.append("=" * 80)
        report.append("APEX TACTICS PROJECT DEPENDENCY ANALYSIS")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("SUMMARY:")
        report.append(f"  Total project files: {usage['total']}")
        report.append(f"  Used files: {usage['used_count']} ({usage['used_count']/usage['total']*100:.1f}%)")
        report.append(f"  Unused files: {usage['unused_count']} ({usage['unused_count']/usage['total']*100:.1f}%)")
        report.append("")
        
        # Main entry points dependency trees
        main_entries = ['apex-tactics.py', 'apex-tactics-websocket-client.py', 'apex-tactics-enhanced.py', 'run_game_engine.py']
        
        for entry in main_entries:
            if entry in self.all_files:
                deps = self.get_all_dependencies(entry)
                report.append(f"DEPENDENCY TREE FOR {entry}:")
                report.append(f"  Total dependencies: {len(deps)}")
                
                # Direct imports
                direct_deps = sorted(self.dependencies.get(entry, set()))
                report.append(f"  Direct imports ({len(direct_deps)}):")
                for dep in direct_deps:
                    report.append(f"    {dep}")
                report.append("")
        
        # Categorize unused files
        unused_by_category = self.categorize_files(usage['unused'])
        
        if unused_by_category:
            report.append("UNUSED FILES BY CATEGORY:")
            for category, files in sorted(unused_by_category.items()):
                if files:
                    report.append(f"  {category.upper().replace('_', ' ')} ({len(files)} files):")
                    for file in sorted(files)[:10]:  # Show first 10
                        report.append(f"    {file}")
                    if len(files) > 10:
                        report.append(f"    ... and {len(files)-10} more")
                    report.append("")
        
        # Most imported files
        report.append("MOST IMPORTED PROJECT FILES:")
        import_counts = [(len(importers), file) for file, importers in self.reverse_dependencies.items()]
        import_counts.sort(reverse=True)
        
        for count, file in import_counts[:15]:
            if count > 0:
                report.append(f"  {file}: imported by {count} files")
        
        report.append("")
        
        # Removal candidates
        report.append("HIGH-CONFIDENCE REMOVAL CANDIDATES:")
        safe_categories = ['tests', 'demos', 'scripts']
        
        for category in safe_categories:
            if category in unused_by_category:
                files = unused_by_category[category]
                if files:
                    report.append(f"  {category.upper()} ({len(files)} files)")
        
        # Uncertain files that might be dynamically loaded
        uncertain_patterns = ['loader', 'manager', 'factory', 'registry', 'plugin']
        uncertain_files = []
        
        for file in usage['unused']:
            for pattern in uncertain_patterns:
                if pattern in file.lower():
                    uncertain_files.append(file)
                    break
        
        if uncertain_files:
            report.append("")
            report.append("UNCERTAIN FILES (MAY BE DYNAMICALLY LOADED):")
            for file in sorted(uncertain_files)[:10]:
                report.append(f"  {file}")
        
        return '\n'.join(report)

if __name__ == "__main__":
    analyzer = ProjectDependencyAnalyzer("/home/junior/src/apex-tactics")
    report = analyzer.generate_report()
    print(report)
    
    # Save report to file
    with open("/home/junior/src/apex-tactics/project_dependency_report.txt", "w") as f:
        f.write(report)
    
    print(f"\nReport saved to project_dependency_report.txt")