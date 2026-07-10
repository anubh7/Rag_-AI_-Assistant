"""
Word (.docx) loader — uses LangChain's Docx2txtLoader.
"""
from langchain_community.document_loaders import Docx2txtLoader
from langchain_core.documents import Document
from typing import List


def load_word(file_path: str) -> List[Document]:
    loader = Docx2txtLoader(file_path)
    documents = loader.load()
    for doc in documents:
        doc.metadata["source"] = file_path
        doc.metadata["file_type"] = "word"
    return documents
