# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

import json

from fastapi import FastAPI, WebSocket

from app.utils import Process
from app.models import Flow


def run_from_file(path: str, debug: bool = False):
    with open(path, "r") as f:
        process = Process(Flow(**json.loads(f.read())), debug=debug)
    return process.run()


def create_http_app():
    app = FastAPI()

    @app.post("/api/run")
    async def run(body: Flow, debug: bool = False):
        process = Process(body, debug=debug)
        return await process.run()

    return app


def create_ws_app():
    app = FastAPI()

    @app.websocket("/ws/run")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        while True:
            data = await websocket.receive_json()
            process = Process(Flow(**data))
            await websocket.send_json(await process.run())

    return app
