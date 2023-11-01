# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

import json
import asyncio

from fastapi import FastAPI, WebSocket

from app.utils import Process
from app.models import Flow


def run_from_file(path: str, debug: bool = False):
    with open(path, "r") as f:
        process = Process(Flow(**json.loads(f.read())), debug=debug)
    return asyncio.run(process.run())


def create_app(debug: bool = False):
    app = FastAPI()

    def print_debug(message: str):
        if debug:
            print(message)

    @app.post("/api/run")
    async def run(body: Flow):
        process = Process(body, debug=debug)
        print_debug("Starting process")
        asyncio.create_task(process.run())
        return "Started process."

    @app.websocket("/ws/run")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()

        async def send_update(update):
            print_debug(f"Sending update: {update}")
            await websocket.send_json(update)

        processing = False

        while True:
            data = await websocket.receive_json()
            print_debug("Received data")
            await websocket.send_text("Received data.")
            if not processing:
                print_debug("Processing")
                await websocket.send_text("Processing.")
                processing = True
                try:
                    flow = Flow(**data)
                except Exception:
                    await websocket.send_text("Invalid flow data.")
                    await websocket.close()
                    break

                process = Process(flow, update=send_update, debug=debug)
                await process.run()
                print_debug("Finished processing")
                await websocket.send_text("Finished processing.")
                processing = False
            elif "cancel" in data:
                print_debug("Cancelling")
                await websocket.send_text("Stopping process.")
                process._cancel = True
                await websocket.send_text("Closing connection per user request.")
                await websocket.close()
                break
            else:
                print_debug("Already processing")
                await websocket.send_text("Already processing.")
        print_debug("Closing connection")
        await websocket.close()

    return app


def create_debug_app():
    return create_app(debug=True)
