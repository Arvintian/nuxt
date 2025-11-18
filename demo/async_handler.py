from nuxt import config, logger
from nuxt.asyncio import Blueprint, register_blueprint
from nuxt.asyncio import Request, Response, WebSocket, WebSocketDisconnect, WebSocketState
from nuxt.asyncio import render_template, render_html
from nuxt.asyncio import route, websocket_route, mount
from nuxt.asyncio.repositorys.validation import fields, use_args
from nuxt.asyncio.proxies import make_proxy_response


@route("/async", methods=["GET"])
async def index(request):
    return render_template(request, "index.html", user="Arvin"), {"content-type": "text/html"}


@route("/async/user/<string:name>", methods=["GET"])
async def user_info(request, name):
    """
    userinfo
    """
    if name != "zoe":
        raise Exception("I not know you {}".format(name))
    return render_html(request, "user/info.html", name=name)


@route("/async/arg/<arg>", methods=["GET"])
async def demo_args(request, arg: str):
    return {
        "code": 200,
        "result": "async hello {}".format(arg)
    }


@route("/async/openapi", methods=["POST"])
@use_args({"user_id": fields.Int(required=True)}, location="form")
@use_args({"user_name": fields.Str(required=False)}, location="query")
async def demo_openapi(request: Request, form_args: dict, query_args: dict,  **kwargs):
    """
    tags:
      - test
    """
    return {
        "code": 200,
        "result": {
            "query": query_args,
            "form": form_args
        }
    }


@route("/async/openapi2/<int:user_id>", methods=["POST"])
@use_args({"user_id": fields.Int(required=True)}, location="path")
@use_args({"user_name": fields.Str(required=False)}, location="json")
async def demo_openapi2(request: Request, path_args: dict, json_args: dict, user_id: int):
    """
    tags:
      - async
    """
    return {
        "code": 200,
        "result": {
            "json": json_args,
            "path": path_args,
            "user_id": user_id
        }
    }


@websocket_route("/async/ws/echo")
async def ws_echo(socket: WebSocket):
    """
    tags:
      - websocket
    """
    await socket.accept()
    try:
        while True:
            text = await socket.receive_text()
            recv = "echo:{}".format(text)
            await socket.send_text(recv)
    except WebSocketDisconnect as e:
        pass
    except Exception as e:
        logger.error(e)


bp_async = Blueprint("bp_async")


@bp_async.websocket_route("/ws/echo")
async def bp_ws_echo(socket: WebSocket):
    """
    tags:
      - websocket
    """
    await socket.accept()
    try:
        while True:
            text = await socket.receive_text()
            recv = "echo:{}".format(text)
            await socket.send_text(recv)
    except WebSocketDisconnect as e:
        pass
    except Exception as e:
        logger.error(e)
    finally:
        if socket.client_state != WebSocketState.DISCONNECTED:
            await socket.close()


@bp_async.route("/user/<string:name>", methods=["GET"])
async def bp_user_info(request, name):
    """
    tags:
      - asyncbp
    """
    logger.info("user name %s" % name)
    return render_html(request, "user/info.html", name=name)

register_blueprint(bp_async, url_prefix="/asyncbp", middlewares=["async_middleware.M5"])
# proxy pass all sub route to backend server
mount("/proxy", make_proxy_response("http://127.0.0.1:6000"))
