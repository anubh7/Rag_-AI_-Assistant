"""
Prompt template for general (non-RAG) chat, when use_rag=False.
"""
from langchain_core.prompts import ChatPromptTemplate
from app.prompts.system_prompt import SYSTEM_PROMPT

general_prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ]
)


def build_general_prompt(question: str):
    return general_prompt_template.format_messages(question=question)
