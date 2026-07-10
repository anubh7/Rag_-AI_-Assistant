"""
Health router — basic liveness check.
"""
from fastapi import APIRouter
from app.utils.response import success_response

router = APIRouter()


@router.get("/")
def health_check():
    return success_response("Service is healthy.", data={"status": "ok"})
