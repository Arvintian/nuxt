from madara.blueprints import Blueprint
from madara.wrappers import Request, Response
from werkzeug.utils import redirect, send_file, send_from_directory
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.routing import Route as __Route
from nuxt.templating import render_template, render_html
from nuxt.utils import to_asgi_pattern as __to_asgi_pattern
from nuxt.app import wsgi_app as __wsgi_app
from nuxt.app import wsgi_wapper_app as __wsgi_wapper_app
from nuxt.app import asgi_app as __asgi_app

__origin_add_url_rule = __wsgi_app.add_url_rule


def __add_url_rule(pattern: str, endpoint=None, view_func=None, provide_automatic_options=None, **options):
    __asgi_app.routes.append(__Route(__to_asgi_pattern(pattern), __wsgi_wapper_app, methods=options.get("methods")))
    return __origin_add_url_rule(pattern, endpoint, view_func, provide_automatic_options, **options)


__wsgi_app.add_url_rule = __add_url_rule


route = __wsgi_app.route
websocket_route = __asgi_app.websocket_route
register_blueprint = __wsgi_app.register_blueprint
config: dict = __wsgi_app.config
logger = __wsgi_app.logger
