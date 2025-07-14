#!/usr/bin/env python3
"""
Comprehensive dependency analyzer for Apex Tactics project.
Builds dependency trees from all entry points.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import defaultdict, deque

class DependencyAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.all_files = set()
        self.dependencies = defaultdict(set)  # file -> set of files it imports
        self.reverse_dependencies = defaultdict(set)  # file -> set of files that import it
        self.entry_points = set()
        self.scan_project()
    
    def scan_project(self):
        """Scan all Python files in the project."""
        for py_file in self.project_root.rglob("*.py"):
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
            print(f"Error parsing {file_path}: {e}")
        
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
        """Find all entry points (files with __main__ blocks)."""
        entry_points = set()
        
        # Known entry points
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
        
        # Get all dependencies from all entry points
        for entry_point in self.entry_points:
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
    
    def find_dynamic_imports(self):
        """Find potential dynamic imports that might not be caught."""
        dynamic_patterns = [
            r'importlib\.import_module',
            r'__import__',
            r'exec\s*\(',
            r'eval\s*\(',
            r'getattr.*import',
        ]
        
        dynamic_files = set()
        
        for file_str in self.all_files:
            file_path = self.project_root / file_str
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for pattern in dynamic_patterns:
                        if re.search(pattern, content):
                            dynamic_files.add(file_str)
                            break
            except:
                continue
        
        return dynamic_files
    
    def generate_report(self):
        """Generate comprehensive dependency report."""
        self.build_dependency_graph()
        entry_points = self.find_entry_points()
        usage = self.analyze_usage()
        dynamic_files = self.find_dynamic_imports()
        
        report = []
        report.append("=" * 80)
        report.append("APEX TACTICS DEPENDENCY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("SUMMARY:")
        report.append(f"  Total Python files: {usage['total']}")
        report.append(f"  Used files: {usage['used_count']} ({usage['used_count']/usage['total']*100:.1f}%)")
        report.append(f"  Unused files: {usage['unused_count']} ({usage['unused_count']/usage['total']*100:.1f}%)")
        report.append(f"  Entry points found: {len(entry_points)}")
        report.append(f"  Files with dynamic imports: {len(dynamic_files)}")
        report.append("")
        
        # Entry points
        report.append("ENTRY POINTS:")
        for entry in sorted(entry_points):
            deps_count = len(self.get_all_dependencies(entry))
            report.append(f"  {entry} -> {deps_count} dependencies")
        report.append("")
        
        # Top-level dependencies from main entry points
        main_entries = [
            'apex-tactics.py',
            'apex-tactics-websocket-client.py', 
            'apex-tactics-enhanced.py',
            'run_game_engine.py'
        ]
        
        for entry in main_entries:
            if entry in self.all_files:
                report.append(f"DIRECT IMPORTS FOR {entry}:")
                direct_deps = sorted(self.dependencies.get(entry, set()))
                for dep in direct_deps:
                    report.append(f"  {dep}")
                report.append("")
        
        # Dynamic import candidates
        if dynamic_files:
            report.append("FILES WITH DYNAMIC IMPORTS (UNCERTAIN):")
            for file in sorted(dynamic_files):
                report.append(f"  {file}")
            report.append("")
        
        # Unused files (candidates for removal)
        if usage['unused']:
            report.append("UNUSED FILES (REMOVAL CANDIDATES):")
            unused_by_category = defaultdict(list)
            
            for file in usage['unused']:
                if '/test' in file or file.startswith('test_'):
                    category = 'tests'
                elif '/scripts/' in file:
                    category = 'scripts'
                elif '/demos/' in file:
                    category = 'demos'
                elif '/src/' in file:
                    category = 'source'
                else:
                    category = 'root'
                
                unused_by_category[category].append(file)
            
            for category, files in sorted(unused_by_category.items()):
                report.append(f"  {category.upper()} ({len(files)} files):")
                for file in sorted(files):
                    report.append(f"    {file}")
                report.append("")
        
        # Most connected files
        report.append("MOST IMPORTED FILES (TOP 20):")
        import_counts = [(len(importers), file) for file, importers in self.reverse_dependencies.items()]
        import_counts.sort(reverse=True)
        
        for count, file in import_counts[:20]:
            if count > 0:
                report.append(f"  {file}: imported by {count} files")
        
        return '\n'.join(report)

if __name__ == "__main__":
    analyzer = DependencyAnalyzer("/home/junior/src/apex-tactics")
    report = analyzer.generate_report()
    print(report)
    
    # Save report to file
    with open("/home/junior/src/apex-tactics/dependency_report.txt", "w") as f:
        f.write(report)
    
    print("\nReport saved to dependency_report.txt")