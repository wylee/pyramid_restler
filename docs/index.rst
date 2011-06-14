pyramid_restler
===============

Overview
--------

``pyramid_restler`` implements a pattern for mapping URLs to views. The view
layer is agnostic to any back end model. The context layer adapts the back end
model for the view.

URL Mapping
-----------

Request method /pattern => route name => view method => context method::

    GET /{name} => get_{name}_collection => get_collection() => get_collection()
    GET /{name}/{id} => get_{name} => get_member() => get_member(id)
    POST /{name} => create_{name} =>  create_member() => create_member(**data)
    PUT /{name}/{id} => update_{name} => update_member() => update_member(id, **data)
    DELETE /{name}/{id} => delete_{name} => delete_member() => delete_member(id)

Configuration Directives
------------------------

``pyramid_restler`` adds the :func:`pyramid_restler.config.add_restful_routes`
directive to the config object.

More Info
---------

.. toctree::
   :maxdepth: 1

   api

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
