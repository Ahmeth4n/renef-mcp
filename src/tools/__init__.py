# Tools Package - Auto-import all tool modules
import importlib
import pkgutil
from pathlib import Path

# Auto-discover and import all modules in this package (recursively)
package_dir = Path(__file__).parent

def _import_submodules(package_path: Path, package_name: str):
    for module_info in pkgutil.iter_modules([str(package_path)]):
        full_name = f"{package_name}.{module_info.name}"
        importlib.import_module(full_name)
        if module_info.ispkg:
            _import_submodules(package_path / module_info.name, full_name)

_import_submodules(package_dir, __package__)
