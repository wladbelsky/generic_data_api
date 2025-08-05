import os
import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.process_data.router import router as process_data_router
from app.services.database import get_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.getenv("CLICKHOUSE_URL") is not None:
        db = get_database()
        db.create_tables()
    else:
        warnings.warn("CLICKHOUSE_URL environment variable not set")
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(process_data_router)


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
