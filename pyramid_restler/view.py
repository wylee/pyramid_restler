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
        collection = self.context.get_collection()
        return self.render_to_response(collection)

    def get_member(self):
        id = self.request.matchdict['id']
        member = self.context.get_member(id)
        return self.render_to_response(member)

    def _get_data(self):
        content_type = self.request.content_type
        if content_type == 'application/json':
            data = json.loads(self.request.body)
        elif content_type == 'application/x-www-form-urlencoded':
            data = dict(self.request.POST)
        return data

    def create_member(self):
        member = self.context.create_member(self._get_data())
        id = self.context.get_member_id_as_string(member)
        headers = {'Location': '/'.join((self.request.path, id))}
        return Response(status=201, headers=headers)

    def update_member(self):
        id = self.request.matchdict['id']
        member = self.context.update_member(id, self._get_data())
        if member is None:
            member = self.context.create_member(self._get_data())
            headers = {'Location': self.request.path}
            return Response(status=201, headers=headers)
        else:
            return Response(status=204, content_type='')

    def delete_member(self):
        id = self.request.matchdict['id']
        self.context.delete_member(id)
        return Response(status=204, content_type='')

    def render_to_response(self, value, fields=None):
        if value is None:
            raise HTTPNotFound(self.context)
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
            body=self.context.to_json(value, self.fields, self.wrap),
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
