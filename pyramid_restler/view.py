from inspect import isfunction
from dataclasses import dataclass, field
from typing import Union

from pyramid.response import Response

from zope.interface import implementer

from pyramid_restler.interfaces import IResourceView


__all__ = ['resource_method', 'ResourceView']


@dataclass
class ResourceMethodConfig:

    allowed_methods: Union[str, tuple] = None
    view_args: dict = field(default_factory=dict)


def resource_method(arg, **view_args):
    if isfunction(arg):
        view_method = arg
        allowed_methods = (view_method.__name__.upper(),)
        view_method.resource_method_config = ResourceMethodConfig(allowed_methods)
        return view_method

    allowed_methods = arg
    if isinstance(allowed_methods, str):
        allowed_methods = (allowed_methods,)
    allowed_methods = tuple(method.upper() for method in allowed_methods)

    def wrapper(view_method):
        view_method.resource_method_config = ResourceMethodConfig(
            allowed_methods, view_args=view_args)
        return view_method

    return wrapper


@implementer(IResourceView)
class ResourceView:

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @resource_method
    def get(self):
        result = self.context.get()
        return self._get_standard_response(result)

    @resource_method
    def delete(self):
        result = self.context.delete()
        return self._get_standard_response(result)

    @resource_method
    def patch(self):
        result = self.context.patch()
        return self._get_standard_response(result)

    @resource_method
    def post(self):
        result = self.context.post()
        return self._get_standard_response(result)

    @resource_method
    def put(self):
        result = self.context.put()
        return self._get_standard_response(result)

    def _get_standard_response(self, result):
        if result is not None:
            context = self.context
            # Content
            try:
                converter = context.configuration.converter
            except AttributeError:
                pass
            else:
                result = converter(result)
            return result
        # No content
        return Response(204)
