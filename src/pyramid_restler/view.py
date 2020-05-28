import logging

from pyramid.httpexceptions import HTTPSeeOther, HTTPNoContent
from pyramid.request import Request


__all__ = ["ResourceView"]


log = logging.getLogger(__name__)


class ResourceView:
    def __init__(self, context, request: Request):
        self.resource = context
        self.request = request

        # XXX: This is for Pyramid, in case it needs it for something
        self.context = context

    def delete(self):
        data = self.resource.delete()
        return self.get_standard_response(data)

    def get(self):
        data = self.resource.get()
        return self.get_standard_response(data)

    def options(self):
        options = self.resource.options()
        return HTTPNoContent(headers=options)

    def patch(self):
        data = self.resource.patch()
        return self.get_standard_response(data)

    def post(self):
        data = self.resource.post()
        return self.get_standard_response(data)

    def put(self):
        data = self.resource.put()
        return self.get_standard_response(data)

    def get_standard_response(self, data):
        """Get a standard response.

        When there's no data, return a ``204 No Content`` response
        regardless of the request method or configured renderers.
        Otherwise...

        For XHR requests, return a ``200 OK`` response with rendered
        data for *all* request methods (typically JSON).

        For non-XHR requests:

        - Return a ``200 OK`` response with rendered data for GET
          requests (typically HTML rendered from a template).

        - Return a ``303 See Other`` response for DELETE, PATCH, PUT,
          and POST requests. If a URL is specified via the ``$next``
          GET or POST parameter, it will be used as redirect location.
          Otherwise, the URL of the current resource will be used.

        """
        if data is None:
            return HTTPNoContent()

        request = self.request
        method = request.method

        if method in ("GET", "HEAD") or request.is_xhr:
            converter = getattr(self.resource, "response_converter", None)
            if converter:
                data = converter(data)
            return data

        location = request.params.get("$next")

        # Redirect after POST et al.
        if method == "DELETE":
            # XXX: It might be nice to *automatically* redirect to the
            # associated container resource on DELETE, but that seems
            # complicated. For now, we'll stick with the explicit next-
            # URL approach.
            if not location:
                log.info(
                    "Pass a next URL using the $next GET or POST "
                    "parameter to avoid 404s on DELETE for route: %s",
                    request.matched_route.name,
                )
            location = location or request.path_info
            return HTTPSeeOther(location=location)
        if method in ("PATCH", "POST", "PUT"):
            # Redirect back to the current resource.
            #
            # XXX: For container resources, it's debatable as to
            # whether it's preferable to redirect to the new item or
            # back to the container, but the latter doesn't require
            # any special configuration or logic.
            location = location or request.path_info
            return HTTPSeeOther(location=location)
