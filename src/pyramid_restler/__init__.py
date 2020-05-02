from . import config
from .resource import Resource
from .view import ResourceView, ResourceViewConfig


def includeme(config_):
    for name in config.__all__:
        method = getattr(config, name)
        config_.add_directive(name, method)
