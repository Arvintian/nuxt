from nuxt.requests import AsyncRequest as Request
from nuxt.requests import WebSocket, WebSocketState
from nuxt.exceptions import WebSocketDisconnect
from nuxt.responses import AsyncResponse as Response
from nuxt.responses import AsyncJSONResponse as JSONResponse
from nuxt.responses import AsyncPlainTextResponse as PlainTextResponse
from nuxt.responses import AsyncHTMLResponse as HTMLResponse
from nuxt.templating import render_template
from nuxt.templating import async_render_html as render_html
from nuxt.app import ASGIBlueprint as Blueprint
from nuxt.app import entry_app as __entry_app
from nuxt.utils import LocalProxy as __LocalProxy

route = __LocalProxy(lambda: __entry_app.asgi_app.route)
websocket_route = __LocalProxy(lambda: __entry_app.asgi_app.websocket_route)
register_blueprint = __LocalProxy(lambda: __entry_app.asgi_app.register_blueprint)
mount = __LocalProxy(lambda: __entry_app.asgi_app.mount)
