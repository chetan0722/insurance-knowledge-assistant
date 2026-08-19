import os
import glob

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from langchain_openai import OpenAIEmbeddings

from langchain_chroma import Chroma


# Load documents
folders = glob.glob("knowledge-base/*")

documents = []

for folder in folders:

    doc_type = os.path.basename(folder)

    loader = DirectoryLoader(
        folder,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={
            "encoding": "utf-8"
        },
    )

    folder_docs = loader.load()

    for doc in folder_docs:
        doc.metadata["doc_type"] = doc_type
        documents.append(doc)


print("Documents:", len(documents))


# Split documents
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=200,
)

chunks = text_splitter.split_documents(
    documents
)

print("Chunks:", len(chunks))


# Embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large"
)


# ONE database path
db_name = "./my_vector_db"


# Delete old database
if os.path.exists(db_name):

    existing_db = Chroma(
        collection_name="langchain",
        persist_directory=db_name,
        embedding_function=embeddings,
    )

    existing_db.delete_collection()


# Create new database
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="langchain",
    persist_directory=db_name,
)

print(
    "Vector DB documents:",
    vectorstore._collection.count()
)