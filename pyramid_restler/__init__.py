from .config import add_resource, add_resources, enable_POST_tunneling
from .rendering import default_renderer_factory


__version__ = '2.0.dev0'


def includeme(config):
    config.add_directive('add_resource', add_resource)
    config.add_directive('add_resources', add_resources)
    config.add_directive('enable_POST_tunneling', enable_POST_tunneling)
    config.add_renderer(None, default_renderer_factory)
