from pyramid.httpexceptions import status_map


def json_formatter(self, *args, **kwargs):
    return {
        "title": self.title,
        "explanation": self.explanation,
        "detail": self.detail,
        "comment": self.comment or "",
        # Everything munged together
        "message": f"{self.explanation}\n\n{self.detail}\n\n{self.comment}".rstrip(),
    }


def exception_response(
    status_code, title=None, explanation=None, detail=None, **kwargs
):
    """Replacement for Pyramid's ``exception_response``.

    Pyramid's :func:`pyramid.httpexceptions.exception_response` munges
    the explanation, detail, and comment together into a single message
    field, but it's often nice to access these independently in JSON
    responses.

    For JSON responses, this keeps the message field but also adds
    separate explanation, detail, and comment fields.

    Pyramid also adds the HTTP status code to the JSON response object,
    which is redundant, so that's not included.

    In addition, this allows the ``title`` and ``explanation`` fields to
    be overridden.

    For HTML responses, the default Pyramid behavior is used.

    """
    error_type = status_map[status_code]
    type_dict = {
        "_json_formatter": json_formatter,
    }
    if title:
        type_dict["title"] = title
    if explanation:
        type_dict["explanation"] = explanation
    error_type = type(error_type.__name__, (error_type,), type_dict)
    return error_type(detail=detail, **kwargs)
