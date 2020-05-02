from typing import Dict

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
    "resource_methods": DEFAULT_RESOURCE_METHODS,
}


TYPES: Dict[str, type] = {
    "default_acl": object,
    "resource_methods": list,
}


NOT_SET = object()


def get_setting(config, name, default=NOT_SET):
    """Get pyramid_restler setting from config.

    If the setting wasn't set in the app, the passed ``default`` value
    will be used. If a ``default`` value wasn't passed, the default from
    :data:`DEFAULT_SETTINGS` will be used.

    """
    if name not in DEFAULT_SETTINGS:
        raise KeyError(f"Unknown pyramid_restler setting: {name}")
    all_settings = config.get_settings()
    settings = all_settings.get("pyramid_restler", {})
    if name in settings:
        value = settings[name]
    elif default is NOT_SET:
        value = DEFAULT_SETTINGS[name]
    else:
        value = default
    type_ = TYPES[name]
    if not isinstance(value, (type_,)):
        if type_ is bool:
            converter = asbool
        elif type_ is list:
            converter = aslist
        elif type_ is object:
            converter = config.maybe_dotted
        elif type_ is str:
            converter = str
        value = converter(value)
    return value
