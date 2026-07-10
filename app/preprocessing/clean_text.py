"""
Text cleaning utilities applied to raw Document page_content before chunking.
"""
import re
from langchain_core.documents import Document
from typing import List


def clean_string(text: str) -> str:
    text = re.sub(r"\s+", " ", text)          # collapse whitespace
    text = re.sub(r"\n{2,}", "\n", text)       # collapse blank lines
    text = text.strip()
    return text


def clean_documents(documents: List[Document]) -> List[Document]:
    for doc in documents:
        doc.page_content = clean_string(doc.page_content)
    return documents
