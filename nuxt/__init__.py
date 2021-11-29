from madara.blueprints import Blueprint
from madara.wrappers import Request, Response
from .wsgi_app import app as __app

route = __app.route
register_blueprint = __app.register_blueprint
config = __app.config
