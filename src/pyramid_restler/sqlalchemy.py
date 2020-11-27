import json
from math import ceil as ceiling
from typing import Sequence

from pyramid.httpexceptions import HTTPNotFound

from sqlalchemy import inspect
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_, or_

from .response import exception_response
from .settings import get_setting
from .util import extract_data, get_param


from .resource import Resource


class SQLAlchemyResource(Resource):

    joined_load_with = ()

    @property
    def key(self):
        """Key used to refer to item or items in returned data."""
        raise NotImplementedError("key property must be implemented in subclasses")

    @property
    def model(self):
        """SQLAlchemy ORM class."""
        raise NotImplementedError("model property must be implemented in subclasses")

    def __init__(self, request):
        super().__init__(request)
        model_info = inspect(self.model)
        settings = self.request.registry.settings
        self.dbsession = request.dbsession
        self.response_fields_getter = get_setting(
            settings, "get_default_response_fields", default=None
        )
        self.item_processor = get_setting(settings, "item_processor", default=None)
        self.column_attrs = tuple(attr.key for attr in model_info.column_attrs)
        self.default_response_fields = self.column_attrs

    def get_response_fields(self, item):
        """Get fields to include in response.

        By default, all column attributes will be included. To include
        additional fields::

            field=*&field=x&field=y&field=z

        The default fields plus ``x``, ``y``, and ``z`` will be
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
        request = self.request
        specified = get_param(request, "field", multi=True, default=None)
        specified = specified or get_param(request, "fields", list, default=None)
        specified = specified or ["*"]
        fields = set()
        for spec in specified:
            if spec == "*":
                fields.update(self.get_default_response_fields(item))
            else:
                fields.add(spec)
        return fields

    def get_default_response_fields(self, item):
        """Get default fields to include in response."""
        model = self.model
        request = self.request
        response_fields_getter = self.response_fields_getter
        if response_fields_getter:
            return response_fields_getter(self, model, item, request)
        return self.default_response_fields

    def extract_fields(self, item, fields=None):
        """Extract fields from item.

        The incoming item is typically an ORM instance and the returned
        item is typically a dict.

        """
        request = self.request

        if fields is None:
            fields = self.get_response_fields(item)

        new_item = {}

        for name in fields:
            name, *rest = name.split(".", 1)
            obj = getattr(item, name)
            if callable(obj):
                obj = obj(request)
            if rest:
                if isinstance(obj, Sequence) and not isinstance(obj, str):
                    result = [self.extract_fields(sub_obj, rest) for sub_obj in obj]
                    if name in new_item:
                        for i, sub_obj in enumerate(result):
                            new_item[name][i].update(sub_obj)
                    else:
                        new_item[name] = result
                else:
                    result = self.extract_fields(obj, rest)
                    if name in new_item:
                        new_item[name].update(result)
                    else:
                        new_item[name] = result
            else:
                new_item[name] = obj

        return new_item

    def process_item(self, item):
        """Process item after fields have been extracted.

        The incoming item is typically a dict. By default, the item is
        returned as is.

        """
        item_processor = self.item_processor
        if item_processor:
            return item_processor(self, self.model, item, self.request)
        return item


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
        items = [self.extract_fields(item) for item in items]
        items = [self.process_item(item) for item in items]
        data[self.key] = items
        return data

    def post(self):
        data = extract_data(self.request)
        item = self.model(**data)
        self.dbsession.add(item)
        self.dbsession.commit()
        return {self.item_key: item}

    def apply_filtering_to_query(self, q, *, skip_filters=()):
        request = self.request
        filters = get_param(request, "filters", converter=json.loads, default=None)

        if not filters:
            return q

        model = self.model
        operations = []
        boolean_operator = filters.pop("$operator", "and").lower()
        supported_operators = self.filtering_supported_operators

        for name, value in filters.items():
            if name in skip_filters:
                continue
            name, *operator = name.split(" ", 1)
            try:
                col = getattr(model, name)
            except AttributeError:
                raise exception_response(
                    400,
                    detail=f"Unknown column on model {model.__name__}: {name}",
                )
            if operator:
                operator = operator[0].lower()
            elif isinstance(value, Sequence) and not isinstance(value, str):
                operator = "in"
            else:
                operator = "="
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
                400,
                detail=f"Unsupported boolean operator: {boolean_operator}",
            )

        return q

    def apply_ordering_to_query(self, q):
        request = self.request
        ordering = get_param(request, "ordering", multi=True, default=None)
        ordering = ordering or self.ordering_default

        if not ordering:
            return q

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
        request = self.request
        page = get_param(request, "page", int, default=1)

        page_size = get_param(request, "page_size", default=None)

        # XXX: Page size "*" disables pagination
        if page_size == "*":
            return q, None

        page_size = get_param(
            request, "page_size", int, default=self.pagination_default_page_size
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
        request = self.request
        for name, value in request.matchdict.items():
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
        item = self.extract_fields(item)
        item = self.process_item(item)
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
