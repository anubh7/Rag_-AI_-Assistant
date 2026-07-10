"""
Prompt template for RAG-grounded answers, built with LangChain's ChatPromptTemplate.
"""
from langchain_core.prompts import ChatPromptTemplate
from app.prompts.system_prompt import SYSTEM_PROMPT

RAG_SYSTEM_INSTRUCTIONS = (
    SYSTEM_PROMPT
    + "\n\nUse ONLY the provided context to answer the user's question. "
    "If the answer isn't contained in the context, say you don't have enough "
    "information — do not make things up. Cite which part of the context you "
    "used when helpful."
)

rag_prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", RAG_SYSTEM_INSTRUCTIONS),
        ("human", "Context:\n{context}\n\nQuestion:\n{question}"),
    ]
)


def build_rag_prompt(context: str, question: str):
    return rag_prompt_template.format_messages(context=context, question=question)
