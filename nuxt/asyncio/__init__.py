from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.requests import Request
from starlette.responses import Response
from nuxt.templating import render_template
from nuxt.templating import async_render_html as render_html
from nuxt.app import ASGIBlueprint as Blueprint
from nuxt.app import entry_app as __entry_app
from werkzeug.local import LocalProxy as __LocalProxy

route = __LocalProxy(lambda: __entry_app.asgi_app.route)
websocket_route = __LocalProxy(lambda: __entry_app.asgi_app.websocket_route)
register_blueprint = __LocalProxy(lambda: __entry_app.asgi_app.register_blueprint)
