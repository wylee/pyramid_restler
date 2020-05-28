import logging
import posixpath
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import List

from pyramid.config import Configurator, ConfigurationError
from pyramid.events import NewRequest, NewResponse
from pyramid.httpexceptions import exception_response
from pyramid.interfaces import IRendererFactory

from .cors import add_cors_headers
from .settings import get_setting
from .util import camel_to_underscore
from .view import ResourceView


__all__ = [
    "add_json_adapters",
    "add_resource",
    "add_resources",
    "enable_cors",
    "enable_post_tunneling",
]


log = logging.getLogger(__name__)


RENDERER_EXT_MAP = {
    "jinja2": "html",
    "mako": "html",
}


RENDERER_ACCEPT_MAP = {
    "json": "application/json",
    "html": "text/html",
}


def add_json_adapters(self: Configurator, *adapters):
    """Add default and additional JSON adapters.

    Adds default JSON adapters for date, datetime, and decimal objects.
    Also adds additional adapters if specified.

    """
    renderer = self.registry.getUtility(IRendererFactory, "json")
    adapters = (
        (date, lambda obj, req: obj.isoformat()),
        (datetime, lambda obj, req: obj.isoformat()),
        (Decimal, lambda obj, req: str(obj)),
    ) + adapters
    for type_, adapter in adapters:
        renderer.add_adapter(type_, adapter)


def add_resource(
    self: Configurator,
    resource_class,
    name=None,
    renderers=["json"],
    # Resource args
    acl=None,
    # Route args
    path=None,
    path_prefix=None,
    id_field=None,
    route_args=None,
    # View args
    view=ResourceView,
    permission=None,
    view_args=None,
):
    """Add routes and views for a resource.

    Given a resource (class), generates a set of routes and associated
    views.

    Args:
        resource_class: The class that implements the resource. An
            ``allowed_methods`` attribute will be attached to this
            class (if it doesn't already have that attribute).

        name: The base route name. If not specified, this will be
            computed from the resource class's module path and class
            name as follows:

            - If the class name ends with "Resource", that's stripped
              off
            - The class name is then converted to camel case
            - The module name containing the class is joined to the
              converted class name with a dot

            So, for a resource class named ``ContainerResource`` in a
            module named ``api``, the computed name will be
            "api.container".

        renderers: A list of renderers to generate routes and views for.
            This can include entries like "json" and/or "template.mako".

            For each renderer, a route with an extension (like ".json"
            and/or ".html") is generated with a view for each
            corresponding resource method. In this case, the response is
            rendered according to the extension.

            In addition, a route with *no* extension is generated with
            a view for each corresponding resource method. In this case,
            the response is rendered according to the Accept header in
            the request.

        acl: An ACL list that will be attached to the resource class as
            its ``__acl__`` attribute. If this isn't specified and the
            resource class doesn't have an ``__acl__`` attribute
            already, the default ACL will be attached instead (assuming
            a default ACL is configured).

        path: The base route path. If not specified, this will be
            computed from ``name`` by replacing dots with slashes
            and underscores with dashes. For the example above, the
            computed path would be "/api/container".

        path_prefix: If specified, this will be prepended to all
            generated route paths.

        id_field: If specified, an ID-field path segment will be
            appended to ``path``. E.g., if "id" is passed, the base path
            will be set to "/whatever/path/{id}". This is useful when an
            explicit ``path`` isn't passed.

        route_args: Common route args that will be passed to *every*
            call to ``config.add_view()``.

        view: The view class that will call methods on the resource
            class. This is optional because in many cases the included/
            default view class will suffice.

        permission: Permission that will be set on all generated views.
            This is a special case for convenience.

        view_args: Common view args that will be passed to *every* call
            to ``config.add_view()``.

    Settings can be set under the "pyramid_restler" key:

    - default_acl: Default ACL to attach to resource classes that
      don't have an __acl__ attribute (when ``acl`` isn't specified).

    - resource_methods: Methods on resource classes that will be
      considered resource methods (these should be lower case); if not
      specified, the default :data:`RESOURCE_METHODS` will be used.

    """
    resource_class = self.maybe_dotted(resource_class)
    resource_name = resource_class.__name__
    view = self.maybe_dotted(view)
    view_name = view.__name__

    if name is None:
        module_name = resource_class.__module__.rsplit(".", 1)[-1]
        name = resource_name
        suffix = "Resource"
        if name.endswith(suffix):
            name = name[: -len(suffix)]
        name = camel_to_underscore(name)
        name = f"{module_name}.{name}"
        log.debug(f"Computed route name: {name}")

    if path is None:
        path = name.replace(".", "/")
        path = path.replace("_", "-")
        path = path.strip("/")
        path = f"/{path}"
        log.debug(f"Computed route pattern: {path}")

    if path_prefix is not None:
        log.debug(f"Prepending path prefix {path_prefix} to route pattern: {path}")
        path = posixpath.join(path_prefix, path.lstrip("/"))

    if id_field is not None:
        log.debug(f"Appending ID field {id_field} to route pattern: {path}")
        path = posixpath.join(path, f"{{{id_field}}}")

    if acl is not None:
        resource_class.__acl__ = acl
    else:
        acl = getattr(resource_class, "__acl__", None)
        if acl is None:
            default_acl = get_setting(self.get_settings(), "default_acl")
            if default_acl is not None:
                log.debug(
                    f"Setting {resource_name}.__acl__ " f"to default ACL: {default_acl}"
                )
                resource_class.__acl__ = default_acl

    route_args = {} if route_args is None else route_args

    view_args = {} if view_args is None else view_args
    view_args.setdefault("http_cache", 0)
    if permission:
        view_args["permission"] = permission

    resource_methods = get_setting(self.get_settings(), "resource_methods")
    resource_methods = tuple(m.lower() for m in resource_methods)
    request_methods = tuple(m.upper() for m in resource_methods)

    method_config = []
    allowed_methods = []
    methods_not_allowed = []
    for method in resource_methods:
        attr = method.lower()
        request_method = method.upper()
        if hasattr(resource_class, attr):
            resource_method = getattr(resource_class, attr)
            resource_config = getattr(resource_method, "resource_config", None)
            method_config.append((method, request_method, resource_config))
            allowed_methods.append(request_method)
            if not hasattr(view, attr):
                raise ConfigurationError(
                    f"View {view_name} "
                    f"has no method `{attr}` "
                    f"corresponding to resource method `{attr}` "
                )
        else:
            methods_not_allowed.append(request_method)

    if allowed_methods:
        if not hasattr(resource_class, "allowed_methods"):
            resource_class.allowed_methods = allowed_methods
    else:
        raise ConfigurationError(
            f"No resource methods found for resource: {resource_name}"
        )

    if methods_not_allowed:
        log.debug(
            f"Resource {resource_name} does not allow these methods: "
            f"{', '.join(methods_not_allowed)}"
        )

    def add_route(route_name, pattern, accept: List[str] = None):
        log.debug(
            f"Adding route {route_name} "
            f"with pattern {pattern} "
            f"for resource {resource_name} "
            f"responding to {', '.join(request_methods)} "
            f"accepting content type {', '.join(accept) if accept else 'ANY'}"
        )
        self.add_route(
            route_name,
            pattern,
            factory=resource_class,
            request_method=request_methods,
            accept=accept,
            **route_args,
        )

    def add_views(route_name, renderer, accept: str = None):
        for attr, request_method, view_config in method_config:
            if view_config:
                args = {**view_config.view_args, **view_args}
            else:
                args = {**view_args}

            log.debug(
                f"Adding view {view_name}.{attr} "
                f"for {route_name} "
                f"responding to {request_method} "
                f"accepting content type {accept or 'ANY'} "
                f"with renderer {renderer}"
            )

            self.add_view(
                route_name=route_name,
                view=view,
                attr=attr,
                request_method=request_method,
                accept=accept,
                renderer=renderer,
                **args,
            )

        for request_method in methods_not_allowed:
            self.add_view(
                route_name=route_name,
                view=method_not_allowed_view,
                request_method=request_method,
                accept=accept,
            )

    def run():
        accepts = []

        # Add route with extension for each renderer. In this case, the
        # accepted renderer is specified by the extension in the URL
        # path (and the Accept header is ignored).
        for renderer in renderers:
            ext, accept = get_ext_and_accept_for_renderer(renderer)
            accepts.append(accept)
            route_name = f"{name}.{ext}"
            pattern = f"{path}.{ext}"
            add_route(route_name, pattern)
            add_views(route_name, renderer)

        # Add route without extension for all renderers. In this case,
        # the accepted renderer is specified by the Accept header.
        add_route(name, path, accepts)
        for accept, renderer in zip(accepts, renderers):
            add_views(name, renderer, accept)

    run()


@contextmanager
def add_resources(self: Configurator, path_prefix, **shared_kwargs):
    """Add multiple resources at the specified path prefix.

    Example::

        with config.add_resources("/api") as add_resource:
            add_resource(".resources.ContainerResource")
            # -> /api/resources/container

            add_resource(".resources.ItemResource")
            # -> /api/resources/item

    """

    def add(resource_class, **kwargs):
        kwargs = {**shared_kwargs, **kwargs}
        self.add_resource(resource_class, path_prefix=path_prefix, **kwargs)

    yield add


def enable_cors(self: Configurator):
    """Enable CORS permissively (for use in development).

    This allows CORS requests from *anywhere*, which is probably not
    what you want, other than in development.

    .. warning:: Use with CAUTION. See :func:`add_cors_headers` for
        additional info.

    """
    self.add_subscriber(add_cors_headers, NewResponse)


def enable_post_tunneling(
    self: Configurator,
    allowed_methods=("DELETE", "PATCH", "PUT"),
    param_name="$method",
    header_name="X-HTTP-Method-Override",
):
    """Allow other request methods to be tunneled via POST.

    This allows DELETE, PATCH, and PUT and requests to be tunneled via
    POST requests. The method can be specified using a parameter or a
    header.

    The name of the parameter is "$method"; it can be a query or POST
    parameter. The query parameter will be preferred if both the query
    and POST parameters are present in the request.

    The name of the header is "X-HTTP-Method-Override". If the parameter
    described above is passed, this will be ignored.

    The request method will be overwritten before it reaches application
    code, such that the application will never be aware of the original
    request method. Likewise, the parameter and header will be removed
    from the request, and the application will never see them.

    """
    allowed_methods = sorted(allowed_methods)
    disallowed_message = (
        f"Only these methods may be tunneled over POST: {allowed_methods}."
    )

    def new_request_subscriber(event):
        request = event.request
        if request.method == "POST":
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
                raise exception_response(405, detail=disallowed_message)

    self.add_subscriber(new_request_subscriber, NewRequest)


def get_ext_and_accept_for_renderer(renderer):
    if "." in renderer:
        ext = renderer.rsplit(".", 1)[1]
    else:
        ext = renderer
    ext = RENDERER_EXT_MAP.get(ext, ext)
    return ext, RENDERER_ACCEPT_MAP.get(ext)


def method_not_allowed_view(request):
    raise exception_response(405)
