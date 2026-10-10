"""
Loader factory — picks the right LangChain loader based on file extension.
This is the "Filter" layer step that normalizes any file type into List[Document].
"""
from typing import List
from langchain_core.documents import Document

from app.loaders.pdf_loader import load_pdf
from app.loaders.csv_loader import load_csv
from app.loaders.excel_loader import load_excel
from app.loaders.word_loader import load_word
from app.loaders.text_loader import load_text
from app.utils.exceptions import UnsupportedFileTypeError

_LOADER_MAP = {
    "pdf": load_pdf,
    "csv": load_csv,
    "excel": load_excel,
    "word": load_word,
    "text": load_text,
}


def get_documents(file_path: str, loader_key: str, progress_cb=None) -> List[Document]:
    """
    Loads a file into Documents. `progress_cb(done, total)` is an optional
    progress hook forwarded to loaders that support incremental reporting
    (currently PDFs — critical for 3000+ page files).
    """
    loader_fn = _LOADER_MAP.get(loader_key)
    if not loader_fn:
        raise UnsupportedFileTypeError(f"No loader registered for '{loader_key}'.")
    if loader_key == "pdf":
        return load_pdf(file_path, progress_cb=progress_cb)
    return loader_fn(file_path)
