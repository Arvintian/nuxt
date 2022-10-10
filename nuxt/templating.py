from jinja2 import Environment, FileSystemLoader
from madara.wrappers import Request, Response
from nuxt.app import wsgi_app
import os


__template_env: Environment = None


def __init_template_env():
    global __template_env
    __template_config: dict = wsgi_app.config.get("template", {})
    __path = __template_config.get("path", "").lstrip("/")
    __template_path: str = os.path.join(os.path.abspath(os.path.dirname(__path)), __path)
    __template_env = Environment(loader=FileSystemLoader([__template_path]))


def render_template(request: Request, template_name: str, **context):
    if __template_env is None:
        __init_template_env()
    template = __template_env.get_template(template_name)
    return template.render(**context)


def render_html(request: Request, template_name: str, **context):
    content = render_template(request, template_name, **context)
    return Response(content, mimetype="text/html")
