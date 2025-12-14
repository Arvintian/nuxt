import os


def run():
    if os.name == "nt":  # windows platform
        from nuxt.__main_uvicorn import run as nt_run
        return nt_run()
    from nuxt.__main_gunicorn import run as posix_run
    return posix_run()
