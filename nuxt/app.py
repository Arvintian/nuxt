from madara.blueprints import Blueprint as MadaraBlueprint
from madara.app import Madara
from starlette.applications import Starlette
from nuxt.routing import BaseRoute, Route
from nuxt.datastructures import ImmutableDict
from nuxt.requests import SyncRequest, AsyncRequest, WebSocket
from nuxt.exceptions import SyncHTTPException, SyncNotFound, SyncInternalServerError
from nuxt.utils import format_pattern, endpoint_from_view_func, load_config, import_string, make_sync_response, make_async_response
from concurrent.futures import ThreadPoolExecutor
from a2wsgi.asgi_typing import Receive, Scope, Send, ASGIApp
from a2wsgi.wsgi_typing import WSGIApp
from a2wsgi.wsgi import WSGIResponder
import traceback
import typing


class WSGIApplicationResponder:

    def __init__(self, app: WSGIApp, executor: ThreadPoolExecutor, endpoint: str, func: typing.Callable) -> None:
        self.app, self.executor, self.endpoint = app, executor, endpoint
        self.__doc__ = func.__doc__

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope.update({"nuxt_endpoint": self.endpoint})
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


class WSGIBlueprint(MadaraBlueprint):

    def route(self, pattern, **options):

        def decorator(func):
            endpoint = options.pop("endpoint", func.__name__)
            self.endpoint_map["sync.%s.%s" % (self.name, endpoint)] = func
            _view_entry = lambda req, **view_args: self.view_entry(req, **view_args)
            _view_entry.__doc__ = func.__doc__
            self.add_url_rule(pattern, endpoint, _view_entry, **options)
            return func

        return decorator


class WSGIApplication(Madara):

    def __init__(self, app: Starlette, config: dict = None):
        super().__init__(config)
        self.base_app = app
        self.executor = ThreadPoolExecutor(
            thread_name_prefix="WSGI", max_workers=self.config.get("workers", 10)
        )

    def dispatch_request(self, request: SyncRequest):
        try:
            endpoint, view_kwargs = request.endpoint, request.view_args
            endpoint_func = self.endpoint_map.get(endpoint, None)
            if not endpoint_func:
                raise SyncNotFound()
            rv = self.process_view_by_middleware(request, endpoint_func, view_kwargs)
            if rv is None:
                rv = endpoint_func(request, **view_kwargs)
            return self.make_response(request, rv)
        except SyncHTTPException as e:
            return e
        except Exception as e:
            if not self._exception_middleware:
                # if no exception process middleware log the traceback.
                self.logger.error(traceback.format_exc())
            try:
                rv = self.process_exception_by_middleware(request, e)
                if rv is None:
                    return SyncInternalServerError(original_exception=e)
                return self.make_response(request, rv)
            except Exception as re:
                # if exception process middleware raise a exception, log the traceback and return an InternalServerError.
                self.logger.error(traceback.format_exc())
                return SyncInternalServerError(original_exception=e)

    def wsgi_app(self, environ: dict, start_response):
        asgi_scope: dict = environ.get("asgi.scope")
        request = SyncRequest(environ)
        try:
            request.endpoint, request.view_args = asgi_scope.get("nuxt_endpoint"), asgi_scope.get("path_params", {})
            response = self._middleware_chain(request)
            return response(environ, start_response)
        except Exception as e:
            # process middleware chain __call__ error
            response = self.make_response(request, SyncInternalServerError(original_exception=e))
            if not self._exception_middleware:
                self.logger.error(traceback.format_exc())
            else:
                # process exception by middleware
                try:
                    rv = self.process_exception_by_middleware(request, e)
                    if not rv is None:
                        response = self.make_response(request, rv)
                except Exception as re:
                    response = self.make_response(request, SyncInternalServerError(original_exception=e))
            return response(environ, start_response)

    def make_response(self, request, rv):
        return make_sync_response(request, rv)

    def get_responder(self, endpoint: str, func):
        self.endpoint_map[endpoint] = func
        return WSGIApplicationResponder(self, self.executor, endpoint, func)

    def add_url_rule(self, pattern: str, endpoint=None, view_func=None, provide_automatic_options=None, **options):
        endpoint = "sync.%s" % (endpoint if endpoint else endpoint_from_view_func(view_func))
        self.base_app.router.routes.append(Route(format_pattern(pattern), self.get_responder(endpoint, view_func),
                                                 methods=options.get("methods"), name=endpoint))


class ASGIApplicationResponder:

    def __init__(self, app: ASGIApp, endpoint: str, func: typing.Callable, sub_app=False) -> None:
        self.app, self.endpoint, self.sub_app = app, endpoint, sub_app
        self.__doc__ = func.__doc__

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope.update({"nuxt_endpoint": self.endpoint, "nuxt_sub_app": self.sub_app})
        await self.app(scope, receive, send)


class ASGIBlueprintSetupState:

    def __init__(self, blueprint, app: Starlette, options: dict):
        self.app = app
        self.blueprint = blueprint
        self.options = options

        url_prefix = self.options.get("url_prefix")
        if url_prefix is None:
            url_prefix = self.blueprint.url_prefix
        self.url_prefix: str = url_prefix

    def add_route(
        self,
        path: str,
        route: typing.Callable,
        methods: typing.Optional[typing.List[str]] = None,
        name: typing.Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        if self.url_prefix is not None:
            path = "/".join((self.url_prefix.rstrip("/"), path.lstrip("/"))) if path else self.url_prefix
        self.app.add_route(
            path, route, methods=methods, name=name, include_in_schema=include_in_schema
        )

    def add_websocket_route(
        self, path: str, route: typing.Callable, name: typing.Optional[str] = None
    ) -> None:
        if self.url_prefix is not None:
            path = "/".join((self.url_prefix.rstrip("/"), path.lstrip("/"))) if path else self.url_prefix
        self.app.add_websocket_route(path, route, name=name)


class ASGIBlueprint:

    def __init__(self, name, url_prefix: str = ""):
        self.name = name
        self.url_prefix = url_prefix
        self.deferred_functions = []
        self.endpoint_map = {}
        self.base_app: Starlette = None
        self._middleware_chain = None

    def record(self, func):
        self.deferred_functions.append(func)

    def make_setup_state(self, app, options):
        return ASGIBlueprintSetupState(self, app, options)

    def register(self, app: Starlette, options: dict):
        self.base_app = app
        state = self.make_setup_state(app, options)
        for deferred in self.deferred_functions:
            deferred(state)
        middlewares = options.get("middlewares", [])
        handler = self.dispatch_request
        for md in reversed(middlewares):
            mw = md
            if isinstance(md, str):
                mw = import_string(md)
            handler = mw(handler)
        self._middleware_chain = handler

    async def dispatch_request(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.base_app is None:
            raise Exception("ASGIBlueprint {} not registered".format(self.name))
        endpoint = scope["nuxt_endpoint"]
        endpoint_func = self.endpoint_map.get(endpoint, None)
        if not endpoint_func:
            await self.base_app.router.not_found(scope, receive, send)
            return

        is_websocket = scope["type"] == "websocket"
        if is_websocket:
            request = WebSocket(scope, receive, send)
        else:
            request = AsyncRequest(scope, receive, send)

        rv = await endpoint_func(request, **request.path_params)

        if is_websocket:
            return

        response = make_async_response(rv)
        await response(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self._middleware_chain(scope, receive, send)

    def get_responder(self, endpoint: str, func):
        self.endpoint_map[endpoint] = func
        return ASGIApplicationResponder(self, endpoint, func)

    def route(self, pattern: str, **options) -> typing.Callable:
        endpoint = options.get("endpoint")
        if endpoint:
            assert "." not in endpoint, "ASGIBlueprint endpoints should not contain dots"

        def decorator(func: typing.Callable) -> typing.Callable:
            name = "async.%s.%s" % (self.name, endpoint if endpoint else endpoint_from_view_func(func))
            self.record(lambda state: state.add_route(
                format_pattern(pattern),
                self.get_responder(name, func),
                methods=options.get("methods"),
                name=name,
                include_in_schema=options.get("include_in_schema", True),
            ))
            return func

        return decorator

    def websocket_route(self, pattern: str, **options) -> typing.Callable:
        endpoint = options.get("endpoint")
        if endpoint:
            assert "." not in endpoint, "ASGIBlueprint websocket endpoints should not contain dots"

        def decorator(func: typing.Callable) -> typing.Callable:
            name = "async.%s.%s" % (self.name, endpoint if endpoint else endpoint_from_view_func(func))
            self.record(lambda state: state.add_websocket_route(format_pattern(pattern), self.get_responder(name, func), name))
            return func

        return decorator


class ASGIApplication:

    def __init__(self, app: Starlette, config: dict = None) -> None:
        self.base_app, self.config = app, config
        self.endpoint_map = {}
        self.blueprints = {}
        self._middleware_chain = None
        self.load_middleware()

    def load_middleware(self):
        middlewares = self.config.get("middlewares", [])
        handler = self.dispatch_request
        for md in reversed(middlewares):
            mw = md
            if isinstance(md, str):
                mw = import_string(md)
            handler = mw(handler)
        self._middleware_chain = handler

    async def dispatch_request(self, scope: Scope, receive: Receive, send: Send) -> None:
        endpoint = scope["nuxt_endpoint"]
        endpoint_func = self.endpoint_map.get(endpoint, None)
        if not endpoint_func:
            await self.base_app.router.not_found(scope, receive, send)
            return

        # blueprint endpoint warp an another ASGIApplicationResponder
        if isinstance(endpoint_func, ASGIApplicationResponder) or scope.get("nuxt_sub_app"):
            await endpoint_func(scope, receive, send)
            return

        is_websocket = scope["type"] == "websocket"
        if is_websocket:
            request = WebSocket(scope, receive, send)
        else:
            request = AsyncRequest(scope, receive, send)

        rv = await endpoint_func(request, **request.path_params)

        if is_websocket:
            return

        response = make_async_response(rv)
        await response(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self._middleware_chain(scope, receive, send)

    def get_responder(self, endpoint: str, func, sub_app=False):
        self.endpoint_map[endpoint] = func
        return ASGIApplicationResponder(self, endpoint, func, sub_app=sub_app)

    def register_blueprint(self, blueprint: ASGIBlueprint, **options) -> None:
        if blueprint.name in self.blueprints:
            assert self.blueprints[blueprint.name] is blueprint, ('Blueprints %r and %r that are created on the fly need unique names.' % (
                blueprint, self.blueprints[blueprint.name]))
        else:
            self.blueprints[blueprint.name] = blueprint
        blueprint.register(self, options)

    def add_route(
        self,
        path: str,
        route: typing.Callable,
        methods: typing.Optional[typing.List[str]] = None,
        name: typing.Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        self.base_app.add_route(
            path, self.get_responder(name, route), methods=methods, name=name, include_in_schema=include_in_schema
        )

    def add_websocket_route(
        self, path: str, route: typing.Callable, name: typing.Optional[str] = None
    ) -> None:
        self.base_app.add_websocket_route(path, self.get_responder(name, route), name=name)

    def add_mount(
        self, path: str, route: typing.Callable, name: typing.Optional[str] = None
    ) -> None:
        self.base_app.mount(path, self.get_responder(name, route, sub_app=True), name=name)

    def route(self, pattern: str, **options) -> typing.Callable:

        def decorator(func: typing.Callable) -> typing.Callable:
            endpoint = "async.%s" % (options.get("endpoint") if options.get("endpoint") else endpoint_from_view_func(func))
            self.add_route(
                format_pattern(pattern),
                func,
                methods=options.get("methods"),
                name=endpoint,
                include_in_schema=options.get("include_in_schema", True),
            )
            return func

        return decorator

    def websocket_route(self, pattern: str, **options) -> typing.Callable:

        def decorator(func: typing.Callable) -> typing.Callable:
            endpoint = "async.%s" % (options.get("endpoint") if options.get("endpoint") else endpoint_from_view_func(func))
            self.add_websocket_route(format_pattern(pattern), func, name=endpoint)
            return func

        return decorator

    def mount(self, pattern: str, func: typing.Callable, **options) -> None:
        endpoint = "async.%s" % (options.get("endpoint") if options.get("endpoint") else endpoint_from_view_func(func))
        self.add_mount(format_pattern(pattern), func, name=endpoint)


class NuxtApplication:

    default_config = ImmutableDict(
        {
            "debug": False,
            "middlewares": {
                "sync": [],
                "async": [],
            },
            "logger_handler": None,
        }
    )

    def __init__(self, config: dict = None) -> None:
        self.config = dict(self.default_config)
        if not config is None:
            self.config.update(load_config(config))

        wsgi_config, asgi_config = {}, {}
        for key, val in self.config.items():
            wsgi_config[key], asgi_config[key] = val, val
            if key == "middlewares":
                wsgi_config[key], asgi_config[key] = val["sync"], val["async"]

        self.base_app = Starlette(debug=self.config.get("debug"), routes=[])
        self.wsgi_app = WSGIApplication(self.base_app, wsgi_config)
        self.asgi_app = ASGIApplication(self.base_app, asgi_config)

    @property
    def routes(self) -> typing.List[BaseRoute]:
        return self.base_app.router.routes

    @property
    def logger(self):
        return self.wsgi_app.logger

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.base_app(scope, receive, send)


entry_app = NuxtApplication()
