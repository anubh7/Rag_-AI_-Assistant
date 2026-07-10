"""
File system helpers: saving uploads, validating extensions/size.
"""
import os
import shutil
from pathlib import Path
from fastapi import UploadFile

from app.config import settings
from app.constants import SUPPORTED_LOADERS
from app.utils.exceptions import UnsupportedFileTypeError, FileTooLargeError


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_file(file: UploadFile) -> str:
    ext = get_extension(file.filename)
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(f"'{ext}' is not supported.")
    return ext


def save_upload_file(file: UploadFile, sub_dir: str) -> str:
    """Saves an UploadFile to app/uploads/<sub_dir>/ and returns the saved path."""
    target_dir = os.path.join(settings.UPLOAD_DIR, sub_dir)
    os.makedirs(target_dir, exist_ok=True)
    dest_path = os.path.join(target_dir, file.filename)

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size_mb = os.path.getsize(dest_path) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        os.remove(dest_path)
        raise FileTooLargeError(f"File is {size_mb:.2f}MB, limit is {settings.MAX_FILE_SIZE_MB}MB.")

    return dest_path


def loader_key_for(ext: str) -> str:
    return SUPPORTED_LOADERS.get(ext, "text")
