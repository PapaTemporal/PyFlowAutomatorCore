# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

import json
import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.utils import Process
from app.models import Flow


def run_from_file(path: str, debug: bool = False):
    with open(path, "r") as f:
        process = Process(Flow(**json.loads(f.read())), debug=debug)
    return asyncio.run(process.run())


def create_app(debug: bool = False):
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
        data = await websocket.receive_json()
        print_debug("Received data")
        await websocket.send_text("Received data.")

        async def send_update(update):
            print_debug(f"Sending update: {update}")
            await websocket.send_json(update)

        try:
            print_debug("Processing")
            await websocket.send_text("Processing.")
            flow = Flow(**data)
        except Exception:
            await websocket.send_text("Invalid flow data.")
            print_debug("Closing connection")
            await websocket.send_text("Closing connection")
            await websocket.close()
            return

        process = Process(flow, update=send_update, debug=debug)
        process_task = asyncio.create_task(process.run())
        receive_task = asyncio.create_task(websocket.receive_json())

        while True:
            done, pending = await asyncio.wait(
                [process_task, receive_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if process_task in done:
                print_debug("Finished processing")
                await websocket.send_text("Finished processing.")
                break

            if receive_task in done:
                data = done.pop().result()
                if "stop" in data:
                    process._cancel = True
                    process_task.cancel()
                    print_debug("Stopping process per user request")
                    await websocket.send_text("Stopping process per user request.")
                    if process_task.cancelled() or process_task.done():
                        break

            if not receive_task.cancelled() and not receive_task.done():
                receive_task = asyncio.create_task(websocket.receive_json())

    return app


def create_debug_app():
    return create_app(debug=True)
