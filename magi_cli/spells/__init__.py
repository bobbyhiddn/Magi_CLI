import pkgutil
import importlib

__all__ = []
commands_list = []  # List to store command functions
aliases = {}  # Dictionary to store aliases

for _, module_name, _ in pkgutil.walk_packages(__path__):
    __all__.append(module_name)
    # Dynamically import the module
    _module = importlib.import_module('.' + module_name, __package__)
    globals()[module_name] = _module
    # Add command function to commands_list
    commands_list.append(vars(_module)[module_name])
    # Collect aliases if present in the module
    if hasattr(_module, 'alias'):
        aliases[_module.alias] = vars(_module)[module_name]