from dataclasses import dataclass

from pyramid.decorator import reify
from pyramid.httpexceptions import exception_response

from sqlalchemy import inspect

from zope.interface import implementer

from .interfaces import IResource
from .util import extract_data, get_json_param


__all__ = [
    'configure',
    'SQLAlchemyORMContainerResource',
    'SQLAlchemyORMNewItemResource',
    'SQLAlchemyORMItemResource',
]


def configure(resource_type, **kwargs):
    configuration_type = resource_type.__annotations__['configuration']
    configuration = configuration_type(**kwargs)
    key = (resource_type, configuration)
    if key not in configure.cache:
        name = f'{resource_type.__name__}For{configuration.model.__name__}'
        bases = (resource_type,)
        attrs = {'configuration': configuration}
        configure.cache[key] = type(name, bases, attrs)
    return configure.cache[key]


configure.cache = {}


def item_as_dict(model, item):
    if hasattr(item, 'as_dict'):
        return item.as_dict()
    inspect_obj = inspect(model)
    fields = [c.key for c in inspect_obj.mapper.column_attrs]
    return {field: getattr(item, field) for field in fields}


@dataclass(frozen=True)
class ContainerConfiguration:

    model: type
    name: str
    item_name: str

    # Filtering
    enable_filtering: bool = True

    # Ordering
    enable_ordering: bool = True
    default_ordering: tuple = ()

    # Pagination
    enable_pagination: bool = True
    default_page_size: int = 10
    max_page_size: int = 50

    def filter_query(self, request, query):
        if not self.enable_filtering:
            return query
        return query

    def order_by(self, request, query):
        if not self.enable_ordering:
            return query
        params = request.GET
        ordering = [field.strip() for field in params.get('ordering', '').split(',')]
        ordering = [field for field in ordering if field]
        ordering = ordering or self.default_ordering
        if ordering:
            query = query.order_by(*ordering)
        return query

    def paginate_query(self, request, query):
        if not self.enable_pagination:
            return query
        page = get_json_param(request, 'page', int)
        if page is not None:
            page_size = get_json_param(request, 'page_size', int, self.default_page_size)
            if page < 1:
                page = 1
            if page_size > self.max_page_size:
                page_size = self.max_page_size
            offset = (page - 1) * page_size
            query = query.offset(offset)
            query = query.limit(page_size)
        return query

    def convert(self, items):
        if isinstance(items, self.model):
            return {self.item_name: item_as_dict(self.model, items)}
        return {self.name: [item_as_dict(self.model, item) for item in items]}


@dataclass(frozen=True)
class ItemConfiguration:

    model: type
    name: str
    id_urlvar: str = 'id'

    def convert(self, item):
        return {self.name: item_as_dict(self.model, item)}


@implementer(IResource)
class SQLAlchemyORMContainerResource:

    configuration: ContainerConfiguration = None

    def __init__(self, request):
        self.request = request

    @reify
    def dbsession(self):
        return self.request.dbsession

    def get(self):
        configuration = self.configuration
        request = self.request
        query = self.dbsession.query(configuration.model)
        query = configuration.filter_query(request, query)
        query = configuration.order_by(request, query)
        query = configuration.paginate_query(request, query)
        items = query.all()
        return items

    def post(self):
        configuration = self.configuration
        request = self.request
        dbsession = self.dbsession
        data = extract_data(request)
        item = configuration.model(**data)
        dbsession.add(item)
        dbsession.commit()
        return item


@implementer(IResource)
class SQLAlchemyORMNewItemResource:

    configuration: ItemConfiguration = None

    def __init__(self, request):
        self.request = request

    def get(self):
        return self.configuration.model()


@implementer(IResource)
class SQLAlchemyORMItemResource:

    configuration: ItemConfiguration = None

    def __init__(self, request):
        self.request = request

    @reify
    def dbsession(self):
        return self.request.dbsession

    def get(self, *, raise_on_not_found=True):
        item_id = self.request.matchdict[self.configuration.id_urlvar]
        item = self.dbsession.query(self.configuration.model).get(item_id)
        if item is None and raise_on_not_found:
            detail = 'No item with ID found: {item_id}'.format_map(locals())
            raise exception_response(404, detail=detail)
        return item

    def delete(self):
        item = self.get()
        dbsession = self.dbsession
        dbsession.delete(item)
        dbsession.commit()
        return item

    def patch(self):
        item = self.get()
        data = extract_data(self.request)
        for name, value in data.items():
            setattr(item, name, value)
        self.dbsession.commit()
        return item

    def put(self):
        item = self.get(raise_on_not_found=False)
        request = self.request
        data = extract_data(request)
        if item is None:
            item = self.configuration.model(**data)
            self.dbsession.add(item)
        else:
            # TODO: Validate that ``data`` represents a complete item?
            for name, value in data.items():
                setattr(item, name, value)
        self.dbsession.commit()
        return item
