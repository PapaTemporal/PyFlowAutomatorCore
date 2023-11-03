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
        process = None
        process_task = None
        receive_task = asyncio.create_task(websocket.receive_json())

        async def send_update(update):
            if isinstance(update, dict):
                await websocket.send_json(update)
            else:
                await websocket.send_text(update)

        while True:
            if process_task and process_task.done():
                print_debug("Process completed")
                await send_update("Process completed.")
                process_task = None
                process = None

            done, pending = await asyncio.wait(
                [receive_task, process_task] if process_task else [receive_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if process_task in done:
                print_debug("Process completed")
                await send_update("Process completed.")
                process_task = None
                process = None
                continue

            if receive_task in done:
                data = done.pop().result()

                if "stop" in data:
                    if process_task:
                        process_task.cancel()
                        print_debug("Stopping process per user request")
                        await send_update("Stopping process per user request.")
                    else:
                        print_debug("No process running.")
                        await send_update("No process running.")
                else:
                    if process_task is None:
                        try:
                            flow = Flow(**data)
                            process = Process(flow, update=send_update, debug=debug)
                            process_task = asyncio.create_task(process.run())
                            print_debug("Starting process")
                            await send_update("Starting process.")
                        except Exception as e:
                            print_debug(f"Invalid flow data: {str(e)}")
                            await send_update(f"Invalid flow data: {str(e)}")
                    else:
                        print_debug(
                            "Process already running. Ignoring new process request."
                        )
                        await send_update(
                            "Process already running. Ignoring new process request."
                        )

                receive_task = asyncio.create_task(websocket.receive_json())

    return app


def create_debug_app():
    return create_app(debug=True)
