from starlette.types import ASGIApp, Receive, Scope, Send
from nuxt.asyncio.proxies.context import ProxyContext, ProxyConfig, BaseURLProxyConfigMixin
from nuxt.asyncio.proxies.http import proxy_http
from nuxt.asyncio.proxies.websocket import proxy_websocket
from urllib.parse import urlparse
import traceback
import logging


log = logging.getLogger(__name__)


def make_proxy_response(upstream_base_url: str) -> ASGIApp:
    """
    Given a upstream_base_url, return a simple ASGI application that can proxy
    HTTP and WebSocket connections.

    The handlers for the protocols can be overridden and/or removed with the
    respective parameters.
    """

    proxy_http_handler = proxy_http
    proxy_websocket_handler = proxy_websocket
    config = type(
        "Config",
        (BaseURLProxyConfigMixin, ProxyConfig),
        {
            "upstream_base_url": upstream_base_url,
            "rewrite_host_header": urlparse(upstream_base_url).netloc,
        },
    )()
    proxy_context = ProxyContext(config)

    async def response(scope: Scope, receive: Receive, send: Send):  # noqa: ANN201
        try:
            if scope["type"] == "lifespan":
                return await proxy_context.close()  # We explicitly do nothing here for this simple app.
            if scope["type"] == "http" and proxy_http_handler:
                await proxy_http_handler(
                    context=proxy_context, scope=scope, receive=receive, send=send
                )
                return await proxy_context.close()
            if scope["type"] == "websocket" and proxy_websocket_handler:
                await proxy_websocket_handler(
                    context=proxy_context, scope=scope, receive=receive, send=send
                )
                return await proxy_context.close()
            raise NotImplementedError(f"Scope {scope} is not understood")
        except Exception as e:
            log.error(traceback.format_exc())
            return await proxy_context.close()

    return response
