#!/usr/bin/env python3
"""
Script to automatically refactor service __init__ methods for IoC/DI support.

Analyzes service files and moves service instantiation out of constructors
by adding optional dependency injection parameters.
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple, Dict, Set


class ServiceRefactorAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze service instantiations in __init__ methods."""

    def __init__(self):
        self.service_dependencies: Dict[str, List[Dict]] = {}
        self.current_class = None
        self.in_init = False

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions."""
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions."""
        if node.name == "__init__" and self.current_class:
            self.in_init = True
            # Extract existing parameters
            existing_params = [arg.arg for arg in node.args.args[1:]]  # Skip 'self'

            # Analyze service instantiations
            dependencies = []
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Attribute):
                            if isinstance(target.value, ast.Name) and target.value.id == 'self':
                                attr_name = target.attr

                                # Check if it's a service instantiation
                                if isinstance(stmt.value, ast.Call):
                                    if isinstance(stmt.value.func, ast.Name):
                                        service_class = stmt.value.func.id

                                        # Check if it's a service (ends with Service or looks like one)
                                        if 'Service' in service_class or 'Serializer' in service_class:
                                            # Extract arguments
                                            args = []
                                            for arg in stmt.value.args:
                                                if isinstance(arg, ast.Constant):
                                                    args.append(repr(arg.value))
                                                elif isinstance(arg, ast.Name):
                                                    args.append(arg.id)

                                            dependencies.append({
                                                'attribute': attr_name,
                                                'class': service_class,
                                                'args': args,
                                                'param_name': attr_name.replace('_', '_') if not attr_name.startswith('_') else attr_name[1:]
                                            })

            if dependencies:
                self.service_dependencies[self.current_class] = {
                    'dependencies': dependencies,
                    'existing_params': existing_params
                }

            self.in_init = False

        self.generic_visit(node)


def analyze_service_file(file_path: Path) -> Dict:
    """Analyze a service file and return dependency information."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        tree = ast.parse(content)
        analyzer = ServiceRefactorAnalyzer()
        analyzer.visit(tree)

        return {
            'file': file_path,
            'content': content,
            'services': analyzer.service_dependencies
        }
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return None


def generate_refactored_init(
    class_name: str,
    dependencies: List[Dict],
    existing_params: List[str],
    original_content: str
) -> str:
    """Generate refactored __init__ method signature and body."""

    # Find the original __init__ method
    init_pattern = r'def __init__\(self.*?\):'
    match = re.search(init_pattern, original_content)
    if not match:
        return None

    # Extract config_path if it exists
    config_path_param = 'config_path: str = "cli.yml"'
    has_config_path = 'config_path' in existing_params

    # Generate new parameters
    new_params = []
    if has_config_path:
        new_params.append(config_path_param)

    # Add dependency injection parameters
    for dep in dependencies:
        param_name = dep['attribute']
        service_class = dep['class']
        new_params.append(f"{param_name}: Optional[{service_class}] = None")

    # Generate new signature
    if new_params:
        new_signature = f"def __init__(\n        self,\n        {',\n        '.join(new_params)},\n    ):"
    else:
        new_signature = "def __init__(self):"

    # Generate new body for service assignments
    new_assignments = []
    for dep in dependencies:
        attr = dep['attribute']
        service_class = dep['class']

        # Handle different argument patterns
        if dep['args']:
            arg_str = ', '.join(dep['args'])
            new_assignments.append(
                f"        self.{attr} = {attr} or {service_class}({arg_str})"
            )
        else:
            new_assignments.append(
                f"        self.{attr} = {attr} or {service_class}()"
            )

    return {
        'signature': new_signature,
        'assignments': new_assignments
    }


def print_analysis_report(service_files: List[Dict]):
    """Print analysis report of all services."""
    print("\n" + "="*80)
    print("SERVICE IOC REFACTORING ANALYSIS")
    print("="*80 + "\n")

    total_services = 0
    total_dependencies = 0

    for file_info in service_files:
        if not file_info or not file_info.get('services'):
            continue

        print(f"\n📁 {file_info['file']}")
        print("-" * 80)

        for class_name, info in file_info['services'].items():
            total_services += 1
            deps = info['dependencies']
            total_dependencies += len(deps)

            print(f"\n  🔧 {class_name}")
            print(f"     Existing params: {info['existing_params']}")
            print(f"     Dependencies found: {len(deps)}")

            for dep in deps:
                print(f"       - {dep['attribute']}: {dep['class']}({', '.join(dep['args'])})")

    print("\n" + "="*80)
    print(f"SUMMARY: {total_services} services with {total_dependencies} dependencies")
    print("="*80 + "\n")


def generate_refactor_script(service_files: List[Dict], output_file: Path):
    """Generate a shell script to perform the refactoring."""

    print(f"\n📝 Generating refactor instructions to {output_file}...")

    with open(output_file, 'w') as f:
        f.write("#!/usr/bin/env python3\n")
        f.write('"""Auto-generated refactoring script for IoC/DI support."""\n\n')
        f.write("# This script shows what changes need to be made\n")
        f.write("# Review carefully before applying!\n\n")

        for file_info in service_files:
            if not file_info or not file_info.get('services'):
                continue

            f.write(f"\n# File: {file_info['file']}\n")
            f.write("#" + "="*70 + "\n")

            for class_name, info in file_info['services'].items():
                f.write(f"\n# Class: {class_name}\n")
                f.write(f"# Current params: {info['existing_params']}\n")
                f.write(f"# Dependencies: {len(info['dependencies'])}\n\n")

                # Generate refactored version
                refactored = generate_refactored_init(
                    class_name,
                    info['dependencies'],
                    info['existing_params'],
                    file_info['content']
                )

                if refactored:
                    f.write("# NEW SIGNATURE:\n")
                    f.write(f"# {refactored['signature']}\n\n")
                    f.write("# NEW ASSIGNMENTS:\n")
                    for assignment in refactored['assignments']:
                        f.write(f"# {assignment}\n")
                    f.write("\n")

    print(f"✅ Refactor instructions written to {output_file}")


def main():
    """Main entry point."""
    # Find all service files
    service_dirs = [
        Path("../src/xp/services/conbus"),
        Path("../src/xp/services/telegram"),
        Path("../src/xp/services/homekit"),
        Path("../src/xp/services/server"),
    ]

    all_service_files = []

    print("🔍 Scanning for service files...")
    for service_dir in service_dirs:
        if not service_dir.exists():
            continue

        for py_file in service_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            file_info = analyze_service_file(py_file)
            if file_info and file_info.get('services'):
                all_service_files.append(file_info)

    # Print analysis report
    print_analysis_report(all_service_files)

    # Generate refactor script
    output_file = Path("refactor_instructions.py")
    generate_refactor_script(all_service_files, output_file)

    # Print summary with recommendations
    print("\n📋 RECOMMENDATIONS:")
    print("="*80)
    print("1. Review the analysis report above")
    print("2. Check refactor_instructions.py for detailed changes")
    print("3. Services to refactor:")

    for file_info in all_service_files:
        if file_info and file_info.get('services'):
            for class_name in file_info['services'].keys():
                print(f"   - {class_name}")

    print("\n4. Pattern to apply:")
    print("""
    OLD:
        def __init__(self, config_path: str = "cli.yml"):
            self.service_a = ServiceA(config_path)
            self.service_b = ServiceB()

    NEW:
        def __init__(
            self,
            config_path: str = "cli.yml",
            service_a: Optional[ServiceA] = None,
            service_b: Optional[ServiceB] = None,
        ):
            self.service_a = service_a or ServiceA(config_path)
            self.service_b = service_b or ServiceB()
    """)

    print("="*80)


if __name__ == "__main__":
    main()
