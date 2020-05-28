import re

from pyramid.httpexceptions import exception_response
from pyramid.interfaces import ICSRFStoragePolicy, IDefaultCSRFOptions


NOT_SET = object()
"""Represents the complete absence of a value."""


def as_bool(string: str) -> bool:
    """Convert string to bool.

    Only the values "1", "true", "0", and "false" are accepted.

    """
    string = string.lower()
    if string in ("1", "true"):
        return True
    if string in ("0", "false"):
        return False
    raise ValueError('Expected value to be one of "1", "true", "0", or "false"')


def as_list(string, sep=",", strip=True):
    """Convert string to list, splitting on comma by default."""
    string = string.strip()
    items = string.split(sep)
    if strip:
        items = [item.strip() for item in items]
    return items


def camel_to_underscore(name):
    """Convert camel case name to underscore name."""
    name = re.sub(r"(?<!\b)(?<!_)([A-Z][a-z])", r"_\1", name)
    name = re.sub(r"(?<!\b)(?<!_)([a-z])([A-Z])", r"\1_\2", name)
    name = name.lower()
    return name


def extract_data(request):
    """Extract request data."""
    content_type = request.content_type

    if content_type == "application/x-www-form-urlencoded":
        data = request.POST
    elif content_type == "application/json":
        data = request.json_body if request.body else None
    else:
        raise TypeError(f"Cannot extract data for content type: {content_type}")

    # Remove CSRF token from data, if present
    policy = request.registry.queryUtility(ICSRFStoragePolicy)
    if policy:
        options = request.registry.queryUtility(IDefaultCSRFOptions)
        if options:
            token = options.token
            if token in data:
                del data[token]

    return data


def get_param(
    params,
    name,
    converter=None,
    *,
    multi=False,
    strip=True,
    convert_empty_to_none=True,
    default=NOT_SET,
):
    """Get the specified request parameter and, optionally, convert it.

    ``params`` can be any dict-like object, but typically it's
    ``request.GET``.

    If ``multi=True``, ``params`` *must* have a ``.getall()`` method for
    extracting multiple parameters of the same ``name``.

    If ``strip=True``, the param value or values will be stripped before
    being converted.

    If ``convert_empty_to_none=True`` and a param value is blank (empty
    string), it will be converted to ``None``.

    If a ``converter`` is specified, the value or values will be passed
    to this callable for conversion (unless converted to ``None``). If a
    value can't be parsed, a 400 response will be returned immediately.

    If the param isn't present and a ``default`` value is specified,
    that default value will be returned. If no default value is
    specified, a ``KeyError`` will be raised.

    """
    if name not in params:
        if default is NOT_SET:
            params[name]
        return default

    def convert(v):
        if strip:
            v = v.strip()
        if not v and convert_empty_to_none:
            return None
        if converter:
            try:
                v = converter(v)
            except (TypeError, ValueError):
                raise exception_response(
                    400,
                    detail=f"Could not parse parameter {name} with {converter}: {v!r}",
                )
        return v

    if converter is bool:
        converter = as_bool
    elif converter is list:
        converter = as_list

    if multi:
        values = params.getall(name)
        values = [convert(value) for value in values]
        return values

    value = params[name]
    value = convert(value)
    return value
