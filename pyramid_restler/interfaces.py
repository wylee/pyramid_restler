from zope.interface import Attribute, Interface


class IView(Interface):

    def __init__(context, request):
        """Initialize view class."""

    def get_collection():
        """Get the entire collection.

        GET /entity -> 200 OK, list of members

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


class IContext(Interface):
    """Interface for adapting a model entity to a view context."""

    entity = Attribute('The entity to operate on.')

    default_fields = Attribute('A list of fields to include in the result.')

    def __init__(request):
        """Initialize context."""

    def get_collection():
        """Return the entire collection."""

    def get_member(id):
        """Return the member identified by ``id``."""

    def create_member(**data):
        """Create a new member."""

    def update_member(id, **data):
        """Update an existing member."""

    def delete_member(id):
        """Delete an existing member."""

    def get_member_id_as_string(member):
        """Get string representation of ``member`` ID."""
