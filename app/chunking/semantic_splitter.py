"""
Semantic chunking using LangChain Experimental's SemanticChunker,
which splits based on embedding-similarity breakpoints rather than fixed size.
"""
from langchain_core.documents import Document
from typing import List


def split_semantic(documents: List[Document], embedding_model) -> List[Document]:
    from langchain_experimental.text_splitter import SemanticChunker

    splitter = SemanticChunker(embedding_model)
    return splitter.split_documents(documents)
