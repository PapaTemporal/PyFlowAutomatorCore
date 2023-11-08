# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

import os
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


def create_app():
    local = os.getenv("PFA_LOCAL", "False").lower() == "true"
    trace = os.getenv("PFA_TRACE", "False").lower() == "true"
    db_class = os.getenv("PFA_DB_CLASS", "app.utils.SimpleInMemoryDB")
    module_name, class_name = db_class.rsplit(".", 1)
    module = __import__(module_name, fromlist=[class_name])
    db = getattr(module, class_name)()

    async def print_trace(message: str):
        if trace:
            print(message)

    app = FastAPI()

    if local:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:5173",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/api/flow")
    async def get(flow_id: str):
        if not db:
            raise ReferenceError("No database setup.")
        return db.read(flow_id)

    @app.post("/api/flow")
    async def save(body: Flow):
        if not db:
            raise ReferenceError("No database setup.")
        return db.create(body)

    @app.put("/api/flow")
    async def update(body: Flow):
        if not db:
            raise ReferenceError("No database setup.")
        return db.update(body)

    @app.delete("/api/flow")
    async def delete(flow_id: str):
        if not db:
            raise ReferenceError("No database setup.")
        return db.delete(flow_id)

    @app.post("/api/run")
    async def run(body: Flow = None, flow_id: str = None):
        if db and flow_id:
            body = db.read(flow_id)
        if not body:
            raise AttributeError("Missing flow data.")
        process = Process(body, debug=trace)
        await print_trace("Starting process")
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
                await print_trace("Process completed")
                await send_update("Process completed.")
                process_task = None
                process = None

            done, pending = await asyncio.wait(
                [receive_task, process_task] if process_task else [receive_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if process_task in done:
                await print_trace("Process completed")
                await send_update("Process completed.")
                process_task = None
                process = None
                continue

            if receive_task in done:
                data = done.pop().result()

                if "stop" in data:
                    if process_task:
                        process_task.cancel()
                        await print_trace("Stopping process per user request")
                        await send_update("Stopping process per user request.")
                    else:
                        await print_trace("No process running.")
                        await send_update("No process running.")
                else:
                    if process_task is None:
                        try:
                            flow = Flow(**data)
                            process = Process(flow, update=send_update, debug=trace)
                            process_task = asyncio.create_task(process.run())
                            await print_trace("Starting process")
                            await send_update("Starting process.")
                        except Exception as e:
                            await print_trace(f"Invalid flow data: {str(e)}")
                            await send_update(f"Invalid flow data: {str(e)}")
                    else:
                        await print_trace(
                            "Process already running. Ignoring new process request."
                        )
                        await send_update(
                            "Process already running. Ignoring new process request."
                        )

                receive_task = asyncio.create_task(websocket.receive_json())

    return app
