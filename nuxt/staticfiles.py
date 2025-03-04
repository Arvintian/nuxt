from starlette.staticfiles import StaticFiles as _StaticFiles
from starlette.staticfiles import PathLike
from starlette.datastructures import URL
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse, RedirectResponse, Response
from starlette.types import Scope, Receive, Send
from starlette.websockets import WebSocket
from html import escape as htmlescape
from urllib import parse as urllibparse
import typing
import anyio
import stat
import sys
import os


class StaticFiles(_StaticFiles):

    def __init__(self, *,
                 directory: typing.Optional[PathLike] = None,
                 packages: typing.Optional[typing.List[typing.Union[str, typing.Tuple[str, str]]]] = None,
                 html: bool = False,
                 check_dir: bool = True,
                 follow_symlink: bool = False,
                 list_directory: bool = False) -> None:
        super().__init__(directory=directory, packages=packages, html=html, check_dir=check_dir, follow_symlink=follow_symlink)
        self.is_list_directory = list_directory

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        The ASGI entry point.
        """
        if scope["type"] == "websocket":
            socket = WebSocket(scope=scope, receive=receive, send=send)
            return await socket.close()

        assert scope["type"] == "http"

        if not self.config_checked:
            await self.check_config()
            self.config_checked = True

        path = self.get_path(scope)
        response = await self.get_response(path, scope)
        await response(scope, receive, send)

    async def get_response(self, path: str, scope: Scope) -> Response:
        """
        Returns an HTTP response, given the incoming path, method and request headers.
        """
        if scope["method"] not in ("GET", "HEAD"):
            raise HTTPException(status_code=405)

        try:
            full_path, stat_result = await anyio.to_thread.run_sync(
                self.lookup_path, path
            )
        except PermissionError:
            raise HTTPException(status_code=401)
        except OSError:
            raise

        if stat_result and stat.S_ISREG(stat_result.st_mode):
            # We have a static file to serve.
            return self.file_response(full_path, stat_result, scope)

        elif stat_result and stat.S_ISDIR(stat_result.st_mode) and self.html:
            # We're in HTML mode, and have got a directory URL.
            # Check if we have 'index.html' file to serve.
            index_path = os.path.join(path, "index.html")
            full_path, stat_result = await anyio.to_thread.run_sync(
                self.lookup_path, index_path
            )
            if stat_result is not None and stat.S_ISREG(stat_result.st_mode):
                if not scope["path"].endswith("/"):
                    # Directory URLs should redirect to always end in "/".
                    url = URL(scope=scope)
                    url = url.replace(path=url.path + "/")
                    return RedirectResponse(url=url)
                return self.file_response(full_path, stat_result, scope)

            if stat_result is None and self.is_list_directory:
                return await anyio.to_thread.run_sync(self.list_directory, path)

        if self.html:
            # Check for '404.html' if we're in HTML mode.
            full_path, stat_result = await anyio.to_thread.run_sync(
                self.lookup_path, "404.html"
            )
            if stat_result and stat.S_ISREG(stat_result.st_mode):
                return FileResponse(
                    full_path,
                    stat_result=stat_result,
                    method=scope["method"],
                    status_code=404,
                )
        raise HTTPException(status_code=404)

    def list_directory(self, path):
        dir_list = os.listdir(path)
        dir_list.sort(key=lambda a: a.lower())
        r = []
        displaypath = urllibparse.unquote(os.path.basename(os.path.realpath(path)), errors='surrogatepass')
        displaypath = htmlescape(displaypath, quote=False)
        enc = sys.getfilesystemencoding()
        title = 'Directory listing for %s' % displaypath
        r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
                 '"http://www.w3.org/TR/html4/strict.dtd">')
        r.append('<html>\n<head>')
        r.append('<meta http-equiv="Content-Type" '
                 'content="text/html; charset=%s">' % enc)
        r.append('<title>%s</title>\n</head>' % title)
        r.append('<body>\n<h1>%s</h1>' % title)
        r.append('<hr>\n<ul>')
        for name in dir_list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            r.append('<li><a href="%s">%s</a></li>' % (urllibparse.quote(linkname, errors='surrogatepass'), htmlescape(displayname, quote=False)))
        r.append('</ul>\n<hr>\n</body>\n</html>\n')
        encoded = '\n'.join(r).encode(enc, 'surrogateescape')

        return Response(encoded, status_code=200, headers={
            "Content-type": "text/html; charset=%s" % enc,
            "Content-Length": str(len(encoded))
        })
