import os


def getcwd():
    # get current path, try to use PWD env first
    try:
        a = os.stat(os.environ['PWD'])
        b = os.stat(os.getcwd())
        if a.st_ino == b.st_ino and a.st_dev == b.st_dev:
            cwd = os.environ['PWD']
        else:
            cwd = os.getcwd()
    except Exception:
        cwd = os.getcwd()
    return cwd


def remove_suffix(s: str, suffix: str) -> str:
    if suffix and s.endswith(suffix):
        return s[:-len(suffix)]
    else:
        return s[:]


def to_asgi_pattern(pattern: str) -> str:
    raw = pattern.replace("<", "{").replace(">", "}")
    out = []
    for c in raw:
        if c != "}":
            out.append(c)
        else:
            param = []
            x = out.pop()
            while x != "{":
                param.append(x)
                x = out.pop()
            param.reverse()
            params = "".join(param).split(":")
            if len(params) < 2:
                out.append("{%s}" % (params[0]))
            else:
                out.append("{%s:%s}" % (params[1], __convertor_type(params[0])))
    return "".join(out)


def __convertor_type(_type: str):
    if _type == "string":
        return "str"
    return _type
