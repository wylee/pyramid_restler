import json
from math import ceil as ceiling
from typing import Sequence

from pyramid.httpexceptions import exception_response, HTTPNotFound

from sqlalchemy import inspect
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_, or_

from .settings import get_setting
from .util import extract_data, get_param


from .resource import Resource


class SQLAlchemyResource(Resource):

    joined_load_with = ()

    @property
    def model(self):
        """SQLAlchemy ORM class."""
        raise NotImplementedError("model property must be implemented in subclasses")

    @property
    def model_adapter(self):
        """Adapter for ORM instances.

        Can be any callable that takes an ORM instance and the current
        request and returns a suitable object. Adaptation will happen
        after items are fetched and before fields are extracted.

        """
        return get_setting(
            self.request.registry.settings, "default_model_adapter", default=None
        )

    @property
    def key(self):
        """Key used to refer to item or items in returned data."""
        raise NotImplementedError("key property must be implemented in subclasses")

    def __init__(self, request):
        super().__init__(request)
        self.dbsession = request.dbsession

    def default_response_fields(self, item):
        """Get default fields to include in response."""
        model = self.model
        request = self.request
        settings = request.registry.settings
        getter = get_setting(settings, "default_response_fields", default=None)
        if getter:
            return getter(self, model, item, request)
        return self.default_default_response_fields(model, item, request)

    def default_default_response_fields(self, model, item, request):
        info = inspect(model)
        fields = set(attr.key for attr in info.column_attrs)
        return fields

    def response_fields(self, item):
        """Get fields to include in response.

        By default, all column attributes will be included. To include
        additional fields::

            field=*&field=x&field=y&field=z

        The default fields plus ``x``, ``y``, and ``z`` will be
        included.

        To exclude some default fields::

            field=*&field=-d&field=-e&field=-f

        The default fields except ``d``, ``e``, and ``f`` will be
        included.

        To specify only some fields::

            field=a&field=b&field=c

        Only fields ``a``, ``b``, and ``c`` will be included.

        Fields can be passed via one or more ``field`` request
        parameters or* via a single ``fields`` request parameter
        formatted as a comma-separated list. These are equivalent::

            field=a&field=b&field=c
            fields=a,b,c

        """
        params = self.request.GET
        specified = get_param(params, "field", multi=True, default=None)
        specified = specified or get_param(params, "fields", list, default=None)
        specified = specified or ["*"]

        fields = set()

        # XXX: Exclusions complicate things and I'm not sure how useful
        #      they are, especially when selecting sub-fields.
        # excluded_fields = set()

        for spec in specified:
            if spec == "*":
                fields.update(self.default_response_fields(item))
            # elif spec.startswith("-"):
            #     excluded_fields.add(spec[1:])
            elif spec.startswith("+"):
                fields.add(spec[1:])
            else:
                fields.add(spec)

        # fields = fields - excluded_fields
        return fields

    def extract_fields(self, item):
        fields = self.response_fields(item)
        return self._extract_fields(item, fields)

    def _extract_fields(self, item, fields):
        request = self.request
        new_item = {}
        for name in fields:
            name, *rest = name.split(".", 1)
            obj = getattr(item, name)
            if callable(obj):
                obj = obj(request)
            if rest:
                if isinstance(obj, Sequence) and not isinstance(obj, str):
                    result = [self._extract_fields(sub_obj, rest) for sub_obj in obj]
                    if name in new_item:
                        for i, sub_obj in enumerate(result):
                            new_item[name][i].update(sub_obj)
                    else:
                        new_item[name] = result
                else:
                    result = self._extract_fields(obj, rest)
                    if name in new_item:
                        new_item[name].update(result)
                    else:
                        new_item[name] = result
            else:
                new_item[name] = obj
        return new_item


class SQLAlchemyContainerResource(SQLAlchemyResource):

    key = "items"
    item_key = "item"

    filtering_enabled = True
    filtering_supported_operators = {
        "=": "__eq__",
        "!=": "__ne__",
        "<": "__lt__",
        "<=": "__lte__",
        ">": "__gt__",
        ">=": "__gte__",
        "in": "in_",
        "not in": "notin_",
        "like": "like",
        "not like": "notlike",
        "ilike": "ilike",
        "not ilike": "notilike",
        "is": "is_",
        "is not": "isnot",
    }

    ordering_enabled = True
    ordering_default = ()

    # Enabled by default to avoid huge queries
    pagination_enabled = True
    pagination_default_page_size = 50
    pagination_max_page_size = 250

    def get(self, *, wrapped=True):
        """Get items in container."""
        data = {}
        q = self.dbsession.query(self.model)
        if self.filtering_enabled:
            q = self.apply_filtering_to_query(q)
        if self.ordering_enabled:
            q = self.apply_ordering_to_query(q)
        if self.pagination_enabled:
            q, pagination_data = self.apply_pagination_to_query(q)
            if pagination_data is not None:
                data["pagination_data"] = pagination_data
        for item in self.joined_load_with:
            q = q.options(joinedload(item))
        items = q.all()
        if not wrapped:
            return items
        if self.model_adapter:
            items = [self.model_adapter(item, self.request) for item in items]
        items = [self.extract_fields(item) for item in items]
        data[self.key] = items
        return data

    def post(self):
        data = extract_data(self.request)
        item = self.model(**data)
        self.dbsession.add(item)
        self.dbsession.commit()
        return {self.item_key: item}

    def apply_filtering_to_query(self, q):
        params = self.request.GET
        filters = get_param(params, "filters", converter=json.loads, default=None)

        if filters:
            model = self.model
            operations = []
            boolean_operator = filters.pop("$operator", "and").lower()
            supported_operators = self.filtering_supported_operators

            for name, value in filters.items():
                name, *operator = name.split(" ", 1)
                try:
                    col = getattr(model, name)
                except AttributeError:
                    raise exception_response(
                        400, detail=f"Unknown column on model {model.__name__}: {name}"
                    )
                operator = operator[0].lower() if operator else "="
                if operator not in supported_operators:
                    raise exception_response(
                        400, detail=f"Unsupported SQL operator: {operator}"
                    )
                operator = supported_operators[operator]
                operator = getattr(col, operator)
                operations.append(operator(value))

            if boolean_operator == "and":
                q = q.filter(and_(*operations))
            elif boolean_operator == "or":
                q = q.filter(or_(*operations))
            else:
                raise exception_response(
                    400, detail=f"Unsupported boolean operator: {boolean_operator}"
                )

        return q

    def apply_ordering_to_query(self, q):
        params = self.request.GET
        ordering = get_param(params, "ordering", multi=True, default=None)
        ordering = ordering or self.ordering_default
        if ordering:
            order_by = []
            for item in ordering:
                if isinstance(item, str):
                    if item.startswith("-"):
                        item = item[1:]
                        desc = True
                    else:
                        desc = False
                    item = getattr(self.model, item)
                    if desc:
                        item = item.desc()
                order_by.append(item)
            q = q.order_by(*order_by)
        return q

    def apply_pagination_to_query(self, q):
        params = self.request.GET
        page = get_param(params, "page", int, default=1)

        page_size = get_param(params, "page_size", default=None)

        # XXX: Page size "*" disables pagination
        if page_size == "*":
            return q, None

        page_size = get_param(
            params, "page_size", int, default=self.pagination_default_page_size
        )

        if page < 1:
            page = 1

        if self.pagination_max_page_size and page_size > self.pagination_max_page_size:
            page_size = self.pagination_max_page_size

        count = q.count()
        num_pages = ceiling(count / page_size)
        offset = (page - 1) * page_size

        q = q.offset(offset)
        q = q.limit(page_size)

        pagination_data = {
            "pages": num_pages,
            "current_page": page,
            "previous_page": 1 if page == 1 else page - 1,
            "next_page": page + 1,
            "page_size": page_size,
            "count": count,
        }

        return q, pagination_data


class SQLAlchemyItemResource(SQLAlchemyResource):

    key = "item"

    def delete(self):
        item = self.get(wrapped=False)
        self.dbsession.delete(item)
        self.dbsession.commit()
        return {self.key: item}

    def get(self, *, wrapped=True):
        """Get an item."""
        filters = {}
        for name, value in self.request.matchdict.items():
            try:
                value = json.loads(value)
            except ValueError:
                pass
            filters[name] = value
        q = self.dbsession.query(self.model).filter_by(**filters)
        for item in self.joined_load_with:
            q = q.options(joinedload(item))
        try:
            item = q.one()
        except NoResultFound:
            detail = f"No item found for filters: {filters!r}"
            raise exception_response(404, detail=detail)
        if not wrapped:
            return item
        if self.model_adapter:
            item = self.model_adapter(item, self.request)
        item = self.extract_fields(item)
        return {self.key: item}

    def patch(self):
        item = self.get(wrapped=False)
        data = extract_data(self.request)
        for name, value in data.items():
            setattr(item, name, value)
        self.dbsession.commit()
        return {self.key: item}

    def put(self):
        try:
            item = self.get(wrapped=False)
        except HTTPNotFound:
            item = None
        data = extract_data(self.request)
        if item is None:
            item = self.model(**data)
            self.dbsession.add(item)
        else:
            # TODO: Validate that ``data`` represents a complete item?
            for name, value in data.items():
                setattr(item, name, value)
        self.dbsession.commit()
        return {self.key: item}
