from pyramid_restler.view import RESTfulView


def add_restful_routes(self, name, factory, view_class=RESTfulView, **kwargs):
    """Add a set of RESTful routes for an entity.

    URL patterns for an entity are mapped to a set of views encapsulated in
    a view class. The view class interacts with the model through a context
    adapter that knows the particulars of that model.

    To use this directive in your application, first call
    `config.include('pyramid_restler')` somewhere in your application's
    `main` function, then call `config.add_restful_routes(...)`.

    ``name`` is used as the base name for all route names and patterns. In
    route names, it will be used as-is. In route patterns, underscores will
    be converted to dashes.

    ``factory`` is the model adapter that the view interacts with. It can be
    any class that implements the :class:`pyramid_restler.interfaces.IContext`
    interface.

    Any additional keyword args will be passed directly through to every
    `add_route` call.

    """
    subs = dict(
        name=name,
        slug=name.replace('_', '-'),
        id='{id:[^/\.]+}',
        renderer='{renderer:(\.[a-z]+)?}')

    # GET collection
    self.add_route(
        'get_{name}_collection'.format(**subs),
        '/{slug}{renderer}'.format(**subs),
        request_method='GET',
        view=view_class,
        view_attr='get_collection',
        factory=factory)

    # Get member
    self.add_route(
        'get_{name}'.format(**subs),
        '/{slug}/{id}{renderer}'.format(**subs),
        request_method='GET',
        view=view_class,
        view_attr='get_member',
        factory=factory)

    # Create member
    self.add_route(
        'create_{name}'.format(**subs),
        '/{slug}'.format(**subs),
        request_method='POST',
        view=view_class,
        view_attr='create_member',
        factory=factory)

    # Update member
    self.add_route(
        'update_{name}'.format(**subs),
        '/{slug}/{id}'.format(**subs),
        request_method='PUT',
        view=view_class,
        view_attr='update_member',
        factory=factory)

    # Delete member
    self.add_route(
        'delete_{name}'.format(**subs),
        '/{slug}/{id}'.format(**subs),
        request_method='DELETE',
        view=view_class,
        view_attr='delete_member',
        factory=factory)
