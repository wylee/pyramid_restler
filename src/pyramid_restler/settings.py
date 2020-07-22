from typing import Any, Callable, Dict, List

from pyramid.path import DottedNameResolver
from pyramid.settings import asbool, aslist

from .util import NOT_SET


DEFAULT_RESOURCE_METHODS = (
    "delete",
    "get",
    "options",
    "patch",
    "post",
    "put",
)


DEFAULT_SETTINGS = {
    "default_acl": None,
    "get_default_response_fields": None,
    "item_processor": None,
    "resource_methods": DEFAULT_RESOURCE_METHODS,
}
"""Default settings."""


TYPES: Dict[str, Any] = {
    "default_acl": Any,
    "get_default_response_fields": Callable[..., Any],
    "item_processor": Callable[..., Any],
    "resource_methods": List,
}
"""Types of the :data:`DEFAULT_SETTINGS`.

Used to determine how to convert settings values.

"""


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
        elif type_ is List:
            converter = aslist
        elif type_ is Any:
            resolver = DottedNameResolver()
            converter = resolver.maybe_resolve
        else:
            converter = None
        if converter is not None:
            value = converter(value)
    return value
