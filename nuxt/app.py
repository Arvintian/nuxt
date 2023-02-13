from starlette.applications import Starlette
from a2wsgi import WSGIMiddleware
from madara.app import Madara

# setup wsgi app
wsgi_app = Madara()
wsgi_wapper_app = WSGIMiddleware(app=wsgi_app)

# setup asgi app
asgi_app = Starlette(debug=False, routes=[])
asgi_app.router.default = wsgi_wapper_app
