"""
Collection router (Controller) — manage Qdrant collections.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.models.collection_request import CollectionRequest
from app.services.collection_service import CollectionService
from app.dependencies import get_collection_service
from app.utils.response import success_response, error_response
from app.utils.exceptions import AppException

router = APIRouter()


@router.get("/")
def list_collections(service: CollectionService = Depends(get_collection_service)):
    return success_response("Collections fetched.", data=service.list_collections())


@router.post("/")
def create_collection(
    request: CollectionRequest,
    service: CollectionService = Depends(get_collection_service),
):
    try:
        result = service.create_collection(request.collection_name, request.vector_size)
        return success_response("Collection created.", data=result)
    except AppException as e:
        return JSONResponse(status_code=e.status_code, content=error_response(e.message).dict())


@router.delete("/{collection_name}")
def delete_collection(
    collection_name: str,
    service: CollectionService = Depends(get_collection_service),
):
    try:
        result = service.delete_collection(collection_name)
        return success_response("Collection deleted.", data=result)
    except AppException as e:
        return JSONResponse(status_code=e.status_code, content=error_response(e.message).dict())
