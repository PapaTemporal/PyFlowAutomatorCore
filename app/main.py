# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

import json

from fastapi import FastAPI
from websocket_server import WebsocketServer

from app.utils import Process
from app.models import Flow


def run_from_file(path: str, debug: bool = False):
    with open(path, "r") as f:
        process = Process(Flow(**json.loads(f.read())), debug=debug)
    return process.run()


def create_app():
    app = FastAPI()

    @app.post("/run")
    async def run(body: Flow, debug: bool = False):
        process = Process(body, debug=debug)
        return await process.run()

    return app


# Called for every client connecting (after handshake)
def new_client(client, server):
    print(f"Client({client['id']}) connected from {client['address']}")


# Called for every client disconnecting
def client_left(client, server):
    print(f"Client({client['id']}) disconnected")


# Called when a client sends a message
def message_received(client, server, message):
    if len(message) > 200:
        message = message[:200] + ".."
    print(f"Client({client['id']}) said: {message}")


def create_ws_server(host: str = "127.0.0.1", port: int = 9001):
    server = WebsocketServer(host=host, port=port)
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    server.run_forever()
