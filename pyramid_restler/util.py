import json

from pyramid.httpexceptions import exception_response


def get_json_param(request, name, kind=object, default=None):
    if name not in request.GET:
        return default
    value = request.GET[name]
    try:
        parsed_value = json.loads(value)
    except ValueError:
        raise exception_response(400, f'Could not parse value as JSON: {value!r}')
    if not isinstance(parsed_value, kind):
        raise exception_response(400, f'Expected JSON value with type {kind}; got {value!r}')
    return parsed_value


def extract_data(request):
    content_type = request.content_type
    if content_type == 'application/x-www-form-urlencoded':
        return request.POST
    elif content_type == 'application/json':
        return request.json_body if request.body else None
    raise TypeError(f'Cannot extract data for content type: {content_type}')
