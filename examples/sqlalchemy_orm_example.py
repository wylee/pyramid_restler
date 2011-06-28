"""
SQLAlchemy ORM Example
======================

To run this example, first install pyramid_restler and SQLAlchemy (perhaps
in a virtualenv). Once that's done, cd into the examples/ directory, run
`python sqlalchemy_orm_example.py`, and open http://localhost:5000/ in
your browser. From there, you can play around with CRUD from a very simple
UI.

Note: a temporary SQLite database is created in the current working
directory every time this module is run; it is removed automatically when
the server is shut down normally (e.g., via Ctrl-C). The `DB_NAME` global
specifies the name of this database.

"""
import os

from paste.httpserver import serve

from pyramid.config import Configurator

from pyramid_restler.model import SQLAlchemyORMContext

from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String


DB_NAME = 'pyramid_restler_example.db'

engine = create_engine('sqlite:///{0}'.format(DB_NAME))
Session = sessionmaker(bind=engine)
Base = declarative_base(bind=engine)


class MyThing(Base):

    __tablename__ = 'my_thing'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String)


class MyThingContextFactory(SQLAlchemyORMContext):

    entity = MyThing

    def session_factory(self):
        return Session()


def root_view(context, request):
    things = Session().query(MyThing).all()
    return dict(things=things, Thing=MyThing)


def main(**settings):
    create_and_populate_database()
    config = Configurator(settings=settings)
    config.add_route('root', '/')
    config.add_view(route_name='root', view=root_view, renderer='example.mako')
    config.include('pyramid_restler')
    config.add_restful_routes('thing', MyThingContextFactory)
    config.enable_POST_tunneling()
    return config.make_wsgi_app()


def create_and_populate_database():
    Base.metadata.create_all()
    session = Session()
    session.add_all([
        MyThing(title='One'),
        MyThing(title='Two'),
        MyThing(title='Three'),
    ])
    session.commit()


if __name__ == '__main__':
    settings = {'mako.directories': '.'}
    app = main(**settings)
    serve(app, host='0.0.0.0', port=5000)
    os.remove(DB_NAME)
