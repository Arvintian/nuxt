# Nuxt

Nuxt is a integration framework for build web app with python, built on top of [Madara](https://github.com/Arvintian/madara)/[Starlette](https://github.com/encode/starlette)/[Gunicorn](https://github.com/benoitc/gunicorn)/[Uvicorn](https://github.com/encode/uvicorn).

* [Install](#install)
* [Usage](#usage)
* [QuickStart](#quickstart)
* [User’s Guide](#users-guide)
    * [Routing](#routing)
    * [Request](#request)
    * [Response](#response)
    * [Template](#template)
    * [Static](#static)
    * [Blueprint](#blueprint)
    * [Middleware](#middleware)
* [AsyncIO](#asyncio)
* [API Schemas](#api-schemas)
* [Design](#design)

## Install

```
pip install nuxt
```

## Usage

```
Usage: nuxt [OPTIONS]

Options:
  --module TEXT            Your python module.
  --config TEXT            Your nuxt app config json file path.
  --openapi BOOLEAN        Enable openapi schema and swagger ui.
  --openapi-url-path TEXT  Openapi schema and ui path, default is /docs
  --static TEXT            Your static file directory path.
  --static-index BOOLEAN   Display the index page if path in static is dir.
  --static-url-path TEXT   Your static url path, default is static directory path basename.
  --debug BOOLEAN          Enable nuxt app debug mode.
  --address TEXT           Listen and serve address.
  --port INTEGER           Listen and serve port.
  --workers INTEGER        Prefork work count, default is cpu core count.
  --help                   Show this message and exit.
```


## QuickStart

```
> cat example.py

from nuxt import route

@route("/demo", methods=["GET"])
def demo(request):
    return {
        "code": 200,
        "result": "hello"
    }

> nuxt --module example

[2021-04-27 12:07:56 +0800] [4284] [INFO] Starting gunicorn 20.1.0
[2021-04-27 12:07:56 +0800] [4284] [INFO] Listening at: http://0.0.0.0:5000 (4284)
[2021-04-27 12:07:56 +0800] [4284] [INFO] Using worker: uvicorn.workers.UvicornWorker
[2021-04-27 12:07:56 +0800] [4287] [INFO] Booting worker with pid: 4287
[2021-04-27 12:07:56 +0800] [4288] [INFO] Booting worker with pid: 4288

> curl -v http://127.0.0.1:5000/demo
```

## User’s Guide

### Routing

Use the route() decorator to bind a function to a URL.

```
@route('/')
def index(request):
    return 'Index Page'

@route('/hello')
def hello(request):
    return 'Hello, World'
```

You can add variable sections to a URL by marking sections with <variable_name>. Your function then receives the <variable_name> as a keyword argument. Optionally, you can use a converter to specify the type of the argument like <converter:variable_name>.

```
@route('/user/<username>')
def show_user_profile(request, username):
    # show the user profile for that user
    return 'User %s' % escape(username)

@route('/post/<int:post_id>')
def show_post(request, post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id
```

Converter types:

- `string` (default) accepts any text without a slash

- `int` accepts positive integers

- `float` accepts positive floating point values

- `path` like string but also accepts slashes

- `uuid` accepts UUID strings

Web applications use different HTTP methods when accessing URLs. You should familiarize yourself with the HTTP methods as you work with Nuxt. By default, a route only answers to GET requests. You can use the methods argument of the route() decorator to handle different HTTP methods.

```
@route('/login', methods=['GET', 'POST'])
def login(request):
    if request.method == 'POST':
        return do_the_login()
    else:
        return show_the_login_form()
```

### Request

For web applications it’s crucial to react to the data a client sends to the server. In Nuxt this information is provided by the first param `request` object to your function.

The nuxt request object just a warp of [werkzeug request](https://werkzeug.palletsprojects.com/en/1.0.x/wrappers/#werkzeug.wrappers.Request), so your can access request data by werkzeug's methods.

### Response

The return value from a view function is automatically converted into a [werkzeug response](https://werkzeug.palletsprojects.com/en/1.0.x/wrappers/#werkzeug.wrappers.Response) for you. If the return value is a dict, which will serialize any supported JSON data type and set mimetype to application/json.


### Template

Nuxt's template engine powered by [jinja](https://jinja.palletsprojects.com/en/3.1.x/).

```
from nuxt import render_template
from nuxt import route

@route("/", methods=["GET"])
def index(request):
    return render_template(request, "index.html", user="Arvin"), {"content-type": "text/html"}
```

### Static

Nuxt can be convenient serve static files.

```
nuxt --static <directory path> --static-url-path  <request base url path>
```

### Blueprint

A Blueprint is a way to organize a group of related views and other code. Rather than registering views and other code directly with an application, they are registered with a blueprint.

```
from nuxt import Blueprint,register_blueprint

bp_example = Blueprint("bp_example")

@bp_example.route("/item", methods=["POST"])
def blueprint_route(request: Request):
    data = request.get_json()
    return {
        "code": 0,
        "result": data,
    }

register_blueprint(bp_example, url_prefix="/blueprint")
```

### Middleware

Middleware is a framework of hooks into Nuxt’s request/response processing. It’s a light, low-level “plugin” system for globally altering input or output.

```
class SimpleMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    def process_view(self, request, callback, callback_kwargs):
        return None

    def process_exception(self, request, exception):
        return None
```

The `get_response` callable provided by Nuxt might be the actual view (if this is the last listed middleware) or it might be the next middleware in the chain.

`process_view()` is called just before Nuxt calls the view. It should return either None or an response object. If it returns None, Nuxt will continue processing this request, executing any other `process_view()` middleware and, then, the appropriate view. If it returns an response object, Nuxt won’t bother calling the appropriate view; it’ll apply response middleware to that response and return the result.

Nuxt calls `process_exception()` when a view raises an exception. process_exception() should return either None or an response object.


## AsyncIO

The AsyncIO submodule of Nuxt supports Python's asyncio, allowing Request and Response objects to work in asynchronous mode. Additionally, it enables the implementation of Websockets. Route and Blueprint in an asynchronous manner while maintaining consistency with synchronous mode.

```
from nuxt.asyncio import Blueprint, register_blueprint
from nuxt.asyncio import Request, WebSocket, WebSocketDisconnect
from nuxt.asyncio import route, websocket_route


@websocket_route("/ws/echo")
async def ws_echo(socket: WebSocket):
    await socket.accept()
    try:
        while True:
            text = await socket.receive_text()
            recv = "echo:{}".format(text)
            await socket.send_text(recv)
    except WebSocketDisconnect as e:
        pass


@route("/user/<string:name>", methods=["GET"])
async def user_info(request: Request, name):
    return "hello,{}".format(name)


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


@bp_async.route("/user/<string:name>", methods=["GET"])
async def bp_user_info(request, name):
    return "hello,{}".format(name)

register_blueprint(bp_async, url_prefix="/asyncbp")
```

In asynchronous mode, nuxt's objects is warp of starlette's [request](https://www.starlette.io/requests/) and [response](https://www.starlette.io/responses/) and [websocket](https://www.starlette.io/websockets/).


## API Schemas

Nuxt supports automatically generating API schemas and provides web documentation pages based on Swagger.

```
nuxt --module example --openapi true

> schemas page on: http://127.0.0.1:5000/docs
```

## Design

Nuxt use uvicorn web server as the frontend, dispatch http request to wsgi/madara handlers or static file handlers, dispatch websocket request to asgi/starlette handlers.