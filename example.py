from nuxt import route, Request, config
from nuxt.repositorys.validation import use_args
from webargs import fields


@route("/demo", methods=["GET"])
def demo(request):
    return {
        "code": 200,
        "result": "hello"
    }


@route("/args/<int:the_id>", methods=["GET"])
@use_args({
    "the_id": fields.Int(required=True)
}, location="view_args")
@use_args({
    "body": fields.Int(required=True)
}, location="json")
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
