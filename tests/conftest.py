"""Test setup: makes `goglib` and `goglib_rebuild` importable in tests as modules.

Both scripts are no-extension executables, so we load them via importlib and
register them in sys.modules so `import goglib` / `import goglib_rebuild`
works in any test file.
"""
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _register_script_as_module(script_name, module_name):
    """Load REPO_ROOT/script_name as sys.modules[module_name]."""
    if module_name in sys.modules:
        return sys.modules[module_name]
    path = REPO_ROOT / script_name
    loader = importlib.machinery.SourceFileLoader(module_name, str(path))
    spec = importlib.util.spec_from_loader(module_name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


# Side-effect: register the scripts so `import goglib` works in tests
_register_script_as_module("goglib", "goglib")
_register_script_as_module("goglib-rebuild-manifest", "goglib_rebuild")
