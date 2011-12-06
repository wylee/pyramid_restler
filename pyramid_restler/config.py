from pyramid.events import NewRequest
from pyramid.httpexceptions import HTTPBadRequest

from pyramid_restler.interfaces import ICollectionContext, IMemberContext
from pyramid_restler.view import RESTfulView


def add_restful_views(self,
                      view='pyramid_restler.view.RESTfulView',
                      collection_context=ICollectionContext,
                      member_context=IMemberContext,
                      view_kw=None):

    view_kw = {} if view_kw is None else view_kw
    view_kw.setdefault('http_cache', 0)

    self.add_view(
        view=view,
        attr='get_collection',
        request_method='GET',
        context=ICollectionContext,
        **view_kw)

    self.add_view(
        view=view,
        attr='create_member',
        request_method='POST',
        context=ICollectionContext,
        **view_kw)

    self.add_view(
        view=view,
        attr='get_member',
        request_method='GET',
        context=IMemberContext,
        **view_kw)

    self.add_view(
        view=view,
        attr='update_member',
        request_method='PUT',
        context=IMemberContext,
        **view_kw)

    self.add_view(
        view=view,
        attr='delete_member',
        request_method='DELETE',
        context=IMemberContext,
        **view_kw)


def enable_POST_tunneling(self, allowed_methods=('PUT', 'DELETE')):
    """Allow other request methods to be tunneled via POST.

    This allows PUT and DELETE requests to be tunneled via POST requests.
    The method can be specified using a parameter or a header...

    The name of the parameter is '$method'; it can be a query or POST
    parameter. The query parameter will be preferred if both the query and
    POST parameters are present in the request.

    The name of the header is 'X-HTTP-Method-Override'. If the parameter
    described above is passed, this will be ignored.

    The request method will be overwritten before it reaches application
    code, such that the application will never be aware of the original
    request method. Likewise, the parameter and header will be removed from
    the request, and the application will never see them.

    """
    param_name = '$method'
    header_name = 'X-HTTP-Method-Override'
    allowed_methods = set(allowed_methods)
    disallowed_message = (
        'Only these methods may be tunneled over POST: {0}.'
        .format(sorted(list(allowed_methods))))
    def new_request_subscriber(event):
        request = event.request
        if request.method == 'POST':
            if param_name in request.GET:
                method = request.GET[param_name]
            elif param_name in request.POST:
                method = request.POST[param_name]
            elif header_name in request.headers:
                method = request.headers[header_name]
            else:
                return  # Not a tunneled request
            if method in allowed_methods:
                request.GET.pop(param_name, None)
                request.POST.pop(param_name, None)
                request.headers.pop(header_name, None)
                request.method = method
            else:
                raise HTTPBadRequest(disallowed_message)
    self.add_subscriber(new_request_subscriber, NewRequest)
