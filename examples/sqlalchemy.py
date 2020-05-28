"""SQLAlchemy ORM Example

To run this example, first run ``poetry install``, which will install
the necessary development dependencies. The run the following command
from the top level ``pyramid_restler`` directory::

    PYTHONPATH=. pserve -n sqlalchemy --reload examples/example.ini

Then open http://localhost:6543/ in your browser. From there, you can
play around with CRUD from a very simple UI.

A temporary SQLite database named ``example.db`` will be created in the
``examples`` directory the first time this example is run. On subsequent
runs, if this database already exists, all of its tables will be dropped
and recreated.

"""
from pyramid.config import Configurator

from pyramid_restler.sqlalchemy import (
    SQLAlchemyContainerResource,
    SQLAlchemyItemResource,
)

from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String


Base = declarative_base()


class Item(Base):

    __tablename__ = "item"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String)

    def __json__(self, _request):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
        }


class ContainerResource(SQLAlchemyContainerResource):

    model = Item


class ItemResource(SQLAlchemyItemResource):

    model = Item


def root_view(request):
    items = request.dbsession.query(Item).all()
    return {
        "items": items,
        "model": Item,
    }


def main(global_config, **settings):
    engine = create_engine(f"sqlite:///{settings['db.path']}")
    Session = sessionmaker(bind=engine)
    create_and_populate_database(engine)

    def db_session_factory(request):
        return Session()

    config = Configurator(settings=settings)

    with config:
        config.include("pyramid_mako")
        config.include("pyramid_restler")

        config.add_request_method(db_session_factory, "dbsession", reify=True)

        # These are the pyramid_restler bits
        config.add_resource(
            ContainerResource,
            name="root",
            path="/",
            renderers=["json", "example.mako"],
        )
        config.add_resource(ContainerResource, renderers=["json", "example.mako"])
        config.add_resource(ItemResource, id_field="id")
        config.enable_post_tunneling()

    return config.make_wsgi_app()


def create_and_populate_database(engine):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    engine.execute(
        Item.__table__.insert(),
        dict(title="One", description="First"),
        dict(title="Two", description="Second"),
        dict(title="Three", description="Third"),
    )
