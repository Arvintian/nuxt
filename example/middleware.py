from nuxt import logger
from nuxt.asyncio import Response
import traceback


class M1(object):

    def __init__(self, get_response, app):
        self.current_app = app
        self.get_response = get_response
        # One-time configuration and initialization.
        logger.info("m1 init")

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        logger.info("m1 process request")

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        logger.info("m1 process response")

        return response

    def process_view(self, request, callback, callback_kwargs):
        logger.info("m1 process view")
        return None

    def process_exception(self, request, exception):
        logger.info("m1 process exception: {}".format(exception))
        logger.error(traceback.format_exc())
        return None


class M2(object):

    def __init__(self, get_response, app):
        self.current_app = app
        self.get_response = get_response
        # One-time configuration and initialization.
        logger.info("m2 init")

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        logger.info("m2 process request")

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        logger.info("m2 process response")

        return response

    def process_view(self, request, callback, callback_kwargs):
        logger.info("m2 process view")
        return None

    def process_exception(self, request, exception):
        logger.info("m2 process exception")
        logger.error(traceback.format_exc())
        return {
            "code": -1,
            "msg": "{}".format(exception)
        }


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
            rsp = Response({
                "code": -1,
                "msg": "{}".format(e)
            })
            logger.error(traceback.format_exc())


class M5(object):

    def __init__(self, app):
        self.app = app
        # One-time configuration and initialization.
        logger.info("m5 init")

    async def __call__(self, scope, receive, send) -> None:
        try:
            logger.info("m5 process request")
            await self.app(scope, receive, send)
            logger.info("m5 process finish")
        except Exception as e:
            logger.error(traceback.format_exc())
