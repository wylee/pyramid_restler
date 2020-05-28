import logging

from pyramid.csrf import check_csrf_origin
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
          requests (typically HTML rendered from a template). For HEAD
          requests, the data is also returned so that Pyramid can
          generate a HEAD response.

        - Return a ``303 See Other`` response for DELETE, PATCH, PUT,
          and POST requests:

          - For DELETEs, use the referrer if it's safe (same origin) or
            fall back to the URL of the current resource.

          - For other methods, fall back to the URL of the current
            resource (which is always safe).

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

        # Redirect after POST et al.
        if method == "DELETE":
            # XXX: It might be nice to automatically redirect to the
            # associated container resource on DELETE, but that seems
            # complicated. Redirecting back to the referrer is, so we'll
            # stick with that for that now.
            if check_csrf_origin(request, raises=False):
                location = request.referrer
            else:
                location = request.path_info
                log.warning(
                    "The referrer for this DELETE request isn't from a "
                    "trusted origin; redirecting back to the current"
                    "resource (%s) instead, which will result in a 404 "
                    "response",
                    request.matched_route.name,
                )
            return HTTPSeeOther(location=location)
        if method in ("PATCH", "POST", "PUT"):
            # Redirect back to the current resource.
            #
            # XXX: For container resources, it's debatable as to
            # whether it's preferable to redirect to the new item or
            # back to the container, but the latter doesn't require
            # any special configuration or logic.
            location = request.path_info
            return HTTPSeeOther(location=location)
