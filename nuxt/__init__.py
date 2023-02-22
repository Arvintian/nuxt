from madara.blueprints import Blueprint
from madara.wrappers import Request, Response
from nuxt.templating import render_template, render_html
from nuxt.app import entry_app as __entry_app
from werkzeug.utils import redirect, send_file, send_from_directory
from werkzeug.local import LocalProxy as __LocalProxy
import logging as __logging

route = __LocalProxy(lambda: __entry_app.wsgi_app.route)
register_blueprint = __LocalProxy(lambda: __entry_app.wsgi_app.register_blueprint)

config: dict = __LocalProxy(lambda: __entry_app.config)
logger: __logging.Logger = __LocalProxy(lambda: __entry_app.logger)
