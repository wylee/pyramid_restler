import json

from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid.response import Response

from zope.interface import implements

from pyramid_restler.interfaces import IView


class RESTfulView(object):

    implements(IView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get_collection(self):
        return self.render_to_response(self.context)

    def get_member(self):
        return self.render_to_response(self.context)

    def _get_data(self):
        content_type = self.request.content_type
        if content_type == 'application/json':
            data = json.loads(self.request.body)
        elif content_type == 'application/x-www-form-urlencoded':
            data = dict(self.request.POST)
        return data

    def create_member(self):
        self.context.create(self._get_data())
        id = self.context.id_as_string
        headers = {'Location': '/'.join((self.request.path, id))}
        return Response(status=201, headers=headers)

    def update_member(self):
        if self.context is None:
            self.context.create(self._get_data())
            headers = {'Location': self.request.path}
            return Response(status=201, headers=headers)
        self.context.update(self._get_data())
        return Response(status=204, content_type='')

    def delete_member(self):
        self.context.delete()
        return Response(status=204, content_type='')

    def render_to_response(self, value, fields=None):
        renderer = self.determine_renderer()
        try:
            renderer = getattr(self, 'render_{0}'.format(renderer))
        except AttributeError:
            name = self.__class__.__name__
            raise HTTPBadRequest(
                '{0} view has no renderer "{1}".'.format(name, renderer))
        return Response(**renderer(value))

    def determine_renderer(self):
        request = self.request
        renderer = (request.matchdict or {}).get('renderer', '').lstrip('.')
        if renderer:
            return renderer
        if request.accept.best_match(['application/json']):
            return 'json'
        elif request.accept.best_match(['application/xml']):
            return 'xml'

    def render_json(self, value):
        response_data = dict(
            body=self.context.to_json(self.fields, self.wrap),
            content_type='application/json',
        )
        return response_data

    def render_xml(self, value):
        raise HTTPBadRequest('XML renderer not implemented.')

    @reify
    def fields(self):
        fields = self.request.params.get('$fields', None)
        if fields is not None:
            fields = json.loads(fields)
        return fields

    @reify
    def wrap(self):
        wrap = self.request.params.get('$wrap', 'true').strip().lower()
        return wrap in ('1', 'true')
