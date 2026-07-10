"""
Helper functions to build consistent API responses.
"""
from app.models.response import APIResponse
from app.constants import STATUS_SUCCESS, STATUS_ERROR


def success_response(message: str, data=None) -> APIResponse:
    return APIResponse(status=STATUS_SUCCESS, message=message, data=data)


def error_response(message: str, data=None) -> APIResponse:
    return APIResponse(status=STATUS_ERROR, message=message, data=data)
