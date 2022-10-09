# nuxt

Nuxt is a integration tools for build web app with python, built on top of [Madara](https://github.com/Arvintian/madara)/[Starlette](https://github.com/encode/starlette)/[Gunicorn](https://github.com/benoitc/gunicorn)/[Uvicorn](https://github.com/encode/uvicorn).

Install

```

pip install nuxt

```

Usage

```

Usage: nuxt [OPTIONS]

Options:
  --module TEXT           Your python module.
  --config TEXT           Your nuxt app config json file path.
  --static TEXT           Your static file directory path.
  --static-url-path TEXT  Your static url path.
  --debug BOOLEAN         Enable nuxt app debug mode.
  --address TEXT          Listen and serve address.
  --port INTEGER          Listen and serve port.
  --workers INTEGER       Prefork work count, default is cpu core count.
  --help                  Show this message and exit.

```


QuickStart

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
[2021-04-27 12:07:56 +0800] [4284] [INFO] Using worker: sync
[2021-04-27 12:07:56 +0800] [4287] [INFO] Booting worker with pid: 4287
[2021-04-27 12:07:56 +0800] [4288] [INFO] Booting worker with pid: 4288

> curl -v http://127.0.0.1:5000/demo

```