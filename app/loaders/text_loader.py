"""
Plain text loader — uses LangChain's TextLoader.
"""
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from typing import List


def load_text(file_path: str) -> List[Document]:
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    for doc in documents:
        doc.metadata["source"] = file_path
        doc.metadata["file_type"] = "text"
    return documents
