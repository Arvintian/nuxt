from madara.app import Madara, Request, InternalServerError, NotFound, HTTPException
from madara.utils import _endpoint_from_view_func
from starlette.applications import Starlette
from starlette.routing import Route
from nuxt.utils import to_asgi_pattern
from concurrent.futures import ThreadPoolExecutor
from a2wsgi.types import Receive, Scope, Send, WSGIApp
from a2wsgi.wsgi import WSGIResponder
import traceback


class WSGIApplicationResponder(object):

    def __init__(self, app: WSGIApp, executor: ThreadPoolExecutor, endpoint: str) -> None:
        self.app, self.executor, self.endpoint = app, executor, endpoint

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope.update({"wsgi_endpoint": self.endpoint})
        if scope["type"] == "http":
            responder = WSGIResponder(self.app, self.executor)
            return await responder(scope, receive, send)

        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1000})
            return

        if scope["type"] == "lifespan":
            message = await receive()
            assert message["type"] == "lifespan.startup"
            await send({"type": "lifespan.startup.complete"})
            message = await receive()
            assert message["type"] == "lifespan.shutdown"
            await send({"type": "lifespan.shutdown.complete"})
            return


class WSGIApplication(Madara):

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.executor = ThreadPoolExecutor(
            thread_name_prefix="WSGI", max_workers=self.config.get("workers", 10)
        )

    def dispatch_request(self, request: Request):
        try:
            endpoint, view_kwargs = request.endpoint, request.view_args
            endpoint_func = self.endpoint_map.get(endpoint, None)
            if not endpoint_func:
                raise NotFound()
            rv = self.process_view_by_middleware(request, endpoint_func, view_kwargs)
            if rv is None:
                rv = endpoint_func(request, **view_kwargs)
            return self.make_response(request, rv)
        except HTTPException as e:
            return e
        except Exception as e:
            if not self._exception_middleware:
                # if no exception process middleware log the traceback.
                self.logger.error(traceback.format_exc())
            try:
                rv = self.process_exception_by_middleware(request, e)
                if rv is None:
                    return InternalServerError(original_exception=e)
                return self.make_response(request, rv)
            except Exception as re:
                # if exception process middleware raise a exception, log the traceback and return an InternalServerError.
                self.logger.error(traceback.format_exc())
                return InternalServerError(original_exception=e)

    def wsgi_app(self, environ: dict, start_response):
        asgi_scope: dict = environ.get("asgi.scope")
        request = Request(environ)
        try:
            request.endpoint, request.view_args = asgi_scope.get("wsgi_endpoint"), asgi_scope.get("path_params", {})
            response = self._middleware_chain(request)
            return response(environ, start_response)
        except Exception as e:
            # process middleware chain __call__ error
            response = self.make_response(request, InternalServerError(original_exception=e))
            if not self._exception_middleware:
                self.logger.error(traceback.format_exc())
            else:
                # process exception by middleware
                try:
                    rv = self.process_exception_by_middleware(request, e)
                    if not rv is None:
                        response = self.make_response(request, rv)
                except Exception as re:
                    response = self.make_response(request, InternalServerError(original_exception=e))
            return response(environ, start_response)

    def get_asgi_endpoint(self, endpoint: str):
        return WSGIApplicationResponder(self, self.executor, endpoint)


# setup wsgi app
wsgi_app = WSGIApplication()

# setup asgi app
asgi_app = Starlette(debug=False, routes=[])


_origin_add_url_rule = wsgi_app.add_url_rule


def __add_url_rule(pattern: str, endpoint=None, view_func=None, provide_automatic_options=None, **options):
    if endpoint is None:
        endpoint = _endpoint_from_view_func(view_func)
    asgi_app.routes.append(Route(to_asgi_pattern(pattern), wsgi_app.get_asgi_endpoint(endpoint), methods=options.get("methods")))
    return _origin_add_url_rule(pattern, endpoint, view_func, provide_automatic_options, **options)


wsgi_app.add_url_rule = __add_url_rule
