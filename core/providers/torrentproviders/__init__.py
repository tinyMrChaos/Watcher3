import pkgutil
import importlib

providers = []


__path__ = pkgutil.extend_path(__path__, __name__)
for importer, modname, ispkg in pkgutil.walk_packages(path=__path__, prefix=__name__ + '.'):
        providers.append(modname.split(".")[-1])
        importlib.import_module(modname)
