from starlette.responses import Response, JSONResponse
from starlette.datastructures import Headers
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
import os


def getcwd():
    # get current path, try to use PWD env first
    try:
        a = os.stat(os.environ['PWD'])
        b = os.stat(os.getcwd())
        if a.st_ino == b.st_ino and a.st_dev == b.st_dev:
            cwd = os.environ['PWD']
        else:
            cwd = os.getcwd()
    except Exception:
        cwd = os.getcwd()
    return cwd


def remove_suffix(s: str, suffix: str) -> str:
    if suffix and s.endswith(suffix):
        return s[:-len(suffix)]
    else:
        return s[:]


def format_pattern(pattern: str) -> str:
    raw = pattern.replace("<", "{").replace(">", "}")
    out = []
    for c in raw:
        if c != "}":
            out.append(c)
        else:
            param = []
            x = out.pop()
            while x != "{":
                param.append(x)
                x = out.pop()
            param.reverse()
            params = "".join(param).split(":")
            if len(params) < 2:
                out.append("{%s}" % (params[0]))
            else:
                out.append("{%s:%s}" % (params[1], __convertor_type(params[0])))
    return "".join(out)


def make_response(*rv) -> Response:
    if not rv:
        return Response()

    if len(rv) == 1:
        rv = rv[0]

    status = headers = None

    # unpack tuple returns
    if isinstance(rv, tuple):
        len_rv = len(rv)

        # a 3-tuple is unpacked directly
        if len_rv == 3:
            rv, status, headers = rv
        # decide if a 2-tuple has status or headers
        elif len_rv == 2:
            if isinstance(rv[1], (Headers, dict, tuple, list)):
                rv, headers = rv
            else:
                rv, status = rv
        # other sized tuples are not allowed
        else:
            raise TypeError(
                "The view function did not return a valid response tuple."
                " The tuple must have the form (body, status, headers),"
                " (body, status), or (body, headers)."
            )

    # the body must not be None
    if rv is None:
        raise TypeError(
            "The view function did not return a valid response. The"
            " function either returned None or ended without a return"
            " statement."
        )

    # make sure the body is an instance of the response class
    if not isinstance(rv, Response):
        if isinstance(rv, (str, bytes, bytearray)):
            rv = Response(rv, status_code=status if status else 200, headers=headers)
            status = headers = None
        elif isinstance(rv, dict):
            rv = JSONResponse(content=rv)

    # prefer the status if it was provided
    if status is not None:
        rv.status_code = status

    # extend existing headers with provided headers
    if headers:
        rv.headers.update(headers)

    return rv


def maschema_to_apisepc(schema) -> dict:
    spec = APISpec(
        title="maschema",
        version="1.0.0",
        openapi_version="3.0.2",
        plugins=[MarshmallowPlugin()],
    )
    spec.components.schema("maschema", schema=schema)
    return spec.to_dict()["components"]["schemas"]["maschema"]


def __convertor_type(_type: str):
    if _type == "string":
        return "str"
    return _type
