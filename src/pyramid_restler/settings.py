from typing import Any, Callable, Dict, Type

from pyramid.path import DottedNameResolver
from pyramid.settings import asbool, aslist


DEFAULT_RESOURCE_METHODS = (
    "delete",
    "get",
    "head",
    "patch",
    "post",
    "put",
)


DEFAULT_SETTINGS = {
    "default_acl": None,
    "default_model_adapter": None,
    "default_response_fields": None,
    "resource_methods": DEFAULT_RESOURCE_METHODS,
}


TYPES: Dict[str, Type] = {
    "default_acl": object,
    "default_model_adapter": Callable[..., Any],
    "default_response_fields": Callable[..., Any],
    "resource_methods": list,
}


NOT_SET = object()


def get_setting(all_settings, name, default=NOT_SET):
    """Get pyramid_restler setting from config.

    If the setting wasn't set in the app, the passed ``default`` value
    will be used. If a ``default`` value wasn't passed, the default from
    :data:`DEFAULT_SETTINGS` will be used.

    """
    if name not in DEFAULT_SETTINGS:
        raise KeyError(f"Unknown pyramid_restler setting: {name}")
    settings = all_settings.get("pyramid_restler", {})
    if name in settings:
        value = settings[name]
    elif default is NOT_SET:
        value = DEFAULT_SETTINGS[name]
    else:
        value = default
    if isinstance(value, str):
        type_ = TYPES[name]
        if type_ is bool:
            converter = asbool
        elif type_ is Callable[..., Any]:
            resolver = DottedNameResolver()
            converter = resolver.maybe_resolve
        elif type_ is list:
            converter = aslist
        elif type_ is object:
            resolver = DottedNameResolver()
            converter = resolver.maybe_resolve
        elif type_ is str:
            converter = str
        value = converter(value)
    return value
