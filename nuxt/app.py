from starlette.applications import Starlette
from a2wsgi import WSGIMiddleware
from madara.app import Madara

# setup wsgi app
wsgi_app = Madara()

# setup asgi app
asgi_app = Starlette(debug=wsgi_app.config.get("debug", False), routes=[])
asgi_app.router.default = WSGIMiddleware(app=wsgi_app)
