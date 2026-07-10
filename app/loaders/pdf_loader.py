"""
PDF loader — uses LangChain's PyPDFLoader (wraps pypdf) to load pages as Documents.
"""
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from typing import List


def load_pdf(file_path: str) -> List[Document]:
    loader = PyPDFLoader(file_path)
    documents = loader.load()  # one Document per page, with page metadata
    for doc in documents:
        doc.metadata["source"] = file_path
        doc.metadata["file_type"] = "pdf"
    return documents
