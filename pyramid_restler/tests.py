import json
from unittest import TestCase

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid.response import Response
from pyramid.testing import DummyRequest

try:
    import sqlalchemy
except ImportError:
    pass
else:
    from sqlalchemy.engine import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import Session
    from sqlalchemy.schema import Column
    from sqlalchemy.types import Integer, String

from zope.interface import implements

from pyramid_restler.interfaces import IContext
from pyramid_restler.model import SQLAlchemyORMContext
from pyramid_restler.view import RESTfulView


class Test_SQLAlchemyORMContext(TestCase):

    def setUp(self):
        # For each test, create a new database and populate it with a few
        # things. Then create a context instance to be used by the test.
        engine = create_engine('sqlite://')
        session = Session(bind=engine)
        Base = declarative_base()
        class Entity(Base):
            __tablename__ = 'entity'
            id = Column(Integer, primary_key=True)
            value = Column(String)
        Base.metadata.create_all(bind=engine)
        session.add_all([
            Entity(id=1, value='one'),
            Entity(id=2, value='two'),
            Entity(id=3, value='three'),
        ])
        session.commit()
        class ContextFactory(SQLAlchemyORMContext):
            entity = Entity
        request = DummyRequest()
        request.db_session = session
        self.context = ContextFactory(request)

    def test_interface(self):
        self.assertTrue(IContext.implementedBy(SQLAlchemyORMContext))
        self.assertTrue(IContext.providedBy(self.context))

    def test_get_collection(self):
        collection = self.context.get_collection()
        self.assertEqual(3, len(collection))

    def test_get_member(self):
        member = self.context.get_member(1)
        self.assertEqual(member.id, 1)
        self.assertEqual(member.value, 'one')

    def test_get_nonexistent_member(self):
        member = self.context.get_member(42)
        self.assert_(member is None)

    def test_collection_to_json(self):
        collection = self.context.get_collection()
        json_collection = self.context.to_json(collection)
        self.assertTrue(isinstance(json_collection, basestring))
        should_equal = [
            {'id': 1, 'value': 'one'},
            {'id': 2, 'value': 'two'},
            {'id': 3, 'value': 'three'},
        ]
        self.assertEqual(json.loads(json_collection)['results'], should_equal)

    def test_member_to_json(self):
        member = self.context.get_member(1)
        json_member = self.context.to_json(member)
        self.assertTrue(isinstance(json_member, basestring))
        should_equal = {'id': 1, 'value': 'one'}
        self.assertEqual(json.loads(json_member)['results'], should_equal)


class Test_RESTfulView(TestCase):

    def test_get_collection(self):
        request = DummyRequest(path='/thing.json')
        request.matchdict = {'renderer': 'json'}
        view = RESTfulView(_dummy_context_factory(), request)
        response = view.get_collection()
        self.assertTrue(isinstance(response, Response))

    def test_get_member(self):
        request = DummyRequest(path='/thing/1.json')
        request.matchdict = {'id': 1, 'renderer': 'json'}
        view = RESTfulView(_dummy_context_factory(), request)
        response = view.get_member()
        self.assertTrue(isinstance(response, Response))
        self.assertEqual(response.status_int, 200)

    def test_create_member(self):
        request = DummyRequest(path='/thing', post={'val': 'four'})
        view = RESTfulView(_dummy_context_factory(), request)
        response = view.create_member()
        self.assertTrue(isinstance(response, Response))
        self.assertEqual(response.status_int, 201)

    def test_update_member(self):
        request = DummyRequest(method='PUT', path='/thing/1', post={'val': 'ONE'})
        request.matchdict = {'id': 1}
        view = RESTfulView(_dummy_context_factory(), request)
        response = view.update_member()
        self.assertTrue(isinstance(response, Response))
        self.assertEqual(response.status_int, 204)

    def test_delete_member(self):
        request = DummyRequest(method='DELETE', path='/thing/1')
        request.matchdict = {'id': 1, 'renderer': 'json'}
        view = RESTfulView(_dummy_context_factory(), request)
        response = view.delete_member()
        self.assertTrue(isinstance(response, Response))
        self.assertEqual(response.status_int, 204)
        self.assertRaises(HTTPNotFound, view.get_member)

    def test_get_nonexistent_member_should_raise_404(self):
        request = DummyRequest(path='/thing/42.json')
        request.matchdict = {'id': 42, 'renderer': 'json'}
        view = RESTfulView(_dummy_context_factory(), request)
        self.assertRaises(HTTPNotFound, view.get_member)

    def test_get_member_specific_fields(self):
        request = DummyRequest(path='/thing/1.json', params={'fields': '["id"]'})
        request.matchdict = {'id': 1, 'renderer': 'json'}
        view = RESTfulView(_dummy_context_factory(), request)
        response = view.get_member()
        member = json.loads(response.body)['results'][0]
        self.assert_(member.keys() == ['id'])

    def test_unknown_renderer_should_raise_400(self):
        request = DummyRequest(path='/thing/1.xyz')
        request.matchdict = {'id': 1, 'renderer': 'xyz'}
        view = RESTfulView(_dummy_context_factory(), request)
        self.assertRaises(HTTPBadRequest, view.get_member)


class Test_add_restful_routes(TestCase):

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
            def __call__(self, **kw):
                self.views.append(kw)
            def count(self):
                return len(self.views)
        return AddView()

    def test_directive_registration(self):
        config = self._make_config()
        self.assertTrue(hasattr(config, 'add_restful_routes'))

    def test_add_restful_routes(self):
        config = self._make_config(add_view=self._make_add_view())
        config.add_restful_routes('thing', _dummy_context_factory())
        self.assertEqual(5, config.add_view.count())


def _dummy_context_factory():

    class Context(object):

        implements(IContext)

        _collection = [
            {'id': 1, 'val': 'one'},
            {'id': 2, 'val': 'two'},
            {'id': 3, 'val': 'three'},
        ]

        def _get_member_by_id(self, id):
            for m in self._collection:
                if m['id'] == id:
                    return m
            else:
                return None

        def get_collection(self):
            return self._collection

        def get_member(self, id):
            return self._get_member_by_id(id)

        def create_member(self, **data):
            next_id = max(m['id'] for m in self._collection) + 1
            member = {'id': next_id, 'val': data['val']}
            return member

        def update_member(self, id, **data):
            member = self._get_member_by_id(id)
            if member is None:
                return None
            for name in data:
                member[name] == data[name]
            return member

        def delete_member(self, id):
            for i, m in enumerate(self._collection):
                if m['id'] == id:
                    self._collection.pop(i)
            return None

        def to_json(self, value, fields=None, wrap=True):
            if isinstance(value, dict):
                value = [value]
            if fields:
                for i, r in enumerate(value):
                    value[i] = dict((k, r[k]) for k in fields)
            if wrap:
                response = dict(results=value)
            return json.dumps(response)

    return Context()
