"""
API Documentation Generator

Generates API documentation from Python docstrings.
Uses introspection to extract public APIs.
"""

import ast
import os
from pathlib import Path
from typing import Any


def extract_docstring(node: ast.AST) -> str | None:
    """Extract docstring from AST node"""
    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
        docstring = ast.get_docstring(node)
        return docstring
    return None


def get_public_api(module_path: Path) -> dict[str, Any]:
    """Extract public API from a Python module"""
    with open(module_path, encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    module_doc = extract_docstring(tree)

    classes = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Skip private classes
            if not node.name.startswith("_"):
                doc = extract_docstring(node)
                classes.append({
                    "name": node.name,
                    "doc": doc,
                    "methods": [
                        n.name for n in node.body
                        if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
                    ]
                })
        elif isinstance(node, ast.FunctionDef):
            # Skip private functions and dunder methods
            if not node.name.startswith("_") and not node.name.startswith("__"):
                doc = extract_docstring(node)
                functions.append({
                    "name": node.name,
                    "doc": doc
                })

    return {
        "module": module_path.stem,
        "doc": module_doc,
        "classes": classes,
        "functions": functions
    }


def generate_markdown(api: dict[str, Any]) -> str:
    """Generate Markdown documentation from API data"""
    lines = []

    if api.get("doc"):
        lines.append(f"{api['doc']}\n")

    # Classes
    if api["classes"]:
        lines.append("## Classes\n")
        for cls in api["classes"]:
            lines.append(f"### `{cls['name']}`\n")
            if cls["doc"]:
                lines.append(f"{cls['doc']}\n")
            if cls["methods"]:
                lines.append("**Methods:**")
                for method in cls["methods"]:
                    lines.append(f"- `{method}`")
                lines.append("")

    # Functions
    if api["functions"]:
        lines.append("## Functions\n")
        for func in api["functions"]:
            lines.append(f"### `{func['name']}()`\n")
            if func["doc"]:
                lines.append(f"{func['doc']}\n")

    return "\n".join(lines)


def scan_modules(src_dir: str, output_dir: str):
    """Scan src directory and generate API docs"""
    src_path = Path(src_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Map of module paths to doc file names
    module_docs = {}

    # Core modules to document
    core_modules = [
        "agents",
        "cli",
        "core",
        "datacenter",
        "evaluation",
        "llm",
        "memory",
        "package_manager",
        "skills",
        "flow",
    ]

    for module in core_modules:
        module_path = src_path / module
        if not module_path.exists():
            print(f"Module not found: {module_path}")
            continue

        # Find all Python files in the module
        for py_file in module_path.rglob("*.py"):
            # Skip __init__.py for now, handle separately
            if py_file.name == "__init__.py":
                continue

            try:
                api = get_public_api(py_file)
                if api["classes"] or api["functions"]:
                    md = generate_markdown(api)
                    # Use module name + file name for output
                    out_name = f"{module}_{py_file.stem}"
                    out_file = out_path / f"{out_name}.md"
                    out_file.write_text(md, encoding="utf-8")
                    module_docs[f"src/{module}/{py_file.name}"] = f"{out_name}.md"
            except Exception as e:
                print(f"Error processing {py_file}: {e}")

    # Generate index
    index_lines = ["# API Reference\n"]
    for mod, doc_file in sorted(module_docs.items()):
        index_lines.append(f"- [{mod}]({doc_file})")

    (out_path / "index.md").write_text("\n".join(index_lines), encoding="utf-8")

    print(f"Generated API docs in {output_dir}")
    print(f"Processed {len(module_docs)} modules")


if __name__ == "__main__":
    scan_modules("src", "docs/api/generated")
