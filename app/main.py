"""
App entrypoint — wires up FastAPI, routers, and global exception handling.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import upload, chat, models, collection, health
from app.utils.exceptions import AppException
from app.utils.response import error_response


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)


# CORS configuration for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.message).dict()
    )


app.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)

app.include_router(
    upload.router,
    prefix="/upload",
    tags=["Upload"]
)

app.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)

app.include_router(
    models.router,
    prefix="/models",
    tags=["Models"]
)

app.include_router(
    collection.router,
    prefix="/collection",
    tags=["Collection"]
)