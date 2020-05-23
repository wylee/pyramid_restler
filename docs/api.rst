.. _pyramid_restler_api:

API
===

Configuration
-------------

.. autofunction:: pyramid_restler.config.add_json_adapters

.. autofunction:: pyramid_restler.config.add_resource

.. autofunction:: pyramid_restler.config.add_resources

.. autofunction:: pyramid_restler.config.enable_cors

.. autofunction:: pyramid_restler.config.enable_post_tunneling

Settings
--------

.. autodata:: pyramid_restler.settings.DEFAULT_SETTINGS

.. autofunction:: pyramid_restler.settings.get_setting

Views
-----

.. autoclass:: pyramid_restler.view.ResourceView
   :members:

.. autoclass:: pyramid_restler.view.ResourceViewConfig
   :members:

Resources
---------

.. autoclass:: pyramid_restler.resource.Resource
   :members:

SQLAlchemy Resource Types
-------------------------

.. autoclass:: pyramid_restler.sqlalchemy.SQLAlchemyORMContainerResource
   :members:

.. autoclass:: pyramid_restler.sqlalchemy.SQLAlchemyORMItemResource
   :members:
