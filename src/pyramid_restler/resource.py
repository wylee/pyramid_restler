from dataclasses import dataclass, field

from pyramid.httpexceptions import exception_response
from pyramid.request import Request


__all__ = [
    "resource_config",
    "Resource",
]


class Resource:
    def __init__(self, request: Request):
        self.request = request

    def method_not_allowed(self):
        raise exception_response(405)

    delete = method_not_allowed
    get = method_not_allowed
    patch = method_not_allowed
    post = method_not_allowed
    put = method_not_allowed

    def head(self):
        return self.get()


def resource_config(**view_args):
    """Specify resource config on resource method.

    Currently, all of the supplied keyword args will be passed through
    to Pyramid's ``Configurator.add_view()``. At some point, other
    resource-oriented config options might be added.

    """

    def wrapper(view_method):
        view_method.resource_config = ResourceConfig(view_args=view_args)
        return view_method

    return wrapper


@dataclass
class ResourceConfig:

    view_args: dict = field(default_factory=dict)
