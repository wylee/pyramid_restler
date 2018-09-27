from pyramid.httpexceptions import HTTPBadRequest
from pyramid.renderers import RendererHelper


def default_renderer_factory(info):
    """Default renderer used when a view doesn't specify one."""

    def _render(value, system):
        request = system['request']
        registry = info.registry

        renderer = request.GET.get('$renderer') or request.matchdict.get('renderer') or ''
        renderer = renderer.strip()

        if not renderer:
            acceptable = request.accept.acceptable_offers(['application/json'])
            acceptable = [a[0] for a in acceptable]
            if acceptable[0] == 'application/json':
                renderer = 'json'

        if not renderer:
            raise HTTPBadRequest('No acceptable renderer found for request')

        helper = RendererHelper(renderer, info.package, registry)

        try:
            helper.renderer
        except ValueError:
            raise HTTPBadRequest('No such renderer: "%s"' % renderer)

        return helper.render(value, system, request)

    return _render
