from collections import Iterable
import datetime
import decimal
import json

from pyramid.decorator import reify

from sqlalchemy.schema import Column
from sqlalchemy.util import NamedTuple

from zope.interface import implements

from pyramid_restler.interfaces import IContext


datetime_types = (datetime.time, datetime.date, datetime.datetime)


class DefaultJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        """Convert ``obj`` to something JSON encoder can handle."""
        if isinstance(obj, NamedTuple):
            obj = dict((k, getattr(obj, k)) for k in obj.keys())
        elif isinstance(obj, decimal.Decimal):
            obj = str(obj)
        elif isinstance(obj, datetime_types):
            obj = str(obj)
        return obj


class SQLAlchemyORMContext(object):
    """Adapts a SQLAlchemy ORM class to the
    :class:`pyramid_restler.interfaces.IContext` interface."""

    implements(IContext)

    json_encoder = DefaultJSONEncoder

    def __init__(self, request):
        self.request = request

    @reify
    def session(self):
        return self.session_factory()

    def session_factory(self):
        return self.request.db_session

    def get_collection(self):
        q = self.session.query(self.entity)
        return q.all()

    def get_member(self, id):
        q = self.session.query(self.entity)
        return q.get(id)

    def create_member(self, data):
        member = self.entity(**data)
        self.session.add(member)
        self.session.commit()
        return member

    def update_member(self, id, data):
        q = self.session.query(self.entity)
        member = q.get(id)
        if member is None:
            return None
        for name in data:
            setattr(member, name, data[name])
        self.session.commit()
        return member

    def delete_member(self, id):
        q = self.session.query(self.entity)
        member = q.get(id)
        if member is None:
            return None
        self.session.delete(member)
        self.session.commit()

    def get_member_id(self, member):
        pk = member._sa_instance_state.key
        if pk is None:
            return None
        vals = pk[1]
        if len(vals) == 1:
            return vals[0]
        else:
            return tuple(vals)

    def get_member_id_as_string(self, member):
        id = self.get_member_id(member)
        if isinstance(id, basestring):
            return id
        else:
            return json.dumps(id, cls=self.json_encoder)

    def to_json(self, value, fields=None, wrap=True):
        """Convert instance or sequence of instances to JSON.

        ``value`` is a single ORM instance or an iterable that yields
        instances.

        ``fields`` is a list of fields to include for each instance.

        ``wrap`` indicates whether or not the result should be wrapped or
        returned as-is.

        """
        if fields is None:
            fields = self.default_fields
        if isinstance(value, Iterable):
            result = [self.member_to_dict(m, fields) for m in value]
            result_count = len(result)
        else:
            result = self.member_to_dict(value, fields)
            result_count = 1
        if wrap:
            result = dict(
                results=result,
                result_count=result_count,
            )
        return json.dumps(result, cls=self.json_encoder)

    def member_to_dict(self, member, fields=None):
        if fields is None:
            fields = self.default_fields
        return dict((name, getattr(member, name)) for name in fields)

    @reify
    def default_fields(self):
        fields = []
        class_attrs = dir(self.entity)
        for name in class_attrs:
            if name.startswith('_'):
                continue
            attr = getattr(self.entity, name)
            if isinstance(attr, property):
                fields.append(name)
            else:
                try:
                    clause_el = attr.__clause_element__()
                except AttributeError:
                    pass
                else:
                    if issubclass(clause_el.__class__, Column):
                        fields.append(name)
        fields = set(fields)
        return fields
