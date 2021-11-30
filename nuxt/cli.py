from nuxt.wsgi_app import app
from nuxt.utils import getcwd
from nuxt.reloader import reloader_engines
from madara.app import Madara
from gunicorn.app.base import BaseApplication
from gunicorn.workers.base import Worker
from copy import deepcopy
import traceback
import threading
import sys
import click
import os
import importlib
import json


class WebApplication(BaseApplication):

    def __init__(self, application, module, options=None):
        self.options: dict = options or {}
        self.application: Madara = application
        self.module = module
        self.setup()
        super().__init__()

    def setup(self):
        if self.application.config.get("debug"):
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
            self.application.__init__(self.application.config)
            # reload modified module
            for module in tuple(sys.modules.values()):
                if module == self.module:
                    continue
                if getattr(module, '__file__', "") == fname:
                    importlib.reload(module)
            # realod entry module
            importlib.reload(self.module)
            self.application.logger.info("Worker reloading: %s modified", fname)
        except Exception as e:
            self.application.logger.error("Worker reload error {}".format(traceback.format_exc()))

    def post_fork(self, server, worker: Worker):
        reloader_cls = reloader_engines["auto"]
        reloader: threading.Thread = reloader_cls(extra_files=[], callback=self.reload_app)
        reloader.start()
        self.application.logger.debug("Worker {} start reload watch threading".format(worker.pid))

    def load_config(self):
        the_config = {key: value for key, value in self.options.items()
                      if key in self.cfg.settings and value is not None}
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
    gunicorn_cfg = app.config.get("gunicorn", {})
    if gunicorn_cfg:
        gunicorn_options.update(gunicorn_cfg)
    WebApplication(app, module, gunicorn_options).run()


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
@click.option("--module", default="", type=str, help="Your python module.")
@click.option("--config", default="", type=str, help="Your nuxt app config json file path.")
@click.option("--debug", default=False, type=bool, help="Enable nuxt app debug mode.")
@click.option("--address", default="0.0.0.0", type=str, help="Listen and serve address.")
@click.option("--port", default=5000, type=int, help="Listen and serve port.")
@click.option("--workers", default=os.cpu_count(), type=int, help="Prefork work count, default is cpu core count.")
def run(module: str, config: str, debug: bool, address: str, port: int, workers: int):
    chdir = getcwd()
    os.chdir(chdir)
    # add the path to sys.path
    if chdir not in sys.path:
        sys.path.insert(0, chdir)
    # 1. load user config
    cfg = {
        "debug": debug
    }
    if config:
        with open(config) as fd:
            json_cfg: dict = settings(json.loads(fd.read()))
            cfg.update(json_cfg)
    app.__init__(cfg)
    # 2. import user's module
    _module = module.rstrip(".py")
    module_type = importlib.import_module(_module)
    # 3. start http server
    start_server(address, port, workers, module_type)
