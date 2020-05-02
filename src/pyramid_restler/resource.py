from pyramid.httpexceptions import exception_response


__all__ = ["Resource"]


class Resource:
    def __init__(self, request):
        self.request = request

    def method_not_allowed(self):
        raise exception_response(405)

    delete = method_not_allowed
    get = method_not_allowed
    patch = method_not_allowed
    post = method_not_allowed
    put = method_not_allowed

    def head(self):
        return self.get()
