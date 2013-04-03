from collections import Iterable
import datetime
import decimal
import json

from pyramid.decorator import reify

from sqlalchemy.schema import Column
from sqlalchemy.util import KeyedTuple as NamedTuple

from zope.interface import implementer

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

@implementer(IContext)
class SQLAlchemyORMContext(object):
    """Adapts a SQLAlchemy ORM class to the
    :class:`pyramid_restler.interfaces.IContext` interface."""

    json_encoder = DefaultJSONEncoder

    def __init__(self, request):
        self.request = request

    @reify
    def session(self):
        return self.session_factory()

    def session_factory(self):
        return self.request.db_session

    def get_collection(self, distinct=False, order_by=None, limit=None,
                       offset=None, filters=None):
        """Get the entire collection or a subset of it.

        By default, this will fetch all records for :attr:`entity`. Various
        types of filtering can be applied to instead fetch a subset.

        The simplest "filter" is LIMIT. This can be used by itself or in
        conjunction with other filters.

        There are two types of filters that can be applied: global filters
        that will be applied to *all* queries of this collection and
        per-query filters.

        Global filters are specified by the :attr:`filters` attribute.
        Generally, it will be a class-level attribute, but an instance can
        also set `filters` (perhaps to disable the global defaults). The
        items in the `filters` list can be anything that can be passed into
        SQLAlchemy's `Query.filter` method.

        Per-query filters are specified by passing a `dict` of filters via
        the ``filters`` keyword arg. A key in the `dict` names either a
        method on the entity that is named as {key}_filter *or* an `entity`
        attribute. In the first case, the {key}_filter method is expected to
        return a filter that can be passed into `Query.filter`. In the
        second case, a simple `filter_by(key=value)` is applied to the
        query.

        """
        q = self.session.query(self.entity)

        # XXX: Handle joined loads here?

        # Apply "global" (i.e., every request) filters
        if hasattr(self, 'filters'):
            for f in self.filters:
                q = q.filter(f)

        for k, v in (filters or {}).items():
            #v = self.convert_param(k, v)
            filter_method = getattr(self.entity, '{0}_filter'.format(k), None)
            if filter_method is not None:
                # Prefer a method that returns something that can be passed
                # into `Query.filter()`.
                q = q.filter(filter_method(v))
            else:
                q = q.filter_by(**{k: v})

        if distinct:
            q = q.distinct()
        if order_by is not None:
            q = q.order_by(*order_by)
        if offset is not None:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)

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
        member = self.get_member(id)
        if member is None:
            return None
        for name in data:
            setattr(member, name, data[name])
        self.session.commit()
        return member

    def delete_member(self, id):
        member = self.get_member(id)
        if member is None:
            return None
        self.session.delete(member)
        self.session.commit()
        return member

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
        obj = self.get_json_obj(value, fields, wrap)
        return json.dumps(obj, cls=self.json_encoder)

    def get_json_obj(self, value, fields, wrap):
        if fields is None:
            fields = self.default_fields
        if not isinstance(value, Iterable):
            value = [value]
        obj = [self.member_to_dict(m, fields) for m in value]
        if wrap:
            obj = self.wrap_json_obj(obj)
        return obj

    def wrap_json_obj(self, obj):
        return dict(
            results=obj,
            result_count=len(obj),
        )

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
