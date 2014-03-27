"""
SQLAlchemy ORM Example
======================

To run this example, first install pyramid_restler, waitress, and
SQLAlchemy (preferably in a virtualenv). Once that's done, change into
the examples/ directory, run `pserve --app-name sqlalchemy_orm
example.ini`, and then open http://localhost:5000/ in your browser. From
there, you can play around with CRUD from a very simple UI.

Note: a temporary SQLite database named pyramid_reslter_example.db will
be created in the examples/ directory the first time this example is
run. On subsequent runs, if this database already exists, all of its
tables will be dropped and recreated.

"""
from pyramid.config import Configurator

from pyramid_restler.model import SQLAlchemyORMContext

from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String


Base = declarative_base()


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


def main(global_config, **settings):
    db_path = settings['db_path']
    print('Temporary SQLite database created at {0}.'.format(db_path))

    global Session
    engine = create_engine('sqlite:///{0}'.format(db_path))
    Session = sessionmaker(bind=engine)
    create_and_populate_database(engine)

    config = Configurator(settings=settings)
    config.add_route('root', '/')
    config.add_view(route_name='root', view=root_view, renderer='example.mako')
    config.add_restful_routes('thing', MyThingContextFactory)
    config.enable_POST_tunneling()
    return config.make_wsgi_app()


def create_and_populate_database(engine):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    engine.execute(
        MyThing.__table__.insert(),
        dict(title='One', description='First'),
        dict(title='Two', description='Second'),
        dict(title='Three', description='Third'),
    )
