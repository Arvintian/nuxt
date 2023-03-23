from nuxt import logger
from nuxt.asyncio import JSONResponse
import traceback


class M3(object):

    def __init__(self, app):
        self.app = app
        # One-time configuration and initialization.
        logger.info("m3 init")

    async def __call__(self, scope, receive, send) -> None:
        logger.info("m3 process request")
        await self.app(scope, receive, send)
        logger.info("m3 process finish")


class M4(object):

    def __init__(self, app):
        self.app = app
        # One-time configuration and initialization.
        logger.info("m4 init")

    async def __call__(self, scope, receive, send) -> None:
        try:
            logger.info("m4 process request")
            await self.app(scope, receive, send)
            logger.info("m4 process finish")
        except Exception as e:
            await JSONResponse({
                "code": -1,
                "msg": "{}".format(e)
            })(scope, receive, send)
            logger.error(traceback.format_exc())


class M5(object):

    def __init__(self, app):
        self.app = app
        # One-time configuration and initialization.
        logger.info("m5 init")

    async def __call__(self, scope, receive, send) -> None:
        logger.info("m5 process request")
        await self.app(scope, receive, send)
        logger.info("m5 process finish")
