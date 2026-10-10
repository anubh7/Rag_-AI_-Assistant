"""
PDF loader — parses page-by-page with pypdf so very large files (3000+ pages)
can report incremental progress while loading instead of going silent until
the whole document is parsed. Produces the same Document-per-page shape
(and the same `page` / `source` metadata) as LangChain's PyPDFLoader.
"""
from typing import Callable, List, Optional

from langchain_core.documents import Document
from pypdf import PdfReader

# progress_cb(pages_done, pages_total) — invoked while parsing, at the
# cadence chosen by the caller (the loader itself calls it on every page).
ProgressCb = Optional[Callable[[int, int], None]]


def load_pdf(file_path: str, progress_cb: ProgressCb = None) -> List[Document]:
    reader = PdfReader(file_path)

    # Match PyPDFLoader behaviour: accept empty-password encrypted PDFs,
    # fail with a clear message otherwise. (pypdf returns 0 / NOT_DECRYPTED
    # when the password doesn't work.)
    if reader.is_encrypted and reader.decrypt("") == 0:
        raise ValueError(f"PDF '{file_path}' is encrypted with a non-empty password.")

    total = len(reader.pages)
    documents: List[Document] = []

    for page_index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        documents.append(
            Document(
                page_content=text,
                # Same metadata keys as langchain's PyPDFLoader ("page" is 0-based).
                metadata={"source": file_path, "page": page_index},
            )
        )
        if progress_cb is not None:
            progress_cb(page_index + 1, total)

    for doc in documents:
        doc.metadata["source"] = file_path
        doc.metadata["file_type"] = "pdf"

    return documents
