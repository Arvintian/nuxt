from nuxt import route
from nuxt import logger
from nuxt.asyncio import websocket_route, WebSocket, WebSocketDisconnect


@route("/proxy/demo", methods=["GET"])
def demo(request):
    return {
        "code": 200,
        "result": "hello"
    }


@websocket_route("/proxy/ws/echo")
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
