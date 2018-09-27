from zope.interface import Interface


class IResourceView(Interface):

    def __init__(context, request):
        """Initialize view."""

    def render_to_response(value, fields=None):
        """Render ``value`` to response.

        The request should include an indication of the client's
        preferred representation via the ``Accept`` header.

        """


class IResource(Interface):

    """Interface for adapting a resource for use with a view."""

    def __init__(request):
        """Initialize resource."""
