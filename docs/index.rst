pyramid_restler
+++++++++++++++

Overview
========

`pyramid_restler` is a somewhat-opinionated toolkit for building
resourceful Web services and applications on top of the Pyramid
framework.

Routes
======

A Pyramid configuration directive is provided that makes generating the
various routes and views for a resource easy::

    config.add_resource(ThingsResource, "things")

 This will generate a set of routes and views for the resource:

    HTTP method => view method => resource method

    DELETE /things => delete() => delete()
    GET /things => get() => get()
    PATCH /things =>  patch() => patch()
    POST /things =>  post() => post()
    PUT /things => put() => put()

Views
=====

Resource views are implemented as a standard set of HTTP methods in view
classes. See :class:`pyramid_restler.view.ResourceView` as an example.

Resources
=========

Resource views interact with a resource. A common example of such a
resource is a database table that's mapped to a SQLAlchemy ORM class.

:class:`pyramid_restler.sqlalchemy.SQLAlchemyContainerResource` and
:class:`pyramid_restler.sqlalchemy.SQLAlchemyItemResource` classes are
provided as a starting point.

The purpose of the resource layer is to provide a uniform interface to
any kind of resource. This way, the view layer can be written in a
generic manner.

More Info
=========

.. toctree::
   :maxdepth: 1

   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
