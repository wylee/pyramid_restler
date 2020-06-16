import logging


log = logging.getLogger(__name__)


def add_cors_headers(event):
    """Add CORS headers.

    If the resource handles CORS itself by adding access control headers
    to the response, this does nothing. Otherwise...

    When the request method is OPTIONS, this will return a response that
    allows requests from the request's origin for any method and content
    type.

    When the request method is something other than OPTIONS, this will
    add a header to the response that allows the request.

    .. warning:: This is mainly intended for use in development since it
        allows CORS requests from *anywhere*, which is probably not what
        you want.

    """
    request = event.request
    response = event.response

    origin = request.headers.get("Origin", "").strip()

    if not origin:
        return

    if has_cors_headers(response):
        return

    if request.method == "OPTIONS":
        if has_cors_headers(request):
            response.headers.update(
                {
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
    else:
        response.headers.update({"Access-Control-Allow-Origin": origin})


def has_cors_headers(obj):
    return any(name.startswith("Access-Control") for name in obj.headers)
