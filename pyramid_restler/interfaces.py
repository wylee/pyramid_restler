from zope.interface import Attribute, Interface


class IView(Interface):

    def __init__(context, request):
        """Initialize view class."""

    def get_collection():
        """Get the entire collection.

        GET /entity -> 200 OK, list of members

        If a query parameter named $$ is present on the request, it must be
        a JSON object with keys that correspond to the keyword args of the
        context's `get_collection` method. The object will be JSON-decoded,
        but no further processing will be done on the resulting dict (i.e.,
        types won't be coerced, etc).

        """

    def get_member():
        """Get a specific member by ID.

        GET /entity/id -> 200 OK, member

        """

    def create_member():
        """Create a new member.

        POST /entity?POST_data -> 201 Created, location of new member

        """

    def update_member(id):
        """Update an existing member.

        PUT /entity/id?POST_data -> 204 No Content

        """

    def delete_member(id):
        """Delete an existing member.

        DELETE /entity/id -> 204 No Content

        """

    def render_to_response(value, fields=None):
        """Render a member or list of members to an appropriate response.

        The request should include an indication of the client's preferred
        representation. This can be specified via the Accept header or by
        using the {.renderer} notation at the end of the URL path.

        """


class ICollection(Interface):
    """Marker interface for model classes."""


class IMember(Interface):
    """Marker interface for model instances. ???"""


class IContext(Interface):
    """Adapt a model to a request context."""

    def __init__(request):
        """Initialize context."""

    def fetch():
        """Fetch the data for this context.

        For collection contexts, this should fetch the entire collection or
        a subset of it. For member contexts, this should fetch a specific
        member.

        """


class ICollectionContext(IContext):

    entity = Attribute('The entity to operate on.')

    def fetch(**kwargs):
        """Return the entire collection by default.

        Implementation-specific keyword args may be passed to filter the
        collection or alter it in various ways.

        """

    def create(data):
        """Add a new member to this collection."""


class IMemberContext(IContext):

    default_fields = Attribute('A list of fields to include in the result.')

    id_as_string = Attribute('String representation of ``member`` ID.')

    def fetch(id):
        """Get the member by identified by ``id``; return `None` if such a
        member doesn't exist."""

    def update(id, data):
        """Update member."""

    def delete(id):
        """Delete member."""
