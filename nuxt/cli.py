import sys
import click
import os
import importlib
from gunicorn.app.base import BaseApplication
from .wsgi_app import app
from .utils import getcwd
import json


def start_server(address, port, workers):
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
            return self.application

    options = {
        "bind": "{}:{}".format(address, port),
        "workers": workers,
        "accesslog": "-",
        "errorlog": "-",
    }
    gunicorn_options = app.config.get("gunicorn", {})
    if gunicorn_options:
        options.update(gunicorn_options)
    if app.config.get("debug"):
        app.logger.debug("gunicron config:{}".format(options))
    WebApplication(app, options).run()


@click.command()
@click.option("--module", default="", help="Your python module.")
@click.option("--config", default="", help="Your nuxt app config json file path.")
@click.option("--address", default="0.0.0.0", help="Listen and serve address.")
@click.option("--port", default=5000, help="Listen and serve port.")
@click.option("--workers", default=os.cpu_count(), help="Prefork work count, default is cpu core count.")
def run(module: str, config: str, address: str, port: int, workers: int):
    chdir = getcwd()
    os.chdir(chdir)
    # add the path to sys.path
    if chdir not in sys.path:
        sys.path.insert(0, chdir)
    # 1. load user config
    if config:
        with open(config) as fd:
            cfg: dict = json.loads(fd.read())
            app.__init__(cfg)
    # 2. import user's module
    _module = module.rstrip(".py")
    importlib.import_module(_module)
    # 3. start http server
    start_server(address, port, workers)
