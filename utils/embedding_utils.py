import json
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma
from chromadb.api.types import EmbeddingFunction
import os


chromaDB_persist_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "../databases/recipes"))
# print(chromaDB_persist_directory)
# import chromadb
# print(os.path.exists(chromaDB_persist_directory))
# client = chromadb.PersistentClient(path=chromaDB_persist_directory)  # or HttpClient()
# print(client.count_collections()," ---------")
# col = client.get_collection("recipes")
# print(col.count())
# print(col)
embeddings = SentenceTransformer('BAAI/bge-small-en-v1.5')

class MyEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model: SentenceTransformer):
        self.model = model

    def embed_query(self, text: str) -> list:
        return self.model.encode(text, convert_to_tensor=True).tolist()

custom_embeddings = MyEmbeddingFunction(embeddings)

vector_store = Chroma(
    collection_name="recipes",
    embedding_function=custom_embeddings,
    persist_directory=chromaDB_persist_directory,
)

retriever = vector_store.as_retriever(search_kwargs={"k": 1})
# print("Retriever initialized",retriever.invoke("pizza"))
