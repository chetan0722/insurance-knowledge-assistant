from pathlib import Path

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    convert_to_messages,
)

load_dotenv(override=True)

MODEL = "gpt-4.1-nano"
RETRIEVAL_K = 10

# IMPORTANT: Same database used during ingestion
DB_NAME = str(
    Path(__file__).parent.parent / "my_vector_db"
)

# Same embedding model used during ingestion
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large"
)

# Load the SAME Chroma collection
vectorstore = Chroma(
    collection_name="langchain",
    persist_directory=DB_NAME,
    embedding_function=embeddings,
)

print(
    f"Chroma collection loaded: "
    f"{vectorstore._collection.count()} documents"
)

llm = ChatOpenAI(
    temperature=0,
    model=MODEL,
)

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.

Use the provided context to answer the user's question.

Rules:
1. Use the context to answer the question.
2. Do not invent facts.
3. If the answer is present in the context, answer it directly.
4. If the answer is not present in the context, say you don't know.
5. Keep the answer relevant.

Context:
{context}
"""


def fetch_context(question: str) -> list[Document]:
    """Retrieve relevant documents from Chroma."""

    if not question or not question.strip():
        return []

    return vectorstore.similarity_search(
        question,
        k=RETRIEVAL_K,
    )


def combined_question(
    question: str,
    history: list[dict] | None = None,
) -> str:

    if history is None:
        history = []

    prior = "\n".join(
        message["content"]
        for message in history
        if message.get("role") == "user"
    )

    if prior:
        return prior + "\n" + question

    return question


def answer_question(
    question: str,
    history: list[dict] | None = None,
) -> tuple[str, list[Document]]:

    if history is None:
        history = []

    combined = combined_question(
        question,
        history,
    )

    docs = fetch_context(combined)

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    system_prompt = SYSTEM_PROMPT.format(
        context=context
    )

    messages = [
        SystemMessage(
            content=system_prompt
        )
    ]

    if history:
        messages.extend(
            convert_to_messages(history)
        )

    messages.append(
        HumanMessage(
            content=question
        )
    )

    response = llm.invoke(messages)

    return response.content, docs
