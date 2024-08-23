# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware


def create_app():
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/log")
    async def log(request: Request):
        print(f"request headers: {dict(request.headers.items())}")
        print(f"request query params: {dict(request.query_params.items())}")
        try:
            print(f"request json: {await request.json()}")
        except:
            print(f"request body: {await request.body()}")
        return "received"

    return app

if __name__ == "__main__":
    app = create_app()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)