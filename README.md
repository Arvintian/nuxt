# nuxt

nuxt is a tool let your python function run as a server.

Install

```

pip install nuxt

```

Usage

```

Usage: nuxt [OPTIONS]

Options:
  --module TEXT      Your python module.
  --address TEXT     Listen and serve address.
  --port INTEGER     Listen and serve port.
  --workers INTEGER  Prefork work count, default is cpu core count.
  --help             Show this message and exit.

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


* About to connect() to 127.0.0.1 port 5000 (#0)
*   Trying 127.0.0.1...
* Connected to 127.0.0.1 (127.0.0.1) port 5000 (#0)
> GET /demo HTTP/1.1
> User-Agent: curl/7.29.0
> Host: 127.0.0.1:5000
> Accept: */*
>
< HTTP/1.1 200 OK
< Server: gunicorn
< Date: Tue, 27 Apr 2021 04:08:52 GMT
< Connection: close
< Content-Type: application/json
< Content-Length: 30
<
{"code":200,"result":"hello"}
* Closing connection 0

```