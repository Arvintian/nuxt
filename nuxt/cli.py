import sys
import click
import os
import importlib
from gunicorn.app.base import BaseApplication
from .wsgi_app import app
from .utils import getcwd
import json


def start_server(address, port, workers, module):
    """
    启动 http server
    """

    class WebApplication(BaseApplication):

        def __init__(self, application, options=None):
            self.options = options or {}
            self.application = application
            super().__init__()

        def load_config(self):
            the_config = {key: value for key, value in self.options.items()
                          if key in self.cfg.settings and value is not None}
            for key, value in the_config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            if options.get("preload"):
                self.application.__init__(self.application.config)
                importlib.reload(module)
            return self.application

    options = {
        "bind": "{}:{}".format(address, port),
        "workers": workers,
        "accesslog": "-",
        "errorlog": "-",
    }
    # compatible with gunicorn cfg
    gunicorn_options = app.config.get("gunicorn", {})
    if gunicorn_options:
        options.update(gunicorn_options)
    # debug mode
    if app.config.get("debug"):
        options.update({
            "reload": True,
            "preload": True,
            "workers": 1
        })
        app.logger.debug("gunicron config:{}".format(options))
    WebApplication(app, options).run()


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
            json_cfg: dict = json.loads(fd.read())
            cfg.update(json_cfg)
    app.__init__(cfg)
    # 2. import user's module
    _module = module.rstrip(".py")
    module_type = importlib.import_module(_module)
    # 3. start http server
    start_server(address, port, workers, module_type)
