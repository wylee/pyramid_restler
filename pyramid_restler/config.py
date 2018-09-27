import posixpath
from contextlib import contextmanager
from inspect import isfunction

from pyramid.events import NewRequest
from pyramid.httpexceptions import HTTPBadRequest

from .view import ResourceView


@contextmanager
def add_resources(self, base_route_pattern, **common_kwargs):
    """Add multiple resources at base path/pattern."""

    def add(route_name, route_pattern, resource_factory, **kwargs):
        if not route_pattern.startswith('/'):
            route_pattern = posixpath.join(base_route_pattern, route_pattern)
        kwargs = {**common_kwargs, **kwargs}
        self.add_resource(route_name, route_pattern, resource_factory, **kwargs)

    yield add


def add_resource(self,
                 route_name,
                 route_pattern,
                 resource_factory,
                 view=ResourceView,
                 allowed_methods=None,
                 renderer=None,
                 route_args=None,
                 view_args=None,
                 debug=False):
    """Add route and views for resource."""
    resource_factory = self.maybe_dotted(resource_factory)
    view = self.maybe_dotted(view)
    route_args = route_args or {}
    view_args = view_args or {}
    resource_methods = []

    if renderer is not None:
        view_args['renderer'] = renderer

    for name in dir(view):
        attr = getattr(view, name)
        if isfunction(attr) and getattr(attr, 'resource_method_config', None):
            resource_methods.append((name, attr.resource_method_config))

    if allowed_methods is None:
        # When no route level allowed methods are specified, use the
        # available methods from the resource class.
        allowed_methods = []
        for name, resource_method_config in resource_methods:
            attr = getattr(resource_factory, name, None)
            if isfunction(attr):
                allowed_methods.extend(resource_method_config.allowed_methods)
        allowed_methods = tuple(allowed_methods) or None

    # Add primary route for resource.
    self.add_route(
        route_name,
        route_pattern,
        factory=resource_factory,
        request_method=allowed_methods,
        **route_args)

    if debug:
        print(
            f'config.add_route(\n'
            f'    {route_name!r},\n'
            f'    {route_pattern!r},\n'
            f'    factory={view.__module__}.{resource_factory.__qualname__},\n'
            f'    request_method={allowed_methods!r}\n'
            f')'
        )

    # Keep track of request methods used for view methods associated
    # with the primary route.
    used_methods = set()

    for name, resource_method_config in resource_methods:
        request_method = resource_method_config.allowed_methods
        reused_methods = used_methods.intersection(request_method)

        if reused_methods:
            reused_methods = ', '.join(sorted(reused_methods))
            raise ValueError(f'Request method(s) already used in {view}: {reused_methods}')

        used_methods.update(request_method)

        if allowed_methods:
            request_method = tuple(m for m in request_method if m in allowed_methods)

        if request_method:
            current_view_args = {**view_args, **resource_method_config.view_args}
            self.add_view(
                view,
                attr=name,
                route_name=route_name,
                request_method=request_method,
                **current_view_args)

            if debug:
                print(
                    f'config.add_view(\n'
                    f'    {view.__module__}.{view.__qualname__},\n'
                    f'    attr={name!r},\n'
                    f'    route_name={route_name!r},\n'
                    f'    request_method={request_method!r}\n'
                    f')'
                )


def enable_POST_tunneling(self, allowed_methods=('PUT', 'DELETE')):
    """Allow other request methods to be tunneled via POST.

    This allows PUT and DELETE requests to be tunneled via POST requests.
    The method can be specified using a parameter or a header...

    The name of the parameter is '$method'; it can be a query or POST
    parameter. The query parameter will be preferred if both the query and
    POST parameters are present in the request.

    The name of the header is 'X-HTTP-Method-Override'. If the parameter
    described above is passed, this will be ignored.

    The request method will be overwritten before it reaches application
    code, such that the application will never be aware of the original
    request method. Likewise, the parameter and header will be removed from
    the request, and the application will never see them.

    """
    param_name = '$method'
    header_name = 'X-HTTP-Method-Override'
    allowed_methods = sorted(set(allowed_methods))
    disallowed_message = f'Only these methods may be tunneled over POST: {allowed_methods}.'

    def new_request_subscriber(event):
        request = event.request
        if request.method == 'POST':
            if param_name in request.GET:
                method = request.GET[param_name]
            elif param_name in request.POST:
                method = request.POST[param_name]
            elif header_name in request.headers:
                method = request.headers[header_name]
            else:
                return  # Not a tunneled request
            if method in allowed_methods:
                request.GET.pop(param_name, None)
                request.POST.pop(param_name, None)
                request.headers.pop(header_name, None)
                request.method = method
            else:
                raise HTTPBadRequest(disallowed_message)

    self.add_subscriber(new_request_subscriber, NewRequest)
