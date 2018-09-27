import json
from unittest import TestCase

from pyramid.config import Configurator
from pyramid.events import NewRequest
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid.response import Response
from pyramid.testing import DummyRequest

from webob.acceptparse import create_accept_header

try:
    import sqlalchemy
except ImportError:  # pragma: no cover
    pass
else:
    from sqlalchemy.engine import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import Session
    from sqlalchemy.schema import Column
    from sqlalchemy.types import Integer, String

from zope.interface import implementer

from pyramid_restler.interfaces import IResource
from pyramid_restler.sqlalchemy import (
    configure, SQLAlchemyORMContainerResource, SQLAlchemyORMItemResource)
from pyramid_restler.view import ResourceView


class DummyRequest(DummyRequest):

    @property
    def json_body(self):
        return json.loads(self.body, encoding=self.charset)


Base = declarative_base()


class Model(Base):

    __tablename__ = 'entity'

    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)


ContainerResource = configure(SQLAlchemyORMContainerResource, model=Model, name='items', item_name='item')
ItemResource = configure(SQLAlchemyORMItemResource, model=Model, name='item')


class TestBase(TestCase):

    def setUp(self):
        # For each test, create a new database and populate it with a few
        # things. Then create a resource instance to be used by the test.
        engine = create_engine('sqlite://')
        session = Session(bind=engine)
        Base.metadata.create_all(bind=engine)
        session.add_all([
            Model(id=1, value='one'),
            Model(id=2, value='two'),
            Model(id=3, value='three'),
        ])
        session.commit()
        self.session = session

    def tearDown(self):
        self.session.query(Model).delete()
        self.session.commit()

    def make_request(self, json_body=None, **kwargs):
        if json_body:
            kwargs['body'] = json.dumps(json_body)
        request = DummyRequest(dbsession=self.session, **kwargs)
        return request

    def make_container_resource(self, **request_kwargs):
        request = self.make_request(**request_kwargs)
        container = ContainerResource(request)
        return container

    def make_item_resource(self, **request_kwargs):
        request = self.make_request(**request_kwargs)
        container = ItemResource(request)
        return container


class TestSQLAlchemyORMResources(TestBase):

    def test_interface(self):
        self.assertTrue(IResource.implementedBy(SQLAlchemyORMContainerResource))
        self.assertTrue(IResource.implementedBy(SQLAlchemyORMItemResource))
        self.assertTrue(IResource.providedBy(ContainerResource(DummyRequest())))
        self.assertTrue(IResource.providedBy(ItemResource(DummyRequest(matchdict={'id': 1}))))

    def test_get_from_container(self):
        resource = self.make_container_resource()
        items = resource.get()
        self.assertEqual(3, len(items))

    def test_get_item(self):
        resource = self.make_item_resource(matchdict={'id': 1})
        item = resource.get()
        self.assertEqual(item.id, 1)
        self.assertEqual(item.value, 'one')

    def test_get_nonexistent_item(self):
        resource = self.make_item_resource(matchdict={'id': 42})
        self.assertRaises(HTTPNotFound, resource.get)

    def test_create_item(self):
        resource = self.make_container_resource(
            method='POST', content_type='application/x-www-form-urlencoded', post={'value': 4})
        item = resource.post()
        retrieved_item = self.session.query(Model).get(item.id)
        self.assertEqual(retrieved_item, item)

    def test_create_item_json(self):
        resource = self.make_container_resource(
            method='POST', content_type='application/json', json_body={'value': 4})
        item = resource.post()
        retrieved_item = self.session.query(Model).get(item.id)
        self.assertEqual(retrieved_item, item)

    def test_update_item(self):
        item = self.session.query(Model).get(1)
        self.assertEqual('one', item.value)
        resource = self.make_item_resource(
            method='PATCH',
            content_type='application/json',
            json_body={'value': 'ONE'},
            matchdict={'id': 1},
        )
        item = resource.patch()
        self.assertEqual('ONE', item.value)

    def test_update_nonexistent_item(self):
        resource = self.make_item_resource(
            method='PATCH',
            content_type='application/json',
            json_body={'value': 'FORTY-TWO'},
            matchdict={'id': 42},
        )
        self.assertRaises(HTTPNotFound, resource.patch)

    def test_delete_item(self):
        item = self.session.query(Model).get(1)
        self.assertIsNotNone(item)

        resource = self.make_item_resource(method='DELETE',  matchdict={'id': 1})
        resource.delete()

        item = self.session.query(Model).get(1)
        self.assertIsNone(item)


class TestResourceView(TestBase):

    def test_get_items(self):
        request = self.make_request(path='/thing')
        view = ResourceView(ContainerResource(request), request)
        result = view.get()
        self.assertEqual(request.response.status_code, 200)
        self.assertEqual(result, {
            'items': [
                {'id': 1, 'value': 'one'},
                {'id': 2, 'value': 'two'},
                {'id': 3, 'value': 'three'},
            ]
        })

    def test_get_item(self):
        request = self.make_request(path='/thing/1.json', matchdict={'id': 1})
        view = ResourceView(ItemResource(request), request)
        result = view.get()
        self.assertEqual(request.response.status_code, 200)
        self.assertEqual(result, {'item': {'id': 1, 'value': 'one'}})

    def test_get_nonexistent_item(self):
        request = self.make_request(path='/thing/42.json', matchdict={'id': 42})
        view = ResourceView(ItemResource(request), request)
        self.assertRaises(HTTPNotFound, view.get)

    def test_post_item(self):
        request = self.make_request(
            method='POST', path='/thing', content_type='application/x-www-form-urlencoded',
            post={'value': 'four'})
        view = ResourceView(ContainerResource(request), request)
        result = view.post()
        self.assertEqual(result['item'], {'id': 4, 'value': 'four'})

    def test_post_item_from_json(self):
        request = self.make_request(
            method='POST', path='/thing', content_type='application/json',
            json_body={'value': 'four'})
        view = ResourceView(ContainerResource(request), request)
        result = view.post()
        self.assertEqual(request.response.status_code, 200)
        self.assertEqual(result['item'], {'id': 4, 'value': 'four'})

    def test_put_item(self):
        request = self.make_request(
            method='PUT', path='/thing/1', matchdict={'id': 1}, post={'value': 'ONE'},
            content_type='application/x-www-form-urlencoded')
        view = ResourceView(ItemResource(request), request)
        result = view.put()
        self.assertEqual(request.response.status_code, 200)
        self.assertEqual(result['item'], {'id': 1, 'value': 'ONE'})

    def test_put_new_item(self):
        request = self.make_request(
            method='PUT', path='/thing/42', matchdict={'id': 42}, post={'id': 42, 'value': '42'},
            content_type='application/x-www-form-urlencoded')
        view = ResourceView(ItemResource(request), request)
        result = view.put()
        self.assertEqual(request.response.status_code, 200)
        self.assertEqual(result['item'], {'id': 42, 'value': '42'})

    def test_delete_item(self):
        request = self.make_request(method='DELETE', path='/thing/1', matchdict={'id': 1})
        view = ResourceView(ItemResource(request), request)
        result = view.delete()
        self.assertEqual(request.response.status_code, 200)
        self.assertEqual(result['item'], {'id': 1, 'value': 'one'})

    def test_delete_nonexistent_item(self):
        request = self.make_request(
            method='DELETE', path='/thing/42', matchdict={'id': 42})
        view = ResourceView(ItemResource(request), request)
        self.assertRaises(HTTPNotFound, view.delete)


class TestAddResource(TestCase):

    def _make_config(self, autocommit=True, add_view=None):
        config = Configurator(autocommit=autocommit)
        if add_view is not None:
            config.add_view = add_view
        config.include('pyramid_restler')
        return config

    def _make_add_view(self):
        class AddView(object):
            def __init__(self):
                self.views = []

            def __call__(self, *args, **kwargs):
                self.views.append((args, kwargs))

            @property
            def count(self):
                return len(self.views)

        return AddView()

    def test_directive_registration(self):
        config = self._make_config()
        self.assertTrue(hasattr(config, 'add_resource'))
        self.assertTrue(hasattr(config, 'add_resources'))
        self.assertTrue(hasattr(config, 'enable_POST_tunneling'))

    def test_add_resource(self):
        config = self._make_config(add_view=self._make_add_view())

        # ContainerResource responds to only GET and POST
        config.add_resource('things', '/things', ContainerResource)
        self.assertEqual(2, config.add_view.count)

        # ItemResource responds to GET, DELETE, PATCH, and PUT
        config.add_resource('thing', '/thing', ItemResource)
        self.assertEqual(6, config.add_view.count)


class TestPOSTTunneling(TestCase):

    def _make_app(self):
        config = Configurator()
        config.include('pyramid_restler')
        config.enable_POST_tunneling()
        return config.make_wsgi_app()

    def test_POST_without_tunnel(self):
        app = self._make_app()
        request = DummyRequest(method='POST')
        self.assertEqual('POST', request.method)
        self.assertNotIn('$method', request.params)
        app.registry.notify(NewRequest(request))
        self.assertEqual('POST', request.method)
        self.assertNotIn('$method', request.params)

    def _assert_before(self, request):
        self.assertEqual('POST', request.method)

    def _assert_after(self, request, method):
        self.assertEqual(request.method, method)
        self.assertNotIn('$method', request.GET)
        self.assertNotIn('$method', request.POST)
        self.assertNotIn('X-HTTP-Method-Override', request.headers)

    def test_PUT_using_GET_param(self):
        app = self._make_app()
        request = DummyRequest(method='POST')
        request.GET = {'$method': 'PUT'}
        request.POST = {'$method': 'DUMMY'}
        request.headers['X-HTTP-Method-Override'] = 'DUMMY'
        self._assert_before(request)
        app.registry.notify(NewRequest(request))
        self._assert_after(request, 'PUT')

    def test_PUT_using_POST_param(self):
        app = self._make_app()
        request = DummyRequest(method='POST')
        request.POST = {'$method': 'PUT'}
        request.headers['X-HTTP-Method-Override'] = 'DUMMY'
        self._assert_before(request)
        app.registry.notify(NewRequest(request))
        self._assert_after(request, 'PUT')

    def test_PUT_using_header(self):
        app = self._make_app()
        request = DummyRequest(method='POST')
        request.headers['X-HTTP-Method-Override'] = 'PUT'
        self._assert_before(request)
        app.registry.notify(NewRequest(request))
        self._assert_after(request, 'PUT')

    def test_DELETE_using_POST_param(self):
        app = self._make_app()
        request = DummyRequest(method='POST')
        request.POST = {'$method': 'DELETE'}
        request.headers['X-HTTP-Method-Override'] = 'DUMMY'
        self._assert_before(request)
        app.registry.notify(NewRequest(request))
        self._assert_after(request, 'DELETE')

    def test_unknown_method_using_param(self):
        app = self._make_app()
        request = DummyRequest(params={'$method': 'PANTS'}, method='POST')
        self._assert_before(request)
        self.assertRaises(HTTPBadRequest, app.registry.notify, NewRequest(request))


def _dummy_resource_factory():

    @implementer(IResource)
    class Resource:

        _collection = [
            {'id': 1, 'val': 'one'},
            {'id': 2, 'val': 'two'},
            {'id': 3, 'val': 'three'},
        ]

        def __init__(self, request):
            self.request = request

        def _get_member_by_id(self, id):
            for m in self._collection:
                if m['id'] == id:
                    return m
            else:
                return None

        def get_collection(self, filters=None, **kwargs):
            collection = []
            if filters is not None:
                for m in self._collection:
                    if all(m[k] == v for k, v in filters.items()):
                        collection.append(m)
            return collection

        def get_member(self, id):
            return self._get_member_by_id(id)

        def create_member(self, data):
            next_id = max(m['id'] for m in self._collection) + 1
            member = {'id': next_id, 'val': data['val']}
            self._collection.append(member)
            return member

        def update_member(self, id, data):
            member = self._get_member_by_id(id)
            if member is None:
                return None
            for name in data:
                member[name] = data[name]
            return member

        def delete_member(self, id):
            for i, m in enumerate(self._collection):
                if m['id'] == id:
                    return self._collection.pop(i)
            return None

        def get_member_id_as_string(self, member):
            return str(member['id'])

        def to_json(self, value, fields=None, wrap=True):
            if isinstance(value, dict):
                value = [value]
            if fields:
                for i, r in enumerate(value):
                    value[i] = dict((k, r[k]) for k in fields)
            if wrap:
                response = dict(results=value)
            else:
                response = value
            return json.dumps(response)

    return Resource(DummyRequest())
