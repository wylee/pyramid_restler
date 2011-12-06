from collections import Iterable
import datetime
import decimal
import json

from pyramid.decorator import reify

from pyramid_restler.interfaces import ICollectionContext, IMemberContext

from sqlalchemy.orm import object_session
from sqlalchemy.schema import Column
from sqlalchemy.util import NamedTuple

from zope.component import adapts
from zope.interface import implements


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


class RootFactory(object):

    def __getitem__(self, name):
        parts = name.rsplit('.', 1)
        if len(parts) == 2:
            name, self.request.renderer = parts
        collection = self.collections[name](self.request)
        collection.__name__ = name
        collection.__parent__ = self
        return collection


class MemberContext(object):

    implements(IMemberContext)
    adapts(ISQLAlchemyMember)

    def __init__(self, request, member):
        self.request = request
        self.member = member

    @reify
    def id(self):
        pk = self.member._sa_instance_state.key
        if pk is None:
            return None
        vals = pk[1]
        if len(vals) == 1:
            return vals[0]
        else:
            return tuple(vals)

    @reify
    def id_as_string(self):
        if isinstance(self.id, basestring):
            return self.id
        else:
            return json.dumps(self.id, cls=DefaultJSONEncoder)

    def update(self, data):
        session = object_session(self.member)
        for name in data:
            setattr(self.member, name, data[name])
        session.commit()
        return self.member

    def delete(self):
        session = object_session(self.member)
        session.delete(self.member)
        session.commit()

    def to_dict(self, fields=None):
        if fields is None:
            fields = self.get_default_fields()
        return dict((name, getattr(self.member, name)) for name in fields)

    def to_json(self, fields=None, wrap=True):
        obj = self.get_json_obj(fields, wrap)
        return json.dumps(obj, cls=DefaultJSONEncoder)

    def get_json_obj(self, fields, wrap):
        obj = [self.to_dict(fields)]
        if wrap:
            obj = self.__parent__.wrap_json_obj(obj)
        return obj

    @classmethod
    def get_default_fields(cls):
        if not hasattr(cls, '_default_fields'):
            fields = []
            class_attrs = dir(cls.entity)
            for name in class_attrs:
                if name.startswith('_'):
                    continue
                attr = getattr(cls.entity, name)
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
            cls._default_fields = set(fields)
        return cls._default_fields


class CollectionContext(object):

    implements(ICollectionContext)
    adapts(ISQLAlchemyMember)

    member_context = MemberContext

    def __init__(self, request):
        self.request = request

    def create(self, data):
        member = self.entity(**data)
        self.session.add(member)
        self.session.commit()
        return member

    @reify
    def session(self):
        return self.session_factory()

    def session_factory(self):
        return self.request.db_session

    @reify
    def entity(self):
        return self.member_context.entity

    def __getitem__(self, id):
        q = self.session.query(self.entity)
        member = q.get(id)
        if member is None:
            if self.request.method == 'PUT':
                return self.__class__(self.request)
            else:
                raise KeyError(id)
        context = self.member_context(self.request, member)
        context.__name__ = id
        context.__parent__ = self
        return context

    def fetch(self):
        q = self.session.query(self.entity)

        modifiers = self.request.params.get('$$', {})
        if modifiers:
            modifiers = json.loads(modifiers)

        # XXX: Handle joined loads here?

        # Apply "global" (i.e., every request) filters
        if hasattr(self, 'filters'):
            for f in self.filters:
                q = q.filter(f)

        for k, v in (modifiers.get('filters', {})).items():
            #v = self.convert_param(k, v)
            filter_method = getattr(self.entity, '{0}_filter'.format(k), None)
            if filter_method is not None:
                # Prefer a method that returns something that can be passed
                # into `Query.filter()`.
                q = q.filter(filter_method(v))
            else:
                q = q.filter_by(**{k: v})

        if modifiers.get('distinct'):
            q = q.distinct()
        if 'order_by' in modifiers:
            q = q.order_by(*modifiers['order_by'])
        if 'offset' in modifiers:
            q = q.offset(modifiers['offset'])
        if 'limit' in modifiers:
            q = q.limit(modifiers['limit'])

        return iter(q)

    def to_json(self, fields=None, wrap=True):
        """Convert collection to JSON.

        ``fields`` is a list of fields to include for each instance.

        ``wrap`` indicates whether or not the result should be wrapped or
        returned as-is.

        """
        obj = self.get_json_obj(fields, wrap)
        return json.dumps(obj, cls=DefaultJSONEncoder)

    def get_json_obj(self, fields, wrap):
        obj = [self.member_context(self.request, m).to_dict(fields) for m in self.fetch()]
        if wrap:
            obj = self.wrap_json_obj(obj)
        return obj

    def wrap_json_obj(self, obj):
        return dict(
            results=obj,
            result_count=len(obj),
        )
