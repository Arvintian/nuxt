from madara.blueprints import Blueprint
from madara.wrappers import Request, Response
from werkzeug.utils import redirect, send_file, send_from_directory
from starlette.websockets import WebSocket, WebSocketDisconnect
from nuxt.templating import render_template, render_html
from nuxt.app import wsgi_app as __wsgi_app
from nuxt.app import asgi_app as __asgi_app

route = __wsgi_app.route
websocket_route = __asgi_app.websocket_route
register_blueprint = __wsgi_app.register_blueprint
config: dict = __wsgi_app.config
logger = __wsgi_app.logger
