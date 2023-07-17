import pkgutil

__all__ = []
commands_list = []  # List to store command functions

for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    __all__.append(module_name)
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module
    # Add command function to commands_list
    commands_list.append(vars(_module)[module_name])
