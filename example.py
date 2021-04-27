from mux import route


@route("/demo", methods=["GET"])
def demo(request):
    return {
        "code": 200,
        "result": "hello"
    }
