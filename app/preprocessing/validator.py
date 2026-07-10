"""
Validation checks applied to Documents before they proceed down the pipeline.
"""
from langchain_core.documents import Document
from typing import List


def filter_empty_documents(documents: List[Document]) -> List[Document]:
    return [doc for doc in documents if doc.page_content and doc.page_content.strip()]


def validate_documents(documents: List[Document]) -> List[Document]:
    if not documents:
        raise ValueError("No documents to process — file may be empty or unreadable.")
    documents = filter_empty_documents(documents)
    if not documents:
        raise ValueError("All extracted content was empty after cleaning.")
    return documents
