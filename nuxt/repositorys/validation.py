from madara.wrappers import Request
from webargs import core
import typing
import marshmallow as ma


def is_json_request(req: Request):
    return core.is_json(req.mimetype)


class ValidateException(Exception):
    pass


class MadaraParser(core.Parser):

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

    def _raw_load_json(self, req: Request):
        if not is_json_request(req):
            return core.missing

        return core.parse_json(req.get_data(cache=True))

    def load_view_args(self, req, schema):
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


parser = MadaraParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
