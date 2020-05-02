"""SQLAlchemy ORM Example

To run this example, first install pyramid_restler and SQLAlchemy
(preferably in a virtualenv). Once that's done, change into the
``examples/`` directory and run this::

    python sqlalchemy_example.py

Then open http://localhost:6543/ in your browser. From there, you can
play around with CRUD from a very simple UI.

Note: a temporary SQLite database named ``example.db`` will be created
in the ``examples/`` directory the first time this example is run. On
subsequent runs, if this database already exists, all of its tables will
be dropped and recreated.

"""
from pathlib import Path
from wsgiref.simple_server import make_server

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


class Thing(Base):

    __tablename__ = "my_thing"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String)

    def __json__(self, _request):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
        }


class ThingsResource(SQLAlchemyContainerResource):

    model = Thing


class ThingResource(SQLAlchemyItemResource):

    model = Thing


def root_view(request):
    things = request.dbsession.query(Thing).all()
    return {
        "things": things,
        "model": Thing,
    }


def main():
    here = Path(__file__).parent.absolute()

    settings = {"mako.directories": str(here)}

    db_path = here / "example.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    create_and_populate_database(engine)

    def db_session_factory(request):
        return Session()

    config = Configurator(settings=settings)

    config.include("pyramid_mako")
    config.include("pyramid_restler")

    config.add_request_method(db_session_factory, "dbsession", reify=True)

    config.add_route("root", "/")
    config.add_view(route_name="root", view=root_view, renderer="example.mako")

    # These are the pyramid_restler bits
    config.add_resource(ThingsResource, name="things")
    config.add_resource(ThingResource, name="thing", id_field="id")
    config.enable_post_tunneling()

    app = config.make_wsgi_app()

    print("View app at https://localhost:6543/")
    server = make_server("0.0.0.0", 6543, app)
    server.serve_forever()


def create_and_populate_database(engine):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    engine.execute(
        Thing.__table__.insert(),
        dict(title="One", description="First"),
        dict(title="Two", description="Second"),
        dict(title="Three", description="Third"),
    )


if __name__ == "__main__":
    main()
