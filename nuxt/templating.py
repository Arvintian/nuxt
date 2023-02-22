from nuxt.app import entry_app
from jinja2 import Environment, FileSystemLoader
from starlette.requests import Request as AsyncRequest
from starlette.responses import Response as AsyncResponse
from madara.wrappers import Request, Response
import os


__template_env: Environment = None


def __init_template_env():
    global __template_env
    __template_config: dict = entry_app.config.get("template", {})
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


def async_render_html(request: AsyncRequest, template_name: str, **context):
    content = render_template(request, template_name, **context)
    return AsyncResponse(content, media_type="text/html")
