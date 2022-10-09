from madara.blueprints import Blueprint
from madara.wrappers import Request, Response
from werkzeug.local import LocalProxy as __LocalProxy
from .app import wsgi_app as __app

route = __app.route
register_blueprint = __app.register_blueprint
config: dict = __LocalProxy(lambda: __app.config)
