from nuxt import config, logger
from nuxt.asyncio import Blueprint, register_blueprint
from nuxt.asyncio import Request, Response, WebSocket, WebSocketDisconnect
from nuxt.asyncio import render_template, render_html
from nuxt.asyncio import route, websocket_route


@route("/async", methods=["GET"])
async def index(request):
    return render_template(request, "index.html", user="Arvin"), {"content-type": "text/html"}


@route("/async/user/<string:name>", methods=["GET"])
async def user_info(request, name):
    return render_html(request, "user/info.html", name=name)


@route("/async/arg/<arg>", methods=["GET"])
async def demo_args(request, arg: str):
    return {
        "code": 200,
        "result": "async hello {}".format(arg)
    }


@route("/async/openapi", methods=["GET"])
async def demo_openapi(request):
    """
    responses:
      200:
        description: A Hello.
    """
    return {
        "code": 200,
        "result": "hello world"
    }


@websocket_route("/async/ws/echo")
async def ws_echo(socket: WebSocket):
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


@bp_async.route("/user/<string:name>", methods=["GET"])
async def bp_user_info(request, name):
    logger.info("user name %s" % name)
    return render_html(request, "user/info.html", name=name)

register_blueprint(bp_async, url_prefix="/asyncbp")
