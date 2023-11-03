from nuxt import config
from nuxt.utils import maschema_to_apisepc
from madara.wrappers import Request
from webargs.core import ArgMap, ValidateArg, _UNKNOWN_DEFAULT_PARAM
from webargs import fields as WebargsFields
from webargs import core
from collections.abc import Mapping
import marshmallow as ma
import typing
import yaml


class ValidateException(Exception):
    pass


class SyncParser(core.Parser):

    DEFAULT_UNKNOWN_BY_LOCATION: typing.Dict[str, typing.Optional[str]] = {
        "view_args": ma.RAISE,
        "path": ma.RAISE,
        **core.Parser.DEFAULT_UNKNOWN_BY_LOCATION,
    }
    __location_map__ = dict(
        view_args="load_view_args",
        path="load_view_args",
        **core.Parser.__location_map__,
    )

    def use_args(self, argmap: ArgMap,
                 req: typing.Optional[Request] = None,
                 *,
                 location: typing.Optional[str] = None,
                 unknown: typing.Optional[str] = _UNKNOWN_DEFAULT_PARAM,
                 as_kwargs: bool = False,
                 validate: ValidateArg = None,
                 error_status_code: typing.Optional[int] = None,
                 error_headers: typing.Optional[typing.Mapping[str, str]] = None):
        inner_decorator = super().use_args(argmap, req, location=location, unknown=unknown, as_kwargs=as_kwargs,
                                           validate=validate, error_status_code=error_status_code, error_headers=error_headers)

        if isinstance(argmap, Mapping):
            argmap = ma.Schema.from_dict(argmap)()
        openapi_base_schema: dict = config["openapi"]["base_schema"]
        spec = maschema_to_apisepc(argmap, openapi_base_schema["openapi"])

        def decorator(func):
            parsed: dict = yaml.safe_load(func.__doc__) if func.__doc__ else None
            if not isinstance(parsed, dict) or not parsed:
                parsed = {"parameters": []}
            parameters = parsed.get("parameters", [])
            if location in ["view_args", "path", "querystring", "query"]:
                requireds = spec.get("required", [])
                param_in = "path" if location in ["view_args", "path"] else "query"
                for key, schema in spec.get("properties", {}).items():
                    parameters.append({
                        "name": key,
                        "in": param_in,
                        "required": key in requireds,
                        "schema": schema
                    })
                parsed["parameters"] = parameters
            if location in ["json", "form"]:
                content_type = "application/json" if location in ["json"] else "application/x-www-form-urlencoded"
                parsed["requestBody"] = {
                    "content": {
                        content_type: {
                            "schema": spec
                        }
                    }
                }
            func.__doc__ = yaml.dump(parsed)
            return inner_decorator(func)
        return decorator

    def _raw_load_json(self, req: Request):
        if not core.is_json(req.mimetype):
            return core.missing

        return core.parse_json(req.get_data(cache=True))

    def load_view_args(self, req: Request, schema):
        """Return the request's ``view_args`` or ``missing`` if there are none."""
        return req.view_args or core.missing

    def load_querystring(self, req: Request, schema):
        """Return query params from the request as a MultiDictProxy."""
        return self._makeproxy(req.args, schema)

    def load_form(self, req: Request, schema):
        """Return form values from the request as a MultiDictProxy."""
        return self._makeproxy(req.form, schema)

    def load_cookies(self, req: Request, schema):
        """Return cookies from the request."""
        return req.cookies

    def load_headers(self, req: Request, schema):
        """Return headers from the request."""
        return self._makeproxy(req.headers, schema)

    def load_files(self, req: Request, schema):
        """Return files from the request as a MultiDictProxy."""
        return self._makeproxy(req.files, schema)

    def get_request_from_view_args(self, view, args, kwargs):
        return args[0]

    def handle_error(self, error, req, schema, *, error_status_code, error_headers):
        raise ValidateException(error)


parser = SyncParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
fields = WebargsFields
