from . import config as config_module
from .resource import resource_config, Resource
from .view import ResourceView

__all__ = [
    "resource_config",
    "Resource",
    "ResourceView",
]


def includeme(config):
    for name in config_module.__all__:
        method = getattr(config_module, name)
        config.add_directive(name, method)
