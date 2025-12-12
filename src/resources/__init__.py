"""
Resources Package - Auto-import all resource modules.

This module automatically discovers and imports all resource modules
in the resources/ package tree, enabling MCP resource handlers to be
registered without explicit imports.

Pattern mirrors the tools/ package structure for consistency.
"""

import importlib
import pkgutil
from pathlib import Path


# Get package directory
package_dir = Path(__file__).parent


def _import_submodules(package_path: Path, package_name: str):
    """
    Recursively import all submodules in a package.

    Args:
        package_path: Path to the package directory
        package_name: Full package name (e.g., "src.resources")
    """
    for module_info in pkgutil.iter_modules([str(package_path)]):
        full_name = f"{package_name}.{module_info.name}"

        # Import the module
        importlib.import_module(full_name)

        # If it's a package, recursively import its submodules
        if module_info.ispkg:
            subpackage_path = package_path / module_info.name
            _import_submodules(subpackage_path, full_name)


# Auto-discover and import all resource modules
_import_submodules(package_dir, __package__)
