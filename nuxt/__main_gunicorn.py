from nuxt.app import NuxtApplication, entry_app
from nuxt.utils import getcwd, remove_suffix
from nuxt.reloader import reloader_engines
from nuxt.staticfiles import StaticFiles
from nuxt.openapi import SchemaGenerator
from nuxt.routing import Mount
from gunicorn.app.base import BaseApplication
from gunicorn.workers.base import Worker
from copy import deepcopy
from types import ModuleType
import traceback
import threading
import sys
import click
import os
import importlib
import json


class WebApplication(BaseApplication):

    def __init__(self, application: NuxtApplication, module: ModuleType, options=None):
        self.options: dict = options or {}
        self.application: NuxtApplication = application
        self.module = module
        self.setup()
        super().__init__()

    def setup(self):
        if self.options.get("debug"):
            self.options.update({
                "post_fork": self.post_fork
            })

    def reload_app(self, fname: str):
        try:
            should_reload = False
            for module in tuple(sys.modules.values()):
                if getattr(module, '__file__', "") == fname:
                    should_reload = True
                    break
            if not should_reload:
                return
            # reinit application
            static_routes_count = (1 if self.application.config.get("static") else 0) + (2 if self.application.config.get("openapi") else 0)
            static_routes = self.application.routes[-static_routes_count:]
            self.application.__init__(self.application.config)
            # reload modified module
            for module in tuple(sys.modules.values()):
                if module == self.module:
                    continue
                if getattr(module, '__file__', "") == fname:
                    importlib.reload(module)
            # realod entry module
            importlib.reload(self.module)
            self.application.routes.extend(static_routes)
            self.application.logger.info("Worker reloading: %s modified", fname)
            for route in self.application.routes:
                entry_app.logger.debug(route)
        except Exception as e:
            self.application.logger.error("Worker reload error {}".format(traceback.format_exc()))

    def post_fork(self, server, worker: Worker):
        reloader_cls = reloader_engines["auto"]
        reloader: threading.Thread = reloader_cls(extra_files=[], callback=self.reload_app)
        reloader.start()
        self.application.logger.debug("Worker {} start reload watch threading".format(worker.pid))

    def load_config(self):
        the_config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
        for key, value in the_config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def start_server(address, port, workers, module):
    """
    启动 http server
    """
    gunicorn_options = {
        "bind": "{}:{}".format(address, port),
        "workers": workers,
        "accesslog": "-",
        "errorlog": "-",
        "reload": False,
        "preload": False,
    }
    # compatible with gunicorn cfg
    gunicorn_cfg = entry_app.config.get("gunicorn", {})
    if gunicorn_cfg:
        gunicorn_options.update(gunicorn_cfg)
    gunicorn_options.update({
        "debug": entry_app.config.get("debug", False),
        "worker_class": "uvicorn_worker.UvicornWorker"
    })
    if entry_app.config.get("debug"):
        gunicorn_options.update({"workers": 1})
    WebApplication(entry_app, module, gunicorn_options).run()


def settings(cfg: dict) -> dict:
    res = deepcopy(cfg)
    # ignore command line args
    ignore_command = ["debug"]
    for key in ignore_command:
        res.pop(key, None)
    # ignore command gunicorn config
    ignore_gunicorn = ["bind", "workers", "reload", "preload"]
    gunicorn = res.get("gunicorn", {})
    for key in ignore_gunicorn:
        gunicorn.pop(key, None)
    return res


@click.command()
@click.option("--module", default="nuxt.repositorys.empty", type=str, help="Your python module.")
@click.option("--config", default="", type=str, help="Your nuxt app config json file path.")
@click.option("--openapi", default=False, type=bool, help="Enable openapi schema and swagger ui.")
@click.option("--openapi-url-path", default="/docs", type=str, help="Openapi schema and ui path, default is /docs")
@click.option("--static", default="", type=str, help="Your static file directory path.")
@click.option("--static-index", default=False, type=bool, help="Display the index page if path in static is dir.")
@click.option("--static-url-path", default="", type=str, help="Your static url path, default is static directory path basename.")
@click.option("--debug", default=False, type=bool, help="Enable nuxt app debug mode.")
@click.option("--address", default="0.0.0.0", type=str, help="Listen and serve address.")
@click.option("--port", default=5000, type=int, help="Listen and serve port.")
@click.option("--workers", default=os.cpu_count(), type=int, help="Prefork work count, default is cpu core count.")
def run(module: str, config: str, openapi: bool, openapi_url_path: str, static: str, static_index: bool, static_url_path,
        debug: bool, address: str, port: int, workers: int):
    chdir = getcwd()
    os.chdir(chdir)
    # add the path to sys.path
    if chdir not in sys.path:
        sys.path.insert(0, chdir)
    # 1. load user config
    cfg = {
        "debug": debug,
        "openapi": {
            "enable": openapi,
            "base_schema": {
                "openapi": "3.0.0"
            }
        },
        "static": static != ""
    }
    if config:
        with open(config, "r", encoding="utf-8") as fd:
            json_cfg: dict = settings(json.loads(fd.read()))
            cfg.update(json_cfg)
    # 1.1 reinit app with cfg
    entry_app.__init__(cfg)
    # 2. import user's module
    module_type = None
    if module:
        _module = remove_suffix(module, ".py")
        module_type = importlib.import_module(_module)
    # 3. setup internel route
    if openapi:
        openapi_cfg: dict = cfg.get("openapi")
        schemas = SchemaGenerator(openapi_cfg.get("base_schema"), url_prefx=openapi_url_path)
        entry_app.routes.extend(schemas.routes())
    if static:
        if not static_url_path:
            static_url_path = "/"+os.path.basename(os.path.realpath(static))
        entry_app.routes.append(Mount(static_url_path, app=StaticFiles(directory=static, list_directory=static_index, html=True), name="async.nuxt.static"))
    if cfg["debug"]:
        for route in entry_app.routes:
            entry_app.logger.debug(route)
    # 4. start http server
    start_server(address, port, workers, module_type)
