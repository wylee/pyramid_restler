import json
from unittest import TestCase

from pyramid.config import Configurator
from pyramid.events import NewRequest
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid.testing import DummyRequest

try:
    import sqlalchemy  # noqa: F401
except ImportError:
    pass
else:
    from sqlalchemy.engine import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import Session
    from sqlalchemy.schema import Column
    from sqlalchemy.types import Integer, String

from pyramid_restler.sqlalchemy import (
    SQLAlchemyContainerResource,
    SQLAlchemyItemResource,
)
from pyramid_restler.view import ResourceView


class DummyRequest(DummyRequest):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.registry.settings = {}

    @property
    def json_body(self):
        return json.loads(self.body)


Base = declarative_base()


class Item(Base):

    __tablename__ = "entity"

    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)


class ContainerResource(SQLAlchemyContainerResource):

    model = Item


class ItemResource(SQLAlchemyItemResource):

    model = Item


class TestBase(TestCase):
    def setUp(self):
        # For each test, create a new database and populate it with a few
        # things. Then create a resource instance to be used by the test.
        engine = create_engine("sqlite://")
        session = Session(bind=engine)
        Base.metadata.create_all(bind=engine)
        session.add_all(
            [
                Item(id=1, value="one"),
                Item(id=2, value="two"),
                Item(id=3, value="three"),
            ]
        )
        session.commit()
        self.session = session

    def tearDown(self):
        self.session.query(Item).delete()
        self.session.commit()

    def make_request(self, json_body=None, **kwargs):
        if json_body:
            kwargs["body"] = json.dumps(json_body)
        request = DummyRequest(dbsession=self.session, **kwargs)
        return request


class TestSQLAlchemyContainerResource(TestBase):
    def make_resource(self, **request_kwargs):
        request = self.make_request(**request_kwargs)
        return ContainerResource(request)

    def test_create(self):
        resource = self.make_resource(
            method="POST",
            content_type="application/x-www-form-urlencoded",
            post={"value": 4},
        )
        data = resource.post()
        self.assertIn("item", data)
        item = data["item"]
        retrieved_item = self.session.query(Item).get(item.id)
        self.assertEqual(retrieved_item, item)

    def test_create_json(self):
        resource = self.make_resource(
            method="POST", content_type="application/json", json_body={"value": 4},
        )
        data = resource.post()
        self.assertIn("item", data)
        item = data["item"]
        retrieved_item = self.session.query(Item).get(item.id)
        self.assertEqual(retrieved_item, item)

    def test_get(self):
        resource = self.make_resource()
        data = resource.get()
        self.assertIn("items", data)
        items = data["items"]
        self.assertEqual(3, len(items))


class TestSQLAlchemyItemResource(TestBase):
    def make_resource(self, **request_kwargs):
        request = self.make_request(**request_kwargs)
        return ItemResource(request)

    def test_get(self):
        resource = self.make_resource(matchdict={"id": "1"})
        data = resource.get()
        self.assertIn("item", data)
        item = data["item"]
        self.assertEqual(item["id"], 1)
        self.assertEqual(item["value"], "one")

    def test_get_nonexistent(self):
        resource = self.make_resource(matchdict={"id": "42"})
        self.assertRaises(HTTPNotFound, resource.get)

    def test_update(self):
        item = self.session.query(Item).get(1)
        self.assertEqual("one", item.value)
        resource = self.make_resource(
            method="PATCH",
            content_type="application/json",
            json_body={"value": "ONE"},
            matchdict={"id": "1"},
        )
        data = resource.patch()
        self.assertIn("item", data)
        item = data["item"]
        self.assertEqual("ONE", item.value)

    def test_update_nonexistent(self):
        resource = self.make_resource(
            method="PATCH",
            content_type="application/json",
            json_body={"value": "FORTY-TWO"},
            matchdict={"id": "42"},
        )
        self.assertRaises(HTTPNotFound, resource.patch)

    def test_delete(self):
        item = self.session.query(Item).get(1)
        self.assertIsNotNone(item)
        resource = self.make_resource(method="DELETE", matchdict={"id": "1"})
        resource.delete()
        item = self.session.query(Item).get(1)
        self.assertIsNone(item)


class TestContainerResourceView(TestBase):
    def test_get(self):
        request = self.make_request(path="/things")
        view = ResourceView(ContainerResource(request), request)
        data = view.get()
        self.assertEqual(request.response.status_code, 200)
        self.assertIn("items", data)
        items = data["items"]
        for i, item in enumerate(items, 1):
            self.assertEqual(item["id"], i)

    def test_post(self):
        request = self.make_request(
            method="POST",
            path="/things",
            content_type="application/x-www-form-urlencoded",
            post={"value": "four"},
        )
        view = ResourceView(ContainerResource(request), request)
        data = view.post()
        self.assertEqual(request.response.status_code, 200)
        self.assertIn("item", data)
        item = data["item"]
        self.assertEqual(item.id, 4)
        self.assertEqual(item.value, "four")

    def test_post_json(self):
        request = self.make_request(
            method="POST",
            path="/things",
            content_type="application/json",
            json_body={"value": "four"},
        )
        view = ResourceView(ContainerResource(request), request)
        data = view.post()
        self.assertEqual(request.response.status_code, 200)
        self.assertIn("item", data)
        item = data["item"]
        self.assertEqual(item.id, 4)
        self.assertEqual(item.value, "four")


class TestItemResourceView(TestBase):
    def test_get(self):
        request = self.make_request(path="/thing/1.json", matchdict={"id": "1"})
        view = ResourceView(ItemResource(request), request)
        data = view.get()
        self.assertEqual(request.response.status_code, 200)
        self.assertIn("item", data)
        item = data["item"]
        self.assertEqual(item["id"], 1)
        self.assertEqual(item["value"], "one")

    def test_get_nonexistent(self):
        request = self.make_request(path="/thing/42.json", matchdict={"id": "42"})
        view = ResourceView(ItemResource(request), request)
        self.assertRaises(HTTPNotFound, view.get)

    def test_put(self):
        request = self.make_request(
            method="PUT",
            path="/thing/1",
            matchdict={"id": "1"},
            post={"value": "ONE"},
            content_type="application/x-www-form-urlencoded",
        )
        view = ResourceView(ItemResource(request), request)
        data = view.put()
        self.assertEqual(request.response.status_code, 200)
        self.assertIn("item", data)
        item = data["item"]
        self.assertEqual(item.id, 1)
        self.assertEqual(item.value, "ONE")

    def test_put_new(self):
        request = self.make_request(
            method="PUT",
            path="/thing/42",
            matchdict={"id": "42"},
            post={"id": "42", "value": "42"},
            content_type="application/x-www-form-urlencoded",
        )
        view = ResourceView(ItemResource(request), request)
        data = view.put()
        self.assertEqual(request.response.status_code, 200)
        self.assertIn("item", data)
        item = data["item"]
        self.assertEqual(item.id, 42)
        self.assertEqual(item.value, "42")

    def test_delete(self):
        request = self.make_request(
            method="DELETE", path="/thing/1", matchdict={"id": "1"}
        )
        view = ResourceView(ItemResource(request), request)
        data = view.delete()
        self.assertEqual(request.response.status_code, 200)
        self.assertIn("item", data)
        item = data["item"]
        self.assertEqual(item.id, 1)
        self.assertEqual(item.value, "one")

    def test_delete_nonexistent(self):
        request = self.make_request(
            method="DELETE", path="/thing/42", matchdict={"id": "42"}
        )
        view = ResourceView(ItemResource(request), request)
        self.assertRaises(HTTPNotFound, view.delete)


class TestAddResource(TestCase):
    def _make_config(self, autocommit=True, with_add_view=True):
        config = Configurator(autocommit=autocommit)
        config.add_view = self._make_add_view(config)
        config.include("pyramid_restler")
        return config

    def _make_add_view(self, config):
        class AddView(object):
            def __init__(self, original_add_view):
                self.views = []
                self.original_add_view = original_add_view

            def __call__(self, *args, **kwargs):
                self.views.append((args, kwargs))
                self.original_add_view(*args, **kwargs)

            @property
            def count(self):
                return len(self.views)

        return AddView(config.add_view)

    def test_directive_registration(self):
        config = self._make_config()
        self.assertTrue(hasattr(config, "add_json_adapters"))
        self.assertTrue(hasattr(config, "add_resource"))
        self.assertTrue(hasattr(config, "add_resources"))
        self.assertTrue(hasattr(config, "enable_cors"))
        self.assertTrue(hasattr(config, "enable_post_tunneling"))

    def test_add_container_resource(self):
        config = self._make_config()
        config.add_resource(ContainerResource)
        self.assertEqual(10, config.add_view.count)

    def test_add_item_resource(self):
        config = self._make_config()
        config.add_resource(ItemResource)
        self.assertEqual(10, config.add_view.count)


class TestPOSTTunneling(TestCase):
    def _make_app(self):
        config = Configurator()
        config.include("pyramid_restler")
        config.enable_post_tunneling()
        return config.make_wsgi_app()

    def test_post_without_tunnel(self):
        app = self._make_app()
        request = DummyRequest(method="POST")
        self.assertEqual("POST", request.method)
        self.assertNotIn("$method", request.params)
        app.registry.notify(NewRequest(request))
        self.assertEqual("POST", request.method)
        self.assertNotIn("$method", request.params)

    def _assert_before(self, request):
        self.assertEqual("POST", request.method)

    def _assert_after(self, request, method):
        self.assertEqual(request.method, method)
        self.assertNotIn("$method", request.GET)
        self.assertNotIn("$method", request.POST)
        self.assertNotIn("X-HTTP-Method-Override", request.headers)

    def test_put_using_get_param(self):
        app = self._make_app()
        request = DummyRequest(method="POST")
        request.GET = {"$method": "PUT"}
        request.POST = {"$method": "DUMMY"}
        request.headers["X-HTTP-Method-Override"] = "DUMMY"
        self._assert_before(request)
        app.registry.notify(NewRequest(request))
        self._assert_after(request, "PUT")

    def test_put_using_post_param(self):
        app = self._make_app()
        request = DummyRequest(method="POST")
        request.POST = {"$method": "PUT"}
        request.headers["X-HTTP-Method-Override"] = "DUMMY"
        self._assert_before(request)
        app.registry.notify(NewRequest(request))
        self._assert_after(request, "PUT")

    def test_put_using_header(self):
        app = self._make_app()
        request = DummyRequest(method="POST")
        request.headers["X-HTTP-Method-Override"] = "PUT"
        self._assert_before(request)
        app.registry.notify(NewRequest(request))
        self._assert_after(request, "PUT")

    def test_delete_using_post_param(self):
        app = self._make_app()
        request = DummyRequest(method="POST")
        request.POST = {"$method": "DELETE"}
        request.headers["X-HTTP-Method-Override"] = "DUMMY"
        self._assert_before(request)
        app.registry.notify(NewRequest(request))
        self._assert_after(request, "DELETE")

    def test_unknown_method_using_param(self):
        app = self._make_app()
        request = DummyRequest(params={"$method": "PANTS"}, method="POST")
        self._assert_before(request)
        self.assertRaises(HTTPBadRequest, app.registry.notify, NewRequest(request))
