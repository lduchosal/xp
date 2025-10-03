#!/usr/bin/env python3
"""Extract constructor arguments from all service classes."""

import ast
from pathlib import Path
from typing import List, Tuple


def extract_class_init_args(file_path: Path) -> List[Tuple[str, List[str]]]:
    """Extract __init__ arguments from all classes in a Python file.

    Returns:
        List of tuples (class_name, list_of_arguments)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

    results = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name

            # Find __init__ method
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                    # Extract arguments
                    args = []
                    for arg in item.args.args:
                        if arg.arg != 'self':
                            # Get type annotation if present
                            type_hint = ''
                            if arg.annotation:
                                type_hint = ast.unparse(arg.annotation)

                            # Get default value if present
                            default = ''
                            num_defaults = len(item.args.defaults)
                            num_args = len(item.args.args) - 1  # Exclude self
                            arg_idx = item.args.args.index(arg) - 1  # Exclude self
                            default_idx = arg_idx - (num_args - num_defaults)

                            if default_idx >= 0 and default_idx < num_defaults:
                                default_node = item.args.defaults[default_idx]
                                default = ast.unparse(default_node)

                            # Format argument
                            arg_str = arg.arg
                            if type_hint:
                                arg_str += f": {type_hint}"
                            if default:
                                arg_str += f" = {default}"

                            args.append(arg_str)

                    results.append((class_name, args))
                    break

    return results


def main():
    """Main function to extract all service constructors."""
    # Find all service files
    services_dir = Path('../src/xp/services')
    service_files = sorted(services_dir.rglob('*_service.py'))

    output_lines = []
    output_lines.append("Service Constructor Arguments\n")
    output_lines.append("=" * 80 + "\n\n")

    for service_file in service_files:
        relative_path = service_file
        classes = extract_class_init_args(service_file)

        if classes:
            output_lines.append(f"{relative_path}\n")
            output_lines.append("-" * 80 + "\n")

            for class_name, args in classes:
                output_lines.append(f"\nClass: {class_name}\n")
                if args:
                    output_lines.append("Constructor arguments:\n")
                    for arg in args:
                        output_lines.append(f"  - {arg}\n")
                else:
                    output_lines.append("  (no arguments)\n")

            output_lines.append("\n")

    # Write to file
    output_file = Path('service_ctor.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    print(f"Extracted constructor arguments to {output_file}")
    print(f"Processed {len(service_files)} service files")


if __name__ == '__main__':
    main()
