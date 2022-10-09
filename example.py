from nuxt import Request, WebSocket, WebSocketDisconnect
from nuxt import route, websocket_route
from nuxt import config, logger
from nuxt.repositorys.validation import use_args, fields


@route("/demo", methods=["GET"])
def demo(request):
    return {
        "code": 200,
        "result": "hello world"
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


@websocket_route("/ws/echo")
async def ws_echo(socket: WebSocket):
    await socket.accept()
    try:
        while True:
            text = await socket.receive_text()
            recv = "echoeeeeeeee:{}".format(text)
            await socket.send_text(recv)
    except WebSocketDisconnect as e:
        pass
    except Exception as e:
        logger.error(e)
