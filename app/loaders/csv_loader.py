"""
CSV loader — uses LangChain's CSVLoader, one Document per row.
"""
from langchain_community.document_loaders import CSVLoader
from langchain_core.documents import Document
from typing import List


def load_csv(file_path: str) -> List[Document]:
    loader = CSVLoader(file_path=file_path)
    documents = loader.load()
    for doc in documents:
        doc.metadata["source"] = file_path
        doc.metadata["file_type"] = "csv"
    return documents
