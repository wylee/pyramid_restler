from dataclasses import dataclass, field

from pyramid.response import Response


__all__ = ["ResourceView", "ResourceViewConfig"]


class ResourceView:
    def __init__(self, context, request):
        self.resource = context
        self.request = request

        # XXX: This is for Pyramid, in case it needs it for something
        self.context = context

    def get(self):
        result = self.resource.get()
        return self.get_standard_response(result)

    def delete(self):
        result = self.resource.delete()
        return self.get_standard_response(result)

    def patch(self):
        result = self.resource.patch()
        return self.get_standard_response(result)

    def post(self):
        result = self.resource.post()
        return self.get_standard_response(result)

    def put(self):
        result = self.resource.put()
        return self.get_standard_response(result)

    def get_standard_response(self, data):
        if data is not None:
            # Response has content
            converter = getattr(self.resource, "response_converter", None)
            if converter:
                data = converter(data)
            return data
        # Response has no content
        return Response(204)


@dataclass
class ResourceViewConfig:

    view_args: dict = field(default_factory=dict)


def resource_view_config(**view_args):
    """Specify view config for resource method in resource view.

    The supplied keyword args will be passed through to Pyramid's
    ``Configurator.add_view()``.

    """

    def wrapper(view_method):
        view_method.resource_view_config = ResourceViewConfig(view_args=view_args)
        return view_method

    return wrapper
