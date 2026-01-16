"""
Syntax and import validation tests.

Tests that all Python files in the project can be compiled
and have valid imports. This catches syntax errors and import
issues that functional tests might not detect.
"""

import py_compile
import sys
from pathlib import Path


def get_python_files(root_dir):
    """Recursively find all Python files in the project."""
    root_path = Path(root_dir)
    python_files = []

    # Directories to skip
    skip_dirs = {
        '__pycache__',
        '.venv',
        'venv',
        '.git',
        'migrations/versions',  # Skip migration files (they're generated)
        'instance',
    }

    for py_file in root_path.rglob('*.py'):
        # Skip if any parent directory is in skip_dirs
        if any(skip_dir in py_file.parts for skip_dir in skip_dirs):
            continue
        python_files.append(py_file)

    return python_files


def test_python_syntax():
    """Test that all Python files have valid syntax."""
    project_root = Path(__file__).parent.parent
    python_files = get_python_files(project_root)

    assert len(python_files) > 0, "No Python files found to test"

    errors = []
    for py_file in python_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"{py_file.relative_to(project_root)}: {e}")

    assert not errors, f"Syntax errors found in {len(errors)} file(s):\n" + "\n".join(
        errors
    )


def test_imports():
    """Test that all Python modules can be imported without errors."""
    project_root = Path(__file__).parent.parent

    # Add project root to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Test critical module imports
    critical_imports = [
        'app',
        'app.models',
        'app.forms',
        'app.routes.auth',
        'app.routes.users',
        'app.routes.listings',
        'app.routes.admin',
        'app.routes.categories',
        'app.cli.demo',
        'app.cli.maintenance',
    ]

    errors = []
    for module_name in critical_imports:
        try:
            __import__(module_name)
        except ImportError as e:
            errors.append(f"{module_name}: {e}")
        except Exception as e:
            # Catch other errors (e.g., syntax errors that prevent import)
            errors.append(f"{module_name}: {type(e).__name__}: {e}")

    assert not errors, f"Import errors found in {len(errors)} module(s):\n" + "\n".join(
        errors
    )
