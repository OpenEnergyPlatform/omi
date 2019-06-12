import pkgutil

from omi.dialects.base.register import get_dialect

for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    n = "omi.dialects." + module_name + ".dialect"
    __import__(n)
