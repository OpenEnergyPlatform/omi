from metadata_tool.dialects.base.register import get_dialect
import pkgutil
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    n = 'metadata_tool.dialects.' + module_name + '.dialect'
    __import__(n)
