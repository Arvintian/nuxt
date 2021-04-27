from madara.app import Madara

config = {
    "DEBUG": False,
    "middlewares": []
}

app = Madara()

route = app.route
