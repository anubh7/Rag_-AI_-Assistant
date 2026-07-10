"""
Excel loader — uses LangChain's UnstructuredExcelLoader (falls back to pandas if needed).
"""
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_core.documents import Document
from typing import List
import pandas as pd


def load_excel(file_path: str) -> List[Document]:
    try:
        loader = UnstructuredExcelLoader(file_path, mode="elements")
        documents = loader.load()
    except Exception:
        # Fallback: read sheets manually with pandas and build Documents
        documents = []
        sheets = pd.read_excel(file_path, sheet_name=None)
        for sheet_name, df in sheets.items():
            content = df.to_string(index=False)
            documents.append(
                Document(page_content=content, metadata={"sheet": sheet_name})
            )

    for doc in documents:
        doc.metadata["source"] = file_path
        doc.metadata["file_type"] = "excel"
    return documents
