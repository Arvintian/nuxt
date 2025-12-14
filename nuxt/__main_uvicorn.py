from nuxt.app import NuxtApplication
from nuxt.utils import getcwd, remove_suffix
from nuxt.staticfiles import StaticFiles
from nuxt.openapi import SchemaGenerator
from nuxt.routing import Mount
from uvicorn import Config as UVConfig, Server
from uvicorn.supervisors import ChangeReload, Multiprocess
from copy import deepcopy
import sys
import click
import os
import importlib
import json

STARTUP_FAILURE = 3


class Config(UVConfig):

    def __init__(self, cfg, module, openapi, openapi_url_path, static, static_index, static_url_path,
                 debug: bool, address: str, port: int, workers: int):
        self.cfg = cfg
        self.module = module
        self.openapi, self.openapi_url_path = openapi, openapi_url_path
        self.static, self.static_index, self.static_url_path = static, static_index, static_url_path
        uvicorn_options = {
            "host": address,
            "port": port,
            "workers": workers
        }
        uvicorn_cfg = cfg.get("uvicorn", {})
        if uvicorn_cfg:
            uvicorn_options.update(uvicorn_cfg)
        if debug:
            uvicorn_options.update({
                "workers": 1,
                "reload": True
            })
        super().__init__(app="nuxt.app:entry_app", **uvicorn_options)

    def load(self):
        super().load()
        entry_app: NuxtApplication = self.loaded_app.app
        # 1.1 reinit app with cfg
        entry_app.__init__(self.cfg)
        # 2. import user's module
        if self.module:
            _module = remove_suffix(self.module, ".py")
            importlib.import_module(_module)
        # 3. setup internel route
        if self.openapi:
            openapi_cfg: dict = self.cfg.get("openapi")
            schemas = SchemaGenerator(openapi_cfg.get("base_schema"), url_prefx=self.openapi_url_path)
            entry_app.routes.extend(schemas.routes())
        if self.static:
            if not self.static_url_path:
                self.static_url_path = "/"+os.path.basename(os.path.realpath(self.static))
            entry_app.routes.append(Mount(self.static_url_path, app=StaticFiles(directory=self.static,
                                    list_directory=self.static_index, html=True), name="async.nuxt.static"))
        if self.cfg["debug"]:
            for route in entry_app.routes:
                entry_app.logger.debug(route)


def settings(cfg: dict) -> dict:
    res = deepcopy(cfg)
    # ignore command line args
    ignore_command = ["debug"]
    for key in ignore_command:
        res.pop(key, None)
    # ignore command uvicorn config
    ignore_uvicorn = ["host", "port", "workers", "reload"]
    uvicorn = res.get("uvicorn", {})
    for key in ignore_uvicorn:
        uvicorn.pop(key, None)
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
    config = Config(cfg, module, openapi, openapi_url_path, static, static_index, static_url_path,
                    debug, address, port, workers)
    server = Server(config=config)
    try:
        if config.should_reload:
            sock = config.bind_socket()
            ChangeReload(config, target=server.run, sockets=[sock]).run()
        elif config.workers > 1:
            sock = config.bind_socket()
            Multiprocess(config, target=server.run, sockets=[sock]).run()
        else:
            server.run()
    except KeyboardInterrupt:
        pass  # pragma: full coverage
    finally:
        if config.uds and os.path.exists(config.uds):
            os.remove(config.uds)  # pragma: py-win32

    if not server.started and not config.should_reload and config.workers == 1:
        sys.exit(STARTUP_FAILURE)
