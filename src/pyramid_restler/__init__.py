from . import config as config_module
from .resource import Resource
from .view import ResourceView, ResourceViewConfig


__all__ = [
    "Resource",
    "ResourceView",
    "ResourceViewConfig",
]


def includeme(config):
    for name in config_module.__all__:
        method = getattr(config_module, name)
        config.add_directive(name, method)
