# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

import os
import json
import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.utils.logs import global_logger, log_queue
from app.utils import Process
from app.models import Flow


def run_from_file(path: str):
    with open(path, "r") as f:
        process = Process(Flow(**json.loads(f.read())))
    return asyncio.run(process.run())


def create_app():
    local = os.getenv("PFA_LOCAL", "True").lower() == "true"
    db_class = os.getenv("PFA_DB_CLASS", "app.utils.SimpleInMemoryDB")
    module_name, class_name = db_class.rsplit(".", 1)
    module = __import__(module_name, fromlist=[class_name])
    db = getattr(module, class_name)()

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

    @app.get("/api/settings")
    async def get_settings(setting: str):
        if not db:
            raise ReferenceError("No database setup.")
        return db.read_settings(setting)

    @app.post("/api/settings")
    async def save_settings(setting: str):
        if not db:
            raise ReferenceError("No database setup.")
        return db.create_settings(setting)

    @app.put("/api/settings")
    async def update_settings(setting: str):
        if not db:
            raise ReferenceError("No database setup.")
        return db.update_settings(setting)

    @app.delete("/api/settings")
    async def delete_settings(setting: str):
        if not db:
            raise ReferenceError("No database setup.")
        return db.delete_settings(setting)

    @app.get("/api/flow")
    async def get(flow_id: str):
        if not db:
            raise ReferenceError("No database setup.")
        return db.read_flow(flow_id)

    @app.post("/api/flow")
    async def save(body: Flow):
        if not db:
            raise ReferenceError("No database setup.")
        return db.create_flow(body)

    @app.put("/api/flow")
    async def update(body: Flow):
        if not db:
            raise ReferenceError("No database setup.")
        return db.update_flow(body)

    @app.delete("/api/flow")
    async def delete(flow_id: str):
        if not db:
            raise ReferenceError("No database setup.")
        return db.delete_flow(flow_id)

    @app.post("/api/run")
    async def api_run(body: Flow = None, flow_id: str = None):
        if db and flow_id:
            body = db.read(flow_id)
        if not body:
            raise AttributeError("Missing flow data.")
        process = Process(body)
        asyncio.create_task(process.run())
        return "Started process."

    @app.websocket("/ws/run")
    async def websocket_run(websocket: WebSocket):
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
                await log_queue.put((global_logger, "debug", "Process completed"))
                await send_update("Process completed.")
                process_task = None
                process = None

            done, pending = await asyncio.wait(
                [receive_task, process_task] if process_task else [receive_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if process_task in done:
                await log_queue.put((global_logger, "debug", "Process completed"))
                await send_update("Process completed.")
                process_task = None
                process = None
                continue

            if receive_task in done:
                data = done.pop().result()

                if "stop" in data:
                    if process_task:
                        process_task.cancel()
                        await log_queue.put((global_logger, "debug", "Stopping process per user request"))
                        await send_update("Stopping process per user request.")
                    else:
                        await log_queue.put((global_logger, "debug", "No process running."))
                        await send_update("No process running.")
                else:
                    if process_task is None:
                        try:
                            flow = Flow(**data)
                            process = Process(flow, update=send_update, ws=True)
                            process_task = asyncio.create_task(process.run())
                            await log_queue.put((global_logger, "debug", "Starting process"))
                            await send_update("Starting process.")
                        except Exception as e:
                            await log_queue.put((global_logger, "debug", f"Invalid flow data: {str(e)}"))
                            await send_update(f"Invalid flow data: {str(e)}")
                    else:
                        await log_queue.put((global_logger, "debug", 
                            "Process already running. Ignoring new process request."
                        ))
                        await send_update(
                            "Process already running. Ignoring new process request."
                        )

                receive_task = asyncio.create_task(websocket.receive_json())

    return app
