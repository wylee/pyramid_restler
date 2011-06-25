.. _pyramid_restler_api:

API
===

Configuration
-------------

.. autofunction:: pyramid_restler.config.add_restful_routes

.. autofunction:: pyramid_restler.config.enable_POST_tunneling

Interfaces
----------

.. autointerface:: pyramid_restler.interfaces.IView
   :members:

.. autointerface:: pyramid_restler.interfaces.IContext
   :members:

View
----

.. autoclass:: pyramid_restler.view.RESTfulView
   :members:

Model
-----

.. autoclass:: pyramid_restler.model.SQLAlchemyORMContext
   :members:
