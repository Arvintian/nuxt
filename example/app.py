import async_handler
from nuxt import config, logger
from nuxt import Blueprint, register_blueprint
from nuxt import Request, Response
from nuxt import render_template, render_html
from nuxt.repositorys.validation import use_args, fields
from nuxt import route


@route("/", methods=["GET"])
def index(request):
    return render_template(request, "index.html", user="Arvin"), {"content-type": "text/html"}


@route("/user/<string:name>", methods=["GET"])
def user_info(request, name):
    return render_html(request, "user/info.html", name=name)


@route("/openapi", methods=["PUT"])
def openapi(request: Request, query_args: dict, form_args: dict):
    """
    tags:
      - test
    """
    return {
        "code": 200,
        "result": {
            "user_id": query_args,
            "user_name": form_args
        }
    }


@route("/demo/<arg>", methods=["GET"])
def demo_args(request, arg: str):
    return {
        "code": 200,
        "result": "hello {}".format(arg)
    }


@route("/args/<int:the_id>", methods=["POST"])
@use_args({"the_id": fields.Int(required=True)}, location="view_args")
@use_args({"body": fields.Int(required=True)}, location="json")
def demo_validation(req: Request, view_args: dict, json_args: dict, the_id):
    return {
        "code": 200,
        "result": {
            "config": config.get("middlewares"),
            "view_args": view_args,
            "json_args": json_args,
            "the_id": the_id
        }
    }


bp_api = Blueprint("bp_api")


@bp_api.route("/demo", methods=["GET"])
def api_demo(request):
    return {
        "code": 200,
        "result": "hello world"
    }


register_blueprint(bp_api, url_prefix="/api")
