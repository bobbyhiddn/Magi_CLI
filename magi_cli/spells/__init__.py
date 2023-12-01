import os
import pkgutil
import importlib

# Set default SANCTUM_PATH to the user's home directory if SANCTUM_PATH is not in the environment
SANCTUM_PATH = os.getenv('SANCTUM_PATH', os.path.join(os.path.expanduser('~'), '.sanctum'))

# Now set the SANCTUM environment variable to SANCTUM_PATH if it's not already set
if not os.getenv('SANCTUM'):
    os.environ['SANCTUM'] = SANCTUM_PATH

# Ensure the SANCTUM_PATH directory exists
if not os.path.exists(SANCTUM_PATH):
    os.makedirs(SANCTUM_PATH)

# Set other paths relative to SANCTUM_PATH
TOME_PATH = os.path.join(SANCTUM_PATH, '.tome')
RUNE_DIR = os.path.join(SANCTUM_PATH, '.runes')

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